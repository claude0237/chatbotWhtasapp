"""Unit tests for ReservationService"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.reservations.models import AvailabilitySlot, Reservation, ReservationStatus
from app.reservations.services import ReservationService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def reservation_service(mock_db):
    return ReservationService(mock_db)


def make_slot(available=True) -> AvailabilitySlot:
    now = datetime.utcnow()
    return AvailabilitySlot(
        id=uuid.uuid4(),
        service_id=uuid.uuid4(),
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
        is_available=available,
    )


def make_reservation(status=ReservationStatus.PENDING) -> Reservation:
    return Reservation(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        service_id=uuid.uuid4(),
        slot_id=uuid.uuid4(),
        status=status,
    )


class TestReservationService:

    @pytest.mark.asyncio
    async def test_create_reservation_success(self, reservation_service):
        slot = make_slot(available=True)
        expected = make_reservation()

        with patch.object(reservation_service.slot_repo, "get_by_id", return_value=slot), \
             patch.object(reservation_service.reservation_repo, "create", return_value=expected), \
             patch.object(reservation_service.slot_repo, "mark_unavailable", return_value=slot):

            result = await reservation_service.create_reservation(
                company_id=uuid.uuid4(),
                service_id=uuid.uuid4(),
                slot_id=slot.id,
            )

        assert result.status == ReservationStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_reservation_slot_not_found(self, reservation_service):
        with patch.object(reservation_service.slot_repo, "get_by_id", return_value=None):
            with pytest.raises(ValueError, match="Slot not found"):
                await reservation_service.create_reservation(
                    company_id=uuid.uuid4(),
                    service_id=uuid.uuid4(),
                    slot_id=uuid.uuid4(),
                )

    @pytest.mark.asyncio
    async def test_create_reservation_slot_unavailable(self, reservation_service):
        slot = make_slot(available=False)

        with patch.object(reservation_service.slot_repo, "get_by_id", return_value=slot):
            with pytest.raises(ValueError, match="not available"):
                await reservation_service.create_reservation(
                    company_id=uuid.uuid4(),
                    service_id=uuid.uuid4(),
                    slot_id=slot.id,
                )

    @pytest.mark.asyncio
    async def test_confirm_reservation_success(self, reservation_service):
        reservation = make_reservation(ReservationStatus.PENDING)
        confirmed = Reservation(**{**reservation.__dict__, "status": ReservationStatus.CONFIRMED})

        with patch.object(reservation_service.reservation_repo, "get_by_id", return_value=reservation), \
             patch.object(reservation_service.reservation_repo, "update", return_value=confirmed):

            result = await reservation_service.confirm_reservation(reservation.id)

        assert result.status == ReservationStatus.CONFIRMED

    @pytest.mark.asyncio
    async def test_confirm_already_confirmed_raises(self, reservation_service):
        reservation = make_reservation(ReservationStatus.CONFIRMED)

        with patch.object(reservation_service.reservation_repo, "get_by_id", return_value=reservation):
            with pytest.raises(ValueError, match="Cannot confirm"):
                await reservation_service.confirm_reservation(reservation.id)

    @pytest.mark.asyncio
    async def test_cancel_reservation_frees_slot(self, reservation_service):
        reservation = make_reservation(ReservationStatus.CONFIRMED)
        cancelled = Reservation(**{**reservation.__dict__, "status": ReservationStatus.CANCELLED})
        slot = make_slot(available=False)

        with patch.object(reservation_service.reservation_repo, "get_by_id", return_value=reservation), \
             patch.object(reservation_service.reservation_repo, "update", return_value=cancelled), \
             patch.object(reservation_service.slot_repo, "mark_available", return_value=slot) as mock_free:

            result = await reservation_service.cancel_reservation(reservation.id)

        assert result.status == ReservationStatus.CANCELLED
        mock_free.assert_called_once_with(reservation.slot_id)

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled_raises(self, reservation_service):
        reservation = make_reservation(ReservationStatus.CANCELLED)

        with patch.object(reservation_service.reservation_repo, "get_by_id", return_value=reservation):
            with pytest.raises(ValueError, match="already cancelled"):
                await reservation_service.cancel_reservation(reservation.id)

    @pytest.mark.asyncio
    async def test_get_available_slots(self, reservation_service):
        service_id = uuid.uuid4()
        slots = [make_slot(), make_slot()]

        with patch.object(reservation_service.slot_repo, "get_available_slots", return_value=slots):
            result = await reservation_service.get_available_slots(service_id)

        assert len(result) == 2
