"""SIEM request logging and IP block enforcement."""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.services.siem_service import siem_service

logger = logging.getLogger(__name__)


def _client_ip(request: Request) -> str:
    """Prefer X-Forwarded-For first hop when behind a proxy (Railway)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class SIEMMiddleware(BaseHTTPMiddleware):
    """
    Block requests from IPs on the SIEM blocklist.
    Log completed requests for analysis (after response).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = _client_ip(request)
        path = request.url.path

        # Skip logging noise for static assets (optional)
        if siem_service.is_blocked(ip):
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied: IP blocked by security policy"},
            )

        response = await call_next(request)

        # Log API and page hits (not every tiny static file to reduce noise)
        if path.startswith("/api/") or path in ("/", "/store", "/verify", "/receipt", "/history", "/admin"):
            try:
                siem_service.record(
                    ip=ip,
                    method=request.method,
                    path=path,
                    status_code=response.status_code,
                    user_agent=request.headers.get("user-agent", ""),
                )
            except Exception:
                logger.exception("SIEM record failed")

        return response
