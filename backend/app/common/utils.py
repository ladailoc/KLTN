from __future__ import annotations
from dataclasses import asdict, is_dataclass
from datetime import datetime
from math import sqrt
from pathlib import Path
from typing import Any, Iterable, Tuple

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def bbox_center(bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) // 2, (y1 + y2) // 2)

def euclidean(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    return sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def min_distance(target: Tuple[int, int], points: Iterable[Tuple[int, int]]) -> float:
    points = list(points)
    if not points:
        return float("inf")
    return min(euclidean(target, p) for p in points)

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

def to_jsonable(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj