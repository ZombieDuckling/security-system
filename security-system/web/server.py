"""FastAPI server: static UI, MJPEG stream, alerts API."""

import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

# Shared state is set by main.py before running the server
_stream_state: Optional[dict] = None


def set_stream_state(state: dict) -> None:
    global _stream_state
    _stream_state = state


def get_stream_state() -> Optional[dict]:
    return _stream_state


app = FastAPI(title="Security System PoC")

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def index():
    """Serve main UI."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Static files not found"}


# Minimal 1x1 pixel JPEG so we always send something when no frame yet (avoids stream timeout)
_PLACEHOLDER_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff"
    b"\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r"
    b"\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $."
    b"' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01"
    b"\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
    b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfc\xb2\xdf\xff\xd9"
)


@app.get("/video")
async def video_stream():
    """MJPEG stream of the latest frame (with overlays)."""
    state = get_stream_state()
    if state is None:
        return JSONResponse(content={"error": "Stream not ready"}, status_code=503)

    boundary = b"frame"

    async def generate():
        while True:
            jpeg_bytes = state.get("frame_bytes") if state else None
            if not jpeg_bytes:
                jpeg_bytes = _PLACEHOLDER_JPEG
            yield (
                b"--" + boundary + b"\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: "
                + str(len(jpeg_bytes)).encode()
                + b"\r\n\r\n"
                + jpeg_bytes
                + b"\r\n"
            )
            await asyncio.sleep(0.05)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/snapshot")
async def get_snapshot():
    """Get a single snapshot frame as JPEG."""
    state = get_stream_state()
    if state is None:
        return JSONResponse(content={"error": "Stream not ready"}, status_code=503)

    jpeg_bytes = state.get("frame_bytes")
    if not jpeg_bytes:
        jpeg_bytes = _PLACEHOLDER_JPEG

    return Response(
        content=jpeg_bytes,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
        },
    )


@app.get("/api/alerts")
async def get_alerts(limit: Optional[int] = 50):
    """Recent alerts for the UI."""
    state = get_stream_state()
    if state is None:
        return []
    alerts = state.get("alert_service")
    if alerts is None:
        return []
    return alerts.get_recent_alerts(limit=limit)


@app.get("/api/safe-face/status")
async def get_safe_face_status():
    """Safe face: whether one is set, current face status, and if face recognition is available."""
    state = get_stream_state()
    if state is None:
        return {"safe_face_set": False, "face_status": "none", "available": False}
    return {
        "safe_face_set": state.get("safe_face_set", False),
        "face_status": state.get("face_status", "none"),
        "available": state.get("face_recognition_available", False),
        "capture_message": state.get("capture_message"),
    }


@app.post("/api/safe-face/capture")
async def capture_safe_face():
    """Request that the next frame with a detectable face be saved as the safe face."""
    state = get_stream_state()
    if state is None:
        return JSONResponse(content={"error": "Not ready"}, status_code=503)
    state["capture_safe_face_request"] = True
    return {
        "ok": True,
        "message": "Look at the camera. Safe face will be saved when a face is detected.",
    }


@app.post("/api/safe-face/clear")
async def clear_safe_face():
    """Clear the stored safe face."""
    state = get_stream_state()
    if state is None:
        return JSONResponse(content={"error": "Not ready"}, status_code=503)
    state["clear_safe_face_request"] = True
    return {"ok": True, "message": "Safe face will be cleared."}


@app.get("/api/status")
async def get_status():
    """Get system status: mode, armed state and connection info."""
    state = get_stream_state()
    if state is None:
        return {
            "connected": False,
            "mode": "disarmed",
            "armed": False,
            "face_recognition_available": False,
            "face_status": "none",
        }
    mode = state.get("system_mode", "armed")
    return {
        "connected": True,
        "mode": mode,
        "armed": mode in ("armed", "home"),
        "face_recognition_available": state.get("face_recognition_available", False),
        "face_status": state.get("face_status", "none"),
        "safe_face_set": state.get("safe_face_set", False),
        "safe_word_enabled": state.get("safe_word_enabled", False),
        "voice_commands_enabled": state.get("voice_commands_enabled", False),
    }


@app.post("/api/mode")
async def set_mode(request: dict = None):
    """Set system mode: armed, home, disarmed, or test."""
    from config import SystemMode

    state = get_stream_state()
    if state is None:
        return JSONResponse(content={"error": "Not ready"}, status_code=503)

    mode = "armed"  # default
    if request and "mode" in request:
        mode = request["mode"]

    # Validate mode
    valid_modes = [
        SystemMode.ARMED,
        SystemMode.HOME,
        SystemMode.DISARMED,
        SystemMode.TEST,
    ]
    if mode not in valid_modes:
        mode = SystemMode.ARMED

    state["system_mode"] = mode
    return {"ok": True, "mode": mode}


@app.post("/api/arm")
async def arm_system(request: dict = None):
    """Arm or disarm the system (legacy endpoint, use /api/mode instead)."""
    from config import SystemMode

    state = get_stream_state()
    if state is None:
        return JSONResponse(content={"error": "Not ready"}, status_code=503)

    armed = True
    if request and "armed" in request:
        armed = bool(request["armed"])

    state["system_mode"] = SystemMode.ARMED if armed else SystemMode.DISARMED
    return {"ok": True, "armed": armed, "mode": state["system_mode"]}


@app.get("/api/detection/features")
async def get_detection_features():
    """Get detection features and their enabled status."""
    state = get_stream_state()
    if state is None:
        return {"features": []}

    features = state.get(
        "detection_features",
        {"gesture_detection": True, "weapon_detection": True, "face_recognition": True},
    )
    return {"features": features}


@app.post("/api/detection/features")
async def update_detection_features(request: dict = None):
    """Update detection features enabled status."""
    state = get_stream_state()
    if state is None:
        return JSONResponse(content={"error": "Not ready"}, status_code=503)

    if request and "features" in request:
        state["detection_features"] = request["features"]
        return {"ok": True, "features": state["detection_features"]}
    return JSONResponse(content={"error": "Missing features"}, status_code=400)


@app.get("/api/safe-word")
async def get_safe_word():
    """Get safe word configuration."""
    state = get_stream_state()
    if state is None:
        return {"enabled": False, "configured": False, "available": False}
    return {
        "enabled": state.get("safe_word_enabled", False),
        "configured": bool(state.get("safe_word", "")),
        "available": state.get("safe_word_available", False),
    }


@app.post("/api/safe-word")
async def set_safe_word(request: dict = None):
    """Configure and toggle safe word."""
    from config import SystemMode

    state = get_stream_state()
    if state is None:
        return JSONResponse(content={"error": "Not ready"}, status_code=503)

    if request:
        if "enabled" in request:
            enabled = bool(request["enabled"])
            state["safe_word_enabled"] = enabled

            # Note: Starting/stopping the detector would require access to the detector instance
            # For now, just store the setting - actual detector is started in main.py

    return {
        "ok": True,
        "enabled": state.get("safe_word_enabled", False),
        "configured": bool(state.get("safe_word", "")),
    }


@app.get("/api/voice-commands")
async def get_voice_commands():
    """Get voice commands configuration."""
    state = get_stream_state()
    if state is None:
        return {"enabled": False}
    return {"enabled": state.get("voice_commands_enabled", False)}


@app.post("/api/voice-commands")
async def set_voice_commands(request: dict = None):
    """Configure voice commands."""
    state = get_stream_state()
    if state is None:
        return JSONResponse(content={"error": "Not ready"}, status_code=503)

    if request and "enabled" in request:
        state["voice_commands_enabled"] = bool(request["enabled"])

    return {"ok": True, "enabled": state.get("voice_commands_enabled", False)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8765)
