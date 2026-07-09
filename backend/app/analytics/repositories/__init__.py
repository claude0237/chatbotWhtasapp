"""Analytics Repositories"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.models import AnalyticsMetric, AnalyticsReport


class AnalyticsMetricRepository:
    """Repository for AnalyticsMetric model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, metric: AnalyticsMetric) -> AnalyticsMetric:
        """Create a new metric"""
        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)
        return metric
    
    async def get_by_id(self, metric_id: UUID) -> Optional[AnalyticsMetric]:
        """Get metric by ID"""
        result = await self.db.execute(
            select(AnalyticsMetric).where(AnalyticsMetric.id == metric_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(
        self,
        company_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AnalyticsMetric]:
        """Get metrics by company ID with date range"""
        query = select(AnalyticsMetric).where(AnalyticsMetric.company_id == company_id)
        
        if start_date:
            query = query.where(AnalyticsMetric.timestamp >= start_date)
        if end_date:
            query = query.where(AnalyticsMetric.timestamp <= end_date)
        
        query = query.order_by(AnalyticsMetric.timestamp.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_metric_name(
        self,
        company_id: UUID,
        metric_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AnalyticsMetric]:
        """Get metrics by name for a company"""
        query = select(AnalyticsMetric).where(
            and_(
                AnalyticsMetric.company_id == company_id,
                AnalyticsMetric.metric_name == metric_name
            )
        )
        
        if start_date:
            query = query.where(AnalyticsMetric.timestamp >= start_date)
        if end_date:
            query = query.where(AnalyticsMetric.timestamp <= end_date)
        
        query = query.order_by(AnalyticsMetric.timestamp.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def delete(self, metric_id: UUID) -> bool:
        """Delete metric by ID"""
        metric = await self.get_by_id(metric_id)
        if metric:
            await self.db.delete(metric)
            await self.db.commit()
            return True
        return False


class AnalyticsReportRepository:
    """Repository for AnalyticsReport model"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, report: AnalyticsReport) -> AnalyticsReport:
        """Create a new report"""
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report
    
    async def get_by_id(self, report_id: UUID) -> Optional[AnalyticsReport]:
        """Get report by ID"""
        result = await self.db.execute(
            select(AnalyticsReport).where(AnalyticsReport.id == report_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_company_id(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[AnalyticsReport]:
        """Get reports by company ID with pagination"""
        result = await self.db.execute(
            select(AnalyticsReport)
            .where(AnalyticsReport.company_id == company_id)
            .order_by(AnalyticsReport.generated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_report_type(
        self,
        company_id: UUID,
        report_type: str
    ) -> List[AnalyticsReport]:
        """Get reports by type for a company"""
        result = await self.db.execute(
            select(AnalyticsReport)
            .where(
                and_(
                    AnalyticsReport.company_id == company_id,
                    AnalyticsReport.report_type == report_type
                )
            )
            .order_by(AnalyticsReport.generated_at.desc())
        )
        return result.scalars().all()
    
    async def delete(self, report_id: UUID) -> bool:
        """Delete report by ID"""
        report = await self.get_by_id(report_id)
        if report:
            await self.db.delete(report)
            await self.db.commit()
            return True
        return False
