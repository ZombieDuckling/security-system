#!/usr/bin/env python3
"""
Security System Mobile App Client
Access detection alerts, video stream, and control from any device on local network.
"""

import requests
import cv2
import numpy as np
from urllib.request import urlretrieve

# Change this to your Mac's IP address
SERVER_IP = "192.168.0.85"
PORT = 8765
BASE_URL = f"http://{SERVER_IP}:{PORT}"


class SecurityApp:
    def __init__(self):
        self.running = True

    def get_status(self):
        """Get system status"""
        r = requests.get(f"{BASE_URL}/api/status")
        return r.json()

    def set_mode(self, mode):
        """Set system mode: armed, home, disarmed, test"""
        r = requests.post(f"{BASE_URL}/api/mode", json={"mode": mode})
        return r.json()

    def get_alerts(self, limit=20):
        """Get recent alerts"""
        r = requests.get(f"{BASE_URL}/api/alerts?limit={limit}")
        return r.json()

    def set_features(self, gesture=True, weapon=True, face=True, motion=True):
        """Toggle detection features"""
        features = {
            "gesture_detection": gesture,
            "weapon_detection": weapon,
            "face_recognition": face,
            "motion_detection": motion,
        }
        r = requests.post(
            f"{BASE_URL}/api/detection/features", json={"features": features}
        )
        return r.json()

    def get_snapshot(self):
        """Get a single frame as image"""
        r = requests.get(f"{BASE_URL}/api/snapshot")
        return r.content

    def save_snapshot(self, filename="snapshot.jpg"):
        """Save snapshot to file"""
        data = self.get_snapshot()
        with open(filename, "wb") as f:
            f.write(data)
        print(f"Saved: {filename}")

    def download_video_stream(self, duration=10, output="video.mp4"):
        """Download video stream (for simple testing)"""
        # Note: For real video, use a proper video capture library
        frames = []
        print(f"Capturing {duration}s of video...")
        # This is a simplified version - real implementation would capture MJPEG stream
        print("Note: Use /video endpoint directly in video player for live stream")

    def run_alert_monitor(self):
        """Monitor alerts and print new detections"""
        print("Alert Monitor Started (Ctrl+C to stop)")
        seen_ids = set()

        while self.running:
            try:
                alerts = self.get_alerts(10)
                for alert in alerts:
                    alert_id = f"{alert.get('timestamp')}_{alert.get('alert_type')}"
                    if alert_id not in seen_ids:
                        seen_ids.add(alert_id)
                        conf = alert.get("confidence", 0) * 100
                        atype = alert.get("alert_type", "unknown")
                        print(f"🚨 ALERT: {atype.upper()} - {conf:.0f}% confidence")
            except Exception as e:
                print(f"Error: {e}")
            import time

            time.sleep(2)

    def interactive_menu(self):
        """Simple interactive menu"""
        while self.running:
            print("\n=== Security System Menu ===")
            print("1. Get Status")
            print("2. Set Mode (Armed)")
            print("3. Set Mode (Home)")
            print("4. Set Mode (Disarmed)")
            print("5. View Alerts")
            print("6. Save Snapshot")
            print("7. Toggle All Features On")
            print("8. Exit")

            choice = input("\nChoice: ").strip()

            if choice == "1":
                status = self.get_status()
                print(f"Mode: {status.get('mode')}")
                print(f"Armed: {status.get('armed')}")
                print(f"Face: {status.get('face_status')}")
            elif choice == "2":
                print(self.set_mode("armed"))
            elif choice == "3":
                print(self.set_mode("home"))
            elif choice == "4":
                print(self.set_mode("disarmed"))
            elif choice == "5":
                alerts = self.get_alerts()
                for a in alerts:
                    print(
                        f"  {a.get('timestamp')} - {a.get('alert_type')}: {a.get('confidence', 0) * 100:.0f}%"
                    )
            elif choice == "6":
                self.save_snapshot()
            elif choice == "7":
                print(self.set_features(True, True, True, True))
            elif choice == "8":
                self.running = False
                break


def main():
    import sys

    app = SecurityApp()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "status":
            import json

            print(json.dumps(app.get_status(), indent=2))
        elif cmd == "alerts":
            import json

            print(json.dumps(app.get_alerts(), indent=2))
        elif cmd == "snapshot":
            app.save_snapshot()
        elif cmd == "monitor":
            app.run_alert_monitor()
        else:
            print(f"Unknown command: {cmd}")
            print("Commands: status, alerts, snapshot, monitor")
    else:
        app.interactive_menu()


if __name__ == "__main__":
    main()
