"""Transaction Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_code = Column(String(32), unique=True, nullable=False, index=True)
    idempotency_key = Column(String(128), unique=True, nullable=True)

    # Amounts
    amount = Column(Float, nullable=False)
    origin_currency = Column(String(3), nullable=False)
    destination_currency = Column(String(3), nullable=False)
    fx_rate = Column(Float, default=1.0)

    # Collection
    collection_psp = Column(String(20), nullable=False)
    collection_reference = Column(String(128))
    psp_fee = Column(Float, default=0.0)

    # Payout
    payout_psp = Column(String(20), nullable=False)
    payout_reference = Column(String(128))
    settlement_fee = Column(Float, default=0.0)

    # FrontierPay economics
    frontierpay_markup = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    net_margin = Column(Float, default=0.0)
    net_margin_pct = Column(Float, default=0.0)

    # Status
    status = Column(String(20), default="initiated", index=True)
    status_history = Column(JSONB, default=list)

    # Source / Destination
    source_data = Column(JSONB)
    destination_data = Column(JSONB)

    # Merchant
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=True)
    merchant = relationship("Merchant", back_populates="transactions")

    # Corridor
    corridor_id = Column(UUID(as_uuid=True), ForeignKey("corridors.id"), nullable=True)

    # Metadata
    extra_metadata = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
