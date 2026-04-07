"""Temporal smoothing for detection results to reduce false positives."""

from collections import deque
from typing import Deque, List, Optional, Tuple
import numpy as np


class DetectionSmoother:
    """Smooths detection results over multiple frames using temporal consistency."""

    def __init__(self, window_size: int = 5, confidence_threshold: float = 0.6):
        self.window_size = window_size
        self.confidence_threshold = confidence_threshold
        self._history: Deque[bool] = deque(maxlen=window_size)
        self._confidence_history: Deque[float] = deque(maxlen=window_size)

    def update(self, detected: bool, confidence: float = 0.0) -> Tuple[bool, float]:
        """Update with new detection result. Returns smoothed (detected, confidence)."""
        self._history.append(detected)
        self._confidence_history.append(confidence)

        if not self._history:
            return False, 0.0

        # Count positive detections in window
        positive_count = sum(self._history)

        # Require at least N detections in the window for reliability
        required_positives = max(2, self.window_size // 3)

        is_reliable = positive_count >= required_positives

        # Average confidence of positive detections
        if is_reliable:
            positive_confs = [
                c for c, d in zip(self._confidence_history, self._history) if d
            ]
            avg_confidence = (
                sum(positive_confs) / len(positive_confs) if positive_confs else 0.0
            )
        else:
            avg_confidence = 0.0

        return is_reliable, avg_confidence

    def reset(self) -> None:
        """Clear detection history."""
        self._history.clear()
        self._confidence_history.clear()

    @property
    def detection_count(self) -> int:
        """Number of positive detections in current window."""
        return sum(self._history)

    @property
    def positive_ratio(self) -> float:
        """Ratio of positive detections in current window."""
        if not self._history:
            return 0.0
        return sum(self._history) / len(self._history)


class MultiTracker:
    """Tracks multiple detections (e.g., weapons) with temporal consistency."""

    def __init__(self, iou_threshold: float = 0.3, min_frames: int = 3):
        self.iou_threshold = iou_threshold
        self.min_frames = min_frames
        self._tracked_objects: List[dict] = []
        self._next_id = 0

    def _compute_iou(self, box1, box2) -> float:
        """Compute IoU between two boxes (x1, y1, x2, y2)."""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)

        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = box1_area + box2_area - inter_area

        if union_area == 0:
            return 0.0
        return inter_area / union_area

    def update(
        self,
        boxes: List[Tuple[int, int, int, int]],
        confidences: Optional[List[float]] = None,
    ) -> List[Tuple[Tuple[int, int, int, int], float, int]]:
        """
        Update tracked objects with new detections.
        Returns list of (box, confidence, track_id) for confirmed objects.
        """
        if confidences is None:
            confidences = [1.0] * len(boxes)

        # Match new detections to existing tracks
        matched_tracks = set()
        new_boxes = []

        for box, conf in zip(boxes, confidences):
            best_iou = 0.0
            best_track_idx = -1

            for idx, track in enumerate(self._tracked_objects):
                if idx in matched_tracks:
                    continue
                iou = self._compute_iou(box, track["box"])
                if iou > best_iou and iou >= self.iou_threshold:
                    best_iou = iou
                    best_track_idx = idx

            if best_track_idx >= 0:
                # Update existing track
                self._tracked_objects[best_track_idx]["box"] = box
                self._tracked_objects[best_track_idx]["frames"] += 1
                self._tracked_objects[best_track_idx]["conf"] = conf
                self._tracked_objects[best_track_idx]["last_seen"] = 0
                matched_tracks.add(best_track_idx)
            else:
                # New track
                self._tracked_objects.append(
                    {
                        "box": box,
                        "conf": conf,
                        "frames": 1,
                        "last_seen": 0,
                        "id": self._next_id,
                    }
                )
                self._next_id += 1
                new_boxes.append(best_track_idx)

        # Age and remove stale tracks
        for idx in range(len(self._tracked_objects) - 1, -1, -1):
            self._tracked_objects[idx]["last_seen"] += 1
            if self._tracked_objects[idx]["last_seen"] > 3:
                self._tracked_objects.pop(idx)

        # Return confirmed tracks
        confirmed = []
        for track in self._tracked_objects:
            if track["frames"] >= self.min_frames:
                confirmed.append((track["box"], track["conf"], track["id"]))

        return confirmed

    def reset(self) -> None:
        """Clear all tracked objects."""
        self._tracked_objects.clear()
        self._next_id = 0


class AlertSmoother:
    """Smoother specifically tuned for alert triggering with debouncing."""

    def __init__(self, required_confirmations: int = 3, confirmation_window: int = 10):
        self.required_confirmations = required_confirmations
        self.confirmation_window = confirmation_window
        self._recent_detections: Deque[bool] = deque(maxlen=confirmation_window)

    def should_alert(self, detected: bool) -> bool:
        """Returns True only if enough recent frames confirmed the detection."""
        self._recent_detections.append(detected)

        if not detected:
            return False

        recent_positives = sum(self._recent_detections)
        return recent_positives >= self.required_confirmations

    def reset(self) -> None:
        """Clear detection history."""
        self._recent_detections.clear()
