"""Payment API endpoints."""

from fastapi import APIRouter, HTTPException

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
def validate_promo(code: str):
    """Validate a promo code. Returns discount percent and description."""
    result = payment_service.validate_promo(code)
    if result.get("error"):
        return {"valid": False, "message": result["error"]}
    return {"valid": True, "percent": result["percent"], "description": result["description"]}


@router.get("/saved-cards")
def list_saved_cards():
    """List demo saved cards."""
    return {"cards": payment_service.get_saved_cards()}


@router.post("/", response_model=PaymentResponse)
def create_payment(request: PaymentRequest) -> PaymentResponse:
    """
    Process a new payment. Card payments require SMS verification.
    Use card 4242 for success, 0000 for decline. Promo: DEMO10, SAVE20, HALFOFF.
    """
    return payment_service.process_payment(request)


@router.post("/verify", response_model=VerifyResponse)
def verify_sms(request: VerifyRequest) -> VerifyResponse:
    """Verify SMS code to complete a pending payment. Demo code: 123456"""
    success, message = payment_service.verify_sms(request.payment_id, request.code)
    return VerifyResponse(
        success=success,
        payment_id=request.payment_id,
        message=message,
    )


@router.get("/history")
def get_history():
    """Get transaction history."""
    records = payment_service.get_transaction_history()
    return {"transactions": records}


@router.get("/receipt/{payment_id}")
def get_receipt(payment_id: str):
    """Get receipt data for a payment."""
    data = payment_service.get_receipt_data(payment_id)
    if not data:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return data


@router.get("/{payment_id}")
def get_payment(payment_id: str):
    """Retrieve payment details by ID."""
    payment = payment_service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/refund", response_model=RefundResponse)
def refund_payment(request: RefundRequest) -> RefundResponse:
    """Refund a payment. Omit amount for full refund."""
    result = payment_service.refund_payment(request.payment_id, request.amount)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Refund failed. Payment not found or not refundable.",
        )
    return RefundResponse(**result)
