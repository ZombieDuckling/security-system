"""Motion detection using background subtraction."""

import cv2
import numpy as np
from typing import Tuple, Optional


class MotionDetector:
    """Detects motion in camera frames using background subtraction."""

    def __init__(
        self,
        threshold: int = 25,
        min_area: int = 500,
        history: int = 500,
    ):
        self._threshold = threshold
        self._min_area = min_area
        self._fgbg = cv2.createBackgroundSubtractorMOG2(
            history=history, varThreshold=16, detectShadows=True
        )
        self._kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        self._frame_count = 0

    def process(self, frame_bgr) -> Tuple[bool, float, list]:
        """
        Detect motion in BGR frame.
        Returns (motion_detected, max_confidence, bounding_boxes).
        """
        self._frame_count += 1

        fgmask = self._fgbg.apply(frame_bgr)

        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, self._kernel)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, self._kernel)

        _, thresh = cv2.threshold(fgmask, self._threshold, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        boxes = []
        max_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= self._min_area:
                x, y, w, h = cv2.boundingRect(contour)
                boxes.append((x, y, x + w, y + h))
                max_area = max(max_area, area)

        motion_detected = len(boxes) > 0

        if max_area > 0:
            confidence = min(1.0, max_area / 10000)
        else:
            confidence = 0.0

        return motion_detected, confidence, boxes

    def draw_boxes(
        self,
        frame,
        boxes: list,
        confidences: Optional[list] = None,
    ) -> None:
        """Draw motion bounding boxes on frame (BGR)."""
        for i, (x1, y1, x2, y2) in enumerate(boxes):
            color = (255, 165, 0)  # Orange for motion

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = "Motion"
            if confidences and i < len(confidences):
                label += f" {confidences[i] * 100:.0f}%"

            (label_w, label_h), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(frame, (x1, y1 - label_h - 4), (x1 + label_w, y1), color, -1)
            cv2.putText(
                frame,
                label,
                (x1, y1 - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )
