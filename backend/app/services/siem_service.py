"""
Lightweight in-memory SIEM for the payment gateway demo.
Tracks requests per IP, flags high-volume activity, supports IP blocklist.
For production, forward logs to a real SIEM (Splunk, Elastic, etc.).
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass
class SIEMEvent:
    """Single observed HTTP request (sanitized)."""

    ts: float
    ip: str
    method: str
    path: str
    status_code: int
    user_agent: str = ""


@dataclass
class IPSummary:
    """Aggregated stats for one IP in the sliding window."""

    ip: str
    requests_last_60s: int
    requests_last_5m: int
    last_path: str
    suspicious: bool
    reason: str | None = None


class SIEMService:
    """
    Thread-safe in-memory SIEM. Not durable across restarts.
    """

    def __init__(
        self,
        *,
        max_events: int = 5000,
        suspicious_per_minute: int = 60,
        critical_per_minute: int = 200,
    ) -> None:
        self._lock = threading.Lock()
        self._events: deque[SIEMEvent] = deque(maxlen=max_events)
        self._blocked: set[str] = set()
        self.suspicious_per_minute = suspicious_per_minute
        self.critical_per_minute = critical_per_minute

    def is_blocked(self, ip: str) -> bool:
        with self._lock:
            return ip in self._blocked

    def block_ip(self, ip: str) -> None:
        with self._lock:
            self._blocked.add(ip)

    def unblock_ip(self, ip: str) -> None:
        with self._lock:
            self._blocked.discard(ip)

    def list_blocked(self) -> list[str]:
        with self._lock:
            return sorted(self._blocked)

    def record(
        self,
        ip: str,
        method: str,
        path: str,
        status_code: int,
        user_agent: str = "",
    ) -> None:
        ev = SIEMEvent(
            ts=time.time(),
            ip=ip,
            method=method,
            path=path[:500],
            status_code=status_code,
            user_agent=(user_agent or "")[:200],
        )
        with self._lock:
            self._events.append(ev)

    def _count_in_window(self, ip: str, window_sec: float) -> int:
        now = time.time()
        cutoff = now - window_sec
        with self._lock:
            return sum(1 for e in self._events if e.ip == ip and e.ts >= cutoff)

    def get_ip_summaries(self) -> list[IPSummary]:
        """All IPs seen recently with request counts and suspicion flags."""
        now = time.time()
        with self._lock:
            seen: dict[str, list[SIEMEvent]] = {}
            for e in self._events:
                if e.ts < now - 300:
                    continue
                seen.setdefault(e.ip, []).append(e)

        summaries: list[IPSummary] = []
        for ip, evs in seen.items():
            c60 = sum(1 for e in evs if e.ts >= now - 60)
            c5m = len(evs)
            last_path = evs[-1].path if evs else ""
            suspicious = False
            reason = None
            if c60 >= self.critical_per_minute:
                suspicious = True
                reason = f"Critical: {c60} requests in last 60s (≥{self.critical_per_minute})"
            elif c60 >= self.suspicious_per_minute:
                suspicious = True
                reason = f"Suspicious: {c60} requests in last 60s (≥{self.suspicious_per_minute})"
            summaries.append(
                IPSummary(
                    ip=ip,
                    requests_last_60s=c60,
                    requests_last_5m=c5m,
                    last_path=last_path,
                    suspicious=suspicious,
                    reason=reason,
                )
            )
        summaries.sort(key=lambda s: s.requests_last_60s, reverse=True)
        return summaries

    def get_recent_events(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            tail = list(self._events)[-limit:]
        return [
            {
                "ts": e.ts,
                "ip": e.ip,
                "method": e.method,
                "path": e.path,
                "status_code": e.status_code,
                "user_agent": e.user_agent,
            }
            for e in reversed(tail)
        ]

    def dashboard(self) -> dict[str, Any]:
        summaries = self.get_ip_summaries()
        suspicious = [s for s in summaries if s.suspicious]
        with self._lock:
            total_events = len(self._events)
            blocked = sorted(self._blocked)
        return {
            "total_events_buffered": total_events,
            "unique_ips_recent": len(summaries),
            "suspicious_ip_count": len(suspicious),
            "blocked_ips": blocked,
            "thresholds": {
                "suspicious_requests_per_60s": self.suspicious_per_minute,
                "critical_requests_per_60s": self.critical_per_minute,
            },
            "top_ips": [
                {
                    "ip": s.ip,
                    "requests_last_60s": s.requests_last_60s,
                    "requests_last_5m": s.requests_last_5m,
                    "last_path": s.last_path,
                    "suspicious": s.suspicious,
                    "reason": s.reason,
                }
                for s in summaries[:25]
            ],
        }


def _build_siem() -> SIEMService:
    from app.config import settings

    return SIEMService(
        suspicious_per_minute=settings.siem_suspicious_rpm,
        critical_per_minute=settings.siem_critical_rpm,
    )


siem_service = _build_siem()
