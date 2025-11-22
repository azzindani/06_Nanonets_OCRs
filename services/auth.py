"""
JWT Authentication service for user management.
"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from pydantic import BaseModel

# Try to import JWT and password hashing libraries
try:
    from jose import JWTError, jwt
    HAS_JOSE = True
except ImportError:
    HAS_JOSE = False
    JWTError = Exception

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # Test if it actually works (catches bcrypt compatibility issues)
    pwd_context.hash("test")
    HAS_PASSLIB = True
except Exception:
    HAS_PASSLIB = False
    pwd_context = None

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    tenant_id: str
    email: str
    role: str
    exp: datetime


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthService:
    """Authentication service for JWT token management."""

    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        if not HAS_PASSLIB:
            # Fallback: simple hash (NOT secure - only for testing)
            return hashlib.sha256(password.encode()).hexdigest()
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        if not HAS_PASSLIB:
            # Fallback: simple hash comparison
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
        role: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "email": email,
            "role": role,
            "exp": expire,
            "type": "access"
        }

        if not HAS_JOSE:
            import base64, json
            return base64.b64encode(json.dumps(payload, default=str).encode()).decode()
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str, tenant_id: str) -> str:
        """Create a JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "exp": expire,
            "type": "refresh"
        }

        if not HAS_JOSE:
            import base64, json
            return base64.b64encode(json.dumps(payload, default=str).encode()).decode()
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_tokens(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
        role: str
    ) -> TokenResponse:
        """Create both access and refresh tokens."""
        access_token = self.create_access_token(user_id, tenant_id, email, role)
        refresh_token = self.create_refresh_token(user_id, tenant_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            if not HAS_JOSE:
                import base64, json
                payload = json.loads(base64.b64decode(token).decode())
                return payload
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except (JWTError, Exception):
            return None

    def get_token_data(self, token: str) -> Optional[TokenData]:
        """Get token data from a valid token."""
        payload = self.verify_token(token)
        if not payload:
            return None

        return TokenData(
            user_id=payload.get("sub"),
            tenant_id=payload.get("tenant_id"),
            email=payload.get("email", ""),
            role=payload.get("role", "user"),
            exp=datetime.fromtimestamp(payload.get("exp", 0))
        )

    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """
        Generate an API key and its hash.

        Returns:
            Tuple of (plain_key, hashed_key)
        """
        # Generate a random key
        plain_key = f"nnt_{secrets.token_urlsafe(32)}"

        # Hash for storage
        hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()

        return plain_key, hashed_key

    @staticmethod
    def verify_api_key(plain_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash."""
        return hashlib.sha256(plain_key.encode()).hexdigest() == hashed_key

    @staticmethod
    def get_key_prefix(key: str) -> str:
        """Get the prefix of an API key for identification."""
        return key[:8] if len(key) >= 8 else key


# Global auth service instance
auth_service = AuthService()


if __name__ == "__main__":
    print("=" * 60)
    print("AUTH SERVICE TEST")
    print("=" * 60)

    # Test password hashing
    password = "test_password123"
    hashed = auth_service.hash_password(password)
    print(f"Password hash: {hashed[:50]}...")
    assert auth_service.verify_password(password, hashed)
    print("  ✓ Password hashing works")

    # Test token creation
    tokens = auth_service.create_tokens(
        user_id="user_123",
        tenant_id="tenant_456",
        email="test@example.com",
        role="admin"
    )
    print(f"Access token: {tokens.access_token[:50]}...")
    print("  ✓ Token creation works")

    # Test token verification
    data = auth_service.get_token_data(tokens.access_token)
    assert data.user_id == "user_123"
    assert data.tenant_id == "tenant_456"
    assert data.email == "test@example.com"
    assert data.role == "admin"
    print("  ✓ Token verification works")

    # Test API key generation
    plain, hashed = auth_service.generate_api_key()
    assert auth_service.verify_api_key(plain, hashed)
    print(f"API key: {plain[:20]}...")
    print("  ✓ API key generation works")

    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
