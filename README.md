# Payment Gateway Demo

A demonstration payment gateway with a Python backend and a Stripe-inspired frontend. No real payments are processed — this is for testing and learning.

## Features

- **Backend**: FastAPI with clean structure, validation, and mock payment processing
- **Frontend**: Modern, responsive checkout form inspired by Stripe
- **Test cards**: Use `4242 4242 4242 4242` for success, `0000 0000 0000 0000` for decline

## Quick Start

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the checkout page, or [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the API docs.

## Project Structure

```
paymentgateway/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Settings
│   │   ├── schemas/         # Request/response models
│   │   ├── routers/         # API routes
│   │   └── services/        # Business logic
│   ├── static/              # Frontend assets
│   └── requirements.txt
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/` | Process a payment |
| GET | `/api/payments/{id}` | Get payment details |
| POST | `/api/payments/refund` | Refund a payment |

## License

MIT
