import copy
from decimal import Decimal, ROUND_HALF_UP

SAMPLE_PRODUCTS = {
    "P001": {"name": "Laptop", "price": 1200, "category": "Electronics", "stock": 10},
    "P002": {"name": "Mouse", "price": 25, "category": "Accessories", "stock": 50},
    "P003": {"name": "Keyboard", "price": 75, "category": "Accessories", "stock": 20},
    "P004": {"name": "Monitor", "price": 300, "category": "Electronics", "stock": 15},
}

SAMPLE_ORDERS = [
    {
        "order_id": "ORD001",
        "customer": "Ali",
        "items": [
            {"product_id": "P001", "quantity": 1},
            {"product_id": "P002", "quantity": 2},
        ],
        "payment_status": "paid",
    },
    {
        "order_id": "ORD002",
        "customer": "Ahmed",
        "items": [
            {"product_id": "P003", "quantity": 2},
            {"product_id": "P004", "quantity": 1},
        ],
        "payment_status": "paid",
    },
    {
        "order_id": "ORD003",
        "customer": "Ali",
        "items": [{"product_id": "P002", "quantity": 5}],
        "payment_status": "pending",
    },
]

MAX_PRICE = 1_000_000
DISCOUNT_TIERS = (
    (Decimal("1000"), Decimal("0.15")),
    (Decimal("500"), Decimal("0.10")),
    (Decimal("200"), Decimal("0.05")),
)
FREE_SHIPPING_THRESHOLD = Decimal("500")
SHIPPING_COST = Decimal("20")
LOW_STOCK_LIMIT = 10

def _valid_price(price):
    return (
        not isinstance(price, bool)
        and isinstance(price, (int, float))
        and 0 <= price <= MAX_PRICE
    )


def validate_order(order, products):
    requested_quantity = {}
    if not isinstance(order, dict):
        return False, "order should be a dict"
    order_id = order.get("order_id")
    customer = order.get("customer")
    if not isinstance(order_id, str) or not order_id.strip():
        return False, "missing order_id"
    if not isinstance(customer, str) or not customer.strip():
        return False, "missing customer"
    if order.get("payment_status") not in ("paid", "pending"):
        return False, "invalid payment status"
    items = order.get("items")
    if not isinstance(items, list) or not items:
        return False, "order has no item"
    for item in items:
        if not isinstance(item, dict):
            return False, "item should be a dict"
        quantity = item.get("quantity")
        product_id = item.get("product_id")
        if not isinstance(product_id, str) or product_id not in products:
            return False, f"invalid product_id: {product_id!r}"
        product = products[product_id]
        if not isinstance(product, dict):
            return False, "invalid product format"
        price = product.get("price")
        stock = product.get("stock")
        if not _valid_price(price):
            return False, f"invalid price for {product_id}"
        if isinstance(stock, bool) or not isinstance(stock, int):
            return False, "invalid stock format"
        if type(quantity) is not int or quantity <= 0:
            return False, f"invalid quantity for {product_id}"
        requested_quantity[product_id] = (
            requested_quantity.get(product_id, 0) + quantity
        )
    for product_id, total_quantity in requested_quantity.items():
        if products[product_id]["stock"] < total_quantity:
            return False, f"insufficient stock for {product_id}"
    return True, ""


def validate_products(products):
    if not isinstance(products, dict):
        raise ValueError("products must be a dict")
    for product_id, product in products.items():
        if not isinstance(product, dict):
            raise ValueError(f"{product_id}: product must be a dict")
        for key in ("name", "category"):
            if not isinstance(product.get(key), str):
                raise ValueError(f"{product_id}: missing or invalid {key}")
        price, stock = product.get("price"), product.get("stock")
        if not _valid_price(price):
            raise ValueError(f"{product_id}: invalid price")
        if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:
            raise ValueError(f"{product_id}: invalid stock")


def to_money(value):
    return Decimal(str(value))


def round_money(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_order_subtotal(order, products):
    prices = [
        to_money(products[item["product_id"]]["price"]) * item["quantity"]
        for item in order["items"]
    ]
    return round_money(calculate_total(*prices))


def calculate_discount(subtotal):
    subtotal = to_money(subtotal)
    for threshold, rate in DISCOUNT_TIERS:
        if subtotal >= threshold:
            return round_money(subtotal * rate)
    return Decimal("0.00")


def calculate_shipping(subtotal):
    subtotal = to_money(subtotal)
    return SHIPPING_COST if subtotal < FREE_SHIPPING_THRESHOLD else Decimal("0")


def calculate_total(*prices):
    return sum((to_money(p) for p in prices), Decimal("0"))


def rejected(order_id, customer, reason):
    return {
        "order_id": order_id,
        "customer": customer,
        "outcome": "rejected",
        "payment_status": None,
        "reason": reason,
    }


def process_order(order, products, processed_order_ids=None, **kwargs):
    if processed_order_ids is None:
        processed_order_ids = set()
    elif not isinstance(processed_order_ids, set):
        raise TypeError("processed_order_ids must be a set")

    order_id = "Unknown"
    has_valid_id = False
    customer = None
    if isinstance(order, dict):
        if isinstance(order.get("order_id"), str):
            order_id = order["order_id"].strip().upper()
            has_valid_id = bool(order_id)
        customer = order.get("customer")
        if isinstance(customer, str):
            customer = customer.strip()

    if not isinstance(order, dict):
        return rejected(order_id, customer, "order should be a dict")

    unexpected = set(kwargs) - {"apply_discount", "include_shipping"}
    if unexpected:
        return rejected(
            order_id, customer, f"unknown option(s): {', '.join(sorted(unexpected))}"
        )
    for option_name, value in kwargs.items():
        if not isinstance(value, bool):
            return rejected(order_id, customer, f"{option_name} must be a bool")

    if has_valid_id and order_id in processed_order_ids:
        return rejected(order_id, customer, "order already processed")

    is_valid, reason = validate_order(order, products)
    if not is_valid:
        return rejected(order_id, customer, reason)

    payment_status = order.get("payment_status")
    apply_discount = kwargs.get("apply_discount", True)
    include_shipping = kwargs.get("include_shipping", True)
    subtotal = calculate_order_subtotal(order, products)
    discount = calculate_discount(subtotal) if apply_discount else Decimal("0")
    final_amount = subtotal - discount
    shipping = calculate_shipping(subtotal) if include_shipping else Decimal("0")
    updated_amount = round_money(final_amount + shipping)
    for item in order["items"]:
        products[item["product_id"]]["stock"] -= item["quantity"]
    processed_order_ids.add(order_id)
    success_report = {
        **order,
        "order_id": order_id,
        "customer": customer,
        "items": [
            {
                **item,
                "name": products[item["product_id"]].get("name", item["product_id"]),
                "unit_price": products[item["product_id"]]["price"],
            }
            for item in order["items"]
        ],
        "payment_status": payment_status,
        "outcome": "accepted",
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "total": updated_amount,
    }
    return success_report


def mark_paid(order_id, processed_orders):
    if not isinstance(order_id, str):
        return None, "order_id must be a string"
    order_id = order_id.strip().upper()
    if not isinstance(processed_orders, list):
        raise TypeError("processed_orders must be a list")
    found_paid = False
    for processed in processed_orders:
        if not isinstance(processed, dict):
            continue
        if processed.get("order_id") != order_id:
            continue
        if processed.get("payment_status") == "paid":
            found_paid = True
            continue
        if processed.get("payment_status") != "pending":
            continue
        processed["payment_status"] = "paid"
        return processed, ""
    if found_paid:
        return None, "order already paid"
    return None, "order not found"


def generate_customer_report(processed_orders):
    spending = {}
    display_names = {}
    for order in processed_orders:
        if order["payment_status"] == "paid":
            key = order["customer"].casefold()
            display_names.setdefault(key, order["customer"])
            spending[key] = spending.get(key, Decimal("0")) + order["total"]
    return {display_names[key]: total for key, total in spending.items()}


def generate_product_report(processed_orders, products):
    units_sold = {}
    names = {}
    for order in processed_orders:
        if order["payment_status"] == "paid":
            for item in order["items"]:
                product_id = item["product_id"]
                quantity = item["quantity"]
                units_sold[product_id] = units_sold.get(product_id, 0) + quantity
                names[product_id] = item.get("name", product_id)

    product_report = {}
    for product_id, quantity in units_sold.items():
        product_report[product_id] = {"name": names[product_id], "units_sold": quantity}
    return product_report


def generate_sales_report(processed_orders, products):
    total_orders = len(processed_orders)
    paid_orders = 0
    pending_orders = 0
    rejected_orders = 0
    total_revenue = Decimal("0")
    revenue_excl_shipping = Decimal("0")
    total_discounts = Decimal("0")
    shipping_collected = Decimal("0")
    for order in processed_orders:
        if order["payment_status"] == "paid":
            paid_orders += 1
            total_revenue += order["total"]
            revenue_excl_shipping += order["total"] - order["shipping"]
            total_discounts += order["discount"]
            shipping_collected += order["shipping"]
        elif order["payment_status"] == "pending":
            pending_orders += 1
        elif order["outcome"] == "rejected":
            rejected_orders += 1
    customer_spending = generate_customer_report(processed_orders)
    if customer_spending:
        highest_spent = max(customer_spending.values())
        top_customers = [
            customer
            for customer, spent in customer_spending.items()
            if spent == highest_spent
        ]
    else:
        top_customers = []
    product_report = generate_product_report(processed_orders, products)

    if product_report:
        highest_units = max(
            product["units_sold"] for product in product_report.values()
        )
        top_selling_products = [
            product["name"]
            for product in product_report.values()
            if product["units_sold"] == highest_units
        ]
    else:
        top_selling_products = []
    low_stock_products = {}
    for product_id, product in products.items():
        if product["stock"] <= LOW_STOCK_LIMIT:
            low_stock_products[product_id] = {
                "name": product.get("name", product_id),
                "stock": product["stock"],
            }
    report = {
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "pending_orders": pending_orders,
        "rejected_orders": rejected_orders,
        "total_revenue": total_revenue,
        "revenue_excl_shipping": revenue_excl_shipping,
        "total_discounts": total_discounts,
        "shipping_collected": shipping_collected,
        "top_customer": top_customers,
        "top_selling_product": top_selling_products,
        "low_stock_products": low_stock_products,
    }
    return report


def get_unique_customers(processed_orders):
    names = {}
    for order in processed_orders:
        if order["payment_status"] in ("paid", "pending"):
            names.setdefault(order["customer"].casefold(), order["customer"])
    return set(names.values())


def get_unique_categories(products):
    categories = set()
    for product in products.values():
        categories.add(product["category"])

    return categories


def sort_products_by_price(products):
    return sorted(products.items(), key=lambda item: item[1]["price"])


def display_sales_report(report):
    print("\n============ SALES REPORT =============")
    print(f"Total Orders: {report['total_orders']}")
    print(f"Paid Orders: {report['paid_orders']}")
    print(f"Pending Orders: {report['pending_orders']}")
    print(f"Rejected Orders: {report['rejected_orders']}")
    print(f"Total Revenue (incl. shipping): ${report['total_revenue']:,.2f}")
    print(f"Total Revenue (excl. shipping): ${report['revenue_excl_shipping']:,.2f}")
    print(f"Total Discount: ${report['total_discounts']:,.2f}")
    print(f"Total Shipping: ${report['shipping_collected']:,.2f}")
    print("Top Customer(s):")
    for customer in report["top_customer"]:
        print(f"- {customer}")

    print("Top Selling Product(s):")
    for product in report["top_selling_product"]:
        print(f"- {product}")
    print("Low Stock Products:")
    if report["low_stock_products"]:
        for product_id, info in report["low_stock_products"].items():
            print(f"- {info['name']} ({product_id}): {info['stock']} left")
    else:
        print("- None")

    print("=======================================")


def display_processed_order(order):
    if order["outcome"] == "rejected":
        print(
            f"- {order['order_id']} | {order.get('customer')} | "
            f"status: rejected | reason: {order['reason']}"
        )
    else:
        print(
            f"- {order['order_id']} | {order.get('customer')} | "
            f"status: {order['payment_status']} | total: {order.get('total', 0):.2f}"
        )


def display_customer_report(customer_spending):
    if not customer_spending:
        print("- None")
        return
    for customer, spent in customer_spending.items():
        print(f"- {customer}: {spent:.2f}")


def display_product_report(product_report):
    if not product_report:
        print("- None")
        return
    for product_id, info in product_report.items():
        print(f"- {product_id} | {info['name']} | units sold: {info['units_sold']}")


def display_unique_customers(customers):
    if not customers:
        print("- None")
        return
    for customer in sorted(customers):
        print(f"- {customer}")


def main(orders, products):
    processed_order_ids = set()
    order_processed = False
    processed_orders = []
    products = copy.deepcopy(products)
    validate_products(products)
    while True:

        print("\n===== ORDER PROCESSING SYSTEM =====")
        print("1.Process all orders")
        print("2.View processed orders")
        print("3.Customer report")
        print("4.Product report")
        print("5.Sales report")
        print("6.Unique customers")
        print("7.Unique product categories")
        print("8.Products sorted by price")
        print("9.Mark a pending order as paid")
        print("10.Exit")

        try:
            choice = input("Enter your choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nNo more input. Exiting Order Processing System.")
            break
        if choice == "1":
            if order_processed:
                print("Orders were already processed. Nothing to do.")
                continue
            processed_orders = [
                process_order(order, products, processed_order_ids=processed_order_ids)
                for order in orders
            ]
            print("All orders processed successfully.")
            order_processed = True
        elif choice in ("2", "3", "4", "5", "6", "9") and not order_processed:
            print("No orders processed yet. Choose option 1 first.")
        elif choice == "2":
            for order in processed_orders:
                display_processed_order(order)
        elif choice == "3":
            display_customer_report(generate_customer_report(processed_orders))
        elif choice == "4":
            display_product_report(generate_product_report(processed_orders, products))
        elif choice == "5":
            report = generate_sales_report(processed_orders, products)
            display_sales_report(report)
        elif choice == "6":
            display_unique_customers(get_unique_customers(processed_orders))
        elif choice == "7":
            for category in sorted(get_unique_categories(products)):
                print(f"- {category}")
        elif choice == "8":
            for product_id, product in sort_products_by_price(products):
                print(
                    f"{product_id} | {product['name']} | "
                    f"Price: {product['price']} | Stock: {product['stock']}"
                )
        elif choice == "9":
            order_id = input("Enter the order ID to mark as paid: ").strip()
            updated_order, error = mark_paid(order_id, processed_orders)
            if error or not updated_order:
                print(f"Could not mark paid: {error or 'order not found'}")
            else:
                print(f"{updated_order['order_id']} is now marked as paid.")
        elif choice == "10":
            print("Exiting Order Processing System.")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 10.")


if __name__ == "__main__":
    main(SAMPLE_ORDERS, SAMPLE_PRODUCTS)
