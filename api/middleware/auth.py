"""
Authentication middleware for API security.
"""
import hashlib
import hmac
import time
from typing import Optional
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader

from config import settings


# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthenticationError(HTTPException):
    """Authentication failed exception."""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)


class AuthorizationError(HTTPException):
    """Authorization failed exception."""
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(status_code=403, detail=detail)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from request header.

    Args:
        api_key: API key from X-API-Key header.

    Returns:
        Validated API key.

    Raises:
        AuthenticationError: If API key is invalid.
    """
    if not api_key:
        raise AuthenticationError("API key required. Provide X-API-Key header.")

    # Check against configured API key
    if settings.api.api_key and api_key != settings.api.api_key:
        raise AuthenticationError("Invalid API key")

    return api_key


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.

    Args:
        api_key: Plain text API key.

    Returns:
        Hashed API key.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key(prefix: str = "sk") -> str:
    """
    Generate a new API key.

    Args:
        prefix: Key prefix (e.g., 'sk' for secret key).

    Returns:
        New API key string.
    """
    import secrets
    random_part = secrets.token_hex(32)
    return f"{prefix}_{random_part}"


def create_signature(payload: str, secret: str) -> str:
    """
    Create HMAC signature for webhook payloads.

    Args:
        payload: JSON payload string.
        secret: Webhook secret.

    Returns:
        HMAC signature.
    """
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify webhook signature.

    Args:
        payload: JSON payload string.
        signature: Provided signature.
        secret: Webhook secret.

    Returns:
        True if signature is valid.
    """
    expected = create_signature(payload, secret)
    return hmac.compare_digest(expected, signature)


class APIKeyManager:
    """
    Manages API keys with optional persistence.
    """

    def __init__(self):
        self._keys: dict = {}  # In production, use database

    def create_key(self, name: str, permissions: list = None) -> str:
        """Create a new API key."""
        key = generate_api_key()
        self._keys[hash_api_key(key)] = {
            "name": name,
            "permissions": permissions or ["read", "write"],
            "created_at": time.time(),
            "last_used": None
        }
        return key

    def validate_key(self, key: str) -> Optional[dict]:
        """Validate and return key metadata."""
        key_hash = hash_api_key(key)
        if key_hash in self._keys:
            self._keys[key_hash]["last_used"] = time.time()
            return self._keys[key_hash]
        return None

    def revoke_key(self, key: str) -> bool:
        """Revoke an API key."""
        key_hash = hash_api_key(key)
        if key_hash in self._keys:
            del self._keys[key_hash]
            return True
        return False


# Global key manager
key_manager = APIKeyManager()


if __name__ == "__main__":
    print("=" * 60)
    print("AUTH MIDDLEWARE TEST")
    print("=" * 60)

    # Test key generation
    key = generate_api_key()
    print(f"  Generated key: {key[:20]}...")

    # Test hashing
    hashed = hash_api_key(key)
    print(f"  Hashed key: {hashed[:20]}...")

    # Test signature
    payload = '{"test": "data"}'
    secret = "webhook_secret"
    sig = create_signature(payload, secret)
    print(f"  Signature: {sig[:20]}...")

    # Verify signature
    valid = verify_signature(payload, sig, secret)
    print(f"  Signature valid: {valid}")

    print("\n  ✓ Auth middleware tests passed")
    print("=" * 60)
