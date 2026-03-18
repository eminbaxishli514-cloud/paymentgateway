"""Payment-related request and response schemas."""

import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


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
    saved_card_id: str | None = Field(default=None, max_length=50)
    card_number: str | None = Field(default=None, min_length=13, max_length=19)
    card_exp_month: int | None = Field(default=None, ge=1, le=12)
    card_exp_year: int | None = Field(default=None, ge=2024, le=2030)
    card_cvc: str | None = Field(default=None, min_length=3, max_length=4)
    cardholder_name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    promo_code: str | None = Field(default=None, max_length=20)

    @field_validator("card_number")
    @classmethod
    def card_number_digits_only(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = re.sub(r"\s", "", v)
        if not re.match(r"^\d{13,19}$", cleaned):
            raise ValueError("Card number must contain 13-19 digits")
        return cleaned

    @field_validator("card_cvc")
    @classmethod
    def card_cvc_digits_only(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^\d{3,4}$", v):
            raise ValueError("CVC must be 3 or 4 digits")
        return v

    @field_validator("currency")
    @classmethod
    def currency_valid(cls, v: str) -> str:
        allowed = {"USD", "EUR", "GBP"}
        normalized = (v or "USD").upper()
        if normalized not in allowed:
            raise ValueError(f"Currency must be one of: {', '.join(allowed)}")
        return normalized


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

    payment_id: str = Field(..., max_length=50)
    code: str = Field(..., min_length=4, max_length=8)

    @field_validator("code")
    @classmethod
    def code_digits_only(cls, v: str) -> str:
        if not re.match(r"^\d{4,8}$", v):
            raise ValueError("Verification code must be 4-8 digits")
        return v


class VerifyResponse(BaseModel):
    """Response after SMS verification."""

    success: bool
    payment_id: str
    message: str


class RefundRequest(BaseModel):
    """Request to refund an existing payment."""

    payment_id: str = Field(..., max_length=50)
    amount: float | None = Field(
        default=None, gt=0, le=999999.99, description="Partial refund amount, or full if omitted"
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
