from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    timestamp: str
    confidence: float
    frame_index: int
    source_device: str
    notes: Optional[str] = None
    frame_path: Optional[str] = None
    clip_path: Optional[str] = None
    event_json_path: Optional[str] = None
    verified: bool
    created_at: datetime
    review_status: str | None = None
    verified_by: str | None = None
    reviewer_notes: str | None = None
    reviewed_at: datetime | None = None

class HealthResponse(BaseModel):
    status: str

class SlowFastVerifyResponse(BaseModel):
    video_path: str
    start_sec: float
    end_sec: float
    device: str
    model_name: str
    top_k: list[dict]
    project_scores: dict
    predicted_project_event: str | None
    predicted_project_score: float
    verified: bool
    note: str

class ManualReviewRequest(BaseModel):
    review_status: str
    verified: bool
    reviewer_notes: str | None = None
    verified_by: str | None = "admin"


class ManualReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    verified: bool
    review_status: str | None = None
    verified_by: str | None = None
    reviewer_notes: str | None = None
    reviewed_at: datetime | None = None