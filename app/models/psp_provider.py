"""PSP Provider Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class PSPProvider(Base):
    __tablename__ = "psp_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    psp_code = Column(String(20), unique=True, nullable=False, index=True)

    # Health
    status = Column(String(20), default="active")
    health_score = Column(Integer, default=100)
    success_rate_7d = Column(Float, default=0.99)
    avg_latency_ms = Column(Integer, default=500)

    # Circuit breaker
    circuit_state = Column(String(20), default="closed")
    failure_count = Column(Integer, default=0)
    last_failure_at = Column(DateTime)

    # Exposure / Limits
    current_exposure = Column(Float, default=0.0)
    exposure_limit = Column(Float, default=1_000_000_000.0)
    daily_limit = Column(Float, default=100_000_000.0)

    # Capabilities
    supported_countries = Column(JSONB, default=list)
    supported_currencies = Column(JSONB, default=list)
    supported_methods = Column(JSONB, default=list)

    # Config
    config = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_health_check = Column(DateTime)
