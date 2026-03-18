"""Payment API endpoints."""

from fastapi import APIRouter, HTTPException

from app.schemas.payment import PaymentRequest, PaymentResponse, RefundRequest, RefundResponse
from app.services.payment_service import payment_service

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/", response_model=PaymentResponse)
def create_payment(request: PaymentRequest) -> PaymentResponse:
    """
    Process a new payment. This is a demo endpoint - no real charges are made.
    Use card 4242 4242 4242 4242 for success, 0000 0000 0000 0000 for decline.
    """
    return payment_service.process_payment(request)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: str) -> PaymentResponse:
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
