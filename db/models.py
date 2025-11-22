"""
SQLAlchemy database models for PostgreSQL.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Enum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserRole(str, PyEnum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class JobStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Tenant(Base):
    """Multi-tenant organization."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    # Quotas
    monthly_document_limit = Column(Integer, default=1000)
    monthly_page_limit = Column(Integer, default=10000)
    storage_limit_mb = Column(Integer, default=5000)

    # Usage tracking
    documents_this_month = Column(Integer, default=0)
    pages_this_month = Column(Integer, default=0)
    storage_used_mb = Column(Float, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="tenant")
    documents = relationship("Document", back_populates="tenant")
    api_keys = relationship("APIKey", back_populates="tenant")


class User(Base):
    """User account."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.USER)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Auth tracking
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    documents = relationship("Document", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")

    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_tenant_id", "tenant_id"),
    )


class APIKey(Base):
    """API key for authentication."""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    name = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_day = Column(Integer, default=10000)

    # Usage tracking
    last_used_at = Column(DateTime)
    total_requests = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index("ix_api_keys_key_hash", "key_hash"),
    )


class Document(Base):
    """Uploaded document."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # File info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_hash = Column(String(64))  # SHA-256 for deduplication

    # Processing info
    total_pages = Column(Integer, default=1)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)

    # Results
    extracted_text = Column(Text)
    extracted_fields = Column(JSON)
    confidence_score = Column(Float)

    # Metadata
    metadata = Column(JSON, default={})
    tags = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    deleted_at = Column(DateTime)

    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    user = relationship("User", back_populates="documents")
    jobs = relationship("ProcessingJob", back_populates="document")

    __table_args__ = (
        Index("ix_documents_tenant_id", "tenant_id"),
        Index("ix_documents_user_id", "user_id"),
        Index("ix_documents_status", "status"),
        Index("ix_documents_file_hash", "file_hash"),
    )


class ProcessingJob(Base):
    """Background processing job."""
    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    # Job info
    job_type = Column(String(50), nullable=False)  # ocr, field_extraction, export
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    priority = Column(Integer, default=5)  # 1-10, higher = more important

    # Configuration
    config = Column(JSON, default={})

    # Results
    result = Column(JSON)
    error_message = Column(Text)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    processing_time_ms = Column(Integer)

    # Retry
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_retry_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="jobs")

    __table_args__ = (
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_priority", "priority"),
        Index("ix_jobs_created_at", "created_at"),
    )


class WebhookEndpoint(Base):
    """Webhook configuration for notifications."""
    __tablename__ = "webhook_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    url = Column(String(500), nullable=False)
    secret = Column(String(255))  # For HMAC signing

    # Events to trigger
    events = Column(JSON, default=["document.processed"])

    is_active = Column(Boolean, default=True)

    # Stats
    total_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_delivery_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Audit trail for compliance."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100))

    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_audit_tenant_id", "tenant_id"),
        Index("ix_audit_user_id", "user_id"),
        Index("ix_audit_created_at", "created_at"),
        Index("ix_audit_action", "action"),
    )
