"""Conversation Controller"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.conversations.services import CustomerService, ConversationService, MessageService
from app.conversations.models import ConversationStatus, ConversationPriority, SenderType, ConversationMessageType
from app.auth.dependencies import get_current_active_user, get_current_company_id, require_company_admin
from app.users.models import User, UserRoleEnum
from app.users.services import UserService
from app.customers.repositories import CustomerRepository
from app.whatsapp.services import WhatsAppService


router = APIRouter(prefix="/conversations", tags=["Conversations"])


# Request/Response Schemas
class CustomerResponse(BaseModel):
    """Customer response schema"""
    id: str
    company_id: str
    phone_number: str
    name: Optional[str]
    profile_picture_url: Optional[str]
    first_seen_at: str
    last_seen_at: str
    created_at: str


class CustomerUpdateRequest(BaseModel):
    """Customer update request schema"""
    name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    extra_data: Optional[dict] = None


class ConversationResponse(BaseModel):
    """Conversation response schema"""
    id: str
    company_id: str
    customer_id: str
    channel_id: Optional[str]
    status: str
    priority: str
    assigned_agent_id: Optional[str]
    tags: Optional[list]
    last_activity_at: str
    created_at: str


class ConversationCreateRequest(BaseModel):
    """Conversation create request schema"""
    customer_id: str
    channel_id: Optional[str] = None
    status: ConversationStatus = ConversationStatus.OPEN
    priority: ConversationPriority = ConversationPriority.MEDIUM


class AssignAgentRequest(BaseModel):
    """Assign agent request schema"""
    agent_id: str


class ChangeStatusRequest(BaseModel):
    """Change status request schema"""
    status: ConversationStatus


class AddTagRequest(BaseModel):
    """Add tag request schema"""
    tag: str


class NoteCreateRequest(BaseModel):
    """Note create request schema"""
    content: str = Field(..., min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    """Message response schema"""
    id: str
    conversation_id: str
    sender_type: str
    sender_id: Optional[str]
    content: Optional[str]
    message_type: str
    media_url: Optional[str]
    external_message_id: Optional[str]
    status: str
    sent_at: str
    delivered_at: Optional[str]
    read_at: Optional[str]


class MessageCreateRequest(BaseModel):
    """Message create request schema"""
    content: str = Field(..., min_length=1, max_length=4096)
    message_type: ConversationMessageType = ConversationMessageType.TEXT
    media_url: Optional[str] = None


# Customers endpoints
@router.get("/customers")
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get customers for the current user's company"""
    customer_service = CustomerService(db)
    from app.conversations.repositories import CustomerRepository as _CustRepo
    cust_repo = _CustRepo(db)
    customers = await customer_service.get_by_company_id(company_id, skip, limit)
    total = await cust_repo.count_by_company_id(UUID(company_id))
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "customers": [
            {
                "id": str(c.id),
                "company_id": str(c.company_id),
                "phone_number": c.phone_number,
                "name": c.name,
                "profile_picture_url": c.profile_picture_url,
                "first_seen_at": c.first_seen_at.isoformat(),
                "last_seen_at": c.last_seen_at.isoformat(),
                "created_at": c.created_at.isoformat()
            }
            for c in customers
        ]
    }


@router.get("/customers/{customer_id}")
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get customer by ID"""
    customer_service = CustomerService(db)
    customer = await customer_service.get_by_id(customer_id)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Multi-tenant check
    if str(customer.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": str(customer.id),
        "company_id": str(customer.company_id),
        "phone_number": customer.phone_number,
        "name": customer.name,
        "profile_picture_url": customer.profile_picture_url,
        "first_seen_at": customer.first_seen_at.isoformat(),
        "last_seen_at": customer.last_seen_at.isoformat(),
        "created_at": customer.created_at.isoformat()
    }


@router.put("/customers/{customer_id}")
async def update_customer(
    customer_id: str,
    request: CustomerUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Update customer profile"""
    customer_service = CustomerService(db)
    customer = await customer_service.update_profile(
        customer_id,
        name=request.name,
        profile_picture_url=request.profile_picture_url,
        extra_data=request.extra_data
    )
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return {
        "id": str(customer.id),
        "company_id": str(customer.company_id),
        "phone_number": customer.phone_number,
        "name": customer.name,
        "profile_picture_url": customer.profile_picture_url,
        "first_seen_at": customer.first_seen_at.isoformat(),
        "last_seen_at": customer.last_seen_at.isoformat(),
        "created_at": customer.created_at.isoformat()
    }


# Conversations endpoints
@router.get("/conversations")
async def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[ConversationStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get conversations for the current user's company"""
    conversation_service = ConversationService(db)
    from app.conversations.repositories import ConversationRepository as _ConvRepo
    conv_repo = _ConvRepo(db)
    
    if status:
        conversations = await conversation_service.get_by_status(company_id, status, skip, limit)
    else:
        conversations = await conversation_service.get_by_company_id(company_id, skip, limit)
    
    total = await conv_repo.count_by_company_id(UUID(company_id))

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "conversations": [
            {
                "id": str(c.id),
                "company_id": str(c.company_id),
                "customer_id": str(c.customer_id),
                "channel_id": str(c.channel_id) if c.channel_id else None,
                "status": c.status.value,
                "priority": c.priority.value,
                "assigned_agent_id": str(c.assigned_agent_id) if c.assigned_agent_id else None,
                "tags": c.tags,
                "last_activity_at": c.last_activity_at.isoformat(),
                "created_at": c.created_at.isoformat()
            }
            for c in conversations
        ]
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get conversation by ID"""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Multi-tenant check
    if str(conversation.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": str(conversation.id),
        "company_id": str(conversation.company_id),
        "customer_id": str(conversation.customer_id),
        "channel_id": str(conversation.channel_id) if conversation.channel_id else None,
        "status": conversation.status.value,
        "priority": conversation.priority.value,
        "assigned_agent_id": str(conversation.assigned_agent_id) if conversation.assigned_agent_id else None,
        "tags": conversation.tags,
        "last_activity_at": conversation.last_activity_at.isoformat(),
        "created_at": conversation.created_at.isoformat()
    }


@router.post("/conversations/{conversation_id}/assign")
async def assign_conversation(
    conversation_id: str,
    request: AssignAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Assign conversation to an agent"""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.assign_to_agent(conversation_id, request.agent_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return {
        "id": str(conversation.id),
        "company_id": str(conversation.company_id),
        "customer_id": str(conversation.customer_id),
        "status": conversation.status.value,
        "assigned_agent_id": str(conversation.assigned_agent_id) if conversation.assigned_agent_id else None
    }


@router.post("/conversations/{conversation_id}/status")
async def change_conversation_status(
    conversation_id: str,
    request: ChangeStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Change conversation status"""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.change_status(conversation_id, request.status)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return {
        "id": str(conversation.id),
        "status": conversation.status.value
    }


@router.post("/conversations/{conversation_id}/tags")
async def add_conversation_tag(
    conversation_id: str,
    request: AddTagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Add a tag to conversation"""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.add_tag(conversation_id, request.tag)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return {
        "id": str(conversation.id),
        "tags": conversation.tags
    }


@router.post("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Archive conversation"""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.archive(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return {
        "id": str(conversation.id),
        "status": conversation.status.value
    }


@router.get("/stats")
async def get_conversation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Conversation counts by status + assigned to me"""
    conversation_service = ConversationService(db)
    all_convs = await conversation_service.get_by_company_id(company_id, skip=0, limit=1000)
    counts: dict = {}
    for c in all_convs:
        k = c.status.value
        counts[k] = counts.get(k, 0) + 1
    assigned_to_me = sum(
        1 for c in all_convs
        if c.assigned_agent_id and str(c.assigned_agent_id) == str(current_user.id)
    )
    unassigned = sum(1 for c in all_convs if not c.assigned_agent_id and c.status.value in ("OPEN", "WAITING"))
    return {
        "by_status": counts,
        "assigned_to_me": assigned_to_me,
        "unassigned": unassigned,
        "total": len(all_convs)
    }


@router.post("/conversations/{conversation_id}/take")
async def self_assign_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Agent takes a conversation (self-assign)"""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if str(conversation.company_id) != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    updated = await conversation_service.assign_to_agent(conversation_id, str(current_user.id))
    return {
        "id": str(updated.id),
        "assigned_agent_id": str(updated.assigned_agent_id),
        "status": updated.status.value
    }


@router.post("/auto-assign")
async def auto_assign_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    company_id: str = Depends(get_current_company_id)
):
    """
    Auto-assign (round-robin): distribute all unassigned OPEN/WAITING conversations
    evenly across active agents of the company. Company admin only.
    """
    user_service = UserService(db)
    conversation_service = ConversationService(db)

    all_users = await user_service.get_company_users(company_id)
    active_agents = [
        u for u in all_users
        if u.role in (UserRoleEnum.AGENT, UserRoleEnum.COMPANY_ADMIN) and u.is_active
    ]
    if not active_agents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun agent actif trouvé pour cette entreprise."
        )

    agent_ids = [u.id for u in active_agents]
    result = await conversation_service.auto_assign_round_robin(company_id, agent_ids)
    return result


# Messages endpoints
@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get messages for a conversation"""
    message_service = MessageService(db)
    messages = await message_service.get_by_conversation_id(conversation_id, skip, limit)
    
    return [
        {
            "id": str(m.id),
            "conversation_id": str(m.conversation_id),
            "sender_type": m.sender_type.value,
            "sender_id": str(m.sender_id) if m.sender_id else None,
            "content": m.content,
            "message_type": m.message_type.value,
            "media_url": m.media_url,
            "external_message_id": m.external_message_id,
            "status": m.status.value,
            "sent_at": m.sent_at.isoformat() + "Z",
            "delivered_at": (m.delivered_at.isoformat() + "Z") if m.delivered_at else None,
            "read_at": (m.read_at.isoformat() + "Z") if m.read_at else None
        }
        for m in messages
    ]


@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    request: MessageCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Send a message in a conversation — also dispatches via WhatsApp API"""
    message_service = MessageService(db)
    conv_service = ConversationService(db)

    conversation = await conv_service.get_by_id(UUID(conversation_id))
    if not conversation or str(conversation.company_id) != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    message = await message_service.send_message(
        conversation_id=UUID(conversation_id),
        sender_type=SenderType.AGENT,
        sender_id=current_user.id,
        content=request.content,
        message_type=request.message_type,
        media_url=request.media_url
    )

    # Promote to AGENT as soon as the human writes (covers WAITING, AI, OPEN)
    if conversation.status in (ConversationStatus.WAITING, ConversationStatus.AI, ConversationStatus.OPEN):
        await conv_service.change_status(conversation_id, ConversationStatus.AGENT)

    # Also send via WhatsApp API so the customer receives it and it appears in /whatsapp/messages
    try:
        customer_repo = CustomerRepository(db)
        customer = await customer_repo.get_by_id(conversation.customer_id)
        if customer and customer.phone_number:
            wa_service = WhatsAppService(db)
            wa_msg = await wa_service.send_text_message(
                company_id=conversation.company_id,
                phone_number=customer.phone_number,
                content=request.content,
                display_name=f"{current_user.first_name} {current_user.last_name}".strip() or None,
            )
            # Link conversation message to WhatsApp message_id for status propagation
            if wa_msg and wa_msg.message_id and not wa_msg.message_id.startswith("temp_"):
                from app.conversations.repositories import MessageRepository as MsgRepo
                msg_repo = MsgRepo(db)
                message.external_message_id = wa_msg.message_id
                await msg_repo.update(message)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"WhatsApp dispatch failed for conv {conversation_id}: {e}")

    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "sender_type": message.sender_type.value,
        "sender_id": str(message.sender_id) if message.sender_id else None,
        "content": message.content,
        "message_type": message.message_type.value,
        "status": message.status.value,
        "sent_at": message.sent_at.isoformat()
    }


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Delete a conversation and all its messages, notes, and related WhatsApp messages"""
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_by_id(UUID(conversation_id))
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if str(conversation.company_id) != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    deleted = await conversation_service.delete_conversation(UUID(conversation_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete conversation")
    return {"status": "deleted", "id": conversation_id}


@router.delete("/conversations/{conversation_id}/messages/{message_id}", status_code=status.HTTP_200_OK)
async def delete_message(
    conversation_id: str,
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Delete a single message from a conversation"""
    conv_service = ConversationService(db)
    conversation = await conv_service.get_by_id(UUID(conversation_id))
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if str(conversation.company_id) != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    message_service = MessageService(db)
    msg = await message_service.get_by_id(UUID(message_id))
    if not msg or str(msg.conversation_id) != conversation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    deleted = await message_service.delete_message(UUID(message_id))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete message")
    return {"status": "deleted", "id": message_id}
