"""Background job: follow-up inactive bot conversations and close them after max retries."""
import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.bot.models import BotConversationState, BotConfiguration
from app.bot.repositories import BotConversationStateRepository, BotConfigurationRepository
from app.conversations.models import Conversation, ConversationStatus
from app.whatsapp.services import WhatsAppService

logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 60


async def _process_stale_states(db: AsyncSession) -> None:
    """Scan all active bot states and send follow-ups or close conversations."""

    # Load all active states with their scenario eager-loaded
    result = await db.execute(
        select(BotConversationState).options(selectinload(BotConversationState.scenario))
    )
    states: list[BotConversationState] = list(result.scalars().all())

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

        if idle_minutes < timeout_minutes:
            continue  # Still within timeout window

        # ── Max retries reached → close conversation ──────────────────────
        if state.retry_count >= max_retries:
            logger.info(
                f"[followup] Closing conversation for {state.phone_number} "
                f"after {state.retry_count} retries without response."
            )
            # Find open conversation and close it
            conv_result = await db.execute(
                select(Conversation).where(
                    and_(
                        Conversation.company_id == company_id,
                        Conversation.customer_id.in_(
                            select(Conversation.customer_id).where(
                                Conversation.company_id == company_id
                            )
                        ),
                    )
                ).limit(1)
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
                    conv.status = ConversationStatus.CLOSED
                    conv.closed_at = now
                    conv.updated_at = now
                    await db.commit()
                    logger.info(f"[followup] Conversation {conv.id} closed.")

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

        logger.info(
            f"[followup] Sending retry {state.retry_count + 1}/{max_retries} "
            f"to {state.phone_number}"
        )
        try:
            wa_service = WhatsAppService(db)
            await wa_service.send_text_message(
                company_id=company_id,
                phone_number=state.phone_number,
                content=last_message,
            )
        except Exception as exc:
            logger.warning(f"[followup] Failed to send follow-up to {state.phone_number}: {exc}")

        state.retry_count = (state.retry_count or 0) + 1
        state.updated_at = now
        await db.commit()


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
