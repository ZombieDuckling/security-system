# Security System Proof of Concept

Camera-based gesture and weapon detection that triggers simulated alerts (terminal + web UI). Alerts are printed to the terminal and shown in the web UI.

## Features

- **Gesture detection**: MediaPipe Hands — “hands up” / danger gesture (both hands raised).
- **Weapon detection**: YOLOv8 firearm model (Hugging Face) on camera frames.
- **Face recognition**: Optional safe face — set one face as "safe"; live feed shows Safe/Unknown and green/red boxes.
- **Alerts**: Printed to terminal and shown in the web UI (debounced).
- **Web UI**: Live MJPEG feed, safe face controls, alert log, and pricing breakdown in ZAR.

## Setup

```bash
cd security-system
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

On first run, the weapon model is downloaded from Hugging Face (~6 MB).

## Run

```bash
python main.py
```

Then open **http://localhost:8765** in a browser. Allow camera access when prompted (the app uses the laptop camera).

- **Live feed**: Overlaid hand landmarks, face boxes (Safe/Unknown), and weapon boxes when detected.
- **Safe face**: Set safe face (capture your face), clear it; status shows current face (safe/unknown/none).
- **Alert log**: Recent gesture/weapon alerts.
- **Pricing**: Development and hardware breakdown in South African Rands.

## Config

Edit `config.py` for camera index, resolution, detection thresholds, weapon model run frequency, alert debounce, face recognition interval and tolerance, and server host/port. Set `ALERT_ONLY_UNKNOWN_FACES = True` to suppress gesture/weapon alerts when the safe face is detected.

**Face recognition backends:** If `face_recognition` (and its dependency `dlib`) installs, it is used for best accuracy. If not (e.g. on some Macs without a C++ build), the app falls back to an **OpenCV-only** mode: Haar cascade face detection plus a simple embedding so "Set safe face" and Safe/Unknown labels still work without extra dependencies.

## Project layout

- `main.py` — Entry point; starts detection thread and FastAPI server.
- `config.py` — Camera, detection, and server settings.
- `detection/` — Gesture (MediaPipe), weapon (YOLOv8), and face/safe-face (face_recognition) detectors.
- `alert_service.py` — Alert debouncing, terminal output, in-memory log.
- `web/server.py` — FastAPI app, MJPEG stream, `/api/alerts`, static files.
- `web/static/` — `index.html`, `style.css` (video, alerts, pricing).

## PoC scope

- Single camera (laptop webcam), no auth, no persistent storage. Alerts go to terminal and web UI only.
