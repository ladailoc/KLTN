from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from app.common.constants import EVENT_NO_SEATBELT, EVENT_SMOKING, EVENT_USING_PHONE
from app.common.types import BBox, CandidateEvent, Detection, PoseResult
from app.common.utils import bbox_center, euclidean


Point = Tuple[int, int]


def canon_name(x: str) -> str:
    x = str(x).lower().replace("_", "-").strip()
    alias = {
        "no seatbelt": "no-seatbelt",
        "no_seatbelt": "no-seatbelt",
        "seat-belt": "seatbelt",
        "cell phone": "phone",
        "cell-phone": "phone",
        "mobile-phone": "phone",
        "mobile phone": "phone",
        "smoke": "smoking",
        "cigarette": "smoking",
    }
    return alias.get(x, x)


def get_pt(pose: PoseResult, name: str) -> Optional[Point]:
    return pose.points.get(name)


def midpoint(p1: Point, p2: Point) -> Tuple[float, float]:
    return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)


def box_area(box: BBox) -> float:
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def point_in_box(pt: Optional[Tuple[float, float]], box: Optional[Tuple[float, float, float, float]]) -> bool:
    if pt is None or box is None:
        return False
    x, y = pt
    x1, y1, x2, y2 = box
    return x1 <= x <= x2 and y1 <= y <= y2


def overlap_ratio(box_a: Optional[BBox], box_b: Optional[Tuple[float, float, float, float]]) -> float:
    if box_a is None or box_b is None:
        return 0.0
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = box_area((int(ix1), int(iy1), int(ix2), int(iy2)))
    return inter / max(1.0, box_area(box_a))


def get_shoulder_width(pose: PoseResult) -> float:
    ls = get_pt(pose, "left_shoulder")
    rs = get_pt(pose, "right_shoulder")
    if ls is not None and rs is not None:
        return max(1.0, euclidean(ls, rs))

    lh = get_pt(pose, "left_hip")
    rh = get_pt(pose, "right_hip")
    if lh is not None and rh is not None:
        return max(1.0, euclidean(lh, rh) * 0.9)

    return 80.0


def build_driver_roi(pose: PoseResult, w: int, h: int) -> Optional[Tuple[float, float, float, float]]:
    if not pose.points:
        return None

    valid = list(pose.points.values())
    if len(valid) < 4:
        return None

    xs = [p[0] for p in valid]
    ys = [p[1] for p in valid]

    x1, x2 = min(xs), max(xs)
    y1, y2 = min(ys), max(ys)

    pad_x = (x2 - x1) * 0.30 + 20
    pad_y = (y2 - y1) * 0.25 + 20

    x1 = max(0.0, x1 - pad_x)
    y1 = max(0.0, y1 - pad_y)
    x2 = min(float(w - 1), x2 + pad_x)
    y2 = min(float(h - 1), y2 + pad_y)
    return (x1, y1, x2, y2)


def build_chest_roi(pose: PoseResult, w: int, h: int) -> Optional[Tuple[float, float, float, float]]:
    ls = get_pt(pose, "left_shoulder")
    rs = get_pt(pose, "right_shoulder")
    lh = get_pt(pose, "left_hip")
    rh = get_pt(pose, "right_hip")

    if ls is None or rs is None:
        return None

    shoulder_width = get_shoulder_width(pose)
    shoulder_mid = midpoint(ls, rs)

    if lh is not None and rh is not None:
        hip_mid = midpoint(lh, rh)
        chest_h = abs(hip_mid[1] - shoulder_mid[1]) * 0.65
    else:
        chest_h = shoulder_width * 0.95

    x1 = shoulder_mid[0] - shoulder_width * 0.70
    x2 = shoulder_mid[0] + shoulder_width * 0.70
    y1 = shoulder_mid[1] - shoulder_width * 0.18
    y2 = y1 + chest_h

    x1 = max(0.0, x1)
    y1 = max(0.0, y1)
    x2 = min(float(w - 1), x2)
    y2 = min(float(h - 1), y2)

    return (x1, y1, x2, y2)


class BehaviorRules:
    def __init__(self, config: Dict):
        self.cfg = config

        self.phone_names = {canon_name(n) for n in config["classes"]["phone_names"]}
        self.smoking_names = {canon_name(n) for n in config["classes"]["smoking_names"]}
        self.no_seatbelt_names = {canon_name(n) for n in config["classes"]["no_seatbelt_names"]}
        self.seatbelt_names = {canon_name(n) for n in config["classes"]["seatbelt_names"]}

    def infer(self, detections: List[Detection], pose: PoseResult, frame_shape) -> List[CandidateEvent]:
        h, w = frame_shape[:2]
        driver_roi = build_driver_roi(pose, w, h) if pose.points else None
        chest_roi = build_chest_roi(pose, w, h) if pose.points else None

        events: List[CandidateEvent] = []

        phone_event = self._infer_phone(detections, pose, driver_roi)
        if phone_event:
            events.append(phone_event)

        smoking_event = self._infer_smoking(detections, pose, driver_roi)
        if smoking_event:
            events.append(smoking_event)

        seatbelt_event = self._infer_no_seatbelt(detections, chest_roi)
        if seatbelt_event:
            events.append(seatbelt_event)

        return events

    def _filter_by_names(self, detections: List[Detection], names: set[str]) -> List[Detection]:
        return [d for d in detections if canon_name(d.class_name) in names]

    def _score_phone_behavior(
        self,
        phone_det: Detection,
        pose: PoseResult,
        driver_roi: Optional[Tuple[float, float, float, float]],
    ) -> float:
        score = phone_det.confidence
        shoulder_width = get_shoulder_width(pose)
        center = bbox_center(phone_det.bbox)

        nose = get_pt(pose, "nose")
        l_ear = get_pt(pose, "left_ear")
        r_ear = get_pt(pose, "right_ear")
        l_wrist = get_pt(pose, "left_wrist")
        r_wrist = get_pt(pose, "right_wrist")

        head_pts = [p for p in [nose, l_ear, r_ear] if p is not None]
        hand_pts = [p for p in [l_wrist, r_wrist] if p is not None]

        if hand_pts:
            d_hand = min(euclidean(center, p) for p in hand_pts) / shoulder_width
            if d_hand < self.cfg["rules"]["phone_hand_near_1"]:
                score += 0.28
            elif d_hand < self.cfg["rules"]["phone_hand_near_2"]:
                score += 0.12

        if head_pts:
            d_face = min(euclidean(center, p) for p in head_pts) / shoulder_width
            if d_face < self.cfg["rules"]["phone_face_near_1"]:
                score += 0.20
            elif d_face < self.cfg["rules"]["phone_face_near_2"]:
                score += 0.08

        if driver_roi is not None and point_in_box(center, driver_roi):
            score += self.cfg["rules"]["driver_roi_bonus_phone"]

        rel_area = box_area(phone_det.bbox) / max(1.0, shoulder_width * shoulder_width)
        if self.cfg["rules"]["phone_area_rel_min"] <= rel_area <= self.cfg["rules"]["phone_area_rel_max"]:
            score += 0.08
        else:
            score -= 0.12

        return float(min(max(score, 0.0), 1.0))

    def _score_smoking_behavior(
        self,
        smoke_det: Detection,
        pose: PoseResult,
        driver_roi: Optional[Tuple[float, float, float, float]],
    ) -> float:
        score = smoke_det.confidence
        shoulder_width = get_shoulder_width(pose)
        center = bbox_center(smoke_det.bbox)

        nose = get_pt(pose, "nose")
        mouth_l = get_pt(pose, "mouth_left")
        mouth_r = get_pt(pose, "mouth_right")
        l_wrist = get_pt(pose, "left_wrist")
        r_wrist = get_pt(pose, "right_wrist")

        face_pts = [p for p in [nose, mouth_l, mouth_r] if p is not None]
        hand_pts = [p for p in [l_wrist, r_wrist] if p is not None]

        if face_pts:
            d_face = min(euclidean(center, p) for p in face_pts) / shoulder_width
            if d_face < self.cfg["rules"]["smoking_face_near_1"]:
                score += 0.25
            elif d_face < self.cfg["rules"]["smoking_face_near_2"]:
                score += 0.10

        if hand_pts:
            d_hand = min(euclidean(center, p) for p in hand_pts) / shoulder_width
            if d_hand < self.cfg["rules"]["smoking_hand_near_1"]:
                score += 0.18
            elif d_hand < self.cfg["rules"]["smoking_hand_near_2"]:
                score += 0.08

        if driver_roi is not None and point_in_box(center, driver_roi):
            score += self.cfg["rules"]["driver_roi_bonus_smoking"]

        rel_area = box_area(smoke_det.bbox) / max(1.0, shoulder_width * shoulder_width)
        if self.cfg["rules"]["smoking_area_rel_min"] <= rel_area <= self.cfg["rules"]["smoking_area_rel_max"]:
            score += 0.08
        else:
            score -= 0.10

        return float(min(max(score, 0.0), 1.0))

    def _infer_phone(
        self,
        detections: List[Detection],
        pose: PoseResult,
        driver_roi: Optional[Tuple[float, float, float, float]],
    ) -> Optional[CandidateEvent]:
        # 1. Lấy ra các box được YOLO dự đoán là điện thoại
        phone_dets = self._filter_by_names(detections, self.phone_names)
        if not phone_dets:
            return None

        # 2. KHÔNG có fallback YOLO-only. Nếu không có pose (tức là không thấy pose người), loại ngay
        if not pose.points:
            return None

        # 3. Yêu cầu NGỮ CẢNH NGƯỜI bắt buộc: Phải có Face, Wrist, Shoulder
        nose = get_pt(pose, "nose")
        l_ear = get_pt(pose, "left_ear")
        r_ear = get_pt(pose, "right_ear")
        has_face = any(p is not None for p in [nose, l_ear, r_ear])
        
        l_wrist = get_pt(pose, "left_wrist")
        r_wrist = get_pt(pose, "right_wrist")
        has_wrist = any(p is not None for p in [l_wrist, r_wrist])
        
        l_shoulder = get_pt(pose, "left_shoulder")
        r_shoulder = get_pt(pose, "right_shoulder")
        has_shoulder = any(p is not None for p in [l_shoulder, r_shoulder])
        
        if not (has_face and has_wrist and has_shoulder):
            return None

        # 4. Kiểm tra Driver ROI: Điện thoại bắt buộc nằm trong vùng tài xế ngồi
        valid_phone_dets = []
        for det in phone_dets:
            center = bbox_center(det.bbox)
            if driver_roi is not None and not point_in_box(center, driver_roi):
                continue # Nếu có driver_roi nhưng box lại nằm ngoài -> loại bỏ
            valid_phone_dets.append(det)
            
        if not valid_phone_dets:
            return None

        # 5. Giữ hệ thống tính điểm, đánh giá mức độ rủi ro (scoring distance + raw conf)
        scored = [(self._score_phone_behavior(det, pose, driver_roi), det) for det in valid_phone_dets]
        best_score, best_det = max(scored, key=lambda x: x[0])

        # 6. Activate event nếu điểm số sau khi cộng dồn >= ngưỡng cấu hình (ngưỡng khá cao lúc này)
        if best_score >= self.cfg["rules"]["phone_score_threshold"]:
            return CandidateEvent(
                event_type=EVENT_USING_PHONE,
                score=float(best_score),
                bbox=best_det.bbox,
                raw_confidence=best_det.confidence,
                note="phone detected with strict pose rules",
            )
        return None

    def _infer_smoking(
        self,
        detections: List[Detection],
        pose: PoseResult,
        driver_roi: Optional[Tuple[float, float, float, float]],
    ) -> Optional[CandidateEvent]:
        smoke_dets = self._filter_by_names(detections, self.smoking_names)
        if not smoke_dets:
            return None

        if not pose.points:
            best = max(smoke_dets, key=lambda d: d.confidence)
            if best.confidence >= self.cfg["rules"]["smoking_raw_conf_fallback"]:
                return CandidateEvent(
                    event_type=EVENT_SMOKING,
                    score=float(best.confidence),
                    bbox=best.bbox,
                    raw_confidence=best.confidence,
                    note="fallback no pose",
                )
            return None

        scored = [(self._score_smoking_behavior(det, pose, driver_roi), det) for det in smoke_dets]
        best_score, best_det = max(scored, key=lambda x: x[0])

        if best_score >= self.cfg["rules"]["smoking_score_threshold"]:
            return CandidateEvent(
                event_type=EVENT_SMOKING,
                score=float(best_score),
                bbox=best_det.bbox,
                raw_confidence=best_det.confidence,
                note="smoking score with pose",
            )
        return None

    def _infer_no_seatbelt(
        self,
        detections: List[Detection],
        chest_roi: Optional[Tuple[float, float, float, float]],
    ) -> Optional[CandidateEvent]:
        seatbelt_dets = self._filter_by_names(detections, self.seatbelt_names)
        no_seatbelt_dets = self._filter_by_names(detections, self.no_seatbelt_names)

        def best_scored(cands: List[Detection]) -> Tuple[float, Optional[Detection]]:
            best_score = 0.0
            best_det = None
            for det in cands:
                s = det.confidence
                if chest_roi is not None:
                    s += 0.20 * overlap_ratio(det.bbox, chest_roi)
                if s > best_score:
                    best_score = s
                    best_det = det
            return best_score, best_det

        seatbelt_best, seatbelt_det = best_scored(seatbelt_dets)
        no_seatbelt_best, no_seatbelt_det = best_scored(no_seatbelt_dets)

        thr = self.cfg["rules"]["seatbelt_conf_threshold"]
        margin = self.cfg["rules"]["seatbelt_margin"]

        if (
            no_seatbelt_det is not None
            and no_seatbelt_best >= thr
            and no_seatbelt_best > seatbelt_best + margin
        ):
            return CandidateEvent(
                event_type=EVENT_NO_SEATBELT,
                score=float(min(no_seatbelt_best, 1.0)),
                bbox=no_seatbelt_det.bbox,
                raw_confidence=no_seatbelt_det.confidence,
                note=f"no_seatbelt={no_seatbelt_best:.2f}, seatbelt={seatbelt_best:.2f}",
            )

        return None