"""Analytics Controllers"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.analytics.services import AnalyticsService, DashboardService
from app.analytics.models import ReportType
from app.auth.dependencies import get_current_active_user, get_current_company_id
from app.users.models import User


router = APIRouter(prefix="/analytics", tags=["Analytics"])


# Request/Response Schemas
class ConversationStatsResponse(BaseModel):
    """Conversation statistics response"""
    total_conversations: int
    conversations_in_period: int
    status_breakdown: dict
    start_date: str
    end_date: str


class MessageStatsResponse(BaseModel):
    """Message statistics response"""
    total_messages: int
    sender_breakdown: dict
    start_date: str
    end_date: str


class AgentPerformanceResponse(BaseModel):
    """Agent performance response"""
    agent_id: str
    agent_name: str
    messages_sent: int
    conversations_handled: int
    avg_messages_per_conversation: float


class MLPerformanceResponse(BaseModel):
    """ML performance response"""
    total_ml_responses: int
    total_native_responses: int
    average_confidence: float
    ml_response_rate: float
    start_date: str
    end_date: str


class ResponseTimeStatsResponse(BaseModel):
    """Response time statistics response"""
    average_response_time: float
    min_response_time: float
    max_response_time: float
    total_responses: int


class DashboardResponse(BaseModel):
    """Dashboard response"""
    conversations_today: int
    messages_sent: int
    avg_response_time: float
    new_customers: int
    ml_enabled: bool
    active_agents: int
    date: str


class SuperAdminDashboardResponse(BaseModel):
    """Super admin dashboard response"""
    total_companies: int
    total_users: int
    total_conversations: int
    platform_usage: int
    date: str


# Analytics endpoints
@router.get("/conversations")
async def get_conversation_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get conversation statistics"""
    analytics_service = AnalyticsService(db)
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    stats = await analytics_service.get_conversation_stats(company_id, start_dt, end_dt)
    return stats


@router.get("/messages")
async def get_message_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get message statistics"""
    analytics_service = AnalyticsService(db)
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    stats = await analytics_service.get_message_stats(company_id, start_dt, end_dt)
    return stats


@router.get("/agents")
async def get_agent_performance(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get agent performance statistics"""
    analytics_service = AnalyticsService(db)
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    performance = await analytics_service.get_agent_performance(company_id, start_dt, end_dt)
    return performance


@router.get("/ml")
async def get_ml_performance(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get ML performance statistics"""
    analytics_service = AnalyticsService(db)
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    stats = await analytics_service.get_ml_performance(company_id, start_dt, end_dt)
    return stats


@router.get("/response-time")
async def get_response_time_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get response time statistics"""
    analytics_service = AnalyticsService(db)
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    stats = await analytics_service.get_response_time_stats(company_id, start_dt, end_dt)
    return stats


@router.get("/reports")
async def generate_analytics_report(
    report_name: str = Query(...),
    report_type: str = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Generate analytics report"""
    analytics_service = AnalyticsService(db)
    
    try:
        report_type_enum = ReportType(report_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report type: {report_type}"
        )
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    report = await analytics_service.generate_report(
        company_id,
        report_name,
        report_type_enum,
        start_dt,
        end_dt
    )
    
    return {
        "id": str(report.id),
        "company_id": str(report.company_id),
        "report_name": report.report_name,
        "report_type": report.report_type.value,
        "data": report.data,
        "generated_at": report.generated_at.isoformat()
    }


# Dashboard endpoints
@router.get("/dashboard")
async def get_company_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_current_company_id)
):
    """Get company dashboard data"""
    dashboard_service = DashboardService(db)
    dashboard = await dashboard_service.get_company_dashboard(company_id)
    return dashboard


@router.get("/super-admin/dashboard")
async def get_super_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get super admin dashboard data"""
    # Check if user is super admin
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super admin only."
        )
    
    dashboard_service = DashboardService(db)
    dashboard = await dashboard_service.get_super_admin_dashboard()
    return dashboard
