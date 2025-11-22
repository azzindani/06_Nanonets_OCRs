"""
Authentication API routes for user management and API keys.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from services.auth import auth_service, TokenResponse
from utils.logger import auth_logger, audit_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    tenant_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str
    tenant_id: str
    created_at: datetime


class APIKeyCreate(BaseModel):
    name: str
    expires_days: Optional[int] = 365


class APIKeyResponse(BaseModel):
    id: str
    key: str  # Only returned on creation
    key_prefix: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime]


class RefreshToken(BaseModel):
    refresh_token: str


# In-memory store for demo (replace with database)
_users = {}
_api_keys = {}


@router.post("/register", response_model=UserResponse)
async def register(data: UserRegister):
    """
    Register a new user account.
    """
    # Check if user exists
    if data.email in _users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    import uuid
    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())

    user = {
        "id": user_id,
        "email": data.email,
        "hashed_password": auth_service.hash_password(data.password),
        "full_name": data.full_name,
        "role": "admin",  # First user is admin
        "tenant_id": tenant_id,
        "created_at": datetime.utcnow()
    }

    _users[data.email] = user

    auth_logger.info("User registered", user_id=user_id, email=data.email)

    return UserResponse(
        id=user_id,
        email=data.email,
        full_name=data.full_name,
        role="admin",
        tenant_id=tenant_id,
        created_at=user["created_at"]
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    """
    Authenticate user and return JWT tokens.
    """
    # Find user
    user = _users.get(data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not auth_service.verify_password(data.password, user["hashed_password"]):
        auth_logger.warning("Failed login attempt", email=data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create tokens
    tokens = auth_service.create_tokens(
        user_id=user["id"],
        tenant_id=user["tenant_id"],
        email=user["email"],
        role=user["role"]
    )

    audit_logger.user_login(user["id"], "password")
    auth_logger.info("User logged in", user_id=user["id"])

    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshToken):
    """
    Refresh access token using refresh token.
    """
    payload = auth_service.verify_token(data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    # Find user to get current info
    user = None
    for u in _users.values():
        if u["id"] == user_id:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    tokens = auth_service.create_tokens(
        user_id=user["id"],
        tenant_id=user["tenant_id"],
        email=user["email"],
        role=user["role"]
    )

    return tokens


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(data: APIKeyCreate):
    """
    Create a new API key for the current user.
    """
    import uuid
    from datetime import timedelta

    key_id = str(uuid.uuid4())
    plain_key, hashed_key = auth_service.generate_api_key()

    expires_at = None
    if data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=data.expires_days)

    api_key = {
        "id": key_id,
        "key_hash": hashed_key,
        "key_prefix": auth_service.get_key_prefix(plain_key),
        "name": data.name,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at
    }

    _api_keys[key_id] = api_key

    audit_logger.api_key_created(key_id, "current_user")
    auth_logger.info("API key created", key_id=key_id)

    return APIKeyResponse(
        id=key_id,
        key=plain_key,  # Only returned once
        key_prefix=api_key["key_prefix"],
        name=data.name,
        created_at=api_key["created_at"],
        expires_at=expires_at
    )


@router.get("/api-keys")
async def list_api_keys():
    """
    List all API keys for the current user.
    """
    return [
        {
            "id": k["id"],
            "key_prefix": k["key_prefix"],
            "name": k["name"],
            "created_at": k["created_at"],
            "expires_at": k["expires_at"]
        }
        for k in _api_keys.values()
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: str):
    """
    Revoke an API key.
    """
    if key_id not in _api_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    del _api_keys[key_id]
    auth_logger.info("API key revoked", key_id=key_id)

    return {"status": "revoked", "key_id": key_id}


@router.get("/me", response_model=UserResponse)
async def get_current_user():
    """
    Get current user profile.
    """
    # In production, get from JWT token
    if not _users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    user = list(_users.values())[0]  # Demo: return first user

    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        tenant_id=user["tenant_id"],
        created_at=user["created_at"]
    )
