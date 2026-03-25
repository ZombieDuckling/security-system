"""
Pi-minimal runtime for ZombieDuckling/security-system.

Uses the existing FastAPI endpoints in `web/server.py` (/api/status, /api/snapshot, /api/mode)
but sources `frame_bytes` from the real Pi camera via `v4l2-ctl` MJPEG capture.

This avoids heavy ML dependencies (opencv/mediapipe/ultralytics/face_recognition).
"""

import os
import threading
import time
import subprocess
import tempfile
from pathlib import Path

import config
from web.server import set_stream_state


def _capture_jpeg_bytes_v4l2(device: str, width: int, height: int, timeout_s: float) -> bytes | None:
    tmp_path: str | None = None
    try:
        fd, tmp_path = tempfile.mkstemp(prefix="alrt_frame_", suffix=".jpg")
        os.close(fd)

        subprocess.run(
            [
                "v4l2-ctl",
                "-d",
                device,
                f"--set-fmt-video=width={width},height={height},pixelformat=MJPG",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=timeout_s,
        )
        subprocess.run(
            [
                "v4l2-ctl",
                "-d",
                device,
                "--stream-mmap",
                "--stream-count=1",
                f"--stream-to={tmp_path}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=timeout_s,
        )

        p = Path(tmp_path)
        if not p.exists() or p.stat().st_size <= 0:
            return None
        return p.read_bytes()
    except Exception:
        return None
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def main() -> None:
    device = os.getenv("ALRT_V4L2_DEVICE", "/dev/video0")
    width = int(os.getenv("ALRT_V4L2_WIDTH", str(config.FRAME_WIDTH)))
    height = int(os.getenv("ALRT_V4L2_HEIGHT", str(config.FRAME_HEIGHT)))
    interval_s = float(os.getenv("ALRT_SNAPSHOT_INTERVAL_S", "0.5"))
    timeout_s = float(os.getenv("ALRT_V4L2_TIMEOUT_S", "3.5"))

    # Seed state for the web server.
    state: dict = {
        "frame_bytes": None,
        "alert_service": None,
        "face_status": "none",
        "safe_face_set": False,
        "face_recognition_available": False,
        "capture_safe_face_request": False,
        "clear_safe_face_request": False,
        "capture_message": None,
        "system_mode": os.getenv("ALRT_SYSTEM_MODE", config.SystemMode.DISARMED),
        "detection_features": {
            "gesture_detection": False,
            "weapon_detection": False,
            "face_recognition": False,
            "motion_detection": False,
        },
        "safe_word_enabled": False,
        "safe_word": "",
        "voice_commands_enabled": False,
    }
    set_stream_state(state)

    def loop() -> None:
        while True:
            jpeg = _capture_jpeg_bytes_v4l2(device, width, height, timeout_s=timeout_s)
            if jpeg:
                state["frame_bytes"] = jpeg
            time.sleep(interval_s)

    threading.Thread(target=loop, daemon=True).start()

    import uvicorn

    uvicorn.run(
        "web.server:app",
        host=os.getenv("ALRT_STREAM_HOST", config.HOST),
        port=int(os.getenv("ALRT_STREAM_PORT", str(config.PORT))),
        log_level="info",
    )


if __name__ == "__main__":
    main()

