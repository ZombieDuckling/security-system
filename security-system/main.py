"""
Security System PoC — entry point.
Runs camera capture + detection in a background thread and serves the web UI.
"""

import sys
import threading
import time
import cv2

import config
from config import SystemMode
from detection import GestureDetector, WeaponDetector, MotionDetector
from detection.audio_detector import SafeWordDetector
from detection.face_recognizer import (
    SafeFaceManager,
    is_available as face_recognition_available,
)
from alert_service import AlertService
from web.server import set_stream_state

# Shared state for the web server (frame bytes, alert service, face status, capture request)
_stream_state = {
    "frame_bytes": None,
    "alert_service": None,
    "face_status": "none",  # "safe" | "unknown" | "none"
    "safe_face_set": False,
    "face_recognition_available": False,
    "capture_safe_face_request": False,
    "clear_safe_face_request": False,
    "capture_message": None,  # "Looking for face...", "No face detected", "Saved!", etc.
    "system_mode": SystemMode.ARMED,  # "armed" | "home" | "disarmed" | "test"
    "detection_features": {  # Detection feature toggles
        "gesture_detection": True,
        "weapon_detection": True,
        "face_recognition": True,
        "motion_detection": True,
    },
    "safe_word_enabled": False,
    "safe_word": "",
    "voice_commands_enabled": False,
}


def _run_detection_loop():
    """Background thread: capture frames, run gesture + weapon detection, update stream state."""
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    gesture_det = GestureDetector(
        min_detection_confidence=config.GESTURE_CONFIDENCE_THRESHOLD,
        hands_up_y_threshold=config.HANDS_UP_Y_THRESHOLD,
    )
    weapon_det = WeaponDetector(confidence_threshold=config.WEAPON_CONFIDENCE_THRESHOLD)
    motion_det = MotionDetector(
        threshold=config.MOTION_THRESHOLD,
        min_area=config.MOTION_MIN_AREA,
    )
    alerts = AlertService(
        debounce_seconds=config.ALERT_DEBOUNCE_SECONDS,
        max_alerts=config.MAX_ALERTS_IN_MEMORY,
    )
    safe_face = SafeFaceManager(
        storage_path=config.SAFE_FACE_PATH,
        tolerance=config.SAFE_FACE_TOLERANCE,
    )

    # Initialize safe word detector
    safe_word_detector = None
    try:
        safe_word_detector = SafeWordDetector(
            energy_threshold=config.SAFE_WORD_THRESHOLD,
        )
        _stream_state["safe_word_available"] = safe_word_detector.is_available()
    except Exception as e:
        print(f"[SafeWordDetector] Could not initialize: {e}")
        _stream_state["safe_word_available"] = False

    # Start safe word detector if enabled
    def on_safe_word_triggered():
        print("[Safe Word] Detected! Triggering silent alert.")
        alerts.trigger("safe_word", 1.0)
        _stream_state["safe_word_triggered"] = True

        # Reset after 2 seconds
        def reset_trigger():
            time.sleep(2.0)
            _stream_state["safe_word_triggered"] = False

        threading.Thread(target=reset_trigger, daemon=True).start()

    if safe_word_detector and _stream_state.get("safe_word_enabled"):
        try:
            safe_word_detector.start(on_safe_word_triggered)
            print("[SafeWordDetector] Started listening for safe word (double clap)")
        except Exception as e:
            print(f"[SafeWordDetector] Failed to start: {e}")

    _stream_state["alert_service"] = alerts
    _stream_state["safe_face_set"] = safe_face.is_safe_face_set()
    _stream_state["face_recognition_available"] = face_recognition_available()
    frame_count = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.05)
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_count += 1

            if (
                _stream_state.get("capture_message_clear_at")
                and time.time() > _stream_state["capture_message_clear_at"]
            ):
                _stream_state["capture_message"] = None
                _stream_state["capture_message_clear_at"] = None

            if _stream_state.get("clear_safe_face_request"):
                safe_face.clear_safe_face()
                _stream_state["safe_face_set"] = False
                _stream_state["clear_safe_face_request"] = False
                print("[Safe face] Cleared.", flush=True)

            # Capture safe face on request (use first frame with a face)
            if _stream_state.get("capture_safe_face_request"):
                _stream_state["capture_message"] = "Looking for face…"
                encodings_cap, _ = safe_face.get_encodings_and_locations(
                    frame_rgb, for_capture=True
                )
                if encodings_cap and safe_face.set_safe_face_from_frame(frame_rgb):
                    _stream_state["safe_face_set"] = True
                    _stream_state["capture_safe_face_request"] = False
                    _stream_state["capture_message"] = "Saved!"
                    _stream_state["capture_message_clear_at"] = time.time() + 4.0
                    print("[Safe face] Saved.", flush=True)
                else:
                    _stream_state["capture_message"] = (
                        "No face detected — look at the camera"
                        if not encodings_cap
                        else "Looking for face…"
                    )

            # Face recognition every N frames
            current_face_status = "none"
            if face_recognition_available() and (
                frame_count % config.FACE_RECOGNITION_EVERY_N_FRAMES == 0
            ):
                encodings, locations = safe_face.get_encodings_and_locations(frame_rgb)
                for enc, (top, right, bottom, left) in zip(encodings, locations):
                    is_safe = safe_face.check_face(enc)
                    label = "Safe" if is_safe else "Unknown"
                    color = (0, 255, 0) if is_safe else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(
                        frame,
                        label,
                        (left, top - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2,
                    )
                    if is_safe:
                        current_face_status = "safe"
                    elif current_face_status != "safe":
                        current_face_status = "unknown"
                _stream_state["face_status"] = current_face_status

            _stream_state["safe_face_set"] = safe_face.is_safe_face_set()

            # Get current system mode
            system_mode = _stream_state.get("system_mode", SystemMode.ARMED)
            is_armed = system_mode in (SystemMode.ARMED, SystemMode.HOME)
            is_test_mode = system_mode == SystemMode.TEST

            # Determine which features are active based on mode
            detection_features = _stream_state.get(
                "detection_features",
                {
                    "gesture_detection": True,
                    "weapon_detection": True,
                    "face_recognition": True,
                    "motion_detection": True,
                },
            )

            # In HOME mode, disable weapon detection by default
            if system_mode == SystemMode.HOME:
                detection_features = detection_features.copy()
                detection_features["weapon_detection"] = False

            # Gesture detection every frame (only if armed and feature enabled)
            danger_gesture = False
            suppress_alert = False

            # In test mode, suppress actual alerts but allow detection for testing
            if is_test_mode:
                suppress_alert = True

            if is_armed and detection_features.get("gesture_detection", True):
                danger_gesture, gest_conf, landmarks_list = gesture_det.process(
                    frame_rgb
                )
                suppress_alert_for_gesture = (
                    config.ALERT_ONLY_UNKNOWN_FACES
                    and _stream_state.get("face_status") == "safe"
                )
                if (
                    danger_gesture
                    and not suppress_alert
                    and not suppress_alert_for_gesture
                ):
                    alerts.trigger("gesture", gest_conf)
            else:
                landmarks_list = []
            if landmarks_list:
                gesture_det.draw_landmarks(frame, landmarks_list)

            # Weapon detection every N frames (only if armed and feature enabled)
            if is_armed and detection_features.get("weapon_detection", True):
                if frame_count % config.WEAPON_DETECT_EVERY_N_FRAMES == 0:
                    weapon_found, weapon_conf, boxes = weapon_det.process(frame)
                    suppress_alert_for_weapon = (
                        config.ALERT_ONLY_UNKNOWN_FACES
                        and _stream_state.get("face_status") == "safe"
                    )
                    if (
                        weapon_found
                        and not suppress_alert
                        and not suppress_alert_for_weapon
                    ):
                        alerts.trigger("weapon", weapon_conf)
                    weapon_det.draw_boxes(frame, boxes)

            # Motion detection every N frames (only if armed and feature enabled)
            if is_armed and detection_features.get("motion_detection", True):
                if frame_count % config.MOTION_DETECT_EVERY_N_FRAMES == 0:
                    motion_found, motion_conf, motion_boxes = motion_det.process(frame)
                    suppress_alert_for_motion = (
                        config.ALERT_ONLY_UNKNOWN_FACES
                        and _stream_state.get("face_status") == "safe"
                    )
                    if (
                        motion_found
                        and not suppress_alert
                        and not suppress_alert_for_motion
                    ):
                        alerts.trigger("motion", motion_conf)
                    motion_det.draw_boxes(frame, motion_boxes)

            # Optional labels
            if danger_gesture:
                cv2.putText(
                    frame,
                    "DANGER GESTURE",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 165, 255),
                    2,
                )

            # Show mode indicator
            mode_label = f"MODE: {system_mode.upper()}"
            mode_color = (
                (0, 255, 0)
                if system_mode == SystemMode.ARMED
                else (255, 165, 0)
                if system_mode == SystemMode.HOME
                else (100, 100, 100)
                if system_mode == SystemMode.DISARMED
                else (0, 165, 255)
            )
            cv2.putText(
                frame,
                mode_label,
                (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                mode_color,
                2,
            )

            _, jpeg = cv2.imencode(".jpg", frame)
            _stream_state["frame_bytes"] = jpeg.tobytes()

    except Exception as e:
        print("Detection loop error:", e, file=sys.stderr)
    finally:
        cap.release()
        gesture_det.close()


def main():
    # Placeholder frame so /video stream has data immediately (avoids Safari/browser timeout)
    import numpy as np

    placeholder = np.zeros((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8)
    cv2.putText(
        placeholder,
        "Starting camera...",
        (50, config.FRAME_HEIGHT // 2 - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
    )
    _, jpeg = cv2.imencode(".jpg", placeholder)
    _stream_state["frame_bytes"] = jpeg.tobytes()

    set_stream_state(_stream_state)
    thread = threading.Thread(target=_run_detection_loop, daemon=True)
    thread.start()
    # Give camera time to produce first frame
    time.sleep(1.5)

    import uvicorn

    uvicorn.run(
        "web.server:app",
        host=config.HOST,
        port=config.PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
