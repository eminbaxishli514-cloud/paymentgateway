"""Payment processing logic. In production, this would integrate with real gateways."""

import uuid
from datetime import datetime

from app.schemas.payment import (
    PaymentMethod,
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    TransactionRecord,
)


# Demo promo codes: code -> (percent_off, description)
PROMO_CODES = {
    "DEMO10": (10, "10% off"),
    "SAVE20": (20, "20% off"),
    "HALFOFF": (50, "50% off"),
}

# Demo saved cards (in production these would be tokenized)
SAVED_CARDS = [
    {"id": "card_4242", "last_four": "4242", "brand": "Visa", "exp": "12/26"},
    {"id": "card_5555", "last_four": "5555", "brand": "Mastercard", "exp": "06/27"},
    {"id": "card_0000", "last_four": "0000", "brand": "Visa", "exp": "03/25"},
]

# Full card details for saved cards (demo only)
SAVED_CARD_DETAILS = {
    "card_4242": {
        "card_number": "4242424242424242",
        "exp_month": 12,
        "exp_year": 2026,
        "cvc": "123",
        "cardholder_name": "Demo User",
    },
    "card_5555": {
        "card_number": "5555555555554444",
        "exp_month": 6,
        "exp_year": 2027,
        "cvc": "456",
        "cardholder_name": "Demo User",
    },
    "card_0000": {
        "card_number": "0000000000000000",
        "exp_month": 3,
        "exp_year": 2025,
        "cvc": "789",
        "cardholder_name": "Demo User",
    },
}

# SMS code that always works
VALID_SMS_CODE = "123456"


class PaymentService:
    """
    Handles payment processing. This is a demo implementation that simulates
    gateway behavior without touching real payment networks.
    """

    def __init__(self):
        self._payments: dict[str, dict] = {}

    def validate_promo(self, code: str | None) -> dict:
        """Return {percent, description} or {error}."""
        if not code or not code.strip():
            return {"percent": 0, "description": None}
        code = code.strip().upper()
        if code in PROMO_CODES:
            pct, desc = PROMO_CODES[code]
            return {"percent": pct, "description": desc}
        return {"percent": 0, "error": "Invalid promo code"}

    def get_saved_cards(self) -> list[dict]:
        """Return list of saved cards for demo."""
        return SAVED_CARDS.copy()

    def _resolve_card(self, request: PaymentRequest) -> tuple[str, int, int, str, str] | None:
        """Resolve card details from saved card or request. Returns (number, exp_m, exp_y, cvc, name)."""
        if request.saved_card_id and request.saved_card_id in SAVED_CARD_DETAILS:
            details = SAVED_CARD_DETAILS[request.saved_card_id]
            return (
                details["card_number"],
                details["exp_month"],
                details["exp_year"],
                details["cvc"],
                details["cardholder_name"],
            )
        if request.payment_method == PaymentMethod.CARD and request.card_number:
            return (
                request.card_number.replace(" ", ""),
                request.card_exp_month or 12,
                request.card_exp_year or 2026,
                request.card_cvc or "123",
                request.cardholder_name or "Cardholder",
            )
        return None

    def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """
        Process a payment. Returns success, failure, or pending_verification.
        Card 4242 succeeds, 0000 fails. Card payments require SMS verification.
        """
        payment_id = f"pay_{uuid.uuid4().hex[:24]}"
        now = datetime.utcnow()

        # Apply promo
        promo_result = self.validate_promo(request.promo_code)
        discount_pct = promo_result.get("percent", 0) if "error" not in promo_result else 0
        discount = request.amount * (discount_pct / 100)
        total = request.amount - discount

        # Non-card methods: instant success for demo
        if request.payment_method in (PaymentMethod.PAYPAL, PaymentMethod.APPLE_PAY):
            payment_record = {
                "id": payment_id,
                "status": PaymentStatus.SUCCEEDED,
                "amount": request.amount,
                "discount": discount,
                "total": total,
                "currency": request.currency,
                "payment_method": request.payment_method.value,
                "card_last_four": None,
                "created_at": now,
                "failure_reason": None,
                "description": request.description,
            }
            self._payments[payment_id] = payment_record
            return PaymentResponse(
                id=payment_id,
                status=PaymentStatus.SUCCEEDED,
                amount=request.amount,
                discount=discount,
                total=total,
                currency=request.currency,
                created_at=now,
                requires_verification=False,
            )

        # Card: resolve card details
        card = self._resolve_card(request)
        if not card:
            return PaymentResponse(
                id=payment_id,
                status=PaymentStatus.FAILED,
                amount=request.amount,
                discount=discount,
                total=total,
                currency=request.currency,
                created_at=now,
                failure_reason="Invalid card details",
                requires_verification=False,
            )

        card_number, exp_month, exp_year, cvc, name = card
        card_last_four = card_number[-4:]

        # Card 0000 fails immediately
        if card_last_four == "0000":
            payment_record = {
                "id": payment_id,
                "status": PaymentStatus.FAILED,
                "amount": request.amount,
                "discount": discount,
                "total": total,
                "currency": request.currency,
                "payment_method": "card",
                "card_last_four": card_last_four,
                "created_at": now,
                "failure_reason": "Card declined. Insufficient funds.",
                "description": request.description,
            }
            self._payments[payment_id] = payment_record
            return PaymentResponse(
                id=payment_id,
                status=PaymentStatus.FAILED,
                amount=request.amount,
                discount=discount,
                total=total,
                currency=request.currency,
                created_at=now,
                failure_reason="Card declined. Insufficient funds.",
                requires_verification=False,
            )

        # Card requires SMS verification
        payment_record = {
            "id": payment_id,
            "status": PaymentStatus.PENDING_VERIFICATION,
            "amount": request.amount,
            "discount": discount,
            "total": total,
            "currency": request.currency,
            "payment_method": "card",
            "card_last_four": card_last_four,
            "created_at": now,
            "failure_reason": None,
            "description": request.description,
        }
        self._payments[payment_id] = payment_record

        return PaymentResponse(
            id=payment_id,
            status=PaymentStatus.PENDING_VERIFICATION,
            amount=request.amount,
            discount=discount,
            total=total,
            currency=request.currency,
            created_at=now,
            requires_verification=True,
        )

    def verify_sms(self, payment_id: str, code: str) -> tuple[bool, str]:
        """Verify SMS code and complete payment. Returns (success, message)."""
        record = self._payments.get(payment_id)
        if not record:
            return False, "Payment not found"
        if record["status"] != PaymentStatus.PENDING_VERIFICATION:
            return False, "Payment already processed"

        if code.strip() == VALID_SMS_CODE:
            record["status"] = PaymentStatus.SUCCEEDED
            return True, "Payment verified successfully"
        return False, "Invalid verification code"

    def get_payment(self, payment_id: str) -> dict | None:
        """Retrieve a payment by ID."""
        return self._payments.get(payment_id)

    def get_transaction_history(self) -> list[dict]:
        """Return all transactions sorted by date descending."""
        records = list(self._payments.values())
        records.sort(key=lambda r: r["created_at"], reverse=True)
        return records

    def get_receipt_data(self, payment_id: str) -> dict | None:
        """Get receipt data for a successful payment."""
        record = self._payments.get(payment_id)
        if not record or record["status"] not in (
            PaymentStatus.SUCCEEDED,
            PaymentStatus.REFUNDED,
        ):
            return None
        return record

    def refund_payment(
        self, payment_id: str, amount: float | None = None
    ) -> dict | None:
        """Refund a payment. Full refund if amount is None."""
        record = self._payments.get(payment_id)
        if not record:
            return None
        if record["status"] != PaymentStatus.SUCCEEDED:
            return None

        refund_amount = amount if amount is not None else record["total"]
        if refund_amount > record["total"]:
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


payment_service = PaymentService()
