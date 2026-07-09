"""Reservation Service"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.reservations.models import Service, AvailabilitySlot, Reservation, ReservationStatus
from app.reservations.repositories import ServiceRepository, AvailabilitySlotRepository, ReservationRepository


class ReservationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.service_repo = ServiceRepository(db)
        self.slot_repo = AvailabilitySlotRepository(db)
        self.reservation_repo = ReservationRepository(db)

    async def create_reservation(
        self,
        company_id: UUID,
        service_id: UUID,
        slot_id: UUID,
        customer_id: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> Reservation:
        """Create a new reservation and mark slot as unavailable"""
        # Verify slot is available
        slot = await self.slot_repo.get_by_id(slot_id)
        if not slot:
            raise ValueError("Slot not found")
        if not slot.is_available:
            raise ValueError("Slot is not available")

        reservation = Reservation(
            company_id=company_id,
            customer_id=customer_id,
            service_id=service_id,
            slot_id=slot_id,
            status=ReservationStatus.PENDING,
            notes=notes
        )
        reservation = await self.reservation_repo.create(reservation)
        
        # Mark slot as unavailable
        await self.slot_repo.mark_unavailable(slot_id)
        
        return reservation

    async def confirm_reservation(self, reservation_id: UUID) -> Optional[Reservation]:
        """Confirm a pending reservation"""
        reservation = await self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            return None
        if reservation.status != ReservationStatus.PENDING:
            raise ValueError(f"Cannot confirm reservation with status {reservation.status.value}")
        
        reservation.status = ReservationStatus.CONFIRMED
        reservation.confirmed_at = datetime.utcnow()
        return await self.reservation_repo.update(reservation)

    async def cancel_reservation(self, reservation_id: UUID) -> Optional[Reservation]:
        """Cancel a reservation and free up the slot"""
        reservation = await self.reservation_repo.get_by_id(reservation_id)
        if not reservation:
            return None
        if reservation.status == ReservationStatus.CANCELLED:
            raise ValueError("Reservation is already cancelled")
        
        reservation.status = ReservationStatus.CANCELLED
        reservation.cancelled_at = datetime.utcnow()
        await self.reservation_repo.update(reservation)
        
        # Free the slot
        await self.slot_repo.mark_available(reservation.slot_id)
        
        return reservation

    async def get_available_slots(
        self,
        service_id: UUID,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[AvailabilitySlot]:
        """Get available slots for a service"""
        return await self.slot_repo.get_available_slots(service_id, from_date, to_date)

    async def get_company_reservations(
        self,
        company_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ReservationStatus] = None
    ) -> List[Reservation]:
        """Get all reservations for a company"""
        return await self.reservation_repo.get_by_company_id(company_id, skip, limit, status)

    async def get_reservation(self, reservation_id: UUID) -> Optional[Reservation]:
        return await self.reservation_repo.get_by_id(reservation_id)

    async def create_service(
        self,
        company_id: UUID,
        name: str,
        duration: int,
        description: Optional[str] = None,
        price: Optional[float] = None
    ) -> Service:
        service = Service(
            company_id=company_id,
            name=name,
            description=description,
            duration=duration,
            price=price
        )
        return await self.service_repo.create(service)

    async def get_company_services(self, company_id: UUID, active_only: bool = True) -> List[Service]:
        return await self.service_repo.get_by_company_id(company_id, active_only)

    async def add_availability_slot(
        self,
        service_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> AvailabilitySlot:
        slot = AvailabilitySlot(
            service_id=service_id,
            start_time=start_time,
            end_time=end_time,
            is_available=True
        )
        return await self.slot_repo.create(slot)
