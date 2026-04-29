from __future__ import annotations
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.cloud import crud
from app.cloud.storage import save_upload

def handle_create_alert(
    db: Session,
    *,
    event_type: str,
    timestamp: str,
    confidence: float,
    frame_index: int,
    source_device: str,
    notes: str | None,
    frame_file: UploadFile | None,
    clip_file: UploadFile | None,
    event_file: UploadFile | None,
):
    frame_path = save_upload(frame_file, "frames")
    clip_path = save_upload(clip_file, "clips")
    event_json_path = save_upload(event_file, "events")

    return crud.create_alert(
        db,
        event_type=event_type,
        timestamp=timestamp,
        confidence=confidence,
        frame_index=frame_index,
        source_device=source_device,
        notes=notes,
        frame_path=frame_path,
        clip_path=clip_path,
        event_json_path=event_json_path,
    )