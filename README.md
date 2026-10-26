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
    Shipping is calculated on the subtotal *before* discounts are applied, so a
  discounted order can qualify for free shipping even if the discounted total
  falls below $500.
- **Stock management** — orders reserve stock when placed (paid or pending); products with 10 units or
  fewer are flagged as low stock, with the remaining count shown.
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
  pending-order stock reservation, mark_paid, deleted-product reports,
  the `apply_discount` option, tied top customers, and report display.
   - **Customer names** — trimmed and case-insensitive ("Ali", "Ali " and "ali" are one customer). The first spelling seen is the one shown in reports.

## Requirements

- Python 3.8+
- No external dependencies (standard library only)

## Usage

```bash
python order_processing_system.py
```

You'll see a menu:

   1. Process all orders
   2. View processed orders
   3. Customer report
   4. Product report
   5. Sales report
   6. Unique customers
   7. Unique product categories
   8. Products sorted by price
   9. Mark a pending order as paid
   10. Exit

Orders can only be processed once per run — selecting option 1 again will
not re-deduct stock. Options 2-6 and 9 ask you to run option 1 first if no orders
have been processed yet.

   Pending orders reserve stock when placed. Use option 9 to mark a pending order as paid; this does not change stock, because it was already reserved. A pending order that is never paid keeps its stock reserved, since there is no cancel option.

## Running Tests

Run this from inside the project folder:

```bash
python -m unittest test_processing_system -v
```

All tests should pass.

## Project Structure

```text
EcommerceProject
├── order_processing_system.py   # Main application
├── test_processing_system.py    # Unit tests
└── README.md
```

