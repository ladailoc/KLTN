from __future__ import annotations
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.cloud.database import Base

class AlertModel(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    timestamp = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    frame_index = Column(Integer, nullable=False)
    source_device = Column(String(100), nullable=False, default="edge-01")
    notes = Column(Text, nullable=True)

    frame_path = Column(String(255), nullable=True)
    clip_path = Column(String(255), nullable=True)
    event_json_path = Column(String(255), nullable=True)

    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    review_status = Column(String(50), default="pending")
    verified_by = Column(String(100), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)