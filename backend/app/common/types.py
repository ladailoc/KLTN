from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

BBox = Tuple[int, int, int, int]
Point = Tuple[int, int]

@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: BBox

@dataclass
class PoseResult:
    points: Dict[str, Point] = field(default_factory=dict)

@dataclass
class CandidateEvent:
    event_type: str
    score: float
    bbox: Optional[BBox] = None
    raw_confidence: float = 0.0
    note: str = ""

@dataclass
class AlertEvent:
    event_type: str
    confidence: float
    frame_index: int
    timestamp: str
    bbox: Optional[BBox] = None
    note: str = ""
    source_device: str = "edge-01"