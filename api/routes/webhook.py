"""
Webhook registration and callback endpoints.
"""
import json
import uuid
import time
import hashlib
import hmac
from typing import Dict, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
import httpx

from api.schemas.request import WebhookRequest


router = APIRouter()


class WebhookManager:
    """Manages webhook registrations and deliveries."""

    def __init__(self):
        self._webhooks: Dict[str, dict] = {}
        self._delivery_history: List[dict] = []

    def register(self, url: str, events: List[str], secret: str = None) -> str:
        """
        Register a webhook.

        Args:
            url: Webhook URL.
            events: List of event types to subscribe to.
            secret: Shared secret for signature verification.

        Returns:
            Webhook ID.
        """
        webhook_id = str(uuid.uuid4())

        self._webhooks[webhook_id] = {
            "id": webhook_id,
            "url": url,
            "events": events,
            "secret": secret or hashlib.sha256(webhook_id.encode()).hexdigest()[:32],
            "created_at": time.time(),
            "active": True,
            "delivery_count": 0,
            "failure_count": 0
        }

        return webhook_id

    def unregister(self, webhook_id: str) -> bool:
        """Unregister a webhook."""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            return True
        return False

    def get_webhook(self, webhook_id: str) -> dict:
        """Get webhook details."""
        return self._webhooks.get(webhook_id)

    def list_webhooks(self) -> List[dict]:
        """List all registered webhooks."""
        return list(self._webhooks.values())

    def get_webhooks_for_event(self, event_type: str) -> List[dict]:
        """Get all webhooks subscribed to an event."""
        return [
            wh for wh in self._webhooks.values()
            if wh["active"] and event_type in wh["events"]
        ]

    async def deliver(self, webhook_id: str, payload: dict) -> dict:
        """
        Deliver payload to webhook.

        Args:
            webhook_id: Webhook ID.
            payload: Payload to deliver.

        Returns:
            Delivery result.
        """
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            return {"success": False, "error": "Webhook not found"}

        # Create signature
        payload_str = json.dumps(payload)
        signature = hmac.new(
            webhook["secret"].encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-ID": webhook_id,
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": str(int(time.time()))
        }

        # Deliver
        delivery_id = str(uuid.uuid4())
        result = {
            "delivery_id": delivery_id,
            "webhook_id": webhook_id,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "status_code": None,
            "error": None,
            "attempts": 0
        }

        # Retry logic
        max_attempts = 3
        for attempt in range(max_attempts):
            result["attempts"] = attempt + 1
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        webhook["url"],
                        json=payload,
                        headers=headers,
                        timeout=10.0
                    )

                result["status_code"] = response.status_code
                result["success"] = 200 <= response.status_code < 300

                if result["success"]:
                    webhook["delivery_count"] += 1
                    break
                else:
                    result["error"] = f"HTTP {response.status_code}"

            except Exception as e:
                result["error"] = str(e)

            # Wait before retry
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)

        if not result["success"]:
            webhook["failure_count"] += 1

        self._delivery_history.append(result)
        return result

    def get_delivery_history(self, webhook_id: str = None, limit: int = 100) -> List[dict]:
        """Get webhook delivery history."""
        history = self._delivery_history

        if webhook_id:
            history = [d for d in history if d["webhook_id"] == webhook_id]

        return history[-limit:]


# Global webhook manager
webhook_manager = WebhookManager()


@router.post("/webhooks/register")
async def register_webhook(request: WebhookRequest):
    """
    Register a new webhook.

    Args:
        request: Webhook registration request.

    Returns:
        Webhook registration details.
    """
    webhook_id = webhook_manager.register(
        url=request.url,
        events=request.events,
        secret=request.secret
    )

    webhook = webhook_manager.get_webhook(webhook_id)

    return {
        "webhook_id": webhook_id,
        "url": webhook["url"],
        "events": webhook["events"],
        "secret": webhook["secret"],
        "created_at": datetime.fromtimestamp(webhook["created_at"]).isoformat()
    }


@router.delete("/webhooks/{webhook_id}")
async def unregister_webhook(webhook_id: str):
    """Unregister a webhook."""
    if webhook_manager.unregister(webhook_id):
        return {"message": "Webhook unregistered"}

    raise HTTPException(status_code=404, detail="Webhook not found")


@router.get("/webhooks")
async def list_webhooks():
    """List all registered webhooks."""
    webhooks = webhook_manager.list_webhooks()

    return {
        "webhooks": [
            {
                "id": wh["id"],
                "url": wh["url"],
                "events": wh["events"],
                "active": wh["active"],
                "delivery_count": wh["delivery_count"],
                "failure_count": wh["failure_count"]
            }
            for wh in webhooks
        ]
    }


@router.get("/webhooks/{webhook_id}")
async def get_webhook(webhook_id: str):
    """Get webhook details."""
    webhook = webhook_manager.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {
        "id": webhook["id"],
        "url": webhook["url"],
        "events": webhook["events"],
        "active": webhook["active"],
        "created_at": datetime.fromtimestamp(webhook["created_at"]).isoformat(),
        "delivery_count": webhook["delivery_count"],
        "failure_count": webhook["failure_count"]
    }


@router.get("/webhooks/{webhook_id}/history")
async def get_webhook_history(webhook_id: str, limit: int = 100):
    """Get webhook delivery history."""
    history = webhook_manager.get_delivery_history(webhook_id, limit)

    return {"deliveries": history}


async def trigger_webhook_event(event_type: str, payload: dict, background_tasks: BackgroundTasks):
    """
    Trigger webhooks for an event.

    Args:
        event_type: Event type (e.g., 'document.processed').
        payload: Event payload.
        background_tasks: FastAPI background tasks.
    """
    webhooks = webhook_manager.get_webhooks_for_event(event_type)

    event_payload = {
        "event": event_type,
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "data": payload
    }

    for webhook in webhooks:
        background_tasks.add_task(
            webhook_manager.deliver,
            webhook["id"],
            event_payload
        )


# Import asyncio for retry sleep
import asyncio
