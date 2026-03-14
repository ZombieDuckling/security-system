"""Configuration for the security system PoC."""

# Camera
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Gesture detection
HANDS_UP_Y_THRESHOLD = 0.5  # Wrist above this normalized y = hand raised
MIN_HANDS_FOR_DANGER = 2  # Both hands visible for "hands up" danger
GESTURE_CONFIDENCE_THRESHOLD = 0.5  # Lower = more sensitive

# Weapon detection
WEAPON_DETECT_EVERY_N_FRAMES = 2  # Run YOLO more frequently for better detection
WEAPON_CONFIDENCE_THRESHOLD = 0.35  # Lower = more sensitive
HUGGINGFACE_REPO = "Subh775/Firearm_Detection_Yolov8n"
HUGGINGFACE_WEIGHTS_PATH = "weights/best.pt"

# Alert
ALERT_DEBOUNCE_SECONDS = 3.0  # Min time between same-type alerts (reduced for testing)
MAX_ALERTS_IN_MEMORY = 100

# Face recognition / safe face
FACE_RECOGNITION_EVERY_N_FRAMES = 6  # Run more frequently for better detection
SAFE_FACE_TOLERANCE = 0.5  # Higher = more lenient match (cosine similarity)
SAFE_FACE_PATH = ".cache/safe_face.npy"  # Stored encoding
# When True, gesture/weapon alerts are suppressed if safe face is currently detected
ALERT_ONLY_UNKNOWN_FACES = False

# Motion detection
MOTION_THRESHOLD = 25
MOTION_MIN_AREA = 500
MOTION_DETECT_EVERY_N_FRAMES = 3

# Safe word detection (double clap)
SAFE_WORD_THRESHOLD = 0.03

# Server
HOST = "0.0.0.0"
PORT = 8765


# System modes
class SystemMode:
    ARMED = "armed"  # Full detection, all alerts active
    HOME = "home"  # Home mode - partial detection (no weapons, gesture only)
    DISARMED = "disarmed"  # No detection active
    TEST = "test"  # Test mode - detection but no real alerts
