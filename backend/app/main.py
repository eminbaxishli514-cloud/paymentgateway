"""FastAPI application entry point."""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.core.limiter import limiter
from app.routers import admin, payments
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.siem_middleware import SIEMMiddleware
from app.core.exceptions import generic_exception_handler, validation_exception_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.app_name,
    description="Demo payment gateway for testing and demonstration",
    version="1.0.0",
    docs_url="/docs",  # API documentation
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Middleware order: last added = first executed on incoming request
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(SIEMMiddleware)  # blocklist + request logging (runs first inbound)

app.include_router(admin.router)
app.include_router(payments.router)

# Serve static assets
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def _serve_page(name: str):
    """Serve a static HTML page."""
    path = static_dir / f"{name}.html"
    if path.exists():
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/store")
def serve_store():
    """Serve the online marketplace page."""
    return _serve_page("store")


@app.get("/")
def serve_frontend():
    """Serve the main checkout page."""
    return _serve_page("index")


@app.get("/verify")
def serve_verify():
    """Serve the SMS verification page."""
    return _serve_page("verify")


@app.get("/receipt")
def serve_receipt():
    """Serve the receipt page."""
    return _serve_page("receipt")


@app.get("/history")
def serve_history():
    """Serve the transaction history page."""
    return _serve_page("history")


@app.get("/admin")
def serve_admin():
    """Admin / SIEM dashboard (set ADMIN_API_KEY, use X-Admin-Token in UI)."""
    return _serve_page("admin")


@app.get("/health")
def health_check():
    """Simple health check for monitoring."""
    return {"status": "ok"}
