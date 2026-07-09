"""Analytics Services"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from sqlalchemy.orm import selectinload

from app.analytics.models import AnalyticsMetric, AnalyticsReport, ReportType
from app.analytics.repositories import AnalyticsMetricRepository, AnalyticsReportRepository
from app.conversations.models import Conversation, ConversationStatus, Message
from app.conversations.repositories import ConversationRepository, MessageRepository
from app.users.models import User
from app.users.repositories import UserRepository


class AnalyticsService:
    """Service for tracking and querying analytics metrics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.metric_repository = AnalyticsMetricRepository(db)
        self.report_repository = AnalyticsReportRepository(db)
    
    async def track_metric(
        self,
        company_id: UUID,
        metric_name: str,
        metric_value: float,
        dimensions: Optional[Dict[str, Any]] = None
    ) -> AnalyticsMetric:
        """Track a single metric"""
        metric = AnalyticsMetric(
            company_id=company_id,
            metric_name=metric_name,
            metric_value=metric_value,
            dimensions=dimensions
        )
        return await self.metric_repository.create(metric)
    
    async def get_conversation_stats(
        self,
        company_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get conversation statistics"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        conversation_repo = ConversationRepository(self.db)
        
        # Get total conversations
        total_conversations = await conversation_repo.get_by_company_id(company_id)
        
        # Get conversations by status
        status_counts = {}
        for status in ConversationStatus:
            conversations = await conversation_repo.get_by_status(company_id, status)
            status_counts[status.value] = len(conversations)
        
        # Get conversations in date range
        conversations_in_range = [
            c for c in total_conversations
            if start_date <= c.created_at <= end_date
        ]
        
        return {
            "total_conversations": len(total_conversations),
            "conversations_in_period": len(conversations_in_range),
            "status_breakdown": status_counts,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    async def get_message_stats(
        self,
        company_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get message statistics"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        message_repo = MessageRepository(self.db)
        
        # Get messages in date range
        messages = await message_repo.get_by_company_id(company_id)
        messages_in_range = [
            m for m in messages
            if start_date <= m.created_at <= end_date
        ]
        
        # Count by sender type
        sender_counts = {}
        for msg in messages_in_range:
            sender_type = msg.sender_type.value
            sender_counts[sender_type] = sender_counts.get(sender_type, 0) + 1
        
        return {
            "total_messages": len(messages_in_range),
            "sender_breakdown": sender_counts,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    async def get_agent_performance(
        self,
        company_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get agent performance statistics"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        user_repo = UserRepository(self.db)
        message_repo = MessageRepository(self.db)
        conversation_repo = ConversationRepository(self.db)
        
        # Get agents for company
        agents = await user_repo.get_by_company_id(company_id)
        
        performance = []
        for agent in agents:
            # Get agent's messages
            messages = await message_repo.get_by_sender_id(agent.id)
            messages_in_range = [
                m for m in messages
                if start_date <= m.created_at <= end_date
            ]
            
            # Get agent's conversations
            conversations = await conversation_repo.get_by_agent_id(agent.id)
            conversations_in_range = [
                c for c in conversations
                if start_date <= c.created_at <= end_date
            ]
            
            performance.append({
                "agent_id": str(agent.id),
                "agent_name": agent.full_name,
                "messages_sent": len(messages_in_range),
                "conversations_handled": len(conversations_in_range),
                "avg_messages_per_conversation": len(messages_in_range) / len(conversations_in_range) if conversations_in_range else 0
            })
        
        return performance
    
    async def get_ml_performance(
        self,
        company_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get ML performance statistics"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Track ML metrics from analytics
        ml_metrics = await self.metric_repository.get_by_metric_name(
            company_id,
            "ml_response",
            start_date,
            end_date
        )
        
        # Calculate average confidence
        confidence_values = [m.metric_value for m in ml_metrics]
        avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
        
        # Count ML vs Native responses
        ml_count = len([m for m in ml_metrics if m.dimensions and m.dimensions.get("source") == "ml"])
        native_count = len([m for m in ml_metrics if m.dimensions and m.dimensions.get("source") == "native"])
        
        return {
            "total_ml_responses": ml_count,
            "total_native_responses": native_count,
            "average_confidence": avg_confidence,
            "ml_response_rate": ml_count / (ml_count + native_count) if (ml_count + native_count) > 0 else 0,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    async def get_response_time_stats(
        self,
        company_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get response time statistics"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Track response time metrics
        response_time_metrics = await self.metric_repository.get_by_metric_name(
            company_id,
            "response_time",
            start_date,
            end_date
        )
        
        response_times = [m.metric_value for m in response_time_metrics]
        
        if not response_times:
            return {
                "average_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "total_responses": 0
            }
        
        return {
            "average_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "total_responses": len(response_times)
        }
    
    async def generate_report(
        self,
        company_id: UUID,
        report_name: str,
        report_type: ReportType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AnalyticsReport:
        """Generate an analytics report"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Gather all statistics
        data = {
            "conversation_stats": await self.get_conversation_stats(company_id, start_date, end_date),
            "message_stats": await self.get_message_stats(company_id, start_date, end_date),
            "agent_performance": await self.get_agent_performance(company_id, start_date, end_date),
            "ml_performance": await self.get_ml_performance(company_id, start_date, end_date),
            "response_time_stats": await self.get_response_time_stats(company_id, start_date, end_date),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        report = AnalyticsReport(
            company_id=company_id,
            report_name=report_name,
            report_type=report_type,
            data=data
        )
        
        return await self.report_repository.create(report)


class DashboardService:
    """Service for dashboard data aggregation"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_service = AnalyticsService(db)
    
    async def get_company_dashboard(
        self,
        company_id: UUID
    ) -> Dict[str, Any]:
        """Get company dashboard data"""
        # Get today's stats
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)
        
        conversation_stats = await self.analytics_service.get_conversation_stats(
            company_id,
            yesterday,
            today
        )
        
        message_stats = await self.analytics_service.get_message_stats(
            company_id,
            yesterday,
            today
        )
        
        response_time_stats = await self.analytics_service.get_response_time_stats(
            company_id,
            yesterday,
            today
        )
        
        # Get active agents count
        user_repo = UserRepository(self.db)
        agents = await user_repo.get_by_company_id(company_id)
        
        # Get ML enabled status
        from app.bot.repositories import BotConfigurationRepository
        bot_config_repo = BotConfigurationRepository(self.db)
        config = await bot_config_repo.get_active_configuration(company_id)
        ml_enabled = config.ml_enabled if config else False
        
        return {
            "conversations_today": conversation_stats["conversations_in_period"],
            "messages_sent": message_stats["total_messages"],
            "avg_response_time": response_time_stats["average_response_time"],
            "new_customers": len([a for a in agents if a.created_at >= yesterday]),
            "ml_enabled": ml_enabled,
            "active_agents": len(agents),
            "date": today.isoformat()
        }
    
    async def get_super_admin_dashboard(self) -> Dict[str, Any]:
        """Get super admin dashboard data"""
        from app.companies.repositories import CompanyRepository
        from app.users.repositories import UserRepository
        from app.conversations.repositories import ConversationRepository
        
        company_repo = CompanyRepository(self.db)
        user_repo = UserRepository(self.db)
        conversation_repo = ConversationRepository(self.db)
        
        # Get global stats
        companies = await company_repo.get_all(skip=0, limit=10000)
        users = await user_repo.get_all(skip=0, limit=10000)
        conversations = await conversation_repo.get_all(skip=0, limit=10000)
        
        # Calculate platform usage
        today = datetime.utcnow()
        last_30_days = today - timedelta(days=30)
        
        recent_conversations = [
            c for c in conversations
            if c.created_at >= last_30_days
        ]
        
        return {
            "total_companies": len(companies),
            "total_users": len(users),
            "total_conversations": len(conversations),
            "platform_usage": len(recent_conversations),
            "date": today.isoformat()
        }
