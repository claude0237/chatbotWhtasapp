"""Reservation Models"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ReservationStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class Service(Base):
    """Service model for bookable services"""
    
    __tablename__ = "services"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=False)  # duration in minutes
    price = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    company = relationship("Company", backref="services")
    availability_slots = relationship("AvailabilitySlot", back_populates="service", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="service")
    
    def __repr__(self):
        return f"<Service(id={self.id}, name={self.name})>"


class AvailabilitySlot(Base):
    """Availability slot for a service"""
    
    __tablename__ = "availability_slots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    service = relationship("Service", back_populates="availability_slots")
    reservation = relationship("Reservation", back_populates="slot", uselist=False)
    
    def __repr__(self):
        return f"<AvailabilitySlot(id={self.id}, start={self.start_time}, available={self.is_available})>"


class Reservation(Base):
    """Reservation model"""
    
    __tablename__ = "reservations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_id = Column(UUID(as_uuid=True), ForeignKey("availability_slots.id", ondelete="CASCADE"), nullable=False)
    
    status = Column(SQLEnum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    company = relationship("Company", backref="reservations")
    customer = relationship("Customer", backref="reservations")
    service = relationship("Service", back_populates="reservations")
    slot = relationship("AvailabilitySlot", back_populates="reservation")
    
    def __repr__(self):
        return f"<Reservation(id={self.id}, status={self.status})>"
