"""Payment API endpoints."""

from fastapi import APIRouter, HTTPException, Path, Request

from app.config import settings
from app.core.limiter import limiter
from app.schemas.payment import (
    PaymentRequest,
    PaymentResponse,
    RefundRequest,
    RefundResponse,
    VerifyRequest,
    VerifyResponse,
)
from app.services.payment_service import payment_service

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.get("/promo/{code}")
@limiter.limit(settings.rate_limit_payment)
def validate_promo(request: Request, code: str):
    """Validate a promo code. Returns discount percent and description."""
    if len(code) > 20 or not code.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid promo code format")
    result = payment_service.validate_promo(code)
    if result.get("error"):
        return {"valid": False, "message": result["error"]}
    return {"valid": True, "percent": result["percent"], "description": result["description"]}


@router.get("/saved-cards")
def list_saved_cards():
    """List demo saved cards."""
    return {"cards": payment_service.get_saved_cards()}


@router.post("/", response_model=PaymentResponse)
@limiter.limit(settings.rate_limit_payment)
def create_payment(request: Request, body: PaymentRequest) -> PaymentResponse:
    """
    Process a new payment. Card payments require SMS verification.
    Use card 4242 for success, 0000 for decline. Promo: DEMO10, SAVE20, HALFOFF.
    """
    return payment_service.process_payment(body)


@router.post("/verify", response_model=VerifyResponse)
@limiter.limit(settings.rate_limit_payment)
def verify_sms(request: Request, body: VerifyRequest) -> VerifyResponse:
    """Verify SMS code to complete a pending payment. Demo code: 123456"""
    success, message = payment_service.verify_sms(body.payment_id, body.code)
    return VerifyResponse(
        success=success,
        payment_id=body.payment_id,
        message=message,
    )


@router.get("/history")
def get_history():
    """Get transaction history."""
    records = payment_service.get_transaction_history()
    return {"transactions": records}


@router.get("/receipt/{payment_id}")
def get_receipt(
    payment_id: str = Path(..., pattern=r"^pay_[a-f0-9]{24}$", description="Payment ID"),
):
    """Get receipt data for a payment."""
    data = payment_service.get_receipt_data(payment_id)
    if not data:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return data


@router.get("/{payment_id}")
def get_payment(
    payment_id: str = Path(..., pattern=r"^pay_[a-f0-9]{24}$", description="Payment ID"),
):
    """Retrieve payment details by ID."""
    payment = payment_service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/refund", response_model=RefundResponse)
@limiter.limit(settings.rate_limit_payment)
def refund_payment(request: Request, body: RefundRequest) -> RefundResponse:
    """Refund a payment. Omit amount for full refund."""
    result = payment_service.refund_payment(body.payment_id, body.amount)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Refund failed. Payment not found or not refundable.",
        )
    return RefundResponse(**result)
