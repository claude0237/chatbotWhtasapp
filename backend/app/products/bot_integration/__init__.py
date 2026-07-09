"""Product Bot Integration - Search products and build product card messages"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.products.services import ProductService
from app.products.models import Product


PRODUCT_CARD_TEMPLATE = """🛍️ *{name}*

{description}

💰 Prix : *{price} {currency}*
📦 Stock : {stock}
{category_line}
{images_line}"""


PRODUCT_LIST_TEMPLATE = """🛍️ *Voici nos produits disponibles :*

{products}

Pour plus d'informations sur un produit, tapez son nom."""


class ProductBotIntegration:
    """Integration between bot engine and product catalog"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_service = ProductService(db)
    
    async def search_products(
        self,
        company_id: UUID,
        search_term: str,
        limit: int = 5
    ) -> List[Product]:
        """Search products relevant to a user query"""
        return await self.product_service.search_products(
            company_id,
            search_term,
            limit=limit,
            active_only=True
        )
    
    async def get_product_card(self, product: Product) -> str:
        """Build a product card message for WhatsApp"""
        description = product.description or "Aucune description disponible"
        
        category_line = ""
        if product.category_id:
            category_line = f"🏷️ Catégorie disponible"
        
        images_line = ""
        if product.images:
            images_line = f"🖼️ {len(product.images)} image(s) disponible(s)"
        
        return PRODUCT_CARD_TEMPLATE.format(
            name=product.name,
            description=description,
            price=product.price,
            currency=product.currency,
            stock=f"{product.stock} en stock" if product.stock > 0 else "Rupture de stock",
            category_line=category_line,
            images_line=images_line
        ).strip()
    
    async def get_products_list_message(
        self,
        company_id: UUID,
        search_term: Optional[str] = None,
        limit: int = 5
    ) -> str:
        """Build a products list message for bot response"""
        if search_term:
            products = await self.search_products(company_id, search_term, limit)
        else:
            products = await self.product_service.get_company_products(
                company_id, limit=limit, active_only=True
            )
        
        if not products:
            return "Aucun produit disponible pour le moment."
        
        product_lines = []
        for product in products:
            stock_label = f"({product.stock} en stock)" if product.stock > 0 else "(Rupture)"
            product_lines.append(
                f"• *{product.name}* - {product.price} {product.currency} {stock_label}"
            )
        
        return PRODUCT_LIST_TEMPLATE.format(products="\n".join(product_lines))
    
    async def handle_product_query(
        self,
        company_id: UUID,
        message: str
    ) -> Optional[str]:
        """Detect if a message is a product query and respond accordingly"""
        product_keywords = [
            "produit", "produits", "article", "articles", "catalogue",
            "prix", "acheter", "commander", "stock", "disponible",
            "combien", "coût", "tarif"
        ]
        
        message_lower = message.lower()
        is_product_query = any(kw in message_lower for kw in product_keywords)
        
        if not is_product_query:
            return None
        
        # Try to find specific product
        products = await self.search_products(company_id, message, limit=3)
        
        if products:
            if len(products) == 1:
                return await self.get_product_card(products[0])
            else:
                return await self.get_products_list_message(company_id, message)
        
        # Return general product list
        return await self.get_products_list_message(company_id)
