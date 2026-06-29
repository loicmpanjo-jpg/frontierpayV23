"""Merchant Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    country = Column(String(2), nullable=False)

    # Risk
    risk_score = Column(Integer, default=50)
    risk_tier = Column(String(20), default="standard")
    kyc_status = Column(String(20), default="pending")

    # Volume tracking
    daily_volume = Column(Float, default=0.0)
    monthly_volume = Column(Float, default=0.0)
    volume_limit = Column(Float, default=10_000_000.0)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # API Keys (hashed)
    api_key_hash = Column(String(255))
    webhook_url = Column(String(512))
    webhook_secret = Column(String(255))

    # Settings
    settings = Column(JSON, default=dict)

    # Relations
    transactions = relationship("Transaction", back_populates="merchant")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_transaction_at = Column(DateTime)
