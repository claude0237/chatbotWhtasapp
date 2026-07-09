"""Unit tests for ProductService"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch

from app.products.models import Product
from app.products.services import ProductService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def product_service(mock_db):
    return ProductService(mock_db)


def make_product(**kwargs) -> Product:
    defaults = dict(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        name="Test Product",
        price=29.99,
        currency="EUR",
        stock=10,
        is_active=True,
    )
    defaults.update(kwargs)
    return Product(**defaults)


class TestProductService:

    @pytest.mark.asyncio
    async def test_create_product(self, product_service):
        company_id = uuid.uuid4()
        expected = make_product(company_id=company_id)

        with patch.object(product_service.product_repository, "create", return_value=expected):
            result = await product_service.create_product(
                company_id=company_id,
                name="Test Product",
                price=29.99,
            )

        assert result.name == "Test Product"
        assert result.price == 29.99
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_update_product_partial(self, product_service):
        product = make_product(name="Old Name", price=10.0)
        updated = make_product(id=product.id, name="New Name", price=20.0)

        with patch.object(product_service.product_repository, "get_by_id", return_value=product), \
             patch.object(product_service.product_repository, "update", return_value=updated):

            result = await product_service.update_product(
                product_id=product.id,
                name="New Name",
                price=20.0,
            )

        assert result.name == "New Name"
        assert result.price == 20.0

    @pytest.mark.asyncio
    async def test_update_product_not_found(self, product_service):
        with patch.object(product_service.product_repository, "get_by_id", return_value=None):
            result = await product_service.update_product(
                product_id=uuid.uuid4(),
                name="New Name",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_product(self, product_service):
        with patch.object(product_service.product_repository, "delete", return_value=True):
            result = await product_service.delete_product(uuid.uuid4())

        assert result is True

    @pytest.mark.asyncio
    async def test_search_products(self, product_service):
        company_id = uuid.uuid4()
        products = [make_product(name="Widget A"), make_product(name="Widget B")]

        with patch.object(product_service.product_repository, "search", return_value=products):
            result = await product_service.search_products(company_id, "Widget")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_company_products_active_only(self, product_service):
        company_id = uuid.uuid4()
        active = [make_product(is_active=True)]

        with patch.object(
            product_service.product_repository, "get_by_company_id",
            return_value=active
        ) as mock_repo:
            result = await product_service.get_company_products(company_id, active_only=True)

        mock_repo.assert_called_once_with(company_id, skip=0, limit=100, active_only=True)
        assert len(result) == 1
