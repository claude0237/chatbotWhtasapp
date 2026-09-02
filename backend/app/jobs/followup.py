"""Background job: follow-up inactive bot conversations and close them after max retries."""
import asyncio
import logging
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.bot.models import BotConversationState, BotConfiguration
from app.bot.repositories import BotConversationStateRepository, BotConfigurationRepository
from app.conversations.models import Conversation, ConversationStatus
from app.whatsapp.services import WhatsAppService
from app.logging_config import log_with_context, log_trace

logger = logging.getLogger("app.jobs")

_POLL_INTERVAL_SECONDS = 60


async def _process_stale_states(db: AsyncSession) -> None:
    """Scan all active bot states and send follow-ups or close conversations."""

    # Load all active states with their scenario eager-loaded
    result = await db.execute(
        select(BotConversationState).options(selectinload(BotConversationState.scenario))
    )
    states: list[BotConversationState] = list(result.scalars().all())

    log_trace(
        "FOLLOWUP_JOB_SCAN_STARTED",
        state_count=len(states)
    )

    if not states:
        return

    now = datetime.utcnow()
    config_cache: dict = {}

    for state in states:
        # Load bot config (cached per company)
        company_id = state.company_id
        if company_id not in config_cache:
            config_repo = BotConfigurationRepository(db)
            config = await config_repo.get_by_company_id(company_id)
            config_cache[company_id] = config
        config: BotConfiguration | None = config_cache.get(company_id)

        if not config:
            continue

        timeout_minutes = config.followup_timeout_minutes or 60
        max_retries = config.followup_max_retries or 3

        # Check if the state has been idle longer than the timeout
        last_activity = state.updated_at or state.created_at
        idle_minutes = (now - last_activity).total_seconds() / 60

        log_trace(
            "FOLLOWUP_JOB_STATE_EVAL",
            phone_number=state.phone_number,
            company_id=str(company_id),
            retry_count=state.retry_count,
            max_retries=max_retries,
            idle_minutes=round(idle_minutes, 2),
            timeout_minutes=timeout_minutes,
        )

        if idle_minutes < timeout_minutes:
            continue  # Still within timeout window

        # ── Max retries reached → close conversation ──────────────────────
        if state.retry_count >= max_retries:
            log_with_context(
                logger,
                logging.INFO,
                "FOLLOWUP_MAX_RETRIES_REACHED",
                phone_number=state.phone_number,
                retry_count=state.retry_count,
                company_id=str(company_id)
            )
            log_trace(
                "FOLLOWUP_CLOSE_TRIGGERED",
                phone_number=state.phone_number,
                company_id=str(company_id),
                retry_count=state.retry_count,
                max_retries=max_retries,
                reason="no_customer_response_after_max_retries",
            )
            # Find the conversation via the customer phone number
            from app.customers.models import Customer
            cust_result = await db.execute(
                select(Customer).where(
                    and_(
                        Customer.company_id == company_id,
                        Customer.phone_number == state.phone_number,
                    )
                )
            )
            customer = cust_result.scalar_one_or_none()
            closed_conversation_id = None
            if customer:
                conv_result2 = await db.execute(
                    select(Conversation).where(
                        and_(
                            Conversation.company_id == company_id,
                            Conversation.customer_id == customer.id,
                            Conversation.status.in_([
                                ConversationStatus.AI,
                                ConversationStatus.OPEN,
                                ConversationStatus.WAITING,
                            ]),
                        )
                    ).order_by(Conversation.last_activity_at.desc()).limit(1)
                )
                conv = conv_result2.scalar_one_or_none()
                if conv:
                    # Optionally send closing message before closing
                    closing = config.closing_message or "Merci pour votre temps. La conversation est clôturée."
                    if closing:
                        try:
                            wa_service = WhatsAppService(db)
                            await wa_service.send_text_message(
                                company_id=company_id,
                                phone_number=state.phone_number,
                                content=closing,
                            )
                            log_trace(
                                "FOLLOWUP_CLOSING_MESSAGE_SENT",
                                phone_number=state.phone_number,
                                company_id=str(company_id),
                                conversation_id=str(conv.id),
                            )
                        except Exception as exc:
                            log_trace(
                                "FOLLOWUP_CLOSING_MESSAGE_FAILED",
                                phone_number=state.phone_number,
                                company_id=str(company_id),
                                conversation_id=str(conv.id),
                                error=str(exc),
                            )

                    conv.status = ConversationStatus.CLOSED
                    conv.closed_at = now
                    conv.updated_at = now
                    await db.commit()
                    closed_conversation_id = str(conv.id)
                    logger.info(f"[followup] Conversation {conv.id} closed.")
                    log_trace(
                        "FOLLOWUP_CONVERSATION_CLOSED",
                        phone_number=state.phone_number,
                        company_id=str(company_id),
                        conversation_id=closed_conversation_id,
                        retry_count=state.retry_count,
                    )

            # Delete the bot state
            state_repo = BotConversationStateRepository(db)
            await state_repo.delete(state)
            continue

        # ── Send follow-up ────────────────────────────────────────────────
        last_message = state.last_bot_message
        if not last_message:
            # No stored message to resend → just increment
            state.retry_count = (state.retry_count or 0) + 1
            state.updated_at = now
            await db.commit()
            continue

        log_with_context(
            logger,
            logging.INFO,
            "FOLLOWUP_SENDING_RETRY",
            phone_number=state.phone_number,
            retry_count=state.retry_count + 1,
            max_retries=max_retries,
            company_id=str(company_id)
        )
        log_trace(
            "FOLLOWUP_SENDING",
            phone_number=state.phone_number,
            company_id=str(company_id),
            retry=state.retry_count + 1,
            max_retries=max_retries,
            message_preview=last_message[:80] if last_message else None,
        )
        try:
            wa_service = WhatsAppService(db)
            await wa_service.send_text_message(
                company_id=company_id,
                phone_number=state.phone_number,
                content=last_message,
            )
            log_with_context(
                logger,
                logging.INFO,
                "FOLLOWUP_SENT",
                phone_number=state.phone_number,
                company_id=str(company_id)
            )
            log_trace(
                "FOLLOWUP_SENT_SUCCESS",
                phone_number=state.phone_number,
                company_id=str(company_id),
                retry=state.retry_count + 1,
                max_retries=max_retries,
            )
        except Exception as exc:
            log_with_context(
                logger,
                logging.ERROR,
                "FOLLOWUP_SEND_FAILED",
                phone_number=state.phone_number,
                company_id=str(company_id),
                error_message=str(exc),
                exc_info=True
            )
            log_trace(
                "FOLLOWUP_SEND_ERROR",
                phone_number=state.phone_number,
                company_id=str(company_id),
                retry=state.retry_count + 1,
                error=str(exc),
            )
            logger.warning(f"[followup] Failed to send follow-up to {state.phone_number}: {exc}")

        state.retry_count = (state.retry_count or 0) + 1
        state.updated_at = now
        await db.commit()

    log_trace("FOLLOWUP_JOB_SCAN_FINISHED")


async def run_followup_job() -> None:
    """Infinite loop: poll every POLL_INTERVAL_SECONDS."""
    logger.info("[followup] Background job started.")
    while True:
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
        try:
            async with AsyncSessionLocal() as db:
                await _process_stale_states(db)
        except Exception as exc:
            logger.error(f"[followup] Job error: {exc}", exc_info=True)
