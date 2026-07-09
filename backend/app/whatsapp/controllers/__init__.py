"""WhatsApp Controller"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.whatsapp.services import WhatsAppService
from app.whatsapp.models import MessageType
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


@router.get("/webhook/info")
async def get_webhook_info(
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """Return webhook URL and masked verify token for Meta configuration"""
    base = str(request.base_url).rstrip("/")
    token = settings.whatsapp_webhook_verify_token
    masked = token[:4] + "*" * max(0, len(token) - 6) + token[-2:] if len(token) > 6 else "***"
    return {
        "webhook_url": f"{base}/whatsapp/webhook",
        "verify_token": masked,
        "verify_token_configured": bool(token),
        "events_to_subscribe": ["messages", "message_status"],
    }


# Webhook endpoints (no authentication required for webhooks)
@router.get("/webhook")
async def webhook_verify(request: Request):
    """Verify webhook with WhatsApp"""
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
    """Receive webhook events from WhatsApp — multitenant routing by phone_number_id"""
    import logging
    _log = logging.getLogger(__name__)
    try:
        payload = await request.json()

        # Extract phone_number_id from Meta webhook payload
        # Structure: entry[0].changes[0].value.metadata.phone_number_id
        phone_number_id = (
            payload.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("metadata", {})
            .get("phone_number_id")
        )

        _log.info(f"Webhook received — phone_number_id={phone_number_id} field={payload.get('entry',[{}])[0].get('changes',[{}])[0].get('field')}")

        if not phone_number_id:
            _log.warning(f"Webhook ignored — no phone_number_id. Payload keys: {list(payload.keys())}")
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
