"""Weapon (firearm) detection using YOLOv8 with multiple models for better coverage."""

from typing import List, Tuple, Optional

from huggingface_hub import hf_hub_download

# Lazy import ultralytics so we can run without GPU
_yolo_model = None
_yolo_model_v8 = None


def _get_model_path(model_type: str = "nano") -> str:
    """Download weapon detection model.

    Models:
    - nano: Fast, good for real-time
    - small: More accurate, still fast
    """
    # Try multiple repositories for better coverage
    repos = [
        ("Subh775/Firearm_Detection_Yolov8n", "weights/best.pt"),  # Original
        ("SkalskiP/yolov8-weapon-detection", "yolov8m-weapon.pt"),  # Alternative
    ]

    for repo_id, filename in repos:
        try:
            return hf_hub_download(repo_id=repo_id, filename=filename)
        except Exception:
            continue

    # Fallback - try first one anyway
    return hf_hub_download(
        repo_id="Subh775/Firearm_Detection_Yolov8n", filename="weights/best.pt"
    )


def get_weapon_detector(model_type: str = "nano"):
    """Lazy-load YOLO model (downloads on first use)."""
    global _yolo_model, _yolo_model_v8

    if model_type == "nano":
        if _yolo_model is None:
            from ultralytics import YOLO

            path = _get_model_path("nano")
            _yolo_model = YOLO(path)
        return _yolo_model
    else:
        if _yolo_model_v8 is None:
            from ultralytics import YOLO

            path = _get_model_path("small")
            _yolo_model_v8 = YOLO(path)
        return _yolo_model_v8


class WeaponDetector:
    """Runs firearm detection on frames - ONLY detect guns and knives in threat positions."""

    def __init__(self, confidence_threshold: float = 0.70):
        self._conf_threshold = confidence_threshold
        self._model = None
        self._frame_count = 0

        # ONLY these are valid weapons - no generic "weapon"
        self._valid_weapons = {
            "gun",
            "pistol",
            "rifle",
            "firearm",
            "handgun",
            "shotgun",
            "revolver",
            "knife",
            "knife_weapon",
            "gun_weapon",
        }

        # Other detections to reject
        self._reject_classes = {
            "weapon",
            "cell phone",
            "remote",
            "book",
            "cup",
            "bottle",
            "chair",
            "tv",
            "laptop",
            "phone",
        }

    def _ensure_model(self):
        if self._model is None:
            self._model = get_weapon_detector("nano")

    def _parse_class_name(self, class_id: int, model) -> str:
        """Get class name from model."""
        try:
            if hasattr(model, "names"):
                names = model.names
                if isinstance(names, dict) and class_id in names:
                    return names[class_id].lower()
                elif isinstance(names, list) and class_id < len(names):
                    return names[class_id].lower()
        except Exception:
            pass
        return ""

    def _is_weapon_class(self, class_name: str, class_id: int) -> bool:
        """Check if detected class is a weapon."""
        class_name = class_name.lower() if class_name else ""

        # Check against known weapon classes
        for weapon_term in self._weapon_classes:
            if weapon_term in class_name:
                return True

        return False

    def _validate_detection(
        self, class_name: str, box: Tuple, frame_shape: Tuple
    ) -> bool:
        """Strict validation - must be gun or knife with correct shape."""
        class_name = class_name.lower() if class_name else ""

        # Must be a valid weapon
        if class_name not in self._valid_weapons:
            return False

        # Check aspect ratio - weapons are narrow
        x1, y1, x2, y2 = box
        width = x2 - x1
        height = y2 - y1
        if width == 0 or height == 0:
            return False

        aspect = width / height

        # Guns: narrow (< 0.6), Knives: very narrow (< 0.3)
        if "knife" in class_name:
            if aspect > 0.4:
                return False
        else:  # gun/rifle/etc
            if aspect > 0.7:
                return False

        # Size check - must be reasonable size (0.5% to 15% of frame)
        area = width * height
        frame_area = frame_shape[0] * frame_shape[1]
        ratio = area / frame_area
        if ratio < 0.005 or ratio > 0.15:
            return False

        return True

    def _is_weapon_class(self, class_name: str) -> bool:
        """Check if detected class is a valid weapon."""
        class_name = class_name.lower() if class_name else ""
        return class_name in self._valid_weapons

    def process(self, frame_bgr) -> Tuple[bool, float, List[Tuple[int, int, int, int]]]:
        """
        Run detection on BGR frame. Returns (weapon_detected, max_confidence, list of boxes).
        Boxes are (x1, y1, x2, y2) in pixel coords.
        """
        self._frame_count += 1

        self._ensure_model()

        # Run detection with multiple augmentations for better detection
        results = self._model(
            frame_bgr,
            verbose=False,
            conf=self._conf_threshold,
            iou=0.45,  # Lower IOU for more detections
            agnostic_nms=True,  # Class-agnostic NMS
            max_det=10,  # Max detections per frame
        )[0]

        boxes = []
        max_conf = 0.0
        frame_shape = frame_bgr.shape[:2] if hasattr(frame_bgr, "shape") else (480, 640)

        if results.boxes is not None:
            for box in results.boxes:
                conf = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self._parse_class_name(class_id, self._model)

                # Get box coordinates
                xyxy = box.xyxy[0].cpu().numpy()
                box_coords = tuple(map(int, xyxy))

                # STRICT validation - must pass all checks
                if not self._validate_detection(class_name, box_coords, frame_shape):
                    continue

                boxes.append(box_coords)
                max_conf = max(max_conf, conf)

        return len(boxes) > 0, max_conf, boxes

    def draw_boxes(
        self,
        frame,
        boxes: List[Tuple[int, int, int, int]],
        confidences: Optional[List[float]] = None,
    ) -> None:
        """Draw bounding boxes on frame (BGR)."""
        import cv2

        for i, (x1, y1, x2, y2) in enumerate(boxes):
            # Draw box with gradient color based on confidence
            color = (0, 0, 255)  # Red for weapons

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Draw label
            label = "Weapon"
            if confidences and i < len(confidences):
                label += f" {confidences[i] * 100:.0f}%"

            # Draw label background
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
