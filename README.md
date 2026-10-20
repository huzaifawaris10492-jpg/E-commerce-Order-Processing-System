# Order Processing System

A command-line order processing system for a small e-commerce store, built in
Python. It validates orders, applies discounts and shipping, manages stock
levels, and generates sales and customer reports.

## Features

- **Order validation** — rejects orders with missing or blank fields, invalid
  quantities, unknown products, or insufficient stock, each with a specific
  reason instead of a generic failure or a crash (e.g. `"missing order_id"`,
  `"invalid quantity for P002"`, `"insufficient stock for P001"`).
- **Duplicate protection** — an order can't be processed twice; already-seen
  order IDs are tracked and rejected on resubmission with the reason
  `"order already processed"`.
- **Configurable processing** — `process_order` accepts optional keyword
  arguments:
  - `apply_discount` (default `True`) — set to `False` to skip the discount
    calculation for that order.
  - `include_shipping` (default `True`) — set to `False` to skip shipping for
    that order.
  - Any other keyword argument is rejected with a reason like
    `"unknown option(s): apply_discout"`, so a typo in an option name fails
    loudly instead of being silently ignored.
- **Pricing** — tiered discounts based on subtotal (15% at $1,000+, 10% at
  $500+, 5% at $200+), plus a flat $20 shipping charge for orders under $500
  (free shipping at $500 and above).
- **Stock management** — paid orders deduct stock; products below 5 units are
  flagged as low stock.
- **Reporting**
  - Customer spending report
  - Product sales report (units sold per product)
  - Full sales report: orders by status, total revenue, discounts, shipping,
    top customer(s) — ties included — top-selling product(s) — ties
    included — and low-stock items
- **Utilities** — list unique customers, list unique product categories, view
  products sorted by price.
- **Tested** — unit tests cover discount and shipping calculations, order
  validation (missing/blank fields, bad quantities, unknown products,
  insufficient stock), duplicate-order rejection, unknown-option rejection,
  the `apply_discount` option, tied top customers, and report display.

## Requirements

- Python 3.8+
- No external dependencies (standard library only)

## Usage

```bash
python order_processing_system.py
```

You'll see a menu:
Process all orders
View processed orders
Customer report
Product report
Sales report
Unique customers
Unique product categories
Products sorted by price
Exit

Orders can only be processed once per run — selecting option 1 again will
not re-deduct stock. Options 2–5 ask you to run option 1 first if no orders
have been processed yet.

Note: this applies to pending orders too. Once an order's ID has been
recorded as processed, the same ID can't be resubmitted later as "paid" —
it will be rejected as a duplicate rather than updated. There's currently no
way to transition a pending order to paid after the fact.

## Running Tests

Run this from inside the project folder:

```bash
python -m unittest test_processing_system -v
```

All tests should pass.

## Project Structure

EcomerceProject/
├── order_processing_system.py # Main application
├── test_processing_system.py # Unit tests
└── README.md

# E-commerce-order-processing-system
# E-commerce-Order-Processing-System
# E-commerce-Order-Processing-System
