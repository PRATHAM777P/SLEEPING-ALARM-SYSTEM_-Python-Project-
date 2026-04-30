"""
╔══════════════════════════════════════════════════════════════╗
║          SLEEPING ALARM SYSTEM - Drowsiness Detector         ║
║          Real-Time Eye & Face Monitoring with Alerts          ║
╚══════════════════════════════════════════════════════════════╝

Author  : Prathamesh Penshanwar
Version : 2.0.0
"""

import cv2
import time
import json
import argparse
import os
import sys
from datetime import datetime
from utils.alarm import AlarmSystem
from utils.logger import DrowsinessLogger

# ─────────────────────────────────────────────
#  Load Configuration
# ─────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config(path: str = CONFIG_FILE) -> dict:
    """Load settings from config.json with safe fallback defaults."""
    defaults = {
        "camera_index": 0,
        "sleep_frame_threshold": 20,
        "display_fps": True,
        "display_status_bar": True,
        "save_snapshots": True,
        "snapshot_dir": "snapshots",
        "log_events": True,
        "log_dir": "logs",
        "alarm_beep_frequency": 1000,
        "alarm_beep_duration_ms": 1000,
        "scale_factor": 1.1,
        "min_neighbors_face": 5,
        "min_neighbors_eye": 3,
        "rectangle_color_face": [0, 0, 255],
        "rectangle_color_eye": [0, 255, 0],
    }
    if os.path.exists(path):
        with open(path, "r") as f:
            user_config = json.load(f)
        defaults.update(user_config)
    return defaults


# ─────────────────────────────────────────────
#  Core Detection Engine
# ─────────────────────────────────────────────
class DrowsinessDetector:
    """Main class for real-time drowsiness detection."""

    def __init__(self, config: dict):
        self.cfg = config
        self.sleep_counter = 0
        self.total_sleep_events = 0
        self.session_start = datetime.now()
        self.fps = 0.0
        self._prev_frame_time = 0

        # Load Haar Cascade models
        base = os.path.dirname(__file__)
        self.face_cascade = cv2.CascadeClassifier(os.path.join(base, "face_default.xml"))
        self.eye_cascade  = cv2.CascadeClassifier(os.path.join(base, "eye.xml"))

        if self.face_cascade.empty() or self.eye_cascade.empty():
            raise FileNotFoundError(
                "Haar cascade XML files not found. "
                "Ensure face_default.xml and eye.xml are in the project root."
            )

        # Sub-systems
        self.alarm  = AlarmSystem(
            freq=config["alarm_beep_frequency"],
            duration_ms=config["alarm_beep_duration_ms"],
        )
        self.logger = DrowsinessLogger(
            log_dir=config["log_dir"],
            enabled=config["log_events"],
        )

        # Snapshot directory
        if config["save_snapshots"]:
            os.makedirs(config["snapshot_dir"], exist_ok=True)

    # ── Helpers ────────────────────────────────
    def _calc_fps(self) -> float:
        now = time.time()
        fps = 1.0 / (now - self._prev_frame_time + 1e-9)
        self._prev_frame_time = now
        return fps

    def _draw_hud(self, frame, sleeping: bool):
        """Draw heads-up display: FPS, status, counter."""
        h, w = frame.shape[:2]

        # Status banner
        if sleeping:
            label = "⚠  SLEEPING DETECTED"
            color = (0, 0, 255)
            cv2.rectangle(frame, (0, h - 50), (w, h), (0, 0, 180), -1)
        else:
            label = "✓  AWAKE"
            color = (0, 220, 0)
            cv2.rectangle(frame, (0, h - 50), (w, h), (30, 30, 30), -1)

        cv2.putText(frame, label, (10, h - 18),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 2)

        # FPS counter (top-right)
        if self.cfg["display_fps"]:
            fps_text = f"FPS: {self.fps:.1f}"
            cv2.putText(frame, fps_text, (w - 130, 25),
                        cv2.FONT_HERSHEY_PLAIN, 1.4, (200, 200, 200), 1)

        # Sleep event count (top-left)
        cv2.putText(frame, f"Sleep Events: {self.total_sleep_events}", (10, 25),
                    cv2.FONT_HERSHEY_PLAIN, 1.4, (200, 200, 200), 1)

        return frame

    def _save_snapshot(self, frame):
        """Save a timestamped snapshot when drowsiness is detected."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.cfg["snapshot_dir"], f"sleep_{ts}.jpg")
        cv2.imwrite(path, frame)
        return path

    # ── Main Loop ──────────────────────────────
    def run(self, camera_index: int = None):
        """Start the real-time detection loop."""
        idx = camera_index if camera_index is not None else self.cfg["camera_index"]
        cap = cv2.VideoCapture(idx)

        if not cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera index {idx}. "
                "Check your webcam connection or set 'camera_index' in config.json."
            )

        threshold   = self.cfg["sleep_frame_threshold"]
        face_color  = tuple(self.cfg["rectangle_color_face"])
        eye_color   = tuple(self.cfg["rectangle_color_eye"])
        sf          = self.cfg["scale_factor"]
        mn_face     = self.cfg["min_neighbors_face"]
        mn_eye      = self.cfg["min_neighbors_eye"]

        print("\n[INFO] Drowsiness Detector started. Press ESC to quit.\n")
        self.logger.log_event("SESSION_START", {"camera_index": idx})

        already_alarmed = False   # avoid repeating alarm for same sleep episode

        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Failed to grab frame. Retrying...")
                time.sleep(0.1)
                continue

            self.fps = self._calc_fps()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # ── Face Detection ──────────────────────
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=sf, minNeighbors=mn_face
            )
            sleeping = False

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), face_color, 2)
                roi_gray  = gray[y:y + h, x:x + w]
                roi_color = frame[y:y + h, x:x + w]

                # ── Eye Detection ───────────────────
                eyes = self.eye_cascade.detectMultiScale(
                    roi_gray, scaleFactor=sf, minNeighbors=mn_eye
                )
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), eye_color, 2)

                # ── Drowsiness Logic ────────────────
                if len(eyes) == 0:
                    self.sleep_counter += 1
                else:
                    self.sleep_counter = 0
                    already_alarmed = False

                if self.sleep_counter >= threshold:
                    sleeping = True
                    if not already_alarmed:
                        self.total_sleep_events += 1
                        already_alarmed = True
                        self.alarm.trigger()

                        if self.cfg["save_snapshots"]:
                            snap = self._save_snapshot(frame)
                            self.logger.log_event("SLEEP_DETECTED", {
                                "snapshot": snap,
                                "sleep_counter": self.sleep_counter,
                            })
                        else:
                            self.logger.log_event("SLEEP_DETECTED", {
                                "sleep_counter": self.sleep_counter,
                            })

            # ── Draw HUD & Show ─────────────────────
            frame = self._draw_hud(frame, sleeping)
            cv2.imshow("Drowsiness Detector  |  Press ESC to quit", frame)

            # ── Key Handling ────────────────────────
            key = cv2.waitKey(1) & 0xFF
            if key == 27:            # ESC → quit
                break
            elif key == ord("s"):    # S → manual snapshot
                snap = self._save_snapshot(frame)
                print(f"[SNAP] Saved: {snap}")
            elif key == ord("r"):    # R → reset counters
                self.sleep_counter    = 0
                self.total_sleep_events = 0
                print("[INFO] Counters reset.")

        # ── Cleanup ──────────────────────────────
        duration = (datetime.now() - self.session_start).seconds
        self.logger.log_event("SESSION_END", {
            "duration_seconds": duration,
            "total_sleep_events": self.total_sleep_events,
        })
        cap.release()
        cv2.destroyAllWindows()
        print(f"\n[INFO] Session ended. Duration: {duration}s | Sleep events: {self.total_sleep_events}")


# ─────────────────────────────────────────────
#  CLI Entry Point
# ─────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Sleeping Alarm System — Real-Time Drowsiness Detector"
    )
    parser.add_argument(
        "--camera", type=int, default=None,
        help="Camera index (default: from config.json)"
    )
    parser.add_argument(
        "--threshold", type=int, default=None,
        help="Number of consecutive eye-closed frames before alarm (default: from config.json)"
    )
    parser.add_argument(
        "--config", type=str, default=CONFIG_FILE,
        help="Path to custom config.json file"
    )
    parser.add_argument(
        "--no-snapshots", action="store_true",
        help="Disable saving snapshots on sleep detection"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    cfg  = load_config(args.config)

    # CLI overrides
    if args.threshold:
        cfg["sleep_frame_threshold"] = args.threshold
    if args.no_snapshots:
        cfg["save_snapshots"] = False

    try:
        detector = DrowsinessDetector(cfg)
        detector.run(camera_index=args.camera)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
