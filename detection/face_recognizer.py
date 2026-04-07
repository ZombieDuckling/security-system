"""Safe face storage and comparison. Uses face_recognition if available; else OpenCV-only fallback."""

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

# Prefer face_recognition (best); fallback to OpenCV-only (no extra deps) when dlib not installed
_BACKEND = None
_AVAILABLE = False

try:
    import face_recognition

    _BACKEND = "face_recognition"
    _AVAILABLE = True
except ImportError:
    pass

if not _AVAILABLE:
    _BACKEND = "opencv"
    _AVAILABLE = True  # OpenCV is already a project dependency


def is_available() -> bool:
    return _AVAILABLE


def _get_backend() -> str:
    return _BACKEND or "opencv"


def _opencv_face_detector():
    """Lazy-load OpenCV Haar cascade for face detection."""
    path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    return cv2.CascadeClassifier(path)


def _opencv_lbp_face_detector():
    """Lazy-load OpenCV LBP cascade for better face detection."""
    path = cv2.data.haarcascades + "lbpcascade_frontalface.xml"
    return cv2.CascadeClassifier(path)


def _enhance_face_image(
    rgb_frame: np.ndarray, top: int, right: int, bottom: int, left: int
) -> np.ndarray:
    """Enhance face image for better embedding: crop, align, histogram equalization."""
    crop = rgb_frame[top:bottom, left:right]
    if crop.size == 0:
        return np.array([])

    # Resize to standard size
    resized = cv2.resize(crop, (128, 128), interpolation=cv2.INTER_CUBIC)

    # Convert to YCrCb for histogram equalization
    ycrcb = cv2.cvtColor(resized, cv2.COLOR_RGB2YCrCb)

    # Equalize Y channel (illumination)
    ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])

    # Convert back to RGB
    enhanced = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2RGB)

    # Apply slight Gaussian blur to reduce noise
    enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)

    return enhanced


def _opencv_embed_face(
    rgb_frame: np.ndarray, top: int, right: int, bottom: int, left: int
) -> np.ndarray:
    """Improved embedding: enhanced face processing with HOG features."""
    enhanced = _enhance_face_image(rgb_frame, top, right, bottom, left)
    if enhanced.size == 0:
        return np.array([], dtype=np.float64)

    # Resize to 64x64 for embedding
    small = cv2.resize(enhanced, (64, 64), interpolation=cv2.INTER_AREA)

    # Convert to grayscale for HOG-like features
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)

    # Compute HOG-like features manually
    # Use gradient-based features instead of raw pixels
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(sobelx**2 + sobely**2)

    # Normalize
    mag_norm = magnitude.astype(np.float64)
    if mag_norm.max() > 0:
        mag_norm = mag_norm / mag_norm.max()

    # Flatten and combine with resized grayscale
    resized_gray = (
        cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float64)
        / 255.0
    )
    features = np.concatenate([mag_norm.flatten(), resized_gray.flatten()])

    # Final normalization
    norm = np.linalg.norm(features)
    if norm > 1e-9:
        features = features / norm

    return features


class SafeFaceManager:
    """Load/save one safe face encoding and compare frames against it."""

    def __init__(self, storage_path: str, tolerance: float = 0.5):
        self._path = Path(storage_path)
        self._tolerance = tolerance
        self._encoding: Optional[np.ndarray] = None
        self._haar: Optional[cv2.CascadeClassifier] = None
        self._lbp: Optional[cv2.CascadeClassifier] = None
        self._load()

    def _load(self) -> None:
        if not _AVAILABLE or not self._path.exists():
            return
        try:
            data = np.load(self._path, allow_pickle=True)
            self._encoding = (
                data if isinstance(data, np.ndarray) and data.ndim == 1 else None
            )
        except Exception:
            self._encoding = None

    def is_safe_face_set(self) -> bool:
        return self._encoding is not None

    def get_encodings_and_locations(
        self, rgb_frame: np.ndarray, for_capture: bool = False
    ) -> Tuple[List[np.ndarray], List[Tuple[int, int, int, int]]]:
        """Return (list of encodings, list of (top, right, bottom, left)).
        When for_capture=True, use more permissive detection (OpenCV backend) to make setting safe face easier.
        """
        if not _AVAILABLE:
            return [], []

        if _BACKEND == "face_recognition":
            try:
                import face_recognition

                locations = face_recognition.face_locations(rgb_frame)
                encodings = face_recognition.face_encodings(rgb_frame, locations)
                return encodings, locations
            except Exception:
                return [], []

        if _BACKEND == "opencv":
            try:
                # Try LBP first (usually better), then fall back to Haar
                if self._lbp is None:
                    self._lbp = _opencv_lbp_face_detector()
                if self._haar is None:
                    self._haar = _opencv_face_detector()

                gray = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2GRAY)

                # More permissive params when capturing so user can set safe face more easily
                if for_capture:
                    # Try LBP with relaxed settings
                    rects = self._lbp.detectMultiScale(
                        gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30)
                    )
                    if len(rects) == 0:
                        # Fall back to Haar
                        rects = self._haar.detectMultiScale(
                            gray, scaleFactor=1.05, minNeighbors=3, minSize=(24, 24)
                        )
                else:
                    # Use LBP for detection (faster and often better)
                    rects = self._lbp.detectMultiScale(
                        gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40)
                    )
                    if len(rects) == 0:
                        # Fall back to Haar
                        rects = self._haar.detectMultiScale(
                            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                        )

                encodings = []
                locations = []
                for x, y, w, h in rects:
                    # Add margin around face
                    margin = int(w * 0.1)
                    top = max(0, y - margin)
                    right = min(rgb_frame.shape[1], x + w + margin)
                    bottom = min(rgb_frame.shape[0], y + h + margin)
                    left = max(0, x - margin)

                    enc = _opencv_embed_face(rgb_frame, top, right, bottom, left)
                    if enc.size > 0:
                        encodings.append(enc)
                        locations.append((top, right, bottom, left))
                return encodings, locations
            except Exception:
                return [], []

        return [], []

    def set_safe_face_from_frame(self, rgb_frame: np.ndarray) -> bool:
        """Extract one face encoding from frame and save as safe face. Returns True on success."""
        if not _AVAILABLE:
            return False
        encodings, _ = self.get_encodings_and_locations(rgb_frame, for_capture=True)
        if not encodings:
            return False
        self._encoding = np.array(encodings[0], dtype=np.float64)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        np.save(self._path, self._encoding)
        return True

    def clear_safe_face(self) -> None:
        self._encoding = None
        if self._path.exists():
            try:
                self._path.unlink()
            except Exception:
                pass

    def check_face(self, encoding: np.ndarray) -> bool:
        """Return True if this encoding matches the safe face."""
        if not _AVAILABLE or self._encoding is None:
            return False
        enc = np.asarray(encoding, dtype=np.float64)
        ref = np.asarray(self._encoding, dtype=np.float64)
        if enc.size != ref.size:
            return False

        if _BACKEND == "face_recognition":
            try:
                import face_recognition

                results = face_recognition.compare_faces(
                    [ref], enc, tolerance=self._tolerance
                )
                return bool(results and results[0])
            except Exception:
                return False

        if _BACKEND == "opencv":
            # Improved cosine similarity for normalized vectors
            similarity = np.dot(enc, ref)
            threshold = self._tolerance
            return float(similarity) >= threshold

        return False
