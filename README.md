# CodeAlpha_ECommerceStore

A full-stack, responsive e-commerce web application built with Python, Django, Neon PostgreSQL, and modern responsive CSS.

---

## Features

- **Neon PostgreSQL Support**: Native cloud PostgreSQL connectivity with connection pooling, SSL enforcement (`sslmode=require`), and automatic fallback to local development database.
- **Unique Order ID & Shipment Tracking**: Every checkout generates an explicit, human-readable Order ID (`ORD-YYYYMMDD-XXXX`) alongside real-time shipment tracking numbers (`TRK-YYYYMM-XXXX`).
- **Complete Returns & Refunds System**:
  - Customers can initiate returns directly from their Order History on delivered/shipped orders.
  - Choose whole-order or item-level return with reason, detailed customer notes, and estimated refund amounts.
  - Dedicated customer **Returns & Refunds** dashboard (`/returns/`) for tracking review, approval, warehouse receipt, and refund statuses.
  - Admin approval, rejection, and batch refund actions inside Django Admin.
- **Strict Login & Panel Isolation**:
  - **Storefront Customer Login** (`/accounts/login/`): Dedicated to shoppers for placing orders and managing returns.
  - **Staff Admin Portal** (`/admin/`): Strictly restricted to staff and superusers (`is_staff=True`), guarded against customer logins, with direct staff portal links and dedicated administrative tools.
- **Product Catalog & Details**: Browse products in a responsive grid with category filtering, real-time stock indicators, and comprehensive product detail pages.
- **Session-Based Cart**: Guest and registered users can add items, adjust quantities with stock limits, and view subtotal and grand total calculations.
- **Seeded Demo Data**: Includes a `seed_data` custom management command to prepopulate realistic categories, products, sample delivered orders, and an active return request.

---

## Tech Stack

- **Backend**: Django 5.x / 6.x (Python 3.10+)
- **Database**: Neon Serverless PostgreSQL (or SQLite local fallback) via `dj-database-url` & `psycopg2-binary`
- **Frontend**: Django HTML Templates, Vanilla CSS (Glassmorphism / modern dark theme), JavaScript
- **Image Processing**: Pillow

---

## Database Configuration (Neon PostgreSQL)

To connect your project to a serverless Neon PostgreSQL database:

1. Create a free PostgreSQL database at [https://console.neon.tech](https://console.neon.tech).
2. Copy your Neon connection string (either direct or pooled).
3. Create a `.env` file in the project root (or copy from `.env.example`):
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env
   ```
4. Set your Neon connection URI in `.env`:
   ```env
   DATABASE_URL=postgresql://[user]:[password]@[ep-your-project].us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
5. Apply database migrations to Neon:
   ```bash
   python manage.py migrate
   ```
6. Seed initial demo data (products, admin, customer, demo orders & returns):
   ```bash
   python manage.py seed_data
   ```

*(Note: If no `DATABASE_URL` is configured in `.env`, the project automatically falls back to local SQLite for instant zero-config testing.)*

---

## Getting Started / Setup Instructions

### 1. Create and Activate Virtual Environment
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations & Seed Data
```bash
python manage.py migrate
python manage.py seed_data
```

### 4. Start the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to:
- **Storefront**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Customer Sign In**: [http://127.0.0.1:8000/accounts/login/](http://127.0.0.1:8000/accounts/login/)
- **Staff Admin Portal**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Demo Accounts

| Role | Username | Password | Access Area |
| :--- | :--- | :--- | :--- |
| **Superuser / Staff** | `admin` | `admin123` | Admin Portal (`/admin/`) & Storefront |
| **Customer / Shopper** | `customer` | `customer123` | Storefront, Orders & Returns (`/orders/`, `/returns/`) |

---

## Running Tests
To run the automated test suite covering models, cart, checkout, returns lifecycle, and authentication isolation:
```bash
python manage.py test
```

