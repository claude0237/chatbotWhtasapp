"""WhatsApp Controller"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.whatsapp.services import WhatsAppService
from app.auth.dependencies import get_current_active_user, get_current_company_id
from app.users.models import User
from app.config import settings
from app.channels.repositories import ChannelRepository


router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


class SendMessageRequest(BaseModel):
    """Request schema for sending a message"""
    phone_number: str = Field(..., min_length=10, max_length=50)
    content: str = Field(..., min_length=1, max_length=4096)
    display_name: Optional[str] = Field(None, max_length=255)


class SendTemplateRequest(BaseModel):
    """Request schema for sending a template message"""
    phone_number: str = Field(..., min_length=10, max_length=50)
    template_name: str = Field(..., min_length=1, max_length=255)
    components: Optional[dict] = None
    display_name: Optional[str] = Field(None, max_length=255)


class CreateTemplateRequest(BaseModel):
    """Request schema for creating a template"""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    language: str = Field(default="en", min_length=2, max_length=10)
    components: dict


class WhatsAppPerformanceStats(BaseModel):
    """Performance statistics for a company"""
    company_id: str
    company_name: str
    total_messages_incoming: int = 0
    total_messages_outgoing: int = 0
    total_messages_failed: int = 0
    success_rate: float = 0.0
    avg_response_time_seconds: Optional[float] = None
    total_contacts: int = 0
    new_contacts_period: int = 0
    daily_stats: List[dict] = []


@router.get("/admin/performance-stats")
async def get_performance_stats(
    days: int = 30,
    company_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get performance analytics for companies (SUPER_ADMIN only)"""
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="SUPER_ADMIN only")
    
    from sqlalchemy import select as _select, func as _func
    from app.companies.models import Company as _Company
    from app.customers.models import Customer as _Customer
    from app.whatsapp.models import WhatsAppMessage as _WhatsAppMessage
    from datetime import datetime, timedelta
    
    # Validate days parameter
    days = min(max(days, 1), 365)  # Between 1 and 365 days
    
    # Get companies
    if company_id:
        companies_result = await db.execute(_select(_Company).where(_Company.id == UUID(company_id)))
        companies = companies_result.scalars().all()
    else:
        companies_result = await db.execute(_select(_Company))
        companies = companies_result.scalars().all()
    
    stats = []
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    for company in companies:
        # Total counts
        total_incoming = await db.execute(
            _select(_func.count())
            .where(_WhatsAppMessage.company_id == company.id)
            .where(_WhatsAppMessage.direction == "INCOMING")
            .where(_WhatsAppMessage.created_at >= start_date)
        )
        incoming_count = total_incoming.scalar() or 0
        
        total_outgoing = await db.execute(
            _select(_func.count())
            .where(_WhatsAppMessage.company_id == company.id)
            .where(_WhatsAppMessage.direction == "OUTGOING")
            .where(_WhatsAppMessage.created_at >= start_date)
        )
        outgoing_count = total_outgoing.scalar() or 0
        
        total_failed = await db.execute(
            _select(_func.count())
            .where(_WhatsAppMessage.company_id == company.id)
            .where(_WhatsAppMessage.status == "FAILED")
            .where(_WhatsAppMessage.created_at >= start_date)
        )
        failed_count = total_failed.scalar() or 0
        
        # Success rate
        total_messages = incoming_count + outgoing_count
        success_rate = ((total_messages - failed_count) / total_messages * 100) if total_messages > 0 else 0
        
        # Average response time (time between incoming and outgoing)
        avg_response_time = None
        try:
            avg_response = await db.execute(
                _select(_func.avg(
                    _func.extract('epoch', _WhatsAppMessage.created_at) - 
                    _func.extract('epoch', 
                        _select(_WhatsAppMessage.created_at)
                        .where(_WhatsAppMessage.company_id == company.id)
                        .where(_WhatsAppMessage.direction == "INCOMING")
                        .where(_WhatsAppMessage.phone_number == _WhatsAppMessage.phone_number)
                        .where(_WhatsAppMessage.created_at < _WhatsAppMessage.created_at)
                        .order_by(_WhatsAppMessage.created_at.desc())
                        .limit(1)
                        .scalar_subquery()
                    )
                ))
                .where(_WhatsAppMessage.company_id == company.id)
                .where(_WhatsAppMessage.direction == "OUTGOING")
                .where(_WhatsAppMessage.created_at >= start_date)
            )
            avg_response_time = avg_response.scalar()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to calculate avg response time for {company.id}: {e}")
            avg_response_time = None
        
        # Contact stats
        total_contacts_count = 0
        try:
            total_contacts = await db.execute(
                _select(_func.count())
                .where(_Customer.company_id == company.id)
            )
            total_contacts_count = total_contacts.scalar() or 0
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to get total contacts for {company.id}: {e}")
        
        new_contacts_count = 0
        try:
            new_contacts = await db.execute(
                _select(_func.count())
                .where(_Customer.company_id == company.id)
                .where(_Customer.first_seen_at >= start_date)
            )
            new_contacts_count = new_contacts.scalar() or 0
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to get new contacts for {company.id}: {e}")
        
        # Daily stats (messages + new contacts)
        daily_stats = []
        for day_offset in range(days):
            day_start = start_date + timedelta(days=day_offset)
            day_end = day_start + timedelta(days=1)
            
            day_incoming = await db.execute(
                _select(_func.count())
                .where(_WhatsAppMessage.company_id == company.id)
                .where(_WhatsAppMessage.direction == "INCOMING")
                .where(_WhatsAppMessage.created_at >= day_start)
                .where(_WhatsAppMessage.created_at < day_end)
            )
            day_incoming_count = day_incoming.scalar() or 0
            
            day_outgoing = await db.execute(
                _select(_func.count())
                .where(_WhatsAppMessage.company_id == company.id)
                .where(_WhatsAppMessage.direction == "OUTGOING")
                .where(_WhatsAppMessage.created_at >= day_start)
                .where(_WhatsAppMessage.created_at < day_end)
            )
            day_outgoing_count = day_outgoing.scalar() or 0
            
            day_failed = await db.execute(
                _select(_func.count())
                .where(_WhatsAppMessage.company_id == company.id)
                .where(_WhatsAppMessage.status == "FAILED")
                .where(_WhatsAppMessage.created_at >= day_start)
                .where(_WhatsAppMessage.created_at < day_end)
            )
            day_failed_count = day_failed.scalar() or 0
            
            day_new_contacts = await db.execute(
                _select(_func.count())
                .where(_Customer.company_id == company.id)
                .where(_Customer.first_seen_at >= day_start)
                .where(_Customer.first_seen_at < day_end)
            )
            day_new_contacts_count = day_new_contacts.scalar() or 0
            
            daily_stats.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "incoming": day_incoming_count,
                "outgoing": day_outgoing_count,
                "failed": day_failed_count,
                "new_contacts": day_new_contacts_count
            })
        
        stats.append(WhatsAppPerformanceStats(
            company_id=str(company.id),
            company_name=company.name,
            total_messages_incoming=incoming_count,
            total_messages_outgoing=outgoing_count,
            total_messages_failed=failed_count,
            success_rate=round(success_rate, 2),
            avg_response_time_seconds=round(avg_response_time, 2) if avg_response_time else None,
            total_contacts=total_contacts_count,
            new_contacts_period=new_contacts_count,
            daily_stats=daily_stats
        ))
    
    return {"stats": stats, "period_days": days}


class WhatsAppWebhookStats(BaseModel):
    """Webhook statistics for a company"""
    company_id: str
    company_name: str
    configured: bool
    webhook_url: Optional[str] = None
    last_message_received: Optional[str] = None
    last_message_sent: Optional[str] = None
    messages_incoming_24h: int = 0
    messages_outgoing_24h: int = 0
    messages_failed_24h: int = 0
    api_connection_status: str = "unknown"
    phone_number_id: Optional[str] = None
    status: str = "unknown"


@router.get("/admin/webhook-stats")
async def get_webhook_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get webhook statistics for all companies (SUPER_ADMIN only)"""
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="SUPER_ADMIN only")
    
    from sqlalchemy import select as _select, func as _func
    from app.companies.models import Company as _Company
    from app.channels.models import ChannelType
    from app.whatsapp.models import WhatsAppMessage as _WhatsAppMessage
    from datetime import datetime, timedelta
    import httpx
    
    # Get all companies
    companies_result = await db.execute(_select(_Company))
    companies = companies_result.scalars().all()
    
    stats = []
    now = datetime.utcnow()
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    for company in companies:
        channel_repo = ChannelRepository(db)
        channel = await channel_repo.get_by_type(company.id, ChannelType.WHATSAPP)
        
        if not channel:
            stats.append(WhatsAppWebhookStats(
                company_id=str(company.id),
                company_name=company.name,
                configured=False,
                status="not_configured"
            ))
            continue
        
        # Get configurations
        from app.channels.repositories import ChannelConfigurationRepository
        config_repo = ChannelConfigurationRepository(db)
        configs = await config_repo.get_by_channel_id(channel.id)
        config_map = {c.key: c.value for c in configs}
        
        phone_number_id = config_map.get("phone_number_id")
        webhook_verify_token = config_map.get("webhook_verify_token")
        
        # Get message stats
        # Count messages in last 24h
        incoming_result = await db.execute(
            _select(_func.count())
            .where(_WhatsAppMessage.company_id == company.id)
            .where(_WhatsAppMessage.direction == "INCOMING")
            .where(_WhatsAppMessage.created_at >= twenty_four_hours_ago)
        )
        incoming_count = incoming_result.scalar() or 0
        
        outgoing_result = await db.execute(
            _select(_func.count())
            .where(_WhatsAppMessage.company_id == company.id)
            .where(_WhatsAppMessage.direction == "OUTGOING")
            .where(_WhatsAppMessage.created_at >= twenty_four_hours_ago)
        )
        outgoing_count = outgoing_result.scalar() or 0
        
        failed_result = await db.execute(
            _select(_func.count())
            .where(_WhatsAppMessage.company_id == company.id)
            .where(_WhatsAppMessage.status == "FAILED")
            .where(_WhatsAppMessage.created_at >= twenty_four_hours_ago)
        )
        failed_count = failed_result.scalar() or 0
        
        # Get last message timestamps
        last_incoming = await db.execute(
            _select(_WhatsAppMessage.created_at)
            .where(_WhatsAppMessage.company_id == company.id)
            .where(_WhatsAppMessage.direction == "INCOMING")
            .order_by(_WhatsAppMessage.created_at.desc())
            .limit(1)
        )
        last_incoming_time = last_incoming.scalar_one_or_none()
        
        last_outgoing = await db.execute(
            _select(_WhatsAppMessage.created_at)
            .where(_WhatsAppMessage.company_id == company.id)
            .where(_WhatsAppMessage.direction == "OUTGOING")
            .order_by(_WhatsAppMessage.created_at.desc())
            .limit(1)
        )
        last_outgoing_time = last_outgoing.scalar_one_or_none()
        
        # Determine webhook status
        status = "active"
        if last_incoming_time:
            time_since = (now - last_incoming_time).total_seconds()
            if time_since > 1800:  # 30 minutes
                status = "dead"
            elif time_since > 300:  # 5 minutes
                status = "inactive"
        else:
            status = "no_messages"
        
        # Test API connection
        api_status = "unknown"
        if phone_number_id:
            try:
                from app.channels.repositories import ChannelCredentialRepository
                from app.utils.encryption import decrypt_credential
                cred_repo = ChannelCredentialRepository(db)
                credentials = await cred_repo.get_by_channel_id(channel.id)
                cred_map = {c.credential_type: c.encrypted_value for c in credentials}
                raw_token = cred_map.get("ACCESS_TOKEN")
                
                if raw_token:
                    try:
                        access_token = decrypt_credential(raw_token)
                        async with httpx.AsyncClient(timeout=5) as client:
                            response = await client.get(
                                f"https://graph.facebook.com/{settings.whatsapp_api_version}/{phone_number_id}",
                                params={"fields": "display_phone_number", "access_token": access_token}
                            )
                            api_status = "ok" if response.status_code == 200 else "error"
                    except httpx.TimeoutException:
                        api_status = "timeout"
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).warning(f"API connection test failed for {company.id}: {e}")
                        api_status = "error"
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to test API connection for {company.id}: {e}")
                api_status = "error"
        
        # Build webhook URL
        webhook_url = f"{settings.public_url}/whatsapp/webhook/{company.id}" if webhook_verify_token else None
        
        stats.append(WhatsAppWebhookStats(
            company_id=str(company.id),
            company_name=company.name,
            configured=True,
            webhook_url=webhook_url,
            last_message_received=last_incoming_time.isoformat() + "Z" if last_incoming_time else None,
            last_message_sent=last_outgoing_time.isoformat() + "Z" if last_outgoing_time else None,
            messages_incoming_24h=incoming_count,
            messages_outgoing_24h=outgoing_count,
            messages_failed_24h=failed_count,
            api_connection_status=api_status,
            phone_number_id=phone_number_id,
            status=status
        ))
    
    return {"stats": stats}


@router.get("/webhook/info")
async def get_webhook_info(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id),
):
    """Return webhook URL and masked verify token for Meta configuration"""
    base = str(request.base_url).rstrip("/")
    
    token = settings.whatsapp_webhook_verify_token
    masked = token[:4] + "*" * max(0, len(token) - 6) + token[-2:] if len(token) > 6 else "***"
    
    return {
        "legacy_webhook_url": f"{base}/whatsapp/webhook",
        "legacy_verify_token": masked,
        "tenant_webhook_url": f"{base}/whatsapp/webhook/{company_id}",
        "verify_token_configured": bool(token),
        "events_to_subscribe": ["messages", "message_status"],
    }


class WhatsAppConfigRequest(BaseModel):
    """Request schema for WhatsApp configuration"""
    meta_app_id: Optional[str] = None
    meta_app_secret: Optional[str] = None
    meta_business_id: Optional[str] = None
    phone_number_id: Optional[str] = None
    access_token: Optional[str] = None
    webhook_verify_token: Optional[str] = None


@router.get("/config")
async def get_whatsapp_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get WhatsApp configuration for the current company"""
    from app.channels.models import ChannelType
    from app.channels.repositories import ChannelConfigurationRepository, ChannelCredentialRepository
    from app.utils.encryption import decrypt_credential
    
    channel_repo = ChannelRepository(db)
    channel = await channel_repo.get_by_type(UUID(company_id), ChannelType.WHATSAPP)
    
    if not channel:
        return {
            "configured": False,
            "meta_app_id": "",
            "meta_business_id": "",
            "phone_number_id": "",
            "webhook_verify_token": "",
            "webhook_url": ""
        }
    
    config_repo = ChannelConfigurationRepository(db)
    configs = await config_repo.get_by_channel_id(channel.id)
    config_map = {c.key: c.value for c in configs}
    
    cred_repo = ChannelCredentialRepository(db)
    credentials = await cred_repo.get_by_channel_id(channel.id)
    cred_map = {c.credential_type: c.encrypted_value for c in credentials}
    
    # Decrypt access token for display (masked: 4 first + 4 last)
    raw_token = cred_map.get("ACCESS_TOKEN")
    access_token_masked = ""
    if raw_token:
        try:
            decrypted = decrypt_credential(raw_token)
            if len(decrypted) > 8:
                access_token_masked = decrypted[:4] + "..." + decrypted[-4:]
            else:
                access_token_masked = "***"
        except:
            access_token_masked = "***"
    
    # Decrypt app secret for display (masked: 4 first + 4 last)
    raw_secret = cred_map.get("META_APP_SECRET")
    app_secret_masked = ""
    if raw_secret:
        try:
            decrypted = decrypt_credential(raw_secret)
            if len(decrypted) > 8:
                app_secret_masked = decrypted[:4] + "..." + decrypted[-4:]
            else:
                app_secret_masked = "***"
        except:
            app_secret_masked = "***"
    
    # Mask webhook verify token (4 first + 4 last)
    webhook_verify_token = config_map.get("webhook_verify_token", "")
    webhook_verify_token_masked = ""
    if webhook_verify_token:
        if len(webhook_verify_token) > 8:
            webhook_verify_token_masked = webhook_verify_token[:4] + "..." + webhook_verify_token[-4:]
        else:
            webhook_verify_token_masked = "***"
    
    webhook_url = f"{settings.public_url}/whatsapp/webhook/{company_id}"
    
    return {
        "configured": True,
        "channel_id": str(channel.id),
        "meta_app_id": config_map.get("meta_app_id", ""),
        "meta_app_secret_masked": app_secret_masked,
        "meta_business_id": config_map.get("meta_business_id", ""),
        "phone_number_id": config_map.get("phone_number_id", ""),
        "access_token_masked": access_token_masked,
        "webhook_verify_token_masked": webhook_verify_token_masked,
        "webhook_url": webhook_url
    }


@router.put("/config")
async def update_whatsapp_config(
    request: WhatsAppConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Update WhatsApp configuration for the current company"""
    from app.channels.models import Channel, ChannelType, ChannelStatus, ChannelConfiguration, ChannelCredential
    from app.channels.repositories import ChannelConfigurationRepository, ChannelCredentialRepository
    from app.utils.encryption import encrypt_credential
    
    channel_repo = ChannelRepository(db)
    config_repo = ChannelConfigurationRepository(db)
    cred_repo = ChannelCredentialRepository(db)
    
    # Get or create channel
    channel = await channel_repo.get_by_type(UUID(company_id), ChannelType.WHATSAPP)
    if not channel:
        channel = Channel(
            company_id=UUID(company_id),
            channel_type=ChannelType.WHATSAPP,
            name="WhatsApp",
            status=ChannelStatus.ACTIVE
        )
        db.add(channel)
        await db.flush()
    
    # Update configurations
    if request.meta_app_id is not None:
        existing = await config_repo.get_by_key(channel.id, "meta_app_id")
        if existing:
            existing.value = request.meta_app_id
        else:
            db.add(ChannelConfiguration(channel_id=channel.id, key="meta_app_id", value=request.meta_app_id))
    
    if request.meta_business_id is not None:
        existing = await config_repo.get_by_key(channel.id, "meta_business_id")
        if existing:
            existing.value = request.meta_business_id
        else:
            db.add(ChannelConfiguration(channel_id=channel.id, key="meta_business_id", value=request.meta_business_id))
    
    if request.phone_number_id is not None:
        existing = await config_repo.get_by_key(channel.id, "phone_number_id")
        if existing:
            existing.value = request.phone_number_id
        else:
            db.add(ChannelConfiguration(channel_id=channel.id, key="phone_number_id", value=request.phone_number_id))
    
    # Update webhook verify token if provided
    if request.webhook_verify_token is not None:
        existing_token = await config_repo.get_by_key(channel.id, "webhook_verify_token")
        if existing_token:
            existing_token.value = request.webhook_verify_token
        else:
            db.add(ChannelConfiguration(channel_id=channel.id, key="webhook_verify_token", value=request.webhook_verify_token))
    else:
        # Generate webhook verify token if not exists
        existing_token = await config_repo.get_by_key(channel.id, "webhook_verify_token")
        if not existing_token:
            import uuid
            verify_token = f"verify_{company_id}_{uuid.uuid4().hex[:8]}"
            db.add(ChannelConfiguration(channel_id=channel.id, key="webhook_verify_token", value=verify_token))
    
    # Update credentials (encrypted)
    if request.meta_app_secret is not None:
        encrypted = encrypt_credential(request.meta_app_secret)
        existing_cred = await cred_repo.get_by_type(channel.id, "META_APP_SECRET")
        if existing_cred:
            existing_cred.encrypted_value = encrypted
        else:
            db.add(ChannelCredential(channel_id=channel.id, credential_type="META_APP_SECRET", encrypted_value=encrypted))
    
    if request.access_token is not None:
        encrypted = encrypt_credential(request.access_token)
        existing_cred = await cred_repo.get_by_type(channel.id, "ACCESS_TOKEN")
        if existing_cred:
            existing_cred.encrypted_value = encrypted
        else:
            db.add(ChannelCredential(channel_id=channel.id, credential_type="ACCESS_TOKEN", encrypted_value=encrypted))
    
    await db.commit()
    
    return {"status": "updated", "channel_id": str(channel.id)}


@router.post("/config/test")
async def test_whatsapp_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Test WhatsApp configuration by making a test API call"""
    import httpx
    
    from app.channels.models import ChannelType
    from app.channels.repositories import ChannelConfigurationRepository, ChannelCredentialRepository
    from app.utils.encryption import decrypt_credential
    
    channel_repo = ChannelRepository(db)
    channel = await channel_repo.get_by_type(UUID(company_id), ChannelType.WHATSAPP)
    
    if not channel:
        raise HTTPException(status_code=404, detail="WhatsApp channel not configured")
    
    config_repo = ChannelConfigurationRepository(db)
    configs = await config_repo.get_by_channel_id(channel.id)
    config_map = {c.key: c.value for c in configs}
    
    cred_repo = ChannelCredentialRepository(db)
    credentials = await cred_repo.get_by_channel_id(channel.id)
    cred_map = {c.credential_type: c.encrypted_value for c in credentials}
    
    phone_number_id = config_map.get("phone_number_id")
    raw_token = cred_map.get("ACCESS_TOKEN")
    
    if not phone_number_id or not raw_token:
        return {"valid": False, "error": "Missing phone_number_id or access_token"}
    
    try:
        access_token = decrypt_credential(raw_token)
    except:
        return {"valid": False, "error": "Failed to decrypt access token"}
    
    # Test by fetching phone number info from Meta API
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"https://graph.facebook.com/{settings.whatsapp_api_version}/{phone_number_id}",
                params={"fields": "display_phone_number", "access_token": access_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "valid": True,
                    "phone_number_id": phone_number_id,
                    "display_phone_number": data.get("display_phone_number", "Unknown")
                }
            else:
                return {"valid": False, "error": f"Meta API error: {response.status_code}", "details": response.text}
    except Exception as e:
        return {"valid": False, "error": f"Connection error: {str(e)}"}


# Webhook endpoints (no authentication required for webhooks)

# Legacy global webhook (kept for backward compatibility)
@router.get("/webhook")
async def webhook_verify(request: Request):
    """Verify webhook with WhatsApp (legacy - uses global token)"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == settings.whatsapp_webhook_verify_token:
        return int(challenge)
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid verification token"
    )


@router.post("/webhook")
async def webhook_receive(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive webhook events from WhatsApp — multitenant routing by phone_number_id (legacy)"""
    import logging
    _log = logging.getLogger(__name__)
    try:
        payload = await request.json()
        _log.info(f"[RAW] Webhook received: {payload}")

        # Extract phone_number_id from Meta webhook payload
        phone_number_id = (
            payload.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("metadata", {})
            .get("phone_number_id")
        )

        _log.info(f"Webhook received — phone_number_id={phone_number_id}")

        if not phone_number_id:
            _log.warning(f"Webhook ignored — no phone_number_id")
            return {"status": "ignored", "reason": "no phone_number_id"}

        # Lookup which company owns this phone_number_id
        channel_repo = ChannelRepository(db)
        channel = await channel_repo.get_by_phone_number_id(phone_number_id)

        if not channel:
            return {"status": "ignored", "reason": f"unknown phone_number_id: {phone_number_id}"}

        company_id = channel.company_id

        # Ignore webhooks for disabled or suspended companies
        from sqlalchemy import select as _select
        from app.companies.models import Company as _Company
        _co_result = await db.execute(_select(_Company).where(_Company.id == company_id))
        _company = _co_result.scalar_one_or_none()
        if _company and (not _company.is_active or _company.is_suspended):
            _log.info(f"Webhook ignored — company {company_id} is disabled or suspended")
            return {"status": "ignored", "reason": "company disabled"}

        whatsapp_service = WhatsAppService(db)
        event = await whatsapp_service.receive_webhook(payload, company_id)

        return {"status": "received", "event_id": str(event.id), "company_id": str(company_id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# New tenant-specific webhook endpoints (recommended for multi-tenant setup)
@router.get("/webhook/{company_id}")
async def webhook_verify_tenant(
    company_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Verify webhook with WhatsApp using tenant-specific verify token"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    # Get tenant's webhook verify token from channel configuration
    channel_repo = ChannelRepository(db)
    from app.channels.models import ChannelType
    channel = await channel_repo.get_by_type(company_id, ChannelType.WHATSAPP)
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No WhatsApp channel configured for company {company_id}"
        )
    
    from app.channels.repositories import ChannelConfigurationRepository
    config_repo = ChannelConfigurationRepository(db)
    configs = await config_repo.get_by_channel_id(channel.id)
    config_map = {c.key: c.value for c in configs}
    
    tenant_verify_token = config_map.get("webhook_verify_token")
    
    if not tenant_verify_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook verify token not configured for this tenant"
        )
    
    if mode == "subscribe" and token == tenant_verify_token:
        return int(challenge)
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid verification token"
    )


@router.post("/webhook/{company_id}")
async def webhook_receive_tenant(
    company_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Receive webhook events from WhatsApp for a specific tenant"""
    import logging
    _log = logging.getLogger(__name__)
    
    try:
        # Verify company exists and is active
        from sqlalchemy import select as _select
        from app.companies.models import Company as _Company
        _co_result = await db.execute(_select(_Company).where(_Company.id == company_id))
        _company = _co_result.scalar_one_or_none()
        
        if not _company:
            return {"status": "ignored", "reason": "company not found"}
        
        if not _company.is_active or _company.is_suspended:
            _log.info(f"Webhook ignored — company {company_id} is disabled or suspended")
            return {"status": "ignored", "reason": "company disabled"}
        
        # Verify WhatsApp channel exists
        from app.channels.models import ChannelType
        channel_repo = ChannelRepository(db)
        channel = await channel_repo.get_by_type(company_id, ChannelType.WHATSAPP)
        
        if not channel:
            return {"status": "ignored", "reason": "no WhatsApp channel configured"}
        
        payload = await request.json()
        _log.info(f"[RAW] Webhook received for tenant {payload}")
#        print(f"[RAW] Webhook received for tenant {payload}")

        
        # Verify the phone_number_id in the payload matches the tenant's configuration
        phone_number_id = (
            payload.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("metadata", {})
            .get("phone_number_id")
        )
        
        from app.channels.repositories import ChannelConfigurationRepository
        config_repo = ChannelConfigurationRepository(db)
        configs = await config_repo.get_by_channel_id(channel.id)
        config_map = {c.key: c.value for c in configs}
        
        tenant_phone_number_id = config_map.get("phone_number_id")
        
        if phone_number_id and tenant_phone_number_id and phone_number_id != tenant_phone_number_id:
            _log.warning(f"Webhook ignored — phone_number_id mismatch: {phone_number_id} != {tenant_phone_number_id}")
            return {"status": "ignored", "reason": "phone_number_id mismatch"}
        
        _log.info(f"Webhook received for tenant {company_id} — phone_number_id={phone_number_id}")
        
        whatsapp_service = WhatsAppService(db)
        event = await whatsapp_service.receive_webhook(payload, company_id)

        return {"status": "received", "event_id": str(event.id), "company_id": str(company_id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/messages/send", status_code=status.HTTP_201_CREATED)
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Send a text message via WhatsApp"""
    whatsapp_service = WhatsAppService(db)
    
    try:
        message = await whatsapp_service.send_text_message(
            company_id=company_id,
            phone_number=request.phone_number,
            content=request.content,
            display_name=request.display_name
        )
        return {
            "id": str(message.id),
            "message_id": message.message_id,
            "status": message.status.value,
            "direction": message.direction.value
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/messages/send-template", status_code=status.HTTP_201_CREATED)
async def send_template_message(
    request: SendTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Send a template message via WhatsApp"""
    whatsapp_service = WhatsAppService(db)
    
    try:
        message = await whatsapp_service.send_template_message(
            company_id=company_id,
            phone_number=request.phone_number,
            template_name=request.template_name,
            components=request.components,
            display_name=request.display_name
        )
        return {
            "id": str(message.id),
            "message_id": message.message_id,
            "status": message.status.value,
            "direction": message.direction.value
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/messages")
async def get_messages(
    phone_number: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get messages for the current user's company"""
    whatsapp_service = WhatsAppService(db)
    from app.whatsapp.repositories import WhatsAppMessageRepository
    msg_repo = WhatsAppMessageRepository(db)

    messages = await whatsapp_service.get_messages(
        company_id=company_id,
        phone_number=phone_number,
        skip=skip,
        limit=limit
    )

    if phone_number:
        total = await msg_repo.count_by_phone_number(UUID(company_id), phone_number)
    else:
        total = await msg_repo.count_by_company_id(UUID(company_id))

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "messages": [
            {
                "id": str(msg.id),
                "message_id": msg.message_id,
                "direction": msg.direction.value,
                "status": msg.status.value,
                "message_type": msg.message_type.value,
                "phone_number": msg.phone_number,
                "display_name": msg.display_name,
                "content": msg.content,
                "extra_data": msg.extra_data,
                "media_url": msg.media_url,
                "template_name": msg.template_name,
                "sent_at": (msg.sent_at.isoformat() + "Z") if msg.sent_at else None,
                "delivered_at": (msg.delivered_at.isoformat() + "Z") if msg.delivered_at else None,
                "read_at": (msg.read_at.isoformat() + "Z") if msg.read_at else None,
                "created_at": msg.created_at.isoformat() + "Z"
            }
            for msg in messages
        ]
    }


class DeleteMessagesRequest(BaseModel):
    """Request schema for bulk-deleting WhatsApp messages"""
    message_ids: List[str] = Field(..., min_length=1)


@router.delete("/messages")
async def delete_messages(
    request: DeleteMessagesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Delete one or more WhatsApp messages for the current company"""
    try:
        message_ids = [UUID(mid) for mid in request.message_ids]
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid message id format")

    whatsapp_service = WhatsAppService(db)
    deleted_count = await whatsapp_service.delete_messages(UUID(company_id), message_ids)

    return {"status": "deleted", "deleted_count": deleted_count}


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    request: CreateTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Create a new WhatsApp template"""
    whatsapp_service = WhatsAppService(db)
    
    try:
        template = await whatsapp_service.create_template(
            company_id=company_id,
            name=request.name,
            category=request.category,
            language=request.language,
            components=request.components
        )
        return {
            "id": str(template.id),
            "name": template.name,
            "category": template.category,
            "language": template.language,
            "is_active": template.is_active,
            "is_approved": template.is_approved
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/templates")
async def get_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get templates for the current user's company"""
    whatsapp_service = WhatsAppService(db)
    
    templates = await whatsapp_service.get_templates(
        company_id=company_id,
        skip=skip,
        limit=limit
    )
    
    return [
        {
            "id": str(template.id),
            "name": template.name,
            "category": template.category,
            "language": template.language,
            "is_active": template.is_active,
            "is_approved": template.is_approved,
            "created_at": template.created_at.isoformat()
        }
        for template in templates
    ]


@router.get("/templates/active")
async def get_active_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get active templates for the current user's company"""
    whatsapp_service = WhatsAppService(db)
    
    templates = await whatsapp_service.get_active_templates(company_id)
    
    return [
        {
            "id": str(template.id),
            "name": template.name,
            "category": template.category,
            "language": template.language,
            "is_approved": template.is_approved
        }
        for template in templates
    ]
