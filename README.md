# SehatHub — Online Pharmacy Management System

SehatHub is a full-stack online pharmacy platform built as a DBMS semester project, modeled after real-world services like Dawaai.pk and D.Watson. It covers the complete pharmacy workflow — medicine browsing, prescription verification, ordering, stock management, and delivery tracking — across four dedicated user roles.

## Features

**Customer**
- Medicine catalog with search, category, and brand filters
- Cart, checkout, and Cash on Delivery ordering
- Prescription upload with pharmacist approval workflow
- Live order tracking timeline
- Reviews & ratings, saved-for-later items

**Pharmacist**
- Prescription verification (approve/reject)
- Stock and inventory management with low-stock alerts
- Order fulfillment dashboard

**Admin**
- Sales analytics with Chart.js (revenue trends, top-selling medicines)
- User management (activate/deactivate accounts)
- Full medicine catalog and category management

**Delivery**
- Order dispatch and delivery status updates

**Security**
- Bcrypt password hashing
- Parameterized SQL queries (SQL injection protection)
- CSRF token validation on all state-changing requests
- Role-based access control on every route
- Rate limiting with account lockout after failed login attempts
- Secure, HttpOnly, SameSite session cookies

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, Tailwind CSS, JavaScript |
| Backend | Python, Flask |
| Database | MySQL |
| Templating | Jinja2 |

## Architecture

SehatHub follows a **3-tier architecture** — the browser never talks to the database directly; every request is routed through Flask, which is the only layer with database access.

```
Presentation (HTML/CSS/JS)  →  Business Logic (Flask)  →  Data (MySQL)
```

## Project Structure

```
sehathub/
├── app.py                  # Application entry point
├── requirements.txt
├── config/
│   └── database.py         # MySQL connection setup
├── routes/
│   ├── auth.py              # Login, signup, password reset
│   ├── customer.py          # Catalog, cart, checkout, orders
│   ├── pharmacist.py        # Stock, prescriptions, fulfillment
│   ├── admin.py             # Dashboard, reports, user management
│   └── delivery.py          # Delivery status management
├── templates/                # Jinja2 templates, organized by role
├── static/
│   ├── css/ ├── js/ ├── images/
├── utils/
│   ├── auth_helpers.py       # Role-based access decorators
│   ├── csrf.py               # CSRF token generation/validation
│   ├── rate_limit.py         # Login attempt limiting
│   └── validators.py
└── uploads/prescriptions/    # Uploaded prescription images
```

## Getting Started

**Prerequisites:** Python 3.10+, MySQL (e.g. via XAMPP)

1. Clone the repository
   ```bash
   git clone https://github.com/obaids093-prog/SehatHub-Pharmacy.git
   cd SehatHub-Pharmacy
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database — create a MySQL database and import the schema, then configure your credentials in a `.env` file:
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=sehathub_db
   SECRET_KEY=your-secret-key-here
   ```

4. Run the app
   ```bash
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser

## Database

The schema is normalized across 16+ tables covering users & roles, medicine catalog, orders, and trust & safety (prescriptions, reviews). Key relationships include `users → customers/pharmacists/admins` (1:1), `customers → orders → order_items` (1:N), and `medicines → categories/brands` (N:1).

## Team

| Name | Roll No. |
|---|---|
| Syed Obaid Ali | 9321 |
| Sikander | 9315 |

---

*DBMS Semester Project*
