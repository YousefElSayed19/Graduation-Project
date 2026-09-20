"""
scan_manager.py
----------------
Holds the in-memory state (logs / status / findings) of every scan so
the dashboard can poll it and follow along live.

In a real production build you'd swap this for Redis, but for this
project and local runs a plain in-memory dict is simple and clear enough.
"""

import threading
import time
import uuid


class ScanManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._scans = {}  # scan_uid -> dict

    def create_scan(self, target_url: str, user_id: int) -> str:
        scan_uid = str(uuid.uuid4())
        with self._lock:
            self._scans[scan_uid] = {
                "target_url": target_url,
                "user_id": user_id,
                "status": "pending",  # pending | running | done | failed
                "logs": [],
                "findings": [],
                "created_at": time.time(),
            }
        return scan_uid

    def log(self, scan_uid: str, message: str, level: str = "info"):
        with self._lock:
            if scan_uid not in self._scans:
                return
            self._scans[scan_uid]["logs"].append(
                {"ts": time.time(), "level": level, "message": message}
            )

    def add_finding(self, scan_uid: str, finding: dict):
        with self._lock:
            if scan_uid not in self._scans:
                return
            self._scans[scan_uid]["findings"].append(finding)

    def set_status(self, scan_uid: str, status: str):
        with self._lock:
            if scan_uid not in self._scans:
                return
            self._scans[scan_uid]["status"] = status

    def get_state(self, scan_uid: str):
        with self._lock:
            return self._scans.get(scan_uid)

    def get_logs_since(self, scan_uid: str, since_index: int = 0):
        with self._lock:
            state = self._scans.get(scan_uid)
            if not state:
                return [], 0, "unknown"
            logs = state["logs"][since_index:]
            return logs, len(state["logs"]), state["status"]


# one shared instance used across the whole app
scan_manager = ScanManager()
