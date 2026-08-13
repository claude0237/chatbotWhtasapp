"""Logging Middleware for FastAPI"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from app.logging_config import log_performance, log_with_context


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger("api")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details"""
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Get user info if available
        user_id = None
        company_id = None
        if hasattr(request.state, 'user'):
            user_id = str(request.state.user.id) if request.state.user else None
            company_id = str(request.state.user.company_id) if request.state.user and hasattr(request.state.user, 'company_id') else None
        
        # Log request received
        log_with_context(
            self.logger,
            logging.INFO,
            "API_REQUEST_RECEIVED",
            endpoint=request.url.path,
            method=request.method,
            user_id=user_id,
            company_id=company_id,
            client_ip=client_ip,
            request_id=request_id
        )
        
        # Process request
        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log successful request
            log_with_context(
                self.logger,
                logging.INFO,
                "API_REQUEST_SUCCESS",
                endpoint=request.url.path,
                method=request.method,
                user_id=user_id,
                company_id=company_id,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
                request_id=request_id
            )
            
            # Log performance metric
            log_performance(
                self.logger,
                logging.INFO,
                "API_PERFORMANCE",
                endpoint=request.url.path,
                method=request.method,
                duration_ms=round(duration * 1000, 2),
                status_code=response.status_code
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log failed request
            log_with_context(
                self.logger,
                logging.ERROR,
                "API_REQUEST_FAILED",
                endpoint=request.url.path,
                method=request.method,
                user_id=user_id,
                company_id=company_id,
                error_message=str(e),
                duration_ms=round(duration * 1000, 2),
                request_id=request_id,
                exc_info=True
            )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers (proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
