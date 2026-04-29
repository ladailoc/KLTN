from __future__ import annotations
from pathlib import Path
from typing import Optional
import shutil
from fastapi import UploadFile

from app.common.config import load_config
from app.common.utils import ensure_dir

cfg = load_config()
BASE_UPLOAD_DIR = ensure_dir(cfg["storage"]["cloud_upload_dir"])

def save_upload(upload: Optional[UploadFile], subdir: str) -> str | None:
    if upload is None:
        return None

    target_dir = ensure_dir(BASE_UPLOAD_DIR / subdir)
    target_path = target_dir / upload.filename

    with open(target_path, "wb") as f:
        shutil.copyfileobj(upload.file, f)

    return str(target_path)