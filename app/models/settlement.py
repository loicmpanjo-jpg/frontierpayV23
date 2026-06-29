"""Settlement Position Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class SettlementPosition(Base):
    __tablename__ = "settlement_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    currency = Column(String(3), unique=True, nullable=False, index=True)

    # Balances
    available_balance = Column(Float, default=0.0)
    pending_incoming = Column(Float, default=0.0)
    pending_outgoing = Column(Float, default=0.0)
    reserved_for_settlement = Column(Float, default=0.0)

    # Metrics
    capital_efficiency = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_settlement_at = Column(DateTime)
