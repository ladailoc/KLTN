from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.cloud import crud
from app.cloud.alert_service import handle_create_alert
from app.cloud.database import get_db
from app.cloud.schemas import AlertRead, HealthResponse, ManualReviewRequest, ManualReviewResponse
from app.cloud.storage import save_upload


try:
    from app.cloud.slowfast_service import get_slowfast_service
    SLOWFAST_AVAILABLE = True
except Exception:
    SLOWFAST_AVAILABLE = False


router = APIRouter()


def to_public_url(path: Optional[str]) -> Optional[str]:
    """
    Chuyển đường dẫn file backend lưu trong DB thành URL frontend xem được.
    Ví dụ:
    outputs/cloud_uploads/frames/a.jpg -> /uploads/frames/a.jpg
    """
    if not path:
        return None

    p = str(path).replace("\\", "/")

    marker = "cloud_uploads/"
    if marker in p:
        return "/uploads/" + p.split(marker, 1)[1]

    if p.startswith("/uploads/"):
        return p

    return p


def alert_to_dict(alert) -> dict:
    data = AlertRead.model_validate(alert).model_dump(mode="json")

    data["frame_url"] = to_public_url(alert.frame_path)
    data["clip_url"] = to_public_url(alert.clip_path)
    data["event_json_url"] = to_public_url(alert.event_json_path)

    return data


@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@router.post("/alerts", response_model=AlertRead)
def create_alert(
    event_type: str = Form(...),
    timestamp: str = Form(...),
    confidence: float = Form(...),
    frame_index: int = Form(...),
    source_device: str = Form("edge-01"),
    notes: Optional[str] = Form(None),
    frame_file: Optional[UploadFile] = File(None),
    clip_file: Optional[UploadFile] = File(None),
    event_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    alert = handle_create_alert(
        db,
        event_type=event_type,
        timestamp=timestamp,
        confidence=confidence,
        frame_index=frame_index,
        source_device=source_device,
        notes=notes,
        frame_file=frame_file,
        clip_file=clip_file,
        event_file=event_file,
    )
    return alert


@router.get("/alerts", response_model=list[AlertRead])
def list_alerts_legacy(
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Route cũ để không phá code cũ.
    """
    items, _ = crud.get_alerts(db, limit=limit)
    return items


@router.get("/alerts/{alert_id}", response_model=AlertRead)
def read_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = crud.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.get("/api/alerts")
def list_alerts_api(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    event_type: Optional[str] = Query(None),
    source_device: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    API cho dashboard:
    - phân trang: skip, limit
    - lọc theo event_type
    - lọc theo source_device/device
    - lọc theo verified
    - lọc theo timestamp dạng ISO string
    """
    effective_device = source_device or device

    items, total = crud.get_alerts(
        db,
        skip=skip,
        limit=limit,
        event_type=event_type,
        source_device=effective_device,
        verified=verified,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "items": [alert_to_dict(a) for a in items],
        "total": total,
        "skip": skip,
        "limit": limit,
        "page": (skip // limit) + 1,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
    }


@router.get("/api/statistics")
def get_statistics_api(db: Session = Depends(get_db)):
    return crud.get_statistics(db)


@router.post("/alerts/{alert_id}/verify")
def verify_existing_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    """
    Verify alert bằng SlowFast nếu slowfast_service.py đã được cài.
    Nếu chưa có SlowFast thì trả 501, dashboard vẫn chạy bình thường.
    """
    if not SLOWFAST_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="SlowFast service is not available. Please add app/cloud/slowfast_service.py and install dependencies.",
        )

    alert = crud.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if not alert.clip_path:
        raise HTTPException(status_code=400, detail="Alert has no clip_path to verify")

    clip_path = Path(alert.clip_path)
    if not clip_path.exists():
        raise HTTPException(status_code=400, detail=f"Clip file not found: {clip_path}")

    service = get_slowfast_service()
    result = service.verify_clip(
        video_path=str(clip_path),
        event_type_hint=alert.event_type,
    )

    crud.update_alert_verification(
        db,
        alert_id,
        verified=bool(result.get("verified", False)),
        review_status=result.get("verification_status"),
        verified_by="slowfast",
        notes=(
            f"pred={result.get('predicted_project_event')} "
            f"score={result.get('predicted_project_score')}"
        ),
    )

    return result

@router.post("/alerts/{alert_id}/manual_review", response_model=ManualReviewResponse)
def manual_review_alert(
    alert_id: int,
    payload: ManualReviewRequest,
    db: Session = Depends(get_db),
):
    if payload.review_status not in ["verified", "rejected", "unconfirmed", "pending"]:
        raise HTTPException(
            status_code=400,
            detail="review_status must be one of: verified, rejected, unconfirmed, pending",
        )

    alert = crud.manual_review_alert(
        db,
        alert_id,
        verified=payload.verified,
        review_status=payload.review_status,
        reviewer_notes=payload.reviewer_notes,
        verified_by=payload.verified_by,
    )

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert

@router.delete("/alerts/{alert_id}")
def delete_alert_route(alert_id: int, db: Session = Depends(get_db)):
    success = crud.delete_alert(db, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"detail": "Alert deleted successfully"}

@router.post("/api/verify_clip")
def verify_uploaded_clip(
    clip_file: UploadFile = File(...),
    event_type_hint: Optional[str] = Form(None),
):
    if not SLOWFAST_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="SlowFast service is not available.",
        )

    clip_path = save_upload(clip_file, "verify_clips")
    service = get_slowfast_service()

    result = service.verify_clip(
        video_path=clip_path,
        event_type_hint=event_type_hint,
    )
    return result