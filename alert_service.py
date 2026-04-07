"""Alert logic: terminal output and in-memory log for web UI."""

import time
from collections import deque
from dataclasses import dataclass, asdict
from typing import Deque, List, Optional

import config


@dataclass
class Alert:
    timestamp: str
    alert_type: str  # "gesture" | "weapon"
    confidence: float
    message: str


def _timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


class AlertService:
    """Handles alert debouncing, terminal output, and in-memory log."""

    def __init__(
        self,
        debounce_seconds: float = config.ALERT_DEBOUNCE_SECONDS,
        max_alerts: int = config.MAX_ALERTS_IN_MEMORY,
    ):
        self._debounce = debounce_seconds
        self._max_alerts = max_alerts
        self._last_alert_time: dict[str, float] = {}
        self._alerts: Deque[Alert] = deque(maxlen=max_alerts)

    def trigger(self, alert_type: str, confidence: float) -> bool:
        """
        Record an alert if not within debounce window. Returns True if alert was emitted.
        """
        now = time.time()
        last = self._last_alert_time.get(alert_type, 0)
        if now - last < self._debounce:
            return False
        self._last_alert_time[alert_type] = now

        msg = f"[ALERT] {alert_type.upper()} detected (confidence: {confidence:.2f})"
        alert = Alert(
            timestamp=_timestamp(),
            alert_type=alert_type,
            confidence=round(confidence, 2),
            message=msg,
        )
        self._alerts.append(alert)
        print(msg, f" @ {alert.timestamp}")
        return True

    def get_recent_alerts(self, limit: Optional[int] = None) -> List[dict]:
        """Return recent alerts as list of dicts for JSON (newest last)."""
        out = [asdict(a) for a in self._alerts]
        if limit is not None:
            out = out[-limit:]
        return out
