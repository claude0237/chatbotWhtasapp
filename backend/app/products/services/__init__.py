"""Product Services"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.products.models import Product, ProductCategory
from app.products.repositories import ProductRepository, ProductCategoryRepository


class ProductService:
    """Service for managing products"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repository = ProductRepository(db)
        self.category_repository = ProductCategoryRepository(db)
    
    async def create_product(
        self,
        company_id: UUID,
        name: str,
        price: float,
        description: Optional[str] = None,
        currency: str = "EUR",
        stock: int = 0,
        images: Optional[List[str]] = None,
        category_id: Optional[UUID] = None,
        is_active: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Product:
        """Create a new product"""
        product = Product(
            company_id=company_id,
            name=name,
            description=description,
            price=price,
            currency=currency,
            stock=stock,
            images=images,
            category_id=category_id,
            extra_metadata=metadata,
            is_active=is_active
        )
        return await self.product_repository.create(product)
    
    async def update_product(
        self,
        product_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[float] = None,
        currency: Optional[str] = None,
        stock: Optional[int] = None,
        images: Optional[List[str]] = None,
        category_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Product]:
        """Update an existing product"""
        product = await self.product_repository.get_by_id(product_id)
        if not product:
            return None
        
        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if price is not None:
            product.price = price
        if currency is not None:
            product.currency = currency
        if stock is not None:
            product.stock = stock
        if images is not None:
            product.images = images
        if category_id is not None:
            product.category_id = category_id
        if is_active is not None:
            product.is_active = is_active
        if metadata is not None:
            product.extra_metadata = metadata
        
        return await self.product_repository.update(product)
    
    async def delete_product(self, product_id: UUID) -> bool:
        """Delete a product"""
        return await self.product_repository.delete(product_id)
    
    async def get_product(self, product_id: UUID) -> Optional[Product]:
        """Get a product by ID"""
        return await self.product_repository.get_by_id(product_id)
    
    async def get_company_products(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Product]:
        """Get all products for a company"""
        return await self.product_repository.get_by_company_id(
            company_id,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
    
    async def get_products_by_category(
        self,
        cat_id: UUID,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Product]:
        """Get products filtered by category ID"""
        return await self.product_repository.get_by_category_id(
            cat_id, skip=skip, limit=limit, active_only=active_only
        )

    async def search_products(
        self,
        company_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Product]:
        """Search products by name or description"""
        return await self.product_repository.search(
            company_id,
            search_term,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
    
    async def get_category_products(
        self,
        category_id: UUID,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Product]:
        """Get products by category"""
        return await self.product_repository.get_by_category_id(
            category_id,
            skip=skip,
            limit=limit,
            active_only=active_only
        )


class ProductCategoryService:
    """Service for managing product categories"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.category_repository = ProductCategoryRepository(db)
    
    async def create_category(
        self,
        company_id: UUID,
        name: str,
        is_active: bool = True,
        parent_id: Optional[UUID] = None
    ) -> ProductCategory:
        """Create a new category"""
        category = ProductCategory(
            company_id=company_id,
            name=name,
            is_active=is_active,
            parent_id=parent_id
        )
        return await self.category_repository.create(category)
    
    async def update_category(
        self,
        category_id: UUID,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        parent_id: Optional[UUID] = None
    ) -> Optional[ProductCategory]:
        """Update an existing category"""
        category = await self.category_repository.get_by_id(category_id)
        if not category:
            return None
        
        if name is not None:
            category.name = name
        if is_active is not None:
            category.is_active = is_active
        if parent_id is not None:
            category.parent_id = parent_id
        
        return await self.category_repository.update(category)
    
    async def delete_category(self, category_id: UUID) -> bool:
        """Delete a category"""
        return await self.category_repository.delete(category_id)
    
    async def get_category(self, category_id: UUID) -> Optional[ProductCategory]:
        """Get a category by ID"""
        return await self.category_repository.get_by_id(category_id)
    
    async def get_company_categories(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProductCategory]:
        """Get all categories for a company"""
        return await self.category_repository.get_by_company_id(
            company_id,
            skip=skip,
            limit=limit
        )
    
    async def get_root_categories(self, company_id: UUID) -> List[ProductCategory]:
        """Get root categories for a company"""
        return await self.category_repository.get_root_categories(company_id)
    
    async def get_child_categories(self, parent_id: UUID) -> List[ProductCategory]:
        """Get child categories by parent ID"""
        return await self.category_repository.get_by_parent_id(parent_id)
