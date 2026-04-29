from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.cloud.models import AlertModel

from datetime import datetime

def manual_review_alert(
    db: Session,
    alert_id: int,
    *,
    verified: bool,
    review_status: str,
    reviewer_notes: str | None = None,
    verified_by: str | None = "admin",
):
    obj = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if obj is None:
        return None

    obj.verified = verified
    obj.review_status = review_status
    obj.reviewer_notes = reviewer_notes
    obj.verified_by = verified_by
    obj.reviewed_at = datetime.utcnow()

    note = f"[Manual Review] status={review_status}, verified={verified}, by={verified_by}"
    if reviewer_notes:
        note += f", notes={reviewer_notes}"

    obj.notes = (obj.notes or "") + "\n" + note

    db.commit()
    db.refresh(obj)
    return obj

def create_alert(
    db: Session,
    *,
    event_type: str,
    timestamp: str,
    confidence: float,
    frame_index: int,
    source_device: str,
    notes: str | None,
    frame_path: str | None,
    clip_path: str | None,
    event_json_path: str | None,
) -> AlertModel:
    obj = AlertModel(
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
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_alerts(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[str] = None,
    source_device: Optional[str] = None,
    verified: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Tuple[list[AlertModel], int]:
    query = db.query(AlertModel)

    if event_type:
        query = query.filter(AlertModel.event_type == event_type)

    if source_device:
        query = query.filter(AlertModel.source_device == source_device)

    if verified is not None:
        query = query.filter(AlertModel.verified == verified)

    if start_date:
        query = query.filter(AlertModel.timestamp >= start_date)

    if end_date:
        query = query.filter(AlertModel.timestamp <= end_date)

    total = query.count()

    items = (
        query.order_by(AlertModel.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return items, total


def get_alert_by_id(db: Session, alert_id: int):
    return db.query(AlertModel).filter(AlertModel.id == alert_id).first()


def update_alert_verification(
    db: Session,
    alert_id: int,
    *,
    verified: bool,
    notes: str | None = None,
):
    obj = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if obj is None:
        return None

    obj.verified = verified

    if notes:
        old_notes = obj.notes or ""
        obj.notes = old_notes + f"\n[Cloud Verify] {notes}"

    db.commit()
    db.refresh(obj)
    return obj


def update_alert_clip_path(
    db: Session,
    alert_id: int,
    *,
    clip_path: str,
):
    obj = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if obj is None:
        return None

    obj.clip_path = clip_path
    db.commit()
    db.refresh(obj)
    return obj


def get_statistics(db: Session) -> dict:
    total_alerts = db.query(func.count(AlertModel.id)).scalar() or 0

    verified_count = (
        db.query(func.count(AlertModel.id))
        .filter(AlertModel.verified == True)
        .scalar()
        or 0
    )

    unverified_count = total_alerts - verified_count

    by_event_rows = (
        db.query(AlertModel.event_type, func.count(AlertModel.id))
        .group_by(AlertModel.event_type)
        .all()
    )

    by_device_rows = (
        db.query(AlertModel.source_device, func.count(AlertModel.id))
        .group_by(AlertModel.source_device)
        .all()
    )

    by_verified_rows = (
        db.query(AlertModel.verified, func.count(AlertModel.id))
        .group_by(AlertModel.verified)
        .all()
    )

    latest_alert = (
        db.query(AlertModel)
        .order_by(AlertModel.id.desc())
        .first()
    )

    return {
        "total_alerts": total_alerts,
        "verified_count": verified_count,
        "unverified_count": unverified_count,
        "by_event_type": [
            {"event_type": event_type or "unknown", "count": count}
            for event_type, count in by_event_rows
        ],
        "by_device": [
            {"source_device": source_device or "unknown", "count": count}
            for source_device, count in by_device_rows
        ],
        "by_verified": [
            {"verified": bool(verified), "count": count}
            for verified, count in by_verified_rows
        ],
        "latest_alert_id": latest_alert.id if latest_alert else None,
        "latest_alert_time": latest_alert.timestamp if latest_alert else None,
    }