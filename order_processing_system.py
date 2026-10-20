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
            return False , "invalid product_id"
        product = products[product_id]
        if not isinstance(product, dict):
            return False , "invalid product format"
        price = product.get("price")
        stock = product.get("stock")
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
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
    

def calculate_order_subtotal(order, products):
    prices = [
        products[item["product_id"]]["price"] * item["quantity"]
        for item in order["items"]
    ]
    return calculate_total(*prices)

def calculate_discount(subtotal):
    if subtotal >= 1000:
        return round(subtotal * 0.15 , 2)
    elif subtotal >= 500:
        return round(subtotal * 0.10 , 2)
    elif subtotal >= 200:
        return round(subtotal * 0.05 , 2)
    return 0


def calculate_shipping(subtotal):
    if subtotal < 500:
        return 20
    else:
        return 0


def calculate_total(*prices):
    return sum(prices) 
    
def process_order(order,products,processed_order_ids = None,**kwargs):
    if processed_order_ids is None:
        processed_order_ids = set()
    order_id = "Unknown"
    customer = None
    if isinstance(order, dict):
        if isinstance(order.get("order_id"), str):
            order_id = order["order_id"]
        customer = order.get("customer")
    if order_id in processed_order_ids:
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
    payment_status = order.get("payment_status")
    apply_discount = kwargs.get("apply_discount", True)
    include_shipping = kwargs.get("include_shipping", True)
    subtotal = calculate_order_subtotal(order,products) 
    discount = calculate_discount(subtotal) if apply_discount else 0
    final_amount = subtotal - discount
    shipping = calculate_shipping(subtotal) if include_shipping else 0
    updated_amount = round(final_amount + shipping , 2)
    if payment_status == "paid":    
        for items in order["items"]:
            product_id = items["product_id"]
            quantity = items["quantity"]
            products[product_id]["stock"] -= quantity
    processed_order_ids.add(order_id)
    success_report = {**order,
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
        product_name = products[product_id]["name"]
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
        if product["stock"] < 5:
            low_stock_products[product_id] = product["name"]
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
    print("\n========== SALES REPORT ===========")
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
    
    print("Top selling product")
    for product in report["top_selling_product"]:
        print(f'- {product}')
    print("Low Stock Products")
    if report['low_stock_products']:
        for product_id , name in report['low_stock_products'].items():
            print(f"- {name} ({product_id})")
    else: 
        print("- None")
    
    print("============================================")


import copy
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
        except EOFError:
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
                print(order)
        elif choice == "3":
            print(generate_customer_report(processed_orders))
        elif choice == "4":
            print(generate_product_report(processed_orders, products))
        elif choice == "5":
            report = generate_sales_report(processed_orders, products)
            display_sales_report(report)
        elif choice == "6":
            print(get_unique_customers(processed_orders))
        elif choice == "7":
            print(get_unique_categories(products))
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
