# Ecomlytics — E-commerce Product Intelligence & Decision Platform

A professional, multi-page e-commerce analytics demo that connects store data to metrics, insights and business decisions.

## Features
- Professional login page
- Demo authentication using browser localStorage
- Overview dashboard
- Sales Analytics
- Product Intelligence
- Customer Intelligence
- Retention & Funnel
- Business Insights
- Product search and category filter
- KPI cards and business metrics
- Responsive professional UI
- FastAPI backend
- CSV demo datasets
- Rule-based business insight engine
- Linked navigation and sign-out

## Run

PowerShell:
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Open either:
http://127.0.0.1:8000/

or directly:
http://127.0.0.1:8000/login.html

Demo login:
Any valid email address + any password.

## API
- /api/overview
- /api/products
- /api/customers/segments
- /api/funnel
- /api/insights
- /api/health

## Production note
The login is intentionally demo-only. For a real deployment, replace browser-only authentication with server-side authentication, hashed passwords, sessions/JWT, HTTPS, database-backed users, CSRF protection and proper authorization.
