"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
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


def _serve_page(name: str):
    """Serve a static HTML page."""
    path = static_dir / f"{name}.html"
    if path.exists():
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Page not found")


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


@app.get("/health")
def health_check():
    """Simple health check for monitoring."""
    return {"status": "ok"}
