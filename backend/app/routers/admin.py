"""Admin / SIEM API — protect with X-Admin-Token."""

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.config import settings
from app.schemas.admin import IPActionBody
from app.services.siem_service import siem_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin_token(x_admin_token: str | None = Header(None, alias="X-Admin-Token")) -> None:
    expected = settings.admin_api_key
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API disabled: set ADMIN_API_KEY in environment",
        )
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Token",
        )


@router.get("/siem/dashboard", dependencies=[Depends(verify_admin_token)])
def siem_dashboard():
    """SIEM summary: top IPs, suspicious activity, blocklist."""
    return siem_service.dashboard()


@router.get("/siem/events", dependencies=[Depends(verify_admin_token)])
def siem_events(limit: int = 100):
    """Recent HTTP events (newest first)."""
    limit = max(1, min(limit, 500))
    return {"events": siem_service.get_recent_events(limit)}


@router.post("/siem/block", dependencies=[Depends(verify_admin_token)])
def siem_block_ip(body: IPActionBody):
    """Block an IP address."""
    ip = body.ip.strip()
    siem_service.block_ip(ip)
    return {"ok": True, "blocked": ip, "blocked_ips": siem_service.list_blocked()}


@router.post("/siem/unblock", dependencies=[Depends(verify_admin_token)])
def siem_unblock_ip(body: IPActionBody):
    """Remove IP from blocklist."""
    ip = body.ip.strip()
    siem_service.unblock_ip(ip)
    return {"ok": True, "unblocked": ip, "blocked_ips": siem_service.list_blocked()}


@router.get("/siem/blocked", dependencies=[Depends(verify_admin_token)])
def siem_list_blocked():
    """Current blocklist."""
    return {"blocked_ips": siem_service.list_blocked()}
