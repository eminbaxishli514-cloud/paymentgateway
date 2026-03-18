"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.routers import payments

app = FastAPI(
    title=settings.app_name,
    description="Demo payment gateway for testing and demonstration",
    version="1.0.0",
)

app.include_router(payments.router)

# Serve static assets
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def serve_frontend():
    """Serve the main payment form page."""
    index_path = Path(__file__).parent.parent / "static" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Payment Gateway API", "docs": "/docs"}


@app.get("/health")
def health_check():
    """Simple health check for monitoring."""
    return {"status": "ok"}
