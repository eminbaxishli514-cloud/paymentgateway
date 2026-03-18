"""Rate limiter instance for use across the application."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    application_limits=[settings.rate_limit],
)
