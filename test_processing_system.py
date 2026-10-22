import io
import contextlib
import unittest
from order_processing_system import (
    calculate_discount,
    calculate_shipping,
    calculate_total,
    validate_order,
    calculate_order_subtotal,
    process_order,
    generate_sales_report,
    generate_customer_report,
    display_sales_report,
    get_unique_customers)


class TestPricingCalculations(unittest.TestCase):
    def test_discount(self):
        self.assertEqual(calculate_discount(100),0)
        self.assertEqual(calculate_discount(200),10)
        self.assertEqual(calculate_discount(500),50)
        self.assertEqual(calculate_discount(1000),150)

    def test_shipping(self):
        self.assertEqual(calculate_shipping(500),0)
        self.assertEqual(calculate_shipping(499),20)

    def test_calculate_order_subtotal(self):
        products = {
            "P001": {"name": "Laptop", "price": 10, "stock": 5},
            "P002": {"name": "Mouse", "price": 20, "stock": 5},
        }
        order = {
            "items": [
                {"product_id": "P001", "quantity": 2},
                {"product_id": "P002", "quantity": 3},
            ]
        }
        self.assertEqual(calculate_order_subtotal(order, products), 80)

    def test_calculate_total_accepts_varargs(self):
        self.assertEqual(calculate_total(10, 20, 30), 60)
        self.assertEqual(calculate_total(), 0)


class TestValidateOrder(unittest.TestCase):
    def test_quantity(self):
        products = {
            "p102" : {
                "name" : "mouse",
                "price" : 20,
                "stock" : 5
            }
        }

        order = {
            "order_id" : "T1",
            "customer" : "Test",
            "payment_status" : "paid",
            "items" : [
                {"product_id" : "p102" , "quantity" : 0}
            ]
        }
        self.assertFalse(validate_order(order,products)[0])

    def test_missing_items(self):
        self.assertFalse(
            validate_order(
                {"order_id": "T2", "customer": "Test", "payment_status": "paid"},
                {}
            )[0]
        )

    def test_missing_product_id(self):
        products = {
            "P001": {"price": 100, "stock": 5}
        }
        order = {
            "order_id": "T3",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"quantity": 1}]
        }
        self.assertFalse(validate_order(order, products)[0])

    def test_invalid_quantity(self):
        products = {
            "P001": {"price": 100, "stock": 5}
        }
        order = {
            "order_id": "T4",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": -1}]
        }
        self.assertFalse(validate_order(order, products)[0])

    def test_validate_order_sums_quantity_across_lines(self):
        products = {
            "P001": {"name": "Laptop", "price": 1200, "stock": 10}
        }
        order = {
            "order_id": "T5", "customer": "Test", "payment_status": "paid",
            "items": [
                {"product_id": "P001", "quantity": 10},
                {"product_id": "P001", "quantity": 10},
            ]
        }
        self.assertFalse(validate_order(order, products)[0])

    def test_validate_order_rejects_negative_price(self):
        products = {
            "P001": {"name": "Test", "price": -50, "stock": 5}
        }
        order = {
            "order_id": "T6", "customer": "Test", "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}]
        }
        self.assertFalse(validate_order(order, products)[0])

    def test_validate_order_rejects_blank_order_id(self):
        products = {
            "P001": {"name": "Test", "price": 10, "stock": 5}
        }
        order = {
            "order_id": "   ", "customer": "Test", "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}]
        }
        is_valid, reason = validate_order(order, products)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "missing order_id")

    def test_validate_order_rejects_blank_customer(self):
        products = {
            "P001": {"name": "Test", "price": 10, "stock": 5}
        }
        order = {
            "order_id": "T6b", "customer": "   ", "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}]
        }
        is_valid, reason = validate_order(order, products)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "missing customer")

    def test_validate_order_rejects_insufficient_stock(self):
        products = {
            "P001": {"name": "Test", "price": 10, "stock": 2}
        }
        order = {
            "order_id": "T6c", "customer": "Test", "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 5}]
        }
        is_valid, reason = validate_order(order, products)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "insufficient stock for P001")


class TestProcessOrder(unittest.TestCase):
    def test_process_order_deducts_stock(self):
        products = {
            "P001": {"name": "Laptop", "price": 1200, "stock": 10}
        }
        order = {
            "order_id": "T7", "customer": "Test", "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 3}]
        }
        result = process_order(order, products)
        self.assertEqual(result["status"], "paid")
        self.assertEqual(products["P001"]["stock"], 7)
        
    def test_process_order_pending_does_not_deduct_stock(self):
        products = {
        "P001": {"name": "Laptop", "price": 1200, "stock": 10}
    }
        order = {
        "order_id": "P1", "customer": "Test", "payment_status": "pending",
        "items": [{"product_id": "P001", "quantity": 3}]
    }
        result = process_order(order, products)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(products["P001"]["stock"], 10)
        

    def test_process_order_rejects_duplicate(self):
        products = {
            "P001": {"name": "Laptop", "price": 1200, "stock": 10}
        }
        order = {
            "order_id": "T8", "customer": "Test", "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}]
        }
        processed_ids = set()
        first = process_order(order, products, processed_order_ids=processed_ids)
        second = process_order(order, products, processed_order_ids=processed_ids)
        self.assertEqual(first["status"], "paid")
        self.assertEqual(second["status"], "rejected")
        self.assertEqual(second["reason"], "order already processed")

    def test_process_order_rejects_unknown_option(self):
        products = {
            "P001": {"name": "Laptop", "price": 1200, "stock": 10}
        }
        order = {
            "order_id": "T8b", "customer": "Test", "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}]
        }
        result = process_order(order, products, apply_discout=False)
        self.assertEqual(result["status"], "rejected")
        self.assertIn("unknown option", result["reason"])
        self.assertEqual(products["P001"]["stock"], 10)

    def test_process_order_apply_discount_false(self):
        products = {
            "P001": {"name": "Laptop", "price": 1200, "stock": 10}
        }
        order = {
            "order_id": "T8c", "customer": "Test", "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}]
        }
        result = process_order(order, products, apply_discount=False)
        self.assertEqual(result["discount"], 0)
        self.assertEqual(result["total"], result["subtotal"] + result["shipping"])

    def test_process_order_result_does_not_share_items(self):
        products = {"P001": {"name": "Laptop", "price": 10, "stock": 10}}
        order = {"order_id": "S1", "customer": "Test", "payment_status": "paid",
             "items": [{"product_id": "P001", "quantity": 1}]}
        result = process_order(order, products)
        result["items"].append({"product_id": "P001", "quantity": 99})
        result["items"][0]["quantity"] = 50
        self.assertEqual(order["items"], [{"product_id": "P001", "quantity": 1}])


class TestReports(unittest.TestCase):
    def test_revenue_matches_customer_spending(self):
        products = {
            "P001": {"name": "Laptop", "price": 1200, "stock": 10},
            "P002": {"name": "Mouse", "price": 25, "stock": 50},
        }
        order = {
            "order_id": "T9", "customer": "Test", "payment_status": "paid",
            "items": [{"product_id": "P002", "quantity": 1}]
        }
        processed = [process_order(order, products)]
        report = generate_sales_report(processed, products)
        customer_totals = generate_customer_report(processed)
        self.assertEqual(report["total_revenue"], sum(customer_totals.values()))

    def test_generate_sales_report_handles_tied_top_customers(self):
        products = {
            "P001": {"name": "Widget", "price": 100, "stock": 10},
        }
        order_a = {
            "order_id": "TA1", "customer": "Ali", "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}]
        }
        order_b = {
            "order_id": "TB1", "customer": "Zed", "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}]
        }
        processed = [
            process_order(order_a, products, apply_discount=False, include_shipping=False),
            process_order(order_b, products, apply_discount=False, include_shipping=False),
        ]
        report = generate_sales_report(processed, products)
        self.assertIn("Ali", report["top_customer"])
        self.assertIn("Zed", report["top_customer"])
        self.assertEqual(len(report["top_customer"]), 2)
    
    def test_generate_sales_report_handles_tied_top_products(self):
        products = {
        "P001": {"name": "Widget", "price": 100, "stock": 10},
        "P002": {"name": "Gadget", "price": 100, "stock": 10},
    }
        order_a = {
        "order_id": "PA1", "customer": "Ali", "payment_status": "paid",
        "items": [{"product_id": "P001", "quantity": 1}]
    }
        order_b = {
        "order_id": "PB1", "customer": "Zed", "payment_status": "paid",
        "items": [{"product_id": "P002", "quantity": 1}]
    }
        processed = [
        process_order(order_a, products),
        process_order(order_b, products),
    ]
        report = generate_sales_report(processed, products)
        self.assertIn("Widget", report["top_selling_product"])
        self.assertIn("Gadget", report["top_selling_product"])
        self.assertEqual(len(report["top_selling_product"]), 2)
    
    def test_generate_sales_report_counts_rejected_orders(self):
        products = {
        "P001": {"name": "Laptop", "price": 1200, "stock": 10}
    }
        order = {
        "order_id": "R1", "customer": "Test", "payment_status": "paid",
        "items": [{"product_id": "P001", "quantity": 1}]
    }
        processed_ids = set()
        first = process_order(order, products, processed_order_ids=processed_ids)
        second = process_order(order, products, processed_order_ids=processed_ids)
        report = generate_sales_report([first, second], products)
        self.assertEqual(report["rejected_orders"], 1)
        self.assertEqual(report["paid_orders"], 1)
    
    def test_generate_sales_report_handles_empty_orders(self):
        products = {
        "P001": {"name": "Laptop", "price": 1200, "stock": 10}
    }
        report = generate_sales_report([], products)
        self.assertEqual(report["total_orders"], 0)
        self.assertEqual(report["paid_orders"], 0)
        self.assertEqual(report["pending_orders"], 0)
        self.assertEqual(report["rejected_orders"], 0)
        self.assertEqual(report["total_revenue"], 0)
        self.assertEqual(report["top_customer"], [])
        self.assertEqual(report["top_selling_product"], [])
    
    def test_get_unique_customers_excludes_invalid_and_none(self):
        products = {"P001": {"name": "Laptop", "price": 10, "stock": 10}}
        orders = [
        {"order_id": "U1", "customer": "Ali", "payment_status": "paid",
         "items": [{"product_id": "P001", "quantity": 1}]},
        {"order_id": "U2", "customer": "Bob", "payment_status": "paid",
         "items": [{"product_id": "UNKNOWN", "quantity": 1}]},   
        {"order_id": "U3", "payment_status": "paid",
         "items": [{"product_id": "P001", "quantity": 1}]},   
    ]
        processed = [process_order(o, products) for o in orders]
        self.assertEqual(get_unique_customers(processed), {"Ali"})


class TestDisplaySalesReport(unittest.TestCase):
    def test_display_sales_report_no_low_stock(self):
        report = {
            "total_orders": 0, "paid_orders": 0, "pending_orders": 0,
            "rejected_orders": 0, "total_revenue": 0, "total_discounts": 0,
            "shipping_collected": 0, "top_customer": [],
            "top_selling_product": [], "low_stock_products": {}
        }
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            display_sales_report(report)
        output = buf.getvalue()
        self.assertIn("None", output)

    def test_display_sales_report_with_low_stock(self):
        report = {
            "total_orders": 0, "paid_orders": 0, "pending_orders": 0,
            "rejected_orders": 0, "total_revenue": 0, "total_discounts": 0,
            "shipping_collected": 0, "top_customer": [],
            "top_selling_product": [], "low_stock_products": {"P003": "Keyboard"}
        }
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            display_sales_report(report)
        output = buf.getvalue()
        self.assertIn("Keyboard", output)
        lines_after_keyboard = output.split("Keyboard")[1]
        self.assertNotIn("None", lines_after_keyboard)

    def test_display_sales_report_runs_on_generated_report(self):
        products = {
            "P001": {"name": "Laptop", "price": 1200, "stock": 10},
        }
        order = {
            "order_id": "T10", "customer": "Test", "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}]
        }
        processed = [process_order(order, products)]
        report = generate_sales_report(processed, products)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            display_sales_report(report)
        self.assertIn("Test", buf.getvalue())


if __name__ == "__main__":
    unittest.main()