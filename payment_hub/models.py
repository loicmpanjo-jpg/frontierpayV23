"""Payment models with strict validation."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlalchemy import Column, String, DateTime, Numeric, Enum as SQLEnum, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from config.database import Base


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PSPType(str, Enum):
    KORA = "kora"
    FINCRA = "fincra"
    FLUTTERWAVE = "flutterwave"
    STRIPE = "stripe"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    psp = Column(SQLEnum(PSPType), nullable=False)
    psp_transaction_id = Column(String(100))
    amount = Column(Numeric(19, 8), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    metadata = Column(JSON, default=dict)
    error_message = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_transactions_user_status", "user_id", "status"),
        Index("ix_transactions_created_at", "created_at"),
    )
