"""Corridor Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class Corridor(Base):
    __tablename__ = "corridors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)

    source_country = Column(String(2), nullable=False, index=True)
    destination_country = Column(String(2), nullable=False, index=True)
    source_currency = Column(String(3), nullable=False)
    destination_currency = Column(String(3), nullable=False)

    # Routing defaults
    default_collection_psp = Column(String(20))
    default_payout_psp = Column(String(20))

    # Stats
    volume_30d = Column(Float, default=0.0)
    transaction_count_30d = Column(Integer, default=0)
    avg_fee_pct = Column(Float, default=0.0)

    # Status
    is_active = Column(Boolean, default=True)
    is_beta = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
