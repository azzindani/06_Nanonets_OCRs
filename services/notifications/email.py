"""
Email notification service using SMTP or SendGrid.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List

from services.notifications.base import BaseNotifier, NotificationType
from utils.logger import app_logger


class EmailNotifier(BaseNotifier):
    """Email notification service."""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@nanonets.com")
        self.from_name = os.getenv("FROM_NAME", "Nanonets OCR")

        # SendGrid API key (alternative to SMTP)
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "")

    def send(
        self,
        notification_type: NotificationType,
        recipients: List[str],
        data: Dict[str, Any]
    ) -> bool:
        """Send email notification."""
        subject, body = self._get_email_content(notification_type, data)

        if self.sendgrid_api_key:
            return self._send_via_sendgrid(recipients, subject, body)
        else:
            return self._send_via_smtp(recipients, subject, body)

    def _get_email_content(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any]
    ) -> tuple:
        """Generate email subject and body based on notification type."""
        templates = {
            NotificationType.DOCUMENT_PROCESSED: {
                "subject": "Document Processing Complete",
                "body": """
                <h2>Document Processed Successfully</h2>
                <p>Your document has been processed.</p>
                <ul>
                    <li><strong>Document ID:</strong> {document_id}</li>
                    <li><strong>Pages:</strong> {pages}</li>
                    <li><strong>Processing Time:</strong> {processing_time}</li>
                </ul>
                <p>You can view the results in your dashboard.</p>
                """
            },
            NotificationType.DOCUMENT_FAILED: {
                "subject": "Document Processing Failed",
                "body": """
                <h2>Document Processing Failed</h2>
                <p>There was an error processing your document.</p>
                <ul>
                    <li><strong>Document ID:</strong> {document_id}</li>
                    <li><strong>Error:</strong> {error}</li>
                </ul>
                <p>Please try again or contact support.</p>
                """
            },
            NotificationType.EXPORT_COMPLETED: {
                "subject": "Data Export Complete",
                "body": """
                <h2>Export Completed</h2>
                <p>Your data export has been completed.</p>
                <ul>
                    <li><strong>Export ID:</strong> {export_id}</li>
                    <li><strong>Format:</strong> {format}</li>
                    <li><strong>Records:</strong> {records}</li>
                </ul>
                """
            },
            NotificationType.QUOTA_WARNING: {
                "subject": "Usage Quota Warning",
                "body": """
                <h2>Usage Quota Warning</h2>
                <p>You are approaching your usage limit.</p>
                <ul>
                    <li><strong>Current Usage:</strong> {current}%</li>
                    <li><strong>Limit:</strong> {limit}</li>
                </ul>
                <p>Consider upgrading your plan to avoid service interruption.</p>
                """
            }
        }

        template = templates.get(notification_type, {
            "subject": "Notification from Nanonets OCR",
            "body": "<p>You have a new notification.</p>"
        })

        subject = template["subject"]
        body = template["body"].format(**data) if data else template["body"]

        return subject, body

    def _send_via_smtp(
        self,
        recipients: List[str],
        subject: str,
        body: str
    ) -> bool:
        """Send email via SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ", ".join(recipients)

            html_part = MIMEText(body, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, recipients, msg.as_string())

            app_logger.info("Email sent via SMTP", recipients=recipients)
            return True

        except Exception as e:
            app_logger.error(f"SMTP email failed: {e}")
            return False

    def _send_via_sendgrid(
        self,
        recipients: List[str],
        subject: str,
        body: str
    ) -> bool:
        """Send email via SendGrid API."""
        try:
            import requests

            payload = {
                "personalizations": [
                    {"to": [{"email": r} for r in recipients]}
                ],
                "from": {"email": self.from_email, "name": self.from_name},
                "subject": subject,
                "content": [{"type": "text/html", "value": body}]
            }

            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.sendgrid_api_key}",
                    "Content-Type": "application/json"
                }
            )

            success = response.status_code in [200, 202]
            if success:
                app_logger.info("Email sent via SendGrid", recipients=recipients)
            else:
                app_logger.error(f"SendGrid error: {response.text}")

            return success

        except Exception as e:
            app_logger.error(f"SendGrid email failed: {e}")
            return False

    def health_check(self) -> bool:
        """Check email service health."""
        if self.sendgrid_api_key:
            return True  # Assume SendGrid is available

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=5) as server:
                server.noop()
            return True
        except:
            return False
