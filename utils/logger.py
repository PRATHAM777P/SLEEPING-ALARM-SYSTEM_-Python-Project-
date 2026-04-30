"""
utils/logger.py — Drowsiness Event Logger
Writes JSON-Lines logs to logs/session_YYYYMMDD.jsonl
No personal info, no system paths, no environment variables logged.
"""

import json
import os
from datetime import datetime


class DrowsinessLogger:
    """
    Lightweight event logger that writes structured JSON-Lines files.

    Each line is a self-contained JSON object:
      {"timestamp": "...", "event": "...", "data": {...}}
    """

    def __init__(self, log_dir: str = "logs", enabled: bool = True):
        self.enabled = enabled
        self.log_dir = log_dir
        self._file   = None

        if enabled:
            os.makedirs(log_dir, exist_ok=True)
            date_str = datetime.now().strftime("%Y%m%d")
            path     = os.path.join(log_dir, f"session_{date_str}.jsonl")
            # Open in append mode so multiple sessions don't overwrite each other
            self._file = open(path, "a", encoding="utf-8")  # noqa: WPS515

    def log_event(self, event_name: str, data: dict = None):
        """Append a single event to the log file."""
        if not self.enabled or self._file is None:
            return
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event":     event_name,
            "data":      data or {},
        }
        self._file.write(json.dumps(record) + "\n")
        self._file.flush()

    def close(self):
        if self._file:
            self._file.close()
            self._file = None

    # Support `with` statement
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
