import copy
from decimal import Decimal, ROUND_HALF_UP

products = {
    "P001": {"name": "Laptop", "price": 1200, "category": "Electronics", "stock": 10},
    "P002": {"name": "Mouse", "price": 25, "category": "Accessories", "stock": 50},
    "P003": {"name": "Keyboard", "price": 75, "category": "Accessories", "stock": 20},
    "P004": {"name": "Monitor", "price": 300, "category": "Electronics", "stock": 15}
}

orders = [
    {
        "order_id": "ORD001", "customer": "Ali",
        "items": [
            {"product_id": "P001", "quantity": 1},
            {"product_id": "P002", "quantity": 2}
        ],
        "payment_status": "paid"
    },
    {
        "order_id": "ORD002", "customer": "Ahmed",
        "items": [
            {"product_id": "P003", "quantity": 2},
            {"product_id": "P004", "quantity": 1}
        ],
        "payment_status": "paid"
    },
    {
        "order_id": "ORD003", "customer": "Ali",
        "items": [{"product_id": "P002", "quantity": 5}],
        "payment_status": "pending"
    }
]

MAX_PRICE = 1_000_000
DISCOUNT_TIERS = (
    (Decimal("1000"), Decimal("0.15")),
    (Decimal("500"),  Decimal("0.10")),
    (Decimal("200"),  Decimal("0.05")),
)
FREE_SHIPPING_THRESHOLD = Decimal("500")
SHIPPING_COST = Decimal("20")
LOW_STOCK_LIMIT = 5


def validate_order(order,products):
    requested_quantity = {}
    if not isinstance(order,dict):
        return False , "order should be a dict"
    order_id = order.get("order_id")
    customer = order.get("customer")
    if not isinstance(order_id,str) or not order_id.strip():
        return False , "missing order_id"
    if not isinstance(customer, str) or not customer.strip():
        return False , "missing customer"
    if order.get("payment_status") not in ("paid","pending"):
        return False , "invalid payment status"
    items = order.get("items")
    if not isinstance(items,list) or not items:
        return False , "order has no item"
    for item in items:
        if not isinstance(item,dict):
            return False , "item should be a dict"
        quantity = item.get("quantity")
        product_id = item.get("product_id")
        if not isinstance(product_id, str) or product_id not in products:
            return False , f"invalid product_id: {product_id!r}"
        product = products[product_id]
        if not isinstance(product, dict):
            return False , "invalid product format"
        price = product.get("price")
        stock = product.get("stock")
        if isinstance(price, bool) or not isinstance(price, (int, float)) or not (0 <= price <= MAX_PRICE):
            return False , f"invalid price for {product_id}"
        if isinstance(stock, bool) or not isinstance(stock, int):
            return False , "invalid stock format"
        if type(quantity) is not int or quantity <= 0:
            return False , f"invalid quantity for {product_id}"
        requested_quantity[product_id] = requested_quantity.get(product_id, 0) + quantity
    for product_id , total_quantity in requested_quantity.items():
        if products[product_id]["stock"] < total_quantity:
            return False , f"insufficient stock for {product_id}" 
    return True , ""
    

def to_money(value):
    return Decimal(str(value))

def round_money(value):
    return value.quantize(Decimal("0.01") , rounding = ROUND_HALF_UP)


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
    return sum((to_money(p) for p in prices) , Decimal("0"))

    
def process_order(order,products,processed_order_ids = None,**kwargs):
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
        if isinstance(order.get("customer"), str):
            customer = order["customer"].strip().title()
        else:
            customer = order.get("customer")
        
    if not isinstance(order, dict):
        return {
            "order_id": order_id,
            "customer": customer,
            "status": "rejected",
            "reason": "order should be a dict"
        }
        
    if has_valid_id and order_id in processed_order_ids:
        return {
            "order_id" : order_id,
            "customer" : customer,
            "status" : "rejected",
            "reason" : "order already processed"
        }
    is_valid , reason = validate_order(order,products)
    if not is_valid:
        return {
            "order_id" : order_id,
            "customer" : customer,
            "status" : "rejected",
            "reason" : reason
        }
    unexpected = set(kwargs) - {"apply_discount", "include_shipping"}
    if unexpected:
        return {
            "order_id" : order_id,
            "customer" : customer,
            "status" : "rejected",
            "reason" : f"unknown option(s): {', '.join(sorted(unexpected))}"
        }
    for option_name in ("apply_discount", "include_shipping"):
        if option_name in kwargs and not isinstance(kwargs[option_name], bool):
            return {
            "order_id": order_id,
            "customer": customer,
            "status": "rejected",
            "reason": f"{option_name} must be a bool"
        }
    payment_status = order.get("payment_status")
    apply_discount = kwargs.get("apply_discount", True)
    include_shipping = kwargs.get("include_shipping", True)
    subtotal = calculate_order_subtotal(order,products) 
    discount = calculate_discount(subtotal) if apply_discount else Decimal("0")
    final_amount = subtotal - discount
    shipping = calculate_shipping(subtotal) if include_shipping else Decimal("0")
    updated_amount = round_money(final_amount + shipping)
    if payment_status == "paid":    
        for item in order["items"]:
            product_id = item["product_id"]
            quantity = item["quantity"]
            products[product_id]["stock"] -= quantity
    processed_order_ids.add(order_id)
    success_report = {**order,
                  "order_id" : order_id,
                  "customer" : customer,
                  "items": [dict(item) for item in order["items"]],
                  "status": payment_status,
                  "subtotal": subtotal,
                  "discount": discount,
                  "shipping": shipping,
                  "total": updated_amount}
    return success_report


def generate_customer_report(processed_orders):
    customer_spending = {}
    for order in processed_orders:
        if order["status"] == "paid":
            customer = order["customer"]
            customer_spending[customer] = customer_spending.get(customer,0) + order["total"]
    return customer_spending


def generate_product_report(processed_orders,products):
    units_sold = {}
    for order in processed_orders:
        if order["status"] == "paid":
            for item in order["items"]:
                product_id = item["product_id"]  
                quantity = item["quantity"]
                units_sold[product_id] = (units_sold.get(product_id,0) + quantity)
                
    product_report = {}
    for product_id , quantity in units_sold.items():
        product_name = products[product_id].get("name", product_id)
        product_report[product_id] = {
            "name" : product_name ,
            "units_sold" : quantity
        }
    return product_report
    
    
def generate_sales_report(processed_orders, products):
    total_orders = len(processed_orders)
    paid_orders = 0
    pending_orders = 0
    rejected_orders = 0
    total_revenue = 0
    total_discounts = 0
    shipping_collected = 0
    for order in processed_orders:
        if order["status"] == "paid":
            paid_orders += 1
            total_revenue += order["total"]
            total_discounts += order["discount"]
            shipping_collected += order["shipping"]
        elif order["status"] == "pending":
            pending_orders += 1
        elif order["status"] == "rejected":
            rejected_orders += 1
    customer_spending = generate_customer_report(processed_orders)
    if customer_spending:
        highest_spent = max(customer_spending.values())
        top_customers = [customer for customer, spent in customer_spending.items()
                          if spent == highest_spent]
    else:
        top_customers = []
    product_report = generate_product_report(processed_orders, products)

    if product_report:
        highest_units = max(product["units_sold"] for product in product_report.values())
        top_selling_products = [product["name"] for product in product_report.values()
                    if product["units_sold"] == highest_units
                    ]
    else:
        top_selling_products = []
    low_stock_products = {}
    for product_id, product in products.items():
        if product["stock"] < LOW_STOCK_LIMIT:
            low_stock_products[product_id] = product.get("name", product_id)
    report = {
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "pending_orders": pending_orders,
        "rejected_orders": rejected_orders,
        "total_revenue" : total_revenue,
        "total_discounts": total_discounts,
        "shipping_collected": shipping_collected,
        "top_customer": top_customers,
        "top_selling_product" : top_selling_products,
        "low_stock_products" : low_stock_products
    }
    return report


def get_unique_customers(processed_orders):
    return {
        order["customer"]
        for order in processed_orders
        if order["status"] in ["paid" , "pending"]
    }


def get_unique_categories(products):
    categories = set()
    for product in products.values():
        categories.add(product["category"])

    return categories


def sort_products_by_price(products):
    return sorted(
        products.items(),
        key=lambda item: item[1]["price"]
    )

    
def display_sales_report(report):
    print("\n============ SALES REPORT =============")
    print(f"Total Orders: {report['total_orders']}")
    print(f"Paid Orders: {report['paid_orders']}")
    print(f"Pending Orders: {report['pending_orders']}")
    print(f"Rejected Orders: {report['rejected_orders']}")
    print(f"Total Revenue: {report['total_revenue']:.2f}")
    print(f"Total Discount: {report['total_discounts']:.2f}")
    print(f"Total Shipping: {report['shipping_collected']:.2f}")
    print("Top Customer(s):")
    for customer in report["top_customer"]:
        print(f'- {customer}')
    
    print("Top Selling product(s):")
    for product in report["top_selling_product"]:
        print(f'- {product}')
    print("Low Stock Products:")
    if report['low_stock_products']:
        for product_id , name in report['low_stock_products'].items():
            print(f"- {name} ({product_id})")
    else: 
        print("- None")
    
    print("=======================================")


def display_processed_order(order):
    if order["status"] == "rejected":
        print(f"- {order['order_id']} | {order.get('customer')} | "
              f"status: rejected | reason: {order['reason']}")
    else:
        print(f"- {order['order_id']} | {order.get('customer')} | "
              f"status: {order['status']} | total: {order.get('total', 0):.2f}")
        

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


def main(orders,products):
    processed_order_ids = set()
    order_processed = False
    processed_orders = []
    products = copy.deepcopy(products)
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
        print("9.Exit")

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
        elif choice in ("2", "3", "4", "5", "6") and not order_processed:
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
                print(f"{product_id} | {product['name']} | "
                    f"Price: {product['price']} | Stock: {product['stock']}")
        elif choice == "9":
            print("Exiting Order Processing System.")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 9.")
            
if __name__ == "__main__":
    main(orders,products)
