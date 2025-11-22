"""
Base notification service.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from enum import Enum

from utils.logger import app_logger


class NotificationType(str, Enum):
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_FAILED = "document.failed"
    EXPORT_COMPLETED = "export.completed"
    USER_INVITED = "user.invited"
    QUOTA_WARNING = "quota.warning"


class NotificationService:
    """Unified notification service that dispatches to multiple channels."""

    def __init__(self):
        self.channels = {}

    def register_channel(self, name: str, notifier):
        """Register a notification channel."""
        self.channels[name] = notifier

    def send(
        self,
        notification_type: NotificationType,
        recipients: List[str],
        data: Dict[str, Any],
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        Send notification to specified channels.

        Args:
            notification_type: Type of notification
            recipients: List of recipient identifiers
            data: Notification data
            channels: List of channel names (None = all)

        Returns:
            Dict of channel -> success status
        """
        results = {}
        target_channels = channels or list(self.channels.keys())

        for channel_name in target_channels:
            if channel_name not in self.channels:
                results[channel_name] = False
                continue

            try:
                notifier = self.channels[channel_name]
                success = notifier.send(notification_type, recipients, data)
                results[channel_name] = success

                app_logger.info(
                    "Notification sent",
                    channel=channel_name,
                    type=notification_type.value,
                    success=success
                )

            except Exception as e:
                app_logger.error(
                    "Notification failed",
                    channel=channel_name,
                    error=str(e)
                )
                results[channel_name] = False

        return results


class BaseNotifier(ABC):
    """Base class for notification channels."""

    @abstractmethod
    def send(
        self,
        notification_type: NotificationType,
        recipients: List[str],
        data: Dict[str, Any]
    ) -> bool:
        """Send notification."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if channel is operational."""
        pass
