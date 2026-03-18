"""Payment processing logic. In production, this would integrate with real gateways."""

import uuid
from datetime import datetime

from app.schemas.payment import PaymentRequest, PaymentResponse, PaymentStatus


class PaymentService:
    """
    Handles payment processing. This is a demo implementation that simulates
    gateway behavior without touching real payment networks.
    """

    def __init__(self):
        self._payments: dict[str, dict] = {}

    def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """
        Process a payment. Returns success or failure based on demo rules.
        Test card: 4242 4242 4242 4242 always succeeds.
        """
        payment_id = f"pay_{uuid.uuid4().hex[:24]}"
        now = datetime.utcnow()

        # Demo rule: card ending in 4242 succeeds, 0000 fails, others random-ish
        card_last_four = request.card_number.replace(" ", "")[-4:]
        if card_last_four == "0000":
            status = PaymentStatus.FAILED
            failure_reason = "Card declined. Insufficient funds."
        elif card_last_four == "4242":
            status = PaymentStatus.SUCCEEDED
            failure_reason = None
        else:
            # For other cards, succeed (demo-friendly)
            status = PaymentStatus.SUCCEEDED
            failure_reason = None

        payment_record = {
            "id": payment_id,
            "status": status,
            "amount": request.amount,
            "currency": request.currency,
            "created_at": now,
            "failure_reason": failure_reason,
        }
        self._payments[payment_id] = payment_record

        return PaymentResponse(
            id=payment_id,
            status=status,
            amount=request.amount,
            currency=request.currency,
            created_at=now,
            failure_reason=failure_reason,
        )

    def get_payment(self, payment_id: str) -> PaymentResponse | None:
        """Retrieve a payment by ID."""
        record = self._payments.get(payment_id)
        if not record:
            return None
        return PaymentResponse(**record)

    def refund_payment(
        self, payment_id: str, amount: float | None = None
    ) -> dict | None:
        """
        Refund a payment. Full refund if amount is None.
        Returns refund details or None if payment not found.
        """
        record = self._payments.get(payment_id)
        if not record:
            return None
        if record["status"] != PaymentStatus.SUCCEEDED:
            return None

        refund_amount = amount if amount is not None else record["amount"]
        if refund_amount > record["amount"]:
            return None

        refund_id = f"ref_{uuid.uuid4().hex[:24]}"
        record["status"] = PaymentStatus.REFUNDED

        return {
            "refund_id": refund_id,
            "payment_id": payment_id,
            "amount": refund_amount,
            "status": "succeeded",
            "created_at": datetime.utcnow(),
        }


# Singleton instance for the demo
payment_service = PaymentService()
