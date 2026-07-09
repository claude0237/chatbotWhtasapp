"""Product Controllers"""
from typing import Optional
from uuid import UUID as PyUUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.products.services import ProductService, ProductCategoryService
from app.auth.dependencies import get_current_active_user, get_current_company_id
from app.users.models import User


router = APIRouter(prefix="/companies/{company_id}/products", tags=["Products"])


# Request/Response Schemas
class ProductResponse(BaseModel):
    """Product response"""
    id: str
    company_id: str
    name: str
    description: Optional[str] = None
    price: float
    currency: str
    stock: int
    images: Optional[list] = None
    category_id: Optional[str] = None
    is_active: bool
    metadata: Optional[dict] = None
    created_at: str
    updated_at: str


class CreateProductRequest(BaseModel):
    """Create product request"""
    name: str
    description: Optional[str] = None
    price: float
    currency: str = "EUR"
    stock: int = 0
    images: Optional[list] = None
    category_id: Optional[str] = None
    is_active: bool = True
    metadata: Optional[dict] = None


class UpdateProductRequest(BaseModel):
    """Update product request"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    stock: Optional[int] = None
    images: Optional[list] = None
    category_id: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class ProductCategoryResponse(BaseModel):
    """Product category response"""
    id: str
    company_id: str
    name: str
    is_active: bool
    parent_id: Optional[str] = None
    created_at: str
    updated_at: str


class CreateCategoryRequest(BaseModel):
    """Create category request"""
    name: str
    is_active: bool = True
    parent_id: Optional[str] = None


class UpdateCategoryRequest(BaseModel):
    """Update category request"""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    parent_id: Optional[str] = None


# ── Category endpoints (MUST be declared before /{product_id} to avoid route conflict) ──
@router.get("/categories", response_model=list[ProductCategoryResponse])
async def get_categories(
    company_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Get categories for a company"""
    if current_company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    category_service = ProductCategoryService(db)
    categories = await category_service.get_company_categories(PyUUID(company_id), skip, limit)
    
    return [
        {
            "id": str(c.id),
            "company_id": str(c.company_id),
            "name": c.name,
            "is_active": c.is_active,
            "parent_id": str(c.parent_id) if c.parent_id else None,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat()
        }
        for c in categories
    ]


@router.post("/categories", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    company_id: str,
    request: CreateCategoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Create a new category"""
    if current_company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    category_service = ProductCategoryService(db)
    category = await category_service.create_category(
        company_id=PyUUID(company_id),
        name=request.name,
        is_active=request.is_active,
        parent_id=PyUUID(request.parent_id) if request.parent_id else None
    )
    
    return {
        "id": str(category.id),
        "company_id": str(category.company_id),
        "name": category.name,
        "is_active": category.is_active,
        "parent_id": str(category.parent_id) if category.parent_id else None,
        "created_at": category.created_at.isoformat(),
        "updated_at": category.updated_at.isoformat()
    }


@router.put("/categories/{category_id}", response_model=ProductCategoryResponse)
async def update_category(
    company_id: str,
    category_id: str,
    request: UpdateCategoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Update a category"""
    if current_company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    category_service = ProductCategoryService(db)
    category = await category_service.update_category(
        category_id=PyUUID(category_id),
        name=request.name,
        is_active=request.is_active,
        parent_id=PyUUID(request.parent_id) if request.parent_id else None
    )
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    if str(category.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": str(category.id),
        "company_id": str(category.company_id),
        "name": category.name,
        "is_active": category.is_active,
        "parent_id": str(category.parent_id) if category.parent_id else None,
        "created_at": category.created_at.isoformat(),
        "updated_at": category.updated_at.isoformat()
    }


@router.delete("/categories/{category_id}")
async def delete_category(
    company_id: str,
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Delete a category"""
    if current_company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    category_service = ProductCategoryService(db)
    category = await category_service.get_category(PyUUID(category_id))
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    if str(category.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await category_service.delete_category(PyUUID(category_id))
    return {"message": "Category deleted"}


# ── Product endpoints ────────────────────────────────────────────────────────
@router.get("", response_model=list[ProductResponse])
async def get_products(
    company_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    category_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Get products for a company"""
    if current_company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    product_service = ProductService(db)
    category_service = ProductCategoryService(db)

    if category_name:
        cats = await category_service.get_company_categories(PyUUID(company_id))
        cat = next((c for c in cats if c.name.upper() == category_name.strip().upper()), None)
        if cat:
            products = await product_service.get_products_by_category(
                cat_id=cat.id, skip=skip, limit=limit, active_only=active_only
            )
        else:
            products = []
    elif search:
        products = await product_service.search_products(
            PyUUID(company_id),
            search,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
    else:
        products = await product_service.get_company_products(
            PyUUID(company_id),
            skip=skip,
            limit=limit,
            active_only=active_only
        )
    
    return [
        {
            "id": str(p.id),
            "company_id": str(p.company_id),
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "currency": p.currency,
            "stock": p.stock,
            "images": p.images,
            "category_id": str(p.category_id) if p.category_id else None,
            "is_active": p.is_active,
            "metadata": p.extra_metadata,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat()
        }
        for p in products
    ]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    company_id: str,
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Get a specific product"""
    if current_company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    product_service = ProductService(db)
    product = await product_service.get_product(PyUUID(product_id))
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if str(product.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": str(product.id),
        "company_id": str(product.company_id),
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "currency": product.currency,
        "stock": product.stock,
        "images": product.images,
        "category_id": str(product.category_id) if product.category_id else None,
        "is_active": product.is_active,
        "metadata": product.extra_metadata,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat()
    }


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    company_id: str,
    request: CreateProductRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Create a new product"""
    if current_company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    product_service = ProductService(db)
    product = await product_service.create_product(
        company_id=PyUUID(company_id),
        name=request.name,
        description=request.description,
        price=request.price,
        currency=request.currency,
        stock=request.stock,
        images=request.images,
        category_id=PyUUID(request.category_id) if request.category_id else None,
        is_active=request.is_active,
        metadata=request.metadata
    )
    
    return {
        "id": str(product.id),
        "company_id": str(product.company_id),
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "currency": product.currency,
        "stock": product.stock,
        "images": product.images,
        "category_id": str(product.category_id) if product.category_id else None,
        "is_active": product.is_active,
        "metadata": product.extra_metadata,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat()
    }


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    company_id: str,
    product_id: str,
    request: UpdateProductRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Update a product"""
    if current_company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    product_service = ProductService(db)
    product = await product_service.update_product(
        product_id=PyUUID(product_id),
        name=request.name,
        description=request.description,
        price=request.price,
        currency=request.currency,
        stock=request.stock,
        images=request.images,
        category_id=PyUUID(request.category_id) if request.category_id else None,
        is_active=request.is_active,
        metadata=request.metadata
    )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if str(product.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "id": str(product.id),
        "company_id": str(product.company_id),
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "currency": product.currency,
        "stock": product.stock,
        "images": product.images,
        "category_id": str(product.category_id) if product.category_id else None,
        "is_active": product.is_active,
        "metadata": product.extra_metadata,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat()
    }


@router.delete("/{product_id}")
async def delete_product(
    company_id: str,
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Delete a product"""
    if current_company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    product_service = ProductService(db)
    product = await product_service.get_product(PyUUID(product_id))
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if str(product.company_id) != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await product_service.delete_product(PyUUID(product_id))
    return {"message": "Product deleted"}


