"""Channel Controller"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from uuid import UUID

from app.database import get_db
from app.channels.services import ChannelService
from app.channels.repositories import ChannelRepository, ChannelConfigurationRepository, ChannelCredentialRepository
from app.channels.models import ChannelType, ChannelStatus, Channel, ChannelConfiguration, ChannelCredential
from app.auth.dependencies import get_current_active_user, get_current_company_id
from app.users.models import User
from app.utils.encryption import encrypt_credential


router = APIRouter(prefix="/channels", tags=["Channels"])


class ChannelCreateRequest(BaseModel):
    """Request schema for creating a channel"""
    channel_type: str = Field(..., description="Channel type (WHATSAPP, EMAIL, SMS, etc.)")
    name: str = Field(..., min_length=1, max_length=255)
    configuration: Optional[dict] = None


class ChannelUpdateRequest(BaseModel):
    """Request schema for updating a channel"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = None
    configuration: Optional[dict] = None


class ChannelResponse(BaseModel):
    """Response schema for channel"""
    id: str
    company_id: str
    channel_type: str
    name: str
    status: str
    created_at: str
    updated_at: str


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_channel(
    request: ChannelCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Create a new channel"""
    channel_service = ChannelService(db)
    
    try:
        channel = await channel_service.create_channel(
            company_id=UUID(company_id),
            channel_type=request.channel_type,
            name=request.name,
            configuration=request.configuration
        )
        return channel
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/")
async def get_channels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get channels for the current user's company"""
    channel_repo = ChannelRepository(db)
    
    channels = await channel_repo.get_by_company_id(
        company_id=UUID(company_id),
        skip=skip,
        limit=limit
    )
    
    return [
        {
            "id": str(channel.id),
            "company_id": str(channel.company_id),
            "channel_type": channel.channel_type.value,
            "name": channel.name,
            "status": channel.status.value,
            "created_at": channel.created_at.isoformat(),
            "updated_at": channel.updated_at.isoformat()
        }
        for channel in channels
    ]


@router.get("/{channel_id}")
async def get_channel(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get a specific channel"""
    channel_repo = ChannelRepository(db)
    
    channel = await channel_repo.get_by_id(UUID(channel_id))
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    # Verify channel belongs to user's company
    if str(channel.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": str(channel.id),
        "company_id": str(channel.company_id),
        "channel_type": channel.channel_type.value,
        "name": channel.name,
        "status": channel.status.value,
        "created_at": channel.created_at.isoformat(),
        "updated_at": channel.updated_at.isoformat()
    }


@router.put("/{channel_id}")
async def update_channel(
    channel_id: str,
    request: ChannelUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Update a channel"""
    channel_repo = ChannelRepository(db)
    
    channel = await channel_repo.get_by_id(UUID(channel_id))
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    # Verify channel belongs to user's company
    if str(channel.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update channel
    if request.name:
        channel.name = request.name
    if request.status:
        channel.status = ChannelStatus(request.status)
    
    await channel_repo.update(channel)
    
    return {
        "id": str(channel.id),
        "company_id": str(channel.company_id),
        "channel_type": channel.channel_type.value,
        "name": channel.name,
        "status": channel.status.value,
        "created_at": channel.created_at.isoformat(),
        "updated_at": channel.updated_at.isoformat()
    }


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Delete a channel"""
    channel_repo = ChannelRepository(db)
    
    channel = await channel_repo.get_by_id(UUID(channel_id))
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    # Verify channel belongs to user's company
    if str(channel.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await channel_repo.delete(UUID(channel_id))
    
    return {"message": "Channel deleted successfully"}


@router.post("/{channel_id}/verify")
async def verify_channel(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Verify a channel configuration"""
    channel_repo = ChannelRepository(db)
    
    channel = await channel_repo.get_by_id(UUID(channel_id))
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    # Verify channel belongs to user's company
    if str(channel.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # For now, return a placeholder response
    # In production, this would actually verify the channel credentials
    return {
        "channel_id": channel_id,
        "verified": True,
        "message": "Channel verification successful"
    }


@router.post("/{channel_id}/test")
async def test_channel(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Send a test message through the channel"""
    channel_repo = ChannelRepository(db)
    
    channel = await channel_repo.get_by_id(UUID(channel_id))
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    # Verify channel belongs to user's company
    if str(channel.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # For now, return a placeholder response
    # In production, this would actually send a test message
    return {
        "channel_id": channel_id,
        "test_sent": True,
        "message": "Test message sent successfully"
    }


class WhatsAppCredentialsRequest(BaseModel):
    """Request to save WhatsApp credentials for a company"""
    phone_number_id: str = Field(..., min_length=5, max_length=100)
    access_token: str = Field(..., min_length=10)
    waba_id: Optional[str] = Field(None, max_length=100)
    display_phone_number: Optional[str] = Field(None, max_length=20)


@router.post("/whatsapp/credentials", status_code=status.HTTP_201_CREATED)
async def save_whatsapp_credentials(
    request: WhatsAppCredentialsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Save or update WhatsApp credentials for the current company"""
    channel_repo = ChannelRepository(db)
    config_repo = ChannelConfigurationRepository(db)
    cred_repo = ChannelCredentialRepository(db)

    # Get or create the WHATSAPP channel for this company
    channel = await channel_repo.get_by_type(UUID(company_id), ChannelType.WHATSAPP)
    if not channel:
        channel = Channel(
            company_id=UUID(company_id),
            channel_type=ChannelType.WHATSAPP,
            name="WhatsApp",
            status=ChannelStatus.ACTIVE
        )
        db.add(channel)
        await db.commit()
        await db.refresh(channel)

    # Save/update phone_number_id in configurations
    for key, value in [
        ("phone_number_id", request.phone_number_id),
        ("waba_id", request.waba_id or ""),
        ("display_phone_number", request.display_phone_number or ""),
    ]:
        existing = await config_repo.get_by_key(channel.id, key)
        if existing:
            existing.value = value
            await config_repo.update(existing)
        else:
            db.add(ChannelConfiguration(channel_id=channel.id, key=key, value=value))
    await db.commit()

    # Save/update access_token encrypted
    encrypted_token = encrypt_credential(request.access_token)
    existing_cred = await cred_repo.get_by_type(channel.id, "ACCESS_TOKEN")
    if existing_cred:
        existing_cred.encrypted_value = encrypted_token
        await cred_repo.update(existing_cred)
    else:
        db.add(ChannelCredential(
            channel_id=channel.id,
            credential_type="ACCESS_TOKEN",
            encrypted_value=encrypted_token
        ))
    await db.commit()

    return {
        "channel_id": str(channel.id),
        "company_id": company_id,
        "phone_number_id": request.phone_number_id,
        "display_phone_number": request.display_phone_number,
        "status": channel.status.value,
        "message": "Credentials saved successfully"
    }


@router.get("/whatsapp/credentials")
async def get_whatsapp_credentials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get WhatsApp configuration for the current company (token masked)"""
    channel_repo = ChannelRepository(db)
    config_repo = ChannelConfigurationRepository(db)
    cred_repo = ChannelCredentialRepository(db)

    channel = await channel_repo.get_by_type(UUID(company_id), ChannelType.WHATSAPP)
    if not channel:
        return {"configured": False}

    configs = await config_repo.get_by_channel_id(channel.id)
    config_map = {c.key: c.value for c in configs}

    cred = await cred_repo.get_by_type(channel.id, "ACCESS_TOKEN")
    token_masked = ("*" * 20 + cred.encrypted_value[-6:]) if cred else None

    return {
        "configured": True,
        "channel_id": str(channel.id),
        "status": channel.status.value,
        "phone_number_id": config_map.get("phone_number_id"),
        "waba_id": config_map.get("waba_id"),
        "display_phone_number": config_map.get("display_phone_number"),
        "access_token_masked": token_masked,
    }
