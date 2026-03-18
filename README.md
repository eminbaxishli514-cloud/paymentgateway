# Payment Gateway Demo

A demonstration payment gateway with a Python backend and a Stripe-inspired frontend. No real payments are processed — this is for testing and learning.

## Features

- **Multiple payment methods**: Card, PayPal, Apple Pay
- **Saved cards**: Choose from demo saved cards or enter new card details
- **Promo codes**: DEMO10 (10% off), SAVE20 (20% off), HALFOFF (50% off)
- **SMS verification**: Card payments require 3D Secure–style verification (demo code: 123456)
- **Progress indicator**: Payment → Verify → Complete
- **Receipt**: View and download receipt after successful payment
- **Transaction history**: View all payments from the current session
- **Light/dark mode**: Theme toggle with persisted preference
- **Responsive layout**: Optimized for phones, tablets, and desktops

## Quick Start

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the checkout page.

## Test Data

| Item | Value |
|------|-------|
| Success card | 4242 4242 4242 4242 |
| Decline card | 0000 0000 0000 0000 |
| SMS code | 123456 |
| Promo codes | DEMO10, SAVE20, HALFOFF |

## Pages

- `/` — Checkout
- `/verify?payment_id=xxx` — SMS verification (opens after Pay for card)
- `/receipt?payment_id=xxx` — Receipt
- `/history` — Transaction history

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/payments/promo/{code}` | Validate promo code |
| GET | `/api/payments/saved-cards` | List saved cards |
| POST | `/api/payments/` | Process payment |
| POST | `/api/payments/verify` | Verify SMS and complete payment |
| GET | `/api/payments/history` | Transaction history |
| GET | `/api/payments/receipt/{id}` | Receipt data |
| GET | `/api/payments/{id}` | Payment details |
| POST | `/api/payments/refund` | Refund a payment |

## Project Structure

```
paymentgateway/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── schemas/
│   │   ├── routers/
│   │   └── services/
│   ├── static/
│   │   ├── index.html, verify.html, receipt.html, history.html
│   │   ├── css/style.css
│   │   └── js/
│   └── requirements.txt
└── README.md
```

## License

MIT
