# GroceryMeat POS — Sales & Inventory Management System

A Django 5 + Bootstrap 5 sales and inventory system for a grocery/meat store
selling **canned goods**, **dry goods**, and **fresh meat**. Covers
authentication & RBAC, product/meat CRUD with barcodes & QR codes, a dynamic
pricing engine, POS checkout with automatic inventory deduction, customer
credit/debt tracking, suppliers & purchase orders, a chart-driven dashboard,
exportable reports (CSV/Excel/PDF), notifications, and an audit log.

## ⚠️ Honest status of this build

This was generated in one pass without a live Django environment to run/test
against (no network access to `pip install` in the build sandbox), so **you
must run it locally before trusting it in production**. Specifically:

- All Python files pass a `py_compile` syntax check, and the code follows
  Django conventions closely, but it has **not been executed** against a real
  database — run `python manage.py check` and `migrate` first and fix any
  small issues that surface (typically minor template/field-name mismatches).
- **Fully implemented**: custom User + RBAC, Product/MeatInventory CRUD with
  barcode/QR generation, stock ledger (`InventoryTransaction`), dynamic
  pricing engine (markup calculator, manual override + history, scheduled
  promos), POS checkout (cash + credit) with atomic inventory deduction,
  customer debt/payment tracking with auto-recalculated balances, suppliers +
  purchase orders with "receive delivery → auto stock update", dashboard with
  6 Chart.js charts, CSV/Excel/PDF report exports, notifications, audit
  logging, Docker/docker-compose, `.env` config, and a `seed_data` command.
- **Simplified / left as an extension point**:
  - COGS in the financial report uses each item's *current* cost price
    rather than a historical snapshot at sale time (noted in the template).
  - Barcode scanner integration is "type or paste a scanned code into the
    search box" rather than wiring a camera/hardware-scanner JS library.
  - Dark mode, RBAC, and most CRUD screens are complete, but styling is
    intentionally plain Bootstrap — there's no custom design system.
  - Only a handful of unit tests are included (accounts, inventory, sales,
    customers) — not full coverage of every view.
  - Promo pricing activation and overdue/expiry notifications rely on two
    management commands intended to run via cron (see below) rather than
    a background task queue like Celery.

## Tech stack

- Python / Django 5, Django ORM, Class-Based Views, ModelForms
- Bootstrap 5, Bootstrap Icons, vanilla JS (no build step), Chart.js
- SQLite for local dev, PostgreSQL for production
- `python-barcode` + `qrcode` for barcode/QR generation
- `reportlab` (PDF) + `openpyxl` (Excel) + built-in `csv` for report exports
- Docker + docker-compose + Gunicorn + WhiteNoise for deployment

## Project layout

```
config/         Django settings/urls/wsgi/asgi
core/           RBAC mixins, context processors, seed_data command
accounts/       Custom User model (roles), login/logout/profile/password
dashboard/      Landing page: stat cards + 6 Chart.js charts
inventory/      ProductCategory, Product (canned/dry goods), stock ledger
meat/           MeatInventory (fresh meat, priced/sold per kg)
pricing/        PriceHistory, PromoSchedule, markup/override engine
sales/          Sale, SaleItem, POS screen, checkout API, receipts
customers/      Customer, CustomerDebt, CustomerPayment
suppliers/      Supplier CRUD
purchases/      PurchaseOrder, PurchaseItem, "receive delivery" flow
reports/        Sales/Inventory/Debt/Financial reports + CSV/Excel/PDF export
notifications/  In-app notification bell + broadcast helpers
audit/          AuditLog model + middleware + log_action() helper
templates/      All HTML templates (Bootstrap 5, one base.html)
static/         custom.css, main.js (dark mode + sidebar toggle)
```

## Local setup (SQLite)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # defaults to SQLite; edit as needed

python manage.py makemigrations
python manage.py migrate
python manage.py seed_data         # optional demo data + demo users
python manage.py createsuperuser   # if you skipped seed_data
python manage.py runserver
```

Demo accounts created by `seed_data` (change these immediately in any shared
environment):

| Username     | Password        | Role             |
|--------------|-----------------|------------------|
| admin        | admin12345      | Administrator    |
| manager1     | manager12345    | Manager          |
| cashier1     | cashier12345    | Cashier          |
| inventory1   | inventory12345  | Inventory Staff  |

## Running tests

```bash
python manage.py test
```

## Switching to PostgreSQL

Set in `.env`:

```
DB_ENGINE=postgres
DB_NAME=store_system
DB_USER=store_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

Then `pip install psycopg2-binary` (already in requirements.txt) and re-run
`migrate`.

## Docker deployment

```bash
cp .env.example .env   # set DB_PASSWORD, SECRET_KEY, ALLOWED_HOSTS, etc.
docker compose up --build
```

This starts a Postgres container plus the Django app (via Gunicorn),
running migrations and `collectstatic` automatically. Visit
`http://localhost:8000`.

For a bare-metal / VM deployment: put Nginx in front of Gunicorn, serve
`/static/` and `/media/` directly from Nginx (or keep WhiteNoise for static),
set `DEBUG=False`, a real `SECRET_KEY`, and your real `ALLOWED_HOSTS` in
`.env`.

## Scheduled jobs (cron)

Two management commands are meant to run periodically — wire them into cron
or Celery beat in production:

```bash
# every 5 minutes: activate/expire scheduled promo pricing
*/5 * * * * cd /app && python manage.py apply_scheduled_promos

# once daily: flag overdue debts + notify about expiring stock
0 6 * * * cd /app && python manage.py check_overdue_and_expiring
```

## Key design notes

- **Inventory is never mutated directly from a view.** All stock changes go
  through `inventory/services.py` (`stock_in`, `stock_out`,
  `manual_adjustment`, `deduct_for_sale`, `receive_purchase`), each of which
  writes an `InventoryTransaction` row — this is your audit trail and the
  data source for the "Stock Movement" report. `meat/services.py` mirrors
  this for fresh meat (tracked in kg instead of units).
- **Checkout is one atomic transaction** (`sales/services.py::checkout`):
  cart validation, inventory deduction (product or meat), tax/discount math,
  and — for credit sales — `CustomerDebt` creation all succeed or fail
  together, so you never end up with a sale that deducted stock but didn't
  record a debt (or vice versa).
- **RBAC** is centralized in `core/mixins.py` (`AdminOnlyMixin`,
  `ManagerUpMixin`, `InventoryStaffUpMixin`, `CashierUpMixin`) so every view
  declares its required role in one line instead of re-implementing checks.
- **Audit logging** flows through `audit/utils.py::log_action`, called both
  by the `AuditableMixin` (for standard CRUD) and directly from services
  (login/logout via signals, sales via `sales/services.py`).
