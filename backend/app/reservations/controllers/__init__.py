"""Reservations Controllers"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.reservations.services import ReservationService
from app.reservations.models import ReservationStatus
from app.auth.dependencies import get_current_active_user, get_current_company_id
from app.users.models import User


router = APIRouter(prefix="/companies/{company_id}/reservations", tags=["Reservations"])


# Schemas
class ServiceResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: Optional[str]
    duration: int
    price: Optional[float]
    is_active: bool
    created_at: str


class SlotResponse(BaseModel):
    id: str
    service_id: str
    start_time: str
    end_time: str
    is_available: bool


class ReservationResponse(BaseModel):
    id: str
    company_id: str
    customer_id: Optional[str]
    service_id: str
    slot_id: str
    status: str
    notes: Optional[str]
    confirmed_at: Optional[str]
    cancelled_at: Optional[str]
    created_at: str


class CreateReservationRequest(BaseModel):
    service_id: str
    slot_id: str
    customer_id: Optional[str]
    notes: Optional[str]


class CreateServiceRequest(BaseModel):
    name: str
    duration: int
    description: Optional[str]
    price: Optional[float]


class AddSlotRequest(BaseModel):
    service_id: str
    start_time: str
    end_time: str


def _fmt_reservation(r) -> dict:
    return {
        "id": str(r.id),
        "company_id": str(r.company_id),
        "customer_id": str(r.customer_id) if r.customer_id else None,
        "service_id": str(r.service_id),
        "slot_id": str(r.slot_id),
        "status": r.status.value,
        "notes": r.notes,
        "confirmed_at": r.confirmed_at.isoformat() if r.confirmed_at else None,
        "cancelled_at": r.cancelled_at.isoformat() if r.cancelled_at else None,
        "created_at": r.created_at.isoformat()
    }


# Reservation endpoints
@router.get("")
async def get_reservations(
    company_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Get reservations for a company"""
    if current_company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    status_enum = None
    if status:
        try:
            status_enum = ReservationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    svc = ReservationService(db)
    reservations = await svc.get_company_reservations(company_id, skip, limit, status_enum)
    return [_fmt_reservation(r) for r in reservations]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_reservation(
    company_id: str,
    request: CreateReservationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Create a new reservation"""
    if current_company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    svc = ReservationService(db)
    try:
        reservation = await svc.create_reservation(
            company_id=company_id,
            service_id=request.service_id,
            slot_id=request.slot_id,
            customer_id=request.customer_id,
            notes=request.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return _fmt_reservation(reservation)


@router.put("/{reservation_id}/confirm")
async def confirm_reservation(
    company_id: str,
    reservation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Confirm a reservation"""
    if current_company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    svc = ReservationService(db)
    try:
        reservation = await svc.confirm_reservation(reservation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return _fmt_reservation(reservation)


@router.put("/{reservation_id}/cancel")
async def cancel_reservation(
    company_id: str,
    reservation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Cancel a reservation"""
    if current_company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    svc = ReservationService(db)
    try:
        reservation = await svc.cancel_reservation(reservation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return _fmt_reservation(reservation)


# Services endpoints
@router.get("/services")
async def get_services(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Get all services for a company"""
    if current_company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    svc = ReservationService(db)
    services = await svc.get_company_services(company_id)
    return [
        {
            "id": str(s.id),
            "company_id": str(s.company_id),
            "name": s.name,
            "description": s.description,
            "duration": s.duration,
            "price": s.price,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat()
        }
        for s in services
    ]


@router.post("/services", status_code=status.HTTP_201_CREATED)
async def create_service(
    company_id: str,
    request: CreateServiceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Create a new service"""
    if current_company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    svc = ReservationService(db)
    service = await svc.create_service(
        company_id=company_id,
        name=request.name,
        duration=request.duration,
        description=request.description,
        price=request.price
    )
    return {
        "id": str(service.id),
        "company_id": str(service.company_id),
        "name": service.name,
        "description": service.description,
        "duration": service.duration,
        "price": service.price,
        "is_active": service.is_active,
        "created_at": service.created_at.isoformat()
    }


# Slots endpoints
@router.get("/slots")
async def get_slots(
    company_id: str,
    service_id: str = Query(...),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Get available slots for a service"""
    if current_company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from_dt = datetime.fromisoformat(from_date) if from_date else None
    to_dt = datetime.fromisoformat(to_date) if to_date else None
    
    svc = ReservationService(db)
    slots = await svc.get_available_slots(service_id, from_dt, to_dt)
    return [
        {
            "id": str(s.id),
            "service_id": str(s.service_id),
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(),
            "is_available": s.is_available
        }
        for s in slots
    ]


@router.post("/slots", status_code=status.HTTP_201_CREATED)
async def add_slot(
    company_id: str,
    request: AddSlotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    current_company_id: str = Depends(get_current_company_id)
):
    """Add an availability slot for a service"""
    if current_company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    svc = ReservationService(db)
    slot = await svc.add_availability_slot(
        service_id=request.service_id,
        start_time=datetime.fromisoformat(request.start_time),
        end_time=datetime.fromisoformat(request.end_time)
    )
    return {
        "id": str(slot.id),
        "service_id": str(slot.service_id),
        "start_time": slot.start_time.isoformat(),
        "end_time": slot.end_time.isoformat(),
        "is_available": slot.is_available
    }
