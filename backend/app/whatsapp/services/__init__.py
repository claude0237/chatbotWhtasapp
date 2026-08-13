"""WhatsApp Service"""
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import httpx
import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.config import settings
from app.whatsapp.models import WhatsAppMessage, WhatsAppTemplate, WebhookEvent, MessageDirection, MessageStatus, MessageType
from app.whatsapp.repositories import WhatsAppMessageRepository, WhatsAppTemplateRepository, WebhookEventRepository
from app.channels.repositories import ChannelRepository, ChannelConfigurationRepository, ChannelCredentialRepository
from app.channels.models import ChannelType
from app.utils.encryption import decrypt_credential
from app.bot.engine import BotEngine, HANDOFF_PREFIX
from app.bot.repositories import BotConversationStateRepository
from app.conversations.repositories import CustomerRepository, ConversationRepository, MessageRepository
from app.conversations.models import Conversation, Message, ConversationStatus, SenderType, ConversationMessageType, ConversationMessageStatus
from app.logging_config import log_whatsapp, log_with_context


class WhatsAppService:
    """Service for WhatsApp operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.message_repository = WhatsAppMessageRepository(db)
        self.template_repository = WhatsAppTemplateRepository(db)
        self.webhook_repository = WebhookEventRepository(db)
        self.channel_repository = ChannelRepository(db)
        self.channel_config_repository = ChannelConfigurationRepository(db)
        self.channel_credential_repository = ChannelCredentialRepository(db)
        self.base_url = f"https://graph.facebook.com/{settings.whatsapp_api_version}"

    async def _get_company_credentials(self, company_id: UUID) -> dict:
        """Fetch ALL WhatsApp credentials for a specific company from ChannelCredential table"""
        channel = await self.channel_repository.get_by_type(company_id, ChannelType.WHATSAPP)
        if not channel:
            log_whatsapp(
                logger,
                logging.ERROR,
                "WHATSAPP_CREDENTIALS_INVALID",
                company_id=str(company_id),
                reason="No WhatsApp channel configured"
            )
            raise ValueError(f"No WhatsApp channel configured for company {company_id}")

        configs = await self.channel_config_repository.get_by_channel_id(channel.id)
        config_map = {c.key: c.value for c in configs}

        credentials = await self.channel_credential_repository.get_by_channel_id(channel.id)
        cred_map = {c.credential_type: c.encrypted_value for c in credentials}

        # Get configuration values
        meta_app_id = config_map.get("meta_app_id")
        meta_business_id = config_map.get("meta_business_id")
        phone_number_id = config_map.get("phone_number_id")
        webhook_verify_token = config_map.get("webhook_verify_token")

        # Decrypt credentials
        raw_app_secret = cred_map.get("META_APP_SECRET")
        raw_token = cred_map.get("ACCESS_TOKEN")
        
        app_secret = None
        if raw_app_secret:
            try:
                app_secret = decrypt_credential(raw_app_secret)
            except ValueError:
                app_secret = raw_app_secret
        
        access_token = None
        if raw_token:
            try:
                access_token = decrypt_credential(raw_token)
            except ValueError:
                access_token = raw_token

        if not phone_number_id:
            log_whatsapp(
                logger,
                logging.ERROR,
                "WHATSAPP_CREDENTIALS_INVALID",
                company_id=str(company_id),
                reason="phone_number_id not configured"
            )
            raise ValueError(f"WhatsApp phone_number_id not configured for company {company_id}")
        if not access_token:
            log_whatsapp(
                logger,
                logging.ERROR,
                "WHATSAPP_CREDENTIALS_INVALID",
                company_id=str(company_id),
                reason="access_token not configured"
            )
            raise ValueError(f"WhatsApp access_token not configured for company {company_id}")

        return {
            "meta_app_id": meta_app_id,
            "meta_app_secret": app_secret,
            "meta_business_id": meta_business_id,
            "phone_number_id": phone_number_id,
            "access_token": access_token,
            "webhook_verify_token": webhook_verify_token
        }
    
    async def send_text_message(
        self,
        company_id: UUID,
        phone_number: str,
        content: str,
        display_name: Optional[str] = None
    ) -> WhatsAppMessage:
        """Send a text message via WhatsApp API"""
        creds = await self._get_company_credentials(company_id)
        # Create message record
        message = WhatsAppMessage(
            company_id=company_id,
            message_id=f"temp_{datetime.utcnow().timestamp()}",
            direction=MessageDirection.OUTGOING,
            status=MessageStatus.PENDING,
            message_type=MessageType.TEXT,
            phone_number=phone_number,
            display_name=display_name,
            content=content
        )
        
        # Save to database
        message = await self.message_repository.create(message)
        
        # Send via WhatsApp API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{creds['phone_number_id']}/messages",
                    headers={
                        "Authorization": f"Bearer {creds['access_token']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": phone_number,
                        "type": "text",
                        "text": {"body": content}
                    }
                )
                
                logger.info(f"WhatsApp API response status: {response.status_code}")
                logger.info(f"WhatsApp API response body: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    whatsapp_message_id = data.get("messages", [{}])[0].get("id")
                    
                    # Update message with WhatsApp ID
                    message.message_id = whatsapp_message_id
                    message.status = MessageStatus.SENT
                    message.sent_at = datetime.utcnow()
                    await self.message_repository.update(message)
                    
                    log_whatsapp(
                        logger,
                        logging.INFO,
                        "WHATSAPP_SEND_SUCCESS",
                        company_id=str(company_id),
                        phone_number=phone_number,
                        message_id=whatsapp_message_id,
                        status_code=response.status_code
                    )
                else:
                    logger.warning(f"Meta API send_text error {response.status_code}: {response.text}")
                    message.status = MessageStatus.FAILED
                    await self.message_repository.update(message)
                    
                    log_whatsapp(
                        logger,
                        logging.ERROR,
                        "WHATSAPP_API_ERROR",
                        company_id=str(company_id),
                        phone_number=phone_number,
                        status_code=response.status_code,
                        error_message=response.text
                    )
                    
        except Exception as e:
            error_msg = str(e) if str(e) else f"{type(e).__name__}"
            logger.error(f"WhatsApp send_text exception: {error_msg}", exc_info=True)
            message.status = MessageStatus.FAILED
            await self.message_repository.update(message)
            
            log_whatsapp(
                logger,
                logging.ERROR,
                "WHATSAPP_SEND_FAILED",
                company_id=str(company_id),
                phone_number=phone_number,
                error_message=error_msg,
                error_type=type(e).__name__,
                exc_info=True
            )
            raise e
        
        return message
    
    async def send_template_message(
        self,
        company_id: UUID,
        phone_number: str,
        template_name: str,
        components: Optional[Dict[str, Any]] = None,
        display_name: Optional[str] = None
    ) -> WhatsAppMessage:
        """Send a template message via WhatsApp API"""
        creds = await self._get_company_credentials(company_id)
        # Get template
        template = await self.template_repository.get_by_name(company_id, template_name)
        if not template:
            log_whatsapp(
                logger,
                logging.ERROR,
                "WHATSAPP_TEMPLATE_NOT_FOUND",
                company_id=str(company_id),
                template_name=template_name
            )
            raise ValueError(f"Template {template_name} not found")
        
        # Create message record
        message = WhatsAppMessage(
            company_id=company_id,
            message_id=f"temp_{datetime.utcnow().timestamp()}",
            direction=MessageDirection.OUTGOING,
            status=MessageStatus.PENDING,
            message_type=MessageType.TEMPLATE,
            phone_number=phone_number,
            display_name=display_name,
            template_name=template_name,
            extra_data=components
        )
        
        # Save to database
        message = await self.message_repository.create(message)
        
        # Send via WhatsApp API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{creds['phone_number_id']}/messages",
                    headers={
                        "Authorization": f"Bearer {creds['access_token']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": phone_number,
                        "type": "template",
                        "template": {
                            "name": template_name,
                            "language": {"code": template.language},
                            "components": components or template.components
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    whatsapp_message_id = data.get("messages", [{}])[0].get("id")
                    
                    # Update message with WhatsApp ID
                    message.message_id = whatsapp_message_id
                    message.status = MessageStatus.SENT
                    message.sent_at = datetime.utcnow()
                    await self.message_repository.update(message)
                else:
                    message.status = MessageStatus.FAILED
                    await self.message_repository.update(message)
                    
        except Exception as e:
            message.status = MessageStatus.FAILED
            await self.message_repository.update(message)
            raise e
        
        return message
    
    async def receive_webhook(self, payload: Dict[str, Any], company_id: UUID) -> WebhookEvent:
        """Process incoming webhook event"""
        import logging
        _log = logging.getLogger(__name__)
        
        # Log webhook received
        entry_count = len(payload.get("entry", []))
        log_whatsapp(
            logger,
            logging.INFO,
            "WHATSAPP_WEBHOOK_RECEIVED",
            company_id=str(company_id),
            event_type=payload.get("entry", [{}])[0].get("changes", [{}])[0].get("field", "unknown"),
            entry_count=entry_count
        )
        
        # Create webhook event record
        event = WebhookEvent(
            company_id=company_id,
            event_type=payload.get("entry", [{}])[0].get("changes", [{}])[0].get("field", "unknown"),
            payload=payload
        )
        
        # Save to database
        event = await self.webhook_repository.create(event)
        
        # Process the webhook
        try:
            await self._process_webhook_payload(payload, company_id)
            await self.webhook_repository.mark_as_processed(event.id)
        except Exception as e:
            _log.error(f"Webhook processing FAILED: {type(e).__name__}: {e}", exc_info=True)
            await self.webhook_repository.mark_as_failed(event.id, str(e))
            
            log_whatsapp(
                logger,
                logging.ERROR,
                "WHATSAPP_WEBHOOK_PROCESSING_FAILED",
                company_id=str(company_id),
                webhook_id=str(event.id),
                error_message=str(e),
                exc_info=True
            )
            raise e
        
        return event
    
    async def _process_webhook_payload(self, payload: Dict[str, Any], company_id: UUID):
        """Process webhook payload and create message records"""
        customer_repo = CustomerRepository(self.db)
        conversation_repo = ConversationRepository(self.db)
        message_repo = MessageRepository(self.db)

        entry = payload.get("entry", [])
        for entry_item in entry:
            changes = entry_item.get("changes", [])
            for change in changes:
                field = change.get("field")
                
                if field == "messages":
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    
                    import logging as _logging
                    _wlog = _logging.getLogger(__name__)
                    _wlog.info(f"Processing {len(messages)} incoming message(s)")
                    for msg in messages:
                        # Check if message already exists
                        existing = await self.message_repository.get_by_whatsapp_id(msg.get("id"))
                        if existing:
                            _wlog.info(f"Message {msg.get('id')} already exists, skipping")
                            continue
                        
                        # Extract message data
                        phone_from = msg.get("from")
                        msg_text = msg.get("text", {}).get("body", "")
                        display_name = value.get("contacts", [{}])[0].get("profile", {}).get("name")

                        # ── Save raw WhatsApp message ──
                        wa_message = WhatsAppMessage(
                            company_id=company_id,
                            message_id=msg.get("id"),
                            direction=MessageDirection.INCOMING,
                            status=MessageStatus.DELIVERED,
                            message_type=MessageType.TEXT,
                            phone_number=phone_from,
                            display_name=display_name,
                            content=msg_text,
                            sent_at=datetime.utcfromtimestamp(int(msg.get("timestamp", 0))),
                            created_at=datetime.utcnow()
                        )
                        await self.message_repository.create(wa_message)

                        # ── Get or create Customer ──
                        customer = await customer_repo.get_or_create(
                            company_id=company_id,
                            phone_number=phone_from,
                            name=display_name,
                        )

                        # ── Get or create Conversation ──
                        state_repo = BotConversationStateRepository(self.db)
                        existing_convs = await conversation_repo.get_by_customer_id(customer.id)
                        open_conv = next(
                            (c for c in existing_convs if c.status not in (ConversationStatus.CLOSED, ConversationStatus.ARCHIVED)),
                            None
                        )

                        # Human in control = agent has taken over manually
                        human_in_control = open_conv and open_conv.status in (
                            ConversationStatus.AGENT, ConversationStatus.WAITING
                        )

                        # If human is in control, clear any lingering bot scenario state
                        # so the bot starts fresh if control is returned to AI later
                        if human_in_control:
                            orphan = await state_repo.get_active(company_id, phone_from)
                            if orphan:
                                await state_repo.delete(orphan)

                        # If no open conv (was CLOSED/ARCHIVED), also clear orphan scenario state
                        if not open_conv:
                            orphan = await state_repo.get_active(company_id, phone_from)
                            if orphan:
                                await state_repo.delete(orphan)

                        is_new_conversation = not open_conv

                        # ── Check business hours ──
                        from app.bot.utils import is_within_business_hours, interpolate_message
                        from app.bot.repositories import BotConfigurationRepository as _BotCfgRepo
                        _bot_cfg_repo = _BotCfgRepo(self.db)
                        _bot_cfg = await _bot_cfg_repo.get_by_company_id(company_id)
                        _is_open = is_within_business_hours(
                            _bot_cfg.business_hours if _bot_cfg else None,
                            _bot_cfg.timezone if _bot_cfg else "UTC"
                        )

                        # ── BotEngine: generate automatic reply (only if no human involved) ──
                        # On first contact, skip the engine — welcome message is sent below
                        # and the bot waits for the client's next message.
                        bot_reply = None
                        if msg_text and not human_in_control and not is_new_conversation:
                            if not _is_open and _bot_cfg and _bot_cfg.away_message:
                                # Outside business hours → send away message
                                bot_reply = interpolate_message(_bot_cfg.away_message, _bot_cfg.timezone if _bot_cfg else "UTC")
                            else:
                                try:
                                    bot_engine = BotEngine(self.db)
                                    bot_reply = await bot_engine.process(
                                        company_id=company_id,
                                        phone_number=phone_from,
                                        message_text=msg_text,
                                    )
                                    # If BotEngine returns None (scenario finished without message),
                                    # don't send any reply - let the client continue the conversation
                                except Exception as e:
                                    _wlog.error(
                                        f"BotEngine.process crashed for company {company_id}, "
                                        f"phone {phone_from}: {e}",
                                        exc_info=True,
                                    )
                                    bot_reply = (
                                        _bot_cfg.unknown_message
                                        if _bot_cfg and _bot_cfg.unknown_message
                                        else "Désolé, une erreur est survenue. Un conseiller va vous répondre sous peu."
                                    )

                        # Detect handoff signal from bot engine
                        is_handoff = bool(bot_reply and bot_reply.startswith(HANDOFF_PREFIX))
                        if is_handoff:
                            bot_reply = bot_reply[len(HANDOFF_PREFIX):]

                        # Determine target conv status
                        if is_handoff:
                            target_status = ConversationStatus.WAITING
                        elif bot_reply:
                            target_status = ConversationStatus.AI
                        else:
                            target_status = ConversationStatus.OPEN

                        if open_conv:
                            open_conv.last_activity_at = datetime.utcnow()
                            if not human_in_control:
                                open_conv.status = target_status
                            # AGENT / WAITING → status unchanged, human keeps control
                            await conversation_repo.update(open_conv)
                            conversation = open_conv
                        else:
                            # No open conv (was CLOSED/ARCHIVED or brand new customer)
                            channel = await self.channel_repository.get_by_type(company_id, ChannelType.WHATSAPP)
                            conversation = Conversation(
                                company_id=company_id,
                                customer_id=customer.id,
                                channel_id=channel.id if channel else None,
                                status=target_status,
                            )
                            await conversation_repo.create(conversation)

                        # ── Create Message linked to Conversation ──
                        conv_message = Message(
                            conversation_id=conversation.id,
                            sender_type=SenderType.CUSTOMER,
                            sender_id=customer.id,
                            content=msg_text,
                            message_type=ConversationMessageType.TEXT,
                            external_message_id=msg.get("id"),
                            status=ConversationMessageStatus.DELIVERED,
                            sent_at=datetime.utcfromtimestamp(int(msg.get("timestamp", 0))),
                        )
                        await message_repo.create(conv_message)

                        # ── Send welcome message on new/re-opened conversation ──
                        # If outside business hours, send away_message instead
                        if is_new_conversation and not human_in_control:
                            bot_config = _bot_cfg  # Already fetched above
                            _tz = bot_config.timezone if bot_config else "UTC"
                            if not _is_open and bot_config and bot_config.away_message:
                                welcome = interpolate_message(bot_config.away_message, _tz)
                            else:
                                welcome = interpolate_message(bot_config.welcome_message, _tz) if bot_config else None
                            if welcome:
                                welcome_sent = False
                                welcome_wa_id = None
                                try:
                                    wm = await self.send_text_message(
                                        company_id=company_id,
                                        phone_number=phone_from,
                                        content=welcome,
                                    )
                                    welcome_sent = True
                                    if wm and wm.message_id and not wm.message_id.startswith("temp_"):
                                        welcome_wa_id = wm.message_id
                                except Exception as e:
                                    _wlog.warning(f"Welcome message dispatch failed: {e}")
                                welcome_msg = Message(
                                    conversation_id=conversation.id,
                                    sender_type=SenderType.BOT,
                                    content=welcome,
                                    message_type=ConversationMessageType.TEXT,
                                    status=ConversationMessageStatus.SENT if welcome_sent else ConversationMessageStatus.FAILED,
                                    sent_at=datetime.utcnow(),
                                    external_message_id=welcome_wa_id,
                                )
                                await message_repo.create(welcome_msg)

                        # ── Send bot reply if any ──
                        if bot_reply:
                            import logging
                            _log = logging.getLogger(__name__)
                            bot_sent = False
                            wa_msg_id = None
                            try:
                                wa_msg = await self.send_text_message(
                                    company_id=company_id,
                                    phone_number=phone_from,
                                    content=bot_reply,
                                )
                                bot_sent = True
                                if wa_msg and wa_msg.message_id and not wa_msg.message_id.startswith("temp_"):
                                    wa_msg_id = wa_msg.message_id
                            except Exception as e:
                                _log.warning(f"Bot reply WhatsApp dispatch failed: {e}")
                            bot_msg = Message(
                                conversation_id=conversation.id,
                                sender_type=SenderType.BOT,
                                content=bot_reply,
                                message_type=ConversationMessageType.TEXT,
                                status=ConversationMessageStatus.SENT if bot_sent else ConversationMessageStatus.FAILED,
                                sent_at=datetime.utcnow(),
                                external_message_id=wa_msg_id,
                            )
                            await message_repo.create(bot_msg)
                
                elif field == "message_status":
                    value = change.get("value", {})
                    statuses = value.get("statuses", [])
                    
                    conv_msg_repo = MessageRepository(self.db)
                    for status in statuses:
                        whatsapp_message_id = status.get("id")
                        status_type = status.get("status")
                        ts = status.get("timestamp")
                        ts_dt = datetime.utcfromtimestamp(ts) if ts else datetime.utcnow()

                        # Update WhatsApp message record
                        message = await self.message_repository.get_by_whatsapp_id(whatsapp_message_id)
                        if message:
                            if status_type == "sent":
                                message.status = MessageStatus.SENT
                                message.sent_at = ts_dt
                            elif status_type == "delivered":
                                message.status = MessageStatus.DELIVERED
                                message.delivered_at = ts_dt
                            elif status_type == "read":
                                message.status = MessageStatus.READ
                                message.read_at = ts_dt
                            elif status_type == "failed":
                                message.status = MessageStatus.FAILED
                            await self.message_repository.update(message)

                        # Propagate to conversation Message via external_message_id
                        conv_msg = await conv_msg_repo.get_by_external_id(whatsapp_message_id)
                        if conv_msg:
                            if status_type == "sent":
                                conv_msg.status = ConversationMessageStatus.SENT
                                conv_msg.sent_at = ts_dt
                            elif status_type == "delivered":
                                conv_msg.status = ConversationMessageStatus.DELIVERED
                                conv_msg.delivered_at = ts_dt
                            elif status_type == "read":
                                conv_msg.status = ConversationMessageStatus.READ
                                conv_msg.read_at = ts_dt
                            elif status_type == "failed":
                                conv_msg.status = ConversationMessageStatus.FAILED
                            await conv_msg_repo.update(conv_msg)
    
    async def get_messages(
        self,
        company_id: UUID,
        phone_number: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ):
        """Get messages for a company"""
        if phone_number:
            return await self.message_repository.get_by_phone_number(company_id, phone_number, skip, limit)
        return await self.message_repository.get_by_company_id(company_id, skip, limit)
    
    async def create_template(
        self,
        company_id: UUID,
        name: str,
        category: str,
        language: str,
        components: Dict[str, Any]
    ) -> WhatsAppTemplate:
        """Create a new template"""
        template = WhatsAppTemplate(
            company_id=company_id,
            name=name,
            category=category,
            language=language,
            components=components
        )
        
        return await self.template_repository.create(template)
    
    async def get_templates(self, company_id: UUID, skip: int = 0, limit: int = 100):
        """Get templates for a company"""
        return await self.template_repository.get_by_company_id(company_id, skip, limit)
    
    async def get_active_templates(self, company_id: UUID):
        """Get active templates for a company"""
        return await self.template_repository.get_active_templates(company_id)
    
    async def send_image_message(
        self,
        company_id: UUID,
        phone_number: str,
        image_url: str,
        caption: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> WhatsAppMessage:
        """Send an image message via WhatsApp API"""
        message = WhatsAppMessage(
            company_id=company_id,
            message_id=f"temp_{datetime.utcnow().timestamp()}",
            direction=MessageDirection.OUTGOING,
            status=MessageStatus.PENDING,
            message_type=MessageType.IMAGE,
            phone_number=phone_number,
            display_name=display_name,
            media_url=image_url,
            content=caption
        )
        
        message = await self.message_repository.create(message)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{settings.whatsapp_phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {settings.whatsapp_access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": phone_number,
                        "type": "image",
                        "image": {
                            "link": image_url,
                            "caption": caption
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    whatsapp_message_id = data.get("messages", [{}])[0].get("id")
                    message.message_id = whatsapp_message_id
                    message.status = MessageStatus.SENT
                    message.sent_at = datetime.utcnow()
                    await self.message_repository.update(message)
                else:
                    message.status = MessageStatus.FAILED
                    await self.message_repository.update(message)
                    
        except Exception as e:
            message.status = MessageStatus.FAILED
            await self.message_repository.update(message)
            raise e
        
        return message
    
    async def send_video_message(
        self,
        company_id: UUID,
        phone_number: str,
        video_url: str,
        caption: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> WhatsAppMessage:
        """Send a video message via WhatsApp API"""
        message = WhatsAppMessage(
            company_id=company_id,
            message_id=f"temp_{datetime.utcnow().timestamp()}",
            direction=MessageDirection.OUTGOING,
            status=MessageStatus.PENDING,
            message_type=MessageType.VIDEO,
            phone_number=phone_number,
            display_name=display_name,
            media_url=video_url,
            content=caption
        )
        
        message = await self.message_repository.create(message)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{settings.whatsapp_phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {settings.whatsapp_access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": phone_number,
                        "type": "video",
                        "video": {
                            "link": video_url,
                            "caption": caption
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    whatsapp_message_id = data.get("messages", [{}])[0].get("id")
                    message.message_id = whatsapp_message_id
                    message.status = MessageStatus.SENT
                    message.sent_at = datetime.utcnow()
                    await self.message_repository.update(message)
                else:
                    message.status = MessageStatus.FAILED
                    await self.message_repository.update(message)
                    
        except Exception as e:
            message.status = MessageStatus.FAILED
            await self.message_repository.update(message)
            raise e
        
        return message
    
    async def send_document_message(
        self,
        company_id: UUID,
        phone_number: str,
        document_url: str,
        filename: Optional[str] = None,
        caption: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> WhatsAppMessage:
        """Send a document message via WhatsApp API"""
        message = WhatsAppMessage(
            company_id=company_id,
            message_id=f"temp_{datetime.utcnow().timestamp()}",
            direction=MessageDirection.OUTGOING,
            status=MessageStatus.PENDING,
            message_type=MessageType.DOCUMENT,
            phone_number=phone_number,
            display_name=display_name,
            media_url=document_url,
            content=caption,
            extra_data={"filename": filename} if filename else None
        )
        
        message = await self.message_repository.create(message)
        
        try:
            async with httpx.AsyncClient() as client:
                document_data = {"link": document_url}
                if filename:
                    document_data["filename"] = filename
                if caption:
                    document_data["caption"] = caption
                
                response = await client.post(
                    f"{self.base_url}/{settings.whatsapp_phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {settings.whatsapp_access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": phone_number,
                        "type": "document",
                        "document": document_data
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    whatsapp_message_id = data.get("messages", [{}])[0].get("id")
                    message.message_id = whatsapp_message_id
                    message.status = MessageStatus.SENT
                    message.sent_at = datetime.utcnow()
                    await self.message_repository.update(message)
                else:
                    message.status = MessageStatus.FAILED
                    await self.message_repository.update(message)
                    
        except Exception as e:
            message.status = MessageStatus.FAILED
            await self.message_repository.update(message)
            raise e
        
        return message
    
    async def send_audio_message(
        self,
        company_id: UUID,
        phone_number: str,
        audio_url: str,
        display_name: Optional[str] = None
    ) -> WhatsAppMessage:
        """Send an audio message via WhatsApp API"""
        message = WhatsAppMessage(
            company_id=company_id,
            message_id=f"temp_{datetime.utcnow().timestamp()}",
            direction=MessageDirection.OUTGOING,
            status=MessageStatus.PENDING,
            message_type=MessageType.AUDIO,
            phone_number=phone_number,
            display_name=display_name,
            media_url=audio_url
        )
        
        message = await self.message_repository.create(message)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{settings.whatsapp_phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {settings.whatsapp_access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": phone_number,
                        "type": "audio",
                        "audio": {
                            "link": audio_url
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    whatsapp_message_id = data.get("messages", [{}])[0].get("id")
                    message.message_id = whatsapp_message_id
                    message.status = MessageStatus.SENT
                    message.sent_at = datetime.utcnow()
                    await self.message_repository.update(message)
                else:
                    message.status = MessageStatus.FAILED
                    await self.message_repository.update(message)
                    
        except Exception as e:
            message.status = MessageStatus.FAILED
            await self.message_repository.update(message)
            raise e
        
        return message
