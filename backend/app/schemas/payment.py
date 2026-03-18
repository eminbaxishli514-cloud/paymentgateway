"""Payment-related request and response schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentMethod(str, Enum):
    """Supported payment methods."""

    CARD = "card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"


class PaymentStatus(str, Enum):
    """Possible states of a payment transaction."""

    PENDING = "pending"
    PENDING_VERIFICATION = "pending_verification"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentRequest(BaseModel):
    """Incoming payment request from the client."""

    amount: float = Field(..., gt=0, le=999999.99, description="Amount in currency units")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    payment_method: PaymentMethod = Field(default=PaymentMethod.CARD)
    saved_card_id: str | None = Field(default=None, description="Use saved card if provided")
    card_number: str | None = Field(default=None, min_length=13, max_length=19)
    card_exp_month: int | None = Field(default=None, ge=1, le=12)
    card_exp_year: int | None = Field(default=None, ge=2024, le=2030)
    card_cvc: str | None = Field(default=None, min_length=3, max_length=4)
    cardholder_name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    promo_code: str | None = Field(default=None, max_length=20)


class PaymentResponse(BaseModel):
    """Response returned after processing a payment."""

    id: str
    status: PaymentStatus
    amount: float
    currency: str
    discount: float = 0
    total: float = 0
    created_at: datetime
    failure_reason: str | None = None
    requires_verification: bool = False


class VerifyRequest(BaseModel):
    """SMS verification request."""

    payment_id: str
    code: str = Field(..., min_length=4, max_length=8)


class VerifyResponse(BaseModel):
    """Response after SMS verification."""

    success: bool
    payment_id: str
    message: str


class RefundRequest(BaseModel):
    """Request to refund an existing payment."""

    payment_id: str
    amount: float | None = Field(
        default=None, gt=0, description="Partial refund amount, or full if omitted"
    )
    reason: str | None = Field(default=None, max_length=200)


class RefundResponse(BaseModel):
    """Response after processing a refund."""

    refund_id: str
    payment_id: str
    amount: float
    status: str = "succeeded"
    created_at: datetime


class TransactionRecord(BaseModel):
    """Single transaction for history."""

    id: str
    status: PaymentStatus
    amount: float
    discount: float
    total: float
    currency: str
    payment_method: str
    description: str | None
    created_at: datetime


class ReceiptData(BaseModel):
    """Receipt data for display or download."""

    payment_id: str
    status: str
    amount: float
    discount: float
    total: float
    currency: str
    payment_method: str
    card_last_four: str | None
    created_at: datetime
    description: str | None
