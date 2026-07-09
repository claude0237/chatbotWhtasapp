"""Product Repositories"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.products.models import Product, ProductCategory


class ProductRepository:
    """Repository for Product model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, product: Product) -> Product:
        """Create a new product"""
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product
    
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get product by ID"""
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Product]:
        """Get products by company ID with pagination"""
        query = select(Product).where(Product.company_id == company_id)
        
        if active_only:
            query = query.where(Product.is_active == True)
        
        query = query.order_by(Product.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_category_id(
        self,
        category_id: UUID,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Product]:
        """Get products by category ID with pagination"""
        query = select(Product).where(Product.category_id == category_id)
        
        if active_only:
            query = query.where(Product.is_active == True)
        
        query = query.order_by(Product.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def search(
        self,
        company_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Product]:
        """Search products by name or description"""
        query = select(Product).where(
            and_(
                Product.company_id == company_id,
                or_(
                    Product.name.ilike(f"%{search_term}%"),
                    Product.description.ilike(f"%{search_term}%")
                )
            )
        )
        
        if active_only:
            query = query.where(Product.is_active == True)
        
        query = query.order_by(Product.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update(self, product: Product) -> Product:
        """Update product"""
        await self.db.commit()
        await self.db.refresh(product)
        return product
    
    async def delete(self, product_id: UUID) -> bool:
        """Delete product by ID"""
        product = await self.get_by_id(product_id)
        if product:
            await self.db.delete(product)
            await self.db.commit()
            return True
        return False


class ProductCategoryRepository:
    """Repository for ProductCategory model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, category: ProductCategory) -> ProductCategory:
        """Create a new category"""
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def get_by_id(self, category_id: UUID) -> Optional[ProductCategory]:
        """Get category by ID"""
        result = await self.db.execute(
            select(ProductCategory).where(ProductCategory.id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProductCategory]:
        """Get categories by company ID with pagination"""
        query = select(ProductCategory).where(ProductCategory.company_id == company_id)
        query = query.order_by(ProductCategory.name.asc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_root_categories(self, company_id: UUID) -> List[ProductCategory]:
        """Get root categories (no parent) for a company"""
        query = select(ProductCategory).where(
            and_(
                ProductCategory.company_id == company_id,
                ProductCategory.parent_id.is_(None)
            )
        )
        query = query.order_by(ProductCategory.name.asc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_parent_id(self, parent_id: UUID) -> List[ProductCategory]:
        """Get child categories by parent ID"""
        query = select(ProductCategory).where(ProductCategory.parent_id == parent_id)
        query = query.order_by(ProductCategory.name.asc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update(self, category: ProductCategory) -> ProductCategory:
        """Update category"""
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def delete(self, category_id: UUID) -> bool:
        """Delete category by ID"""
        category = await self.get_by_id(category_id)
        if category:
            await self.db.delete(category)
            await self.db.commit()
            return True
        return False
