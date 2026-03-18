"""Payment-related request and response schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    """Possible states of a payment transaction."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentRequest(BaseModel):
    """Incoming payment request from the client."""

    amount: float = Field(..., gt=0, le=999999.99, description="Amount in currency units")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    card_number: str = Field(..., min_length=13, max_length=19)
    card_exp_month: int = Field(..., ge=1, le=12)
    card_exp_year: int = Field(..., ge=2024, le=2030)
    card_cvc: str = Field(..., min_length=3, max_length=4)
    cardholder_name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class PaymentResponse(BaseModel):
    """Response returned after processing a payment."""

    id: str
    status: PaymentStatus
    amount: float
    currency: str
    created_at: datetime
    failure_reason: str | None = None


class RefundRequest(BaseModel):
    """Request to refund an existing payment."""

    payment_id: str
    amount: float | None = Field(default=None, gt=0, description="Partial refund amount, or full if omitted")
    reason: str | None = Field(default=None, max_length=200)


class RefundResponse(BaseModel):
    """Response after processing a refund."""

    refund_id: str
    payment_id: str
    amount: float
    status: str = "succeeded"
    created_at: datetime
