"""
Slack notification service.
"""
import os
from typing import Dict, Any, List

import requests

from services.notifications.base import BaseNotifier, NotificationType
from utils.logger import app_logger


class SlackNotifier(BaseNotifier):
    """Slack notification service using webhooks."""

    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.default_channel = os.getenv("SLACK_DEFAULT_CHANNEL", "#notifications")

    def send(
        self,
        notification_type: NotificationType,
        recipients: List[str],
        data: Dict[str, Any]
    ) -> bool:
        """Send Slack notification."""
        if not self.webhook_url:
            app_logger.warning("Slack webhook URL not configured")
            return False

        message = self._build_message(notification_type, data)

        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )

            success = response.status_code == 200
            if success:
                app_logger.info("Slack notification sent")
            else:
                app_logger.error(f"Slack error: {response.text}")

            return success

        except Exception as e:
            app_logger.error(f"Slack notification failed: {e}")
            return False

    def _build_message(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build Slack message payload with blocks."""
        color_map = {
            NotificationType.DOCUMENT_PROCESSED: "#36a64f",  # Green
            NotificationType.DOCUMENT_FAILED: "#ff0000",     # Red
            NotificationType.EXPORT_COMPLETED: "#2196f3",    # Blue
            NotificationType.QUOTA_WARNING: "#ff9800",       # Orange
        }

        title_map = {
            NotificationType.DOCUMENT_PROCESSED: ":white_check_mark: Document Processed",
            NotificationType.DOCUMENT_FAILED: ":x: Document Processing Failed",
            NotificationType.EXPORT_COMPLETED: ":outbox_tray: Export Completed",
            NotificationType.QUOTA_WARNING: ":warning: Quota Warning",
        }

        color = color_map.get(notification_type, "#808080")
        title = title_map.get(notification_type, "Notification")

        # Build fields from data
        fields = []
        for key, value in data.items():
            fields.append({
                "title": key.replace("_", " ").title(),
                "value": str(value),
                "short": True
            })

        return {
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "fields": fields,
                    "footer": "Nanonets OCR",
                    "ts": int(__import__('time').time())
                }
            ]
        }

    def send_direct_message(
        self,
        channel: str,
        text: str,
        blocks: List[Dict] = None
    ) -> bool:
        """Send a direct message to a specific channel."""
        if not self.webhook_url:
            return False

        payload = {
            "channel": channel,
            "text": text
        }

        if blocks:
            payload["blocks"] = blocks

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            return response.status_code == 200

        except Exception as e:
            app_logger.error(f"Slack DM failed: {e}")
            return False

    def health_check(self) -> bool:
        """Check Slack webhook health."""
        return bool(self.webhook_url)
