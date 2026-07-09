"""Reservation Repositories"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.reservations.models import Service, AvailabilitySlot, Reservation, ReservationStatus


class ServiceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, service: Service) -> Service:
        self.db.add(service)
        await self.db.commit()
        await self.db.refresh(service)
        return service

    async def get_by_id(self, service_id: UUID) -> Optional[Service]:
        result = await self.db.execute(select(Service).where(Service.id == service_id))
        return result.scalar_one_or_none()

    async def get_by_company_id(self, company_id: UUID, active_only: bool = True) -> List[Service]:
        query = select(Service).where(Service.company_id == company_id)
        if active_only:
            query = query.where(Service.is_active == True)
        result = await self.db.execute(query.order_by(Service.name))
        return result.scalars().all()

    async def update(self, service: Service) -> Service:
        await self.db.commit()
        await self.db.refresh(service)
        return service

    async def delete(self, service_id: UUID) -> bool:
        service = await self.get_by_id(service_id)
        if service:
            await self.db.delete(service)
            await self.db.commit()
            return True
        return False


class AvailabilitySlotRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        self.db.add(slot)
        await self.db.commit()
        await self.db.refresh(slot)
        return slot

    async def get_by_id(self, slot_id: UUID) -> Optional[AvailabilitySlot]:
        result = await self.db.execute(select(AvailabilitySlot).where(AvailabilitySlot.id == slot_id))
        return result.scalar_one_or_none()

    async def get_available_slots(
        self,
        service_id: UUID,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[AvailabilitySlot]:
        query = select(AvailabilitySlot).where(
            and_(
                AvailabilitySlot.service_id == service_id,
                AvailabilitySlot.is_available == True
            )
        )
        if from_date:
            query = query.where(AvailabilitySlot.start_time >= from_date)
        if to_date:
            query = query.where(AvailabilitySlot.start_time <= to_date)
        result = await self.db.execute(query.order_by(AvailabilitySlot.start_time))
        return result.scalars().all()

    async def mark_unavailable(self, slot_id: UUID) -> Optional[AvailabilitySlot]:
        slot = await self.get_by_id(slot_id)
        if slot:
            slot.is_available = False
            await self.db.commit()
            await self.db.refresh(slot)
        return slot

    async def mark_available(self, slot_id: UUID) -> Optional[AvailabilitySlot]:
        slot = await self.get_by_id(slot_id)
        if slot:
            slot.is_available = True
            await self.db.commit()
            await self.db.refresh(slot)
        return slot

    async def delete(self, slot_id: UUID) -> bool:
        slot = await self.get_by_id(slot_id)
        if slot:
            await self.db.delete(slot)
            await self.db.commit()
            return True
        return False


class ReservationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, reservation: Reservation) -> Reservation:
        self.db.add(reservation)
        await self.db.commit()
        await self.db.refresh(reservation)
        return reservation

    async def get_by_id(self, reservation_id: UUID) -> Optional[Reservation]:
        result = await self.db.execute(select(Reservation).where(Reservation.id == reservation_id))
        return result.scalar_one_or_none()

    async def get_by_company_id(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ReservationStatus] = None
    ) -> List[Reservation]:
        query = select(Reservation).where(Reservation.company_id == company_id)
        if status:
            query = query.where(Reservation.status == status)
        result = await self.db.execute(
            query.order_by(Reservation.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_customer_id(self, customer_id: UUID) -> List[Reservation]:
        result = await self.db.execute(
            select(Reservation)
            .where(Reservation.customer_id == customer_id)
            .order_by(Reservation.created_at.desc())
        )
        return result.scalars().all()

    async def update(self, reservation: Reservation) -> Reservation:
        await self.db.commit()
        await self.db.refresh(reservation)
        return reservation

    async def delete(self, reservation_id: UUID) -> bool:
        reservation = await self.get_by_id(reservation_id)
        if reservation:
            await self.db.delete(reservation)
            await self.db.commit()
            return True
        return False
