"""Multi-tenant Middleware"""
from typing import Callable
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Query
from sqlalchemy import and_


class TenantMiddleware:
    """Middleware for multi-tenant isolation"""
    
    @staticmethod
    def filter_by_company(query: Query, company_id: str) -> Query:
        """Filter query by company_id for multi-tenant isolation"""
        return query.filter(
            and_(
                *[
                    getattr(model, 'company_id') == company_id
                    for model in query.column_descriptions
                    if hasattr(model, 'company_id')
                ]
            )
        )
    
    @staticmethod
    def check_company_access(user_company_id: str, resource_company_id: str) -> bool:
        """Check if user has access to a resource"""
        return user_company_id == resource_company_id


async def require_company_access(request: Request, call_next: Callable):
    """Middleware to check company access for all requests"""
    # This middleware can be used to add company_id filtering to all requests
    # For now, we'll use dependency injection in specific endpoints
    response = await call_next(request)
    return response
