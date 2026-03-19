"""Admin API request bodies."""

from pydantic import BaseModel, Field


class IPActionBody(BaseModel):
    ip: str = Field(..., min_length=1, max_length=45)
