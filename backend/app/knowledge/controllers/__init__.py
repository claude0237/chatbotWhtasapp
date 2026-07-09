"""Knowledge Controller"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.knowledge.services import KnowledgeBaseService, KnowledgeCategoryService
from app.knowledge.models import SourceType
from app.auth.dependencies import get_current_active_user, get_current_company_id
from app.users.models import User


router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


# Request/Response Schemas
class KnowledgeBaseResponse(BaseModel):
    """Knowledge base entry response schema"""
    id: str
    company_id: str
    title: str
    content: str
    category_id: Optional[str]
    source_type: str
    source_id: Optional[str]
    metadata: Optional[dict]
    version: int
    is_active: bool
    created_at: str
    updated_at: str


class KnowledgeBaseCreateRequest(BaseModel):
    """Knowledge base entry create request schema"""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    category_id: Optional[str] = None
    source_type: SourceType = SourceType.MANUAL
    source_id: Optional[str] = None
    metadata: Optional[dict] = None


class KnowledgeBaseUpdateRequest(BaseModel):
    """Knowledge base entry update request schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    category_id: Optional[str] = None
    metadata: Optional[dict] = None
    is_active: Optional[bool] = None


class KnowledgeCategoryResponse(BaseModel):
    """Knowledge category response schema"""
    id: str
    company_id: str
    name: str
    parent_id: Optional[str]
    icon: Optional[str]
    created_at: str
    updated_at: str


class KnowledgeCategoryCreateRequest(BaseModel):
    """Knowledge category create request schema"""
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)


class KnowledgeCategoryUpdateRequest(BaseModel):
    """Knowledge category update request schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)


# Knowledge Base endpoints
@router.get("")
async def get_knowledge_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get knowledge base entries for the current user's company"""
    knowledge_service = KnowledgeBaseService(db)
    
    if search:
        entries = await knowledge_service.search(company_id, search, skip, limit)
    elif category_id:
        entries = await knowledge_service.get_by_category(category_id, skip, limit)
    else:
        entries = await knowledge_service.get_by_company_id(company_id, skip, limit)
    
    return [
        {
            "id": str(e.id),
            "company_id": str(e.company_id),
            "title": e.title,
            "content": e.content,
            "category_id": str(e.category_id) if e.category_id else None,
            "source_type": e.source_type.value,
            "source_id": e.source_id,
            "metadata": e.extra_data,
            "version": e.version,
            "is_active": e.is_active,
            "created_at": e.created_at.isoformat(),
            "updated_at": e.updated_at.isoformat()
        }
        for e in entries
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_knowledge_entry(
    request: KnowledgeBaseCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Create a new knowledge base entry"""
    knowledge_service = KnowledgeBaseService(db)
    
    entry = await knowledge_service.create_entry(
        company_id=company_id,
        title=request.title,
        content=request.content,
        category_id=request.category_id,
        source_type=request.source_type,
        source_id=request.source_id,
        metadata=request.metadata
    )
    
    return {
        "id": str(entry.id),
        "company_id": str(entry.company_id),
        "title": entry.title,
        "content": entry.content,
        "category_id": str(entry.category_id) if entry.category_id else None,
        "source_type": entry.source_type.value,
        "source_id": entry.source_id,
        "metadata": entry.extra_data,
        "version": entry.version,
        "is_active": entry.is_active,
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat()
    }


@router.put("/{entry_id}")
async def update_knowledge_entry(
    entry_id: str,
    request: KnowledgeBaseUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Update knowledge base entry"""
    knowledge_service = KnowledgeBaseService(db)
    
    # Check if entry belongs to company
    entry = await knowledge_service.get_by_id(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge entry not found"
        )
    
    if str(entry.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    updated_entry = await knowledge_service.update_entry(
        entry_id=entry_id,
        title=request.title,
        content=request.content,
        category_id=request.category_id,
        metadata=request.metadata,
        is_active=request.is_active
    )
    
    return {
        "id": str(updated_entry.id),
        "company_id": str(updated_entry.company_id),
        "title": updated_entry.title,
        "content": updated_entry.content,
        "category_id": str(updated_entry.category_id) if updated_entry.category_id else None,
        "source_type": updated_entry.source_type.value,
        "source_id": updated_entry.source_id,
        "metadata": updated_entry.extra_data,
        "version": updated_entry.version,
        "is_active": updated_entry.is_active,
        "created_at": updated_entry.created_at.isoformat(),
        "updated_at": updated_entry.updated_at.isoformat()
    }


@router.delete("/{entry_id}")
async def delete_knowledge_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Delete knowledge base entry"""
    knowledge_service = KnowledgeBaseService(db)
    
    # Check if entry belongs to company
    entry = await knowledge_service.get_by_id(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge entry not found"
        )
    
    if str(entry.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await knowledge_service.delete_entry(entry_id)
    
    return {"message": "Knowledge entry deleted successfully"}


# Knowledge Category endpoints
@router.get("/categories")
async def get_knowledge_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get knowledge categories for the current user's company"""
    category_service = KnowledgeCategoryService(db)
    categories = await category_service.get_by_company_id(company_id, skip, limit)
    
    return [
        {
            "id": str(c.id),
            "company_id": str(c.company_id),
            "name": c.name,
            "parent_id": str(c.parent_id) if c.parent_id else None,
            "icon": c.icon,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat()
        }
        for c in categories
    ]


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_knowledge_category(
    request: KnowledgeCategoryCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Create a new knowledge category"""
    category_service = KnowledgeCategoryService(db)
    
    category = await category_service.create_category(
        company_id=company_id,
        name=request.name,
        parent_id=request.parent_id,
        icon=request.icon
    )
    
    return {
        "id": str(category.id),
        "company_id": str(category.company_id),
        "name": category.name,
        "parent_id": str(category.parent_id) if category.parent_id else None,
        "icon": category.icon,
        "created_at": category.created_at.isoformat(),
        "updated_at": category.updated_at.isoformat()
    }
