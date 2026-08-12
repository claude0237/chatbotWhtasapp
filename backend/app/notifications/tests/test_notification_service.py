"""Unit tests for NotificationService"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch

from app.notifications.models import Notification, NotificationPreference, NotificationType, NotificationChannel
from app.notifications.services import NotificationService


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.fixture
def notification_service(mock_db):
    return NotificationService(mock_db)


class TestNotificationService:

    @pytest.mark.asyncio
    async def test_create_notification_respects_disabled_preference(self, notification_service, mock_db):
        """Should not create notification if user disabled that type"""
        user_id = uuid.uuid4()
        pref = NotificationPreference(
            id=uuid.uuid4(),
            user_id=user_id,
            notification_type=NotificationType.NEW_CONVERSATION,
            enabled=False,
            channel=NotificationChannel.IN_APP,
        )

        with patch.object(
            notification_service.preference_repository, "get_by_user_and_type",
            return_value=pref
        ):
            result = await notification_service.create_notification(
                user_id=user_id,
                notification_type=NotificationType.NEW_CONVERSATION,
                title="New conversation",
                message="You have a new conversation"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_create_notification_when_preference_enabled(self, notification_service, mock_db):
        """Should create notification when preference enabled"""
        user_id = uuid.uuid4()
        pref = NotificationPreference(
            id=uuid.uuid4(),
            user_id=user_id,
            notification_type=NotificationType.NEW_CONVERSATION,
            enabled=True,
            channel=NotificationChannel.IN_APP,
        )
        expected = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            notification_type=NotificationType.NEW_CONVERSATION,
            title="New conversation",
            message="You have a new conversation",
            is_read=False,
        )

        with patch.object(
            notification_service.preference_repository, "get_by_user_and_type",
            return_value=pref
        ), patch.object(
            notification_service.notification_repository, "create",
            return_value=expected
        ):
            result = await notification_service.create_notification(
                user_id=user_id,
                notification_type=NotificationType.NEW_CONVERSATION,
                title="New conversation",
                message="You have a new conversation"
            )

        assert result is not None
        assert result.user_id == user_id
        assert result.is_read is False

    @pytest.mark.asyncio
    async def test_mark_as_read(self, notification_service):
        """Should mark notification as read"""
        notification_id = uuid.uuid4()
        notification = Notification(
            id=notification_id,
            user_id=uuid.uuid4(),
            notification_type=NotificationType.SYSTEM,
            title="Test",
            message="Test",
            is_read=False,
        )
        updated = Notification(**{**notification.__dict__, "is_read": True})

        with patch.object(
            notification_service.notification_repository, "get_by_id",
            return_value=notification
        ), patch.object(
            notification_service.notification_repository, "update",
            return_value=updated
        ):
            result = await notification_service.mark_as_read(notification_id)

        assert result.is_read is True

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, notification_service):
        """Should return None when notification not found"""
        with patch.object(
            notification_service.notification_repository, "get_by_id",
            return_value=None
        ):
            result = await notification_service.mark_as_read(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_unread_count(self, notification_service):
        """Should return unread count"""
        user_id = uuid.uuid4()
        with patch.object(
            notification_service.notification_repository, "get_unread_count",
            return_value=5
        ):
            count = await notification_service.get_unread_count(user_id)

        assert count == 5

    @pytest.mark.asyncio
    async def test_set_preference_creates_if_not_exists(self, notification_service):
        """Should create preference if not exists"""
        user_id = uuid.uuid4()
        new_pref = NotificationPreference(
            id=uuid.uuid4(),
            user_id=user_id,
            notification_type=NotificationType.MENTION,
            enabled=True,
            channel=NotificationChannel.EMAIL,
        )
        with patch.object(
            notification_service.preference_repository, "get_by_user_and_type",
            return_value=None
        ), patch.object(
            notification_service.preference_repository, "create",
            return_value=new_pref
        ):
            result = await notification_service.set_preference(
                user_id, NotificationType.MENTION, True, NotificationChannel.EMAIL
            )

        assert result.enabled is True
        assert result.channel == NotificationChannel.EMAIL
