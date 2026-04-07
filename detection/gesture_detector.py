"""Gesture detection using MediaPipe Hand Landmarker (tasks API) for 'hands up' / danger signals."""

import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from mediapipe.tasks.python.core import base_options as base_options_lib
from mediapipe.tasks.python.vision import hand_landmarker
from mediapipe.tasks.python.vision.core import image as image_lib
from mediapipe.tasks.python.vision.core import vision_task_running_mode

# Hand landmark indices
WRIST = 0
THUMB_TIP = 4
INDEX_FINGER_TIP = 8
MIDDLE_FINGER_TIP = 12
RING_FINGER_TIP = 16
PINKY_TIP = 20
INDEX_FINGER_MCP = 5
MIDDLE_FINGER_MCP = 9
RING_FINGER_MCP = 13
PINKY_MCP = 17


HAND_LANDMARKER_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"


def _get_model_path() -> str:
    """Download hand_landmarker.task to a cache file and return its path."""
    cache_dir = Path(__file__).resolve().parent.parent / ".cache"
    cache_dir.mkdir(exist_ok=True)
    path = cache_dir / "hand_landmarker.task"
    if not path.exists():
        urllib.request.urlretrieve(HAND_LANDMARKER_MODEL_URL, path)
    return str(path)


def _is_finger_extended(landmarks, finger_tip_idx: int, finger_mcp_idx: int) -> bool:
    """Check if a finger is extended (tip is above or equal to MCP joint)."""
    tip = landmarks[finger_tip_idx]
    mcp = landmarks[finger_mcp_idx]
    return tip.y <= mcp.y + 0.02


def _detect_raised_hand(landmarks) -> Tuple[bool, float]:
    """Detect if hand is raised in 'hands up' danger gesture.

    Checks if:
    1. Wrist is above all finger tips (all fingers pointing up)
    2. Or wrist is above MCP joints (fingers extended upward)
    3. At least 3-4 fingers are extended

    Returns (is_raised, confidence)
    """
    wrist = landmarks[WRIST]

    fingers_extended = 0
    for tip_idx, mcp_idx in [
        (INDEX_FINGER_TIP, INDEX_FINGER_MCP),
        (MIDDLE_FINGER_TIP, MIDDLE_FINGER_MCP),
        (RING_FINGER_TIP, RING_FINGER_MCP),
        (PINKY_TIP, PINKY_MCP),
    ]:
        if _is_finger_extended(landmarks, tip_idx, mcp_idx):
            fingers_extended += 1

    thumb_extended = _is_finger_extended(landmarks, THUMB_TIP, WRIST)
    if thumb_extended:
        fingers_extended += 1

    wrist_above_tips = all(
        landmarks[i].y < wrist.y - 0.05
        for i in [INDEX_FINGER_TIP, MIDDLE_FINGER_TIP, RING_FINGER_TIP, PINKY_TIP]
    )

    wrist_above_mcps = all(
        landmarks[i].y < wrist.y - 0.02
        for i in [INDEX_FINGER_MCP, MIDDLE_FINGER_MCP, RING_FINGER_MCP, PINKY_MCP]
    )

    is_raised = (wrist_above_tips or wrist_above_mcps) and fingers_extended >= 3

    if is_raised:
        confidence = 0.7 + (fingers_extended * 0.075)
        if wrist_above_tips:
            confidence += 0.15
        return True, min(confidence, 0.98)

    return False, 0.0


class GestureDetector:
    """Detects danger gestures: both hands raised (hands up)."""

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        hands_up_y_threshold: float = 0.5,
    ):
        model_path = _get_model_path()
        base_options = base_options_lib.BaseOptions(model_asset_path=model_path)
        options = hand_landmarker.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision_task_running_mode.VisionTaskRunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_tracking_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = hand_landmarker.HandLandmarker.create_from_options(options)
        self._hands_up_y_threshold = hands_up_y_threshold
        self._timestamp_ms = 0

    def process(self, frame_rgb: np.ndarray) -> Tuple[bool, float, Optional[List]]:
        """
        Process an RGB frame (numpy array, uint8). Returns (danger_detected, confidence, landmarks_for_draw).
        landmarks_for_draw is a list of lists of (x_norm, y_norm) for each hand, for drawing.
        """
        self._timestamp_ms += 1
        if not isinstance(frame_rgb, np.ndarray) or frame_rgb.dtype != np.uint8:
            frame_rgb = np.asarray(frame_rgb, dtype=np.uint8)
        if not frame_rgb.flags.c_contiguous:
            frame_rgb = np.ascontiguousarray(frame_rgb)

        mp_image = image_lib.Image(
            image_format=image_lib.ImageFormat.SRGB, data=frame_rgb
        )
        result = self._landmarker.detect_for_video(mp_image, self._timestamp_ms)

        danger = False
        confidence = 0.0
        landmarks_for_draw = []

        if not result.hand_landmarks:
            return False, 0.0, None

        hands_raised = 0
        total_confidence = 0.0

        for hand_landmarks in result.hand_landmarks:
            landmarks_for_draw.append([(lm.x, lm.y) for lm in hand_landmarks])

            is_raised, hand_confidence = _detect_raised_hand(hand_landmarks)
            if is_raised:
                hands_raised += 1
                total_confidence += hand_confidence

        if hands_raised >= 2:
            danger = True
            confidence = (total_confidence / hands_raised) * 0.85 + 0.1
            confidence = min(confidence, 0.95)

        return danger, confidence, landmarks_for_draw if landmarks_for_draw else None

    def draw_landmarks(self, frame: np.ndarray, landmarks_list: Optional[List]) -> None:
        """Draw hand landmarks on frame (BGR). landmarks_list is list of lists of (x_norm, y_norm)."""
        if not landmarks_list:
            return
        h, w = frame.shape[:2]

        # Define connections to draw hand skeleton
        connections = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),  # thumb
            (0, 5),
            (5, 6),
            (6, 7),
            (7, 8),  # index finger
            (0, 9),
            (9, 10),
            (10, 11),
            (11, 12),  # middle finger
            (0, 13),
            (13, 14),
            (14, 15),
            (15, 16),  # ring finger
            (0, 17),
            (17, 18),
            (18, 19),
            (19, 20),  # pinky
            (5, 9),
            (9, 13),
            (13, 17),  # palm
        ]

        # Draw connections
        for hand_landmarks in landmarks_list:
            for start_idx, end_idx in connections:
                if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                    x1, y1 = hand_landmarks[start_idx]
                    x2, y2 = hand_landmarks[end_idx]
                    x1, y1 = int(x1 * w), int(y1 * h)
                    x2, y2 = int(x2 * w), int(y2 * h)
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Draw landmark points
        for hand_landmarks in landmarks_list:
            for x_norm, y_norm in hand_landmarks:
                x, y = int(x_norm * w), int(y_norm * h)
                cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)

    def close(self) -> None:
        self._landmarker.close()
