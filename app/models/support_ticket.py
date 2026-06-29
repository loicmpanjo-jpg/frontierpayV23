"""Support Ticket Model"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String(32), unique=True, nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="open")

    # AI
    ai_suggestions = Column(JSONB, default=list) # SQLite doesn't support ARRAY
    ai_confidence = Column(Float, default=0.0)

    # Resolution
    assigned_to = Column(String(100))
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)

    # Merchant
    merchant_id = Column(UUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
