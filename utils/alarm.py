"""
utils/alarm.py — Alarm System for Drowsiness Detection
Supports cross-platform audio alerts (beep/winsound/os).
No API keys, no network calls, no system paths exposed.
"""

import sys
import threading


class AlarmSystem:
    """
    Cross-platform alarm trigger.

    Priority order:
      1. winsound (Windows)
      2. pygame  (cross-platform, if installed)
      3. os beep fallback (Linux/macOS terminal bell)
    """

    def __init__(self, freq: int = 1000, duration_ms: int = 1000):
        self.freq        = freq
        self.duration_ms = duration_ms
        self._lock       = threading.Lock()
        self._playing    = False

    # ── Public API ───────────────────────────────────────────────────────────
    def trigger(self):
        """Fire the alarm in a background thread (non-blocking)."""
        with self._lock:
            if self._playing:
                return          # don't stack alarms
            self._playing = True
        t = threading.Thread(target=self._play, daemon=True)
        t.start()

    def stop(self):
        """Stop a running alarm (best-effort for pygame)."""
        self._playing = False

    # ── Internal ─────────────────────────────────────────────────────────────
    def _play(self):
        try:
            if sys.platform == "win32":
                self._play_windows()
            else:
                self._play_fallback()
        finally:
            self._playing = False

    def _play_windows(self):
        import winsound  # stdlib on Windows only
        winsound.Beep(self.freq, self.duration_ms)

    def _play_fallback(self):
        """Try pygame mixer; fall back to terminal bell."""
        try:
            import pygame
            pygame.mixer.init(frequency=self.freq)
            # Generate a simple sine-wave beep using pygame Sound
            import numpy as np
            import struct
            sample_rate = 44100
            num_samples = int(sample_rate * self.duration_ms / 1000)
            buf = (
                np.sin(2 * np.pi * self.freq * np.arange(num_samples) / sample_rate)
                * 32767
            ).astype(np.int16)
            sound = pygame.sndarray.make_sound(buf)
            sound.play()
            pygame.time.delay(self.duration_ms + 100)
        except Exception:
            # Last resort — terminal bell
            sys.stdout.write("\a")
            sys.stdout.flush()
