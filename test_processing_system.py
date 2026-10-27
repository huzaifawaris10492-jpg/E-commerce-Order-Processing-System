import io
import contextlib
import unittest
from decimal import Decimal
from order_processing_system import (
    calculate_discount,
    calculate_shipping,
    calculate_total,
    validate_order,
    calculate_order_subtotal,
    generate_product_report,
    process_order,
    mark_paid,
    generate_sales_report,
    generate_customer_report,
    display_sales_report,
    get_unique_customers,
    validate_products,
)

class TestPricingCalculations(unittest.TestCase):
    def test_discount(self):
        self.assertEqual(calculate_discount(100), 0)
        self.assertEqual(calculate_discount(200), 10)
        self.assertEqual(calculate_discount(500), 50)
        self.assertEqual(calculate_discount(1000), 150)

    def test_shipping(self):
        self.assertEqual(calculate_shipping(500), 0)
        self.assertEqual(calculate_shipping(499), 20)

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
        products = {"p102": {"name": "mouse", "price": 20, "stock": 5}}

        order = {
            "order_id": "T1",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "p102", "quantity": 0}],
        }
        self.assertFalse(validate_order(order, products)[0])

    def test_missing_items(self):
        self.assertFalse(
            validate_order(
                {"order_id": "T2", "customer": "Test", "payment_status": "paid"}, {}
            )[0]
        )

    def test_missing_product_id(self):
        products = {"P001": {"price": 100, "stock": 5}}
        order = {
            "order_id": "T3",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"quantity": 1}],
        }
        self.assertFalse(validate_order(order, products)[0])

    def test_invalid_quantity(self):
        products = {"P001": {"price": 100, "stock": 5}}
        order = {
            "order_id": "T4",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": -1}],
        }
        self.assertFalse(validate_order(order, products)[0])

    def test_validate_order_sums_quantity_across_lines(self):
        products = {"P001": {"name": "Laptop", "price": 1200, "stock": 10}}
        order = {
            "order_id": "T5",
            "customer": "Test",
            "payment_status": "paid",
            "items": [
                {"product_id": "P001", "quantity": 10},
                {"product_id": "P001", "quantity": 10},
            ],
        }
        self.assertFalse(validate_order(order, products)[0])

    def test_validate_order_rejects_negative_price(self):
        products = {"P001": {"name": "Test", "price": -50, "stock": 5}}
        order = {
            "order_id": "T6",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        self.assertFalse(validate_order(order, products)[0])

    def test_validate_order_rejects_blank_order_id(self):
        products = {"P001": {"name": "Test", "price": 10, "stock": 5}}
        order = {
            "order_id": "   ",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        is_valid, reason = validate_order(order, products)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "missing order_id")

    def test_validate_order_rejects_blank_customer(self):
        products = {"P001": {"name": "Test", "price": 10, "stock": 5}}
        order = {
            "order_id": "T6b",
            "customer": "   ",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        is_valid, reason = validate_order(order, products)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "missing customer")

    def test_validate_order_rejects_insufficient_stock(self):
        products = {"P001": {"name": "Test", "price": 10, "stock": 2}}
        order = {
            "order_id": "T6c",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 5}],
        }
        is_valid, reason = validate_order(order, products)
        self.assertFalse(is_valid)
        self.assertEqual(reason, "insufficient stock for P001")

class TestProcessOrder(unittest.TestCase):
    def test_process_order_deducts_stock(self):
        products = {"P001": {"name": "Laptop", "price": 1200, "stock": 10}}
        order = {
            "order_id": "T7",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 3}],
        }
        result = process_order(order, products)
        self.assertEqual(result["payment_status"], "paid")
        self.assertEqual(products["P001"]["stock"], 7)

    def test_process_order_pending_reserves_stock(self):
        products = {"P001": {"name": "Laptop", "price": 1200, "stock": 10}}
        order = {
            "order_id": "P1",
            "customer": "Test",
            "payment_status": "pending",
            "items": [{"product_id": "P001", "quantity": 3}],
        }
        result = process_order(order, products)
        self.assertEqual(result["payment_status"], "pending")
        self.assertEqual(products["P001"]["stock"], 7)

    def test_process_order_rejects_duplicate(self):
        products = {"P001": {"name": "Laptop", "price": 1200, "stock": 10}}
        order = {
            "order_id": "T8",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        processed_ids = set()
        first = process_order(order, products, processed_order_ids=processed_ids)
        second = process_order(order, products, processed_order_ids=processed_ids)
        self.assertEqual(first["payment_status"], "paid")
        self.assertEqual(second["outcome"], "rejected")
        self.assertEqual(second["reason"], "order already processed")

    def test_process_order_rejects_unknown_option(self):
        products = {"P001": {"name": "Laptop", "price": 1200, "stock": 10}}
        order = {
            "order_id": "T8b",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        result = process_order(order, products, apply_discout=False)
        self.assertEqual(result["outcome"], "rejected")
        self.assertIn("unknown option", result["reason"])
        self.assertEqual(products["P001"]["stock"], 10)

    def test_process_order_apply_discount_false(self):
        products = {"P001": {"name": "Laptop", "price": 1200, "stock": 10}}
        order = {
            "order_id": "T8c",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        result = process_order(order, products, apply_discount=False)
        self.assertEqual(result["discount"], 0)
        self.assertEqual(result["total"], result["subtotal"] + result["shipping"])

    def test_process_order_result_does_not_share_items(self):
        products = {"P001": {"name": "Laptop", "price": 10, "stock": 10}}
        order = {
            "order_id": "S1",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        result = process_order(order, products)
        result["items"].append({"product_id": "P001", "quantity": 99})
        result["items"][0]["quantity"] = 50
        self.assertEqual(order["items"], [{"product_id": "P001", "quantity": 1}])

    def test_second_pending_order_cannot_oversell(self):
        products = {"P001": {"name": "Laptop", "price": 1200, "stock": 10}}
        ids = set()
        first = {
            "order_id": "A",
            "customer": "Test",
            "payment_status": "pending",
            "items": [{"product_id": "P001", "quantity": 10}],
        }
        second = dict(first, order_id="B")
        a = process_order(first, products, ids)
        b = process_order(second, products, ids)
        self.assertEqual(a["outcome"], "accepted")
        self.assertEqual(b["outcome"], "rejected")
        self.assertEqual(b["reason"], "insufficient stock for P001")

    def test_shipping_uses_pre_discount_subtotal(self):
        products = {"P001": {"name": "Chair", "price": 520, "stock": 10}}
        order = {
            "order_id": "SH1",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        r = process_order(order, products)
        self.assertEqual(r["subtotal"], Decimal("520.00"))
        self.assertEqual(r["discount"], Decimal("52.00"))
        self.assertEqual(r["shipping"], 0)
        self.assertEqual(r["total"], Decimal("468.00"))
class TestMarkPaid(unittest.TestCase):
    def setUp(self):
        self.products = {
            "P001": {"name": "Laptop", "price": 1200, "stock": 10},
        }

    def make_pending(self, order_id="ORD1"):
        return {
            "order_id": order_id,
            "customer": "Ali",
            "payment_status": "pending",
            "items": [{"product_id": "P001", "quantity": 1}],
        }

    def test_mark_paid_transitions_pending_to_paid(self):
        order = self.make_pending()
        processed = [process_order(order, self.products)]
        self.assertEqual(processed[0]["payment_status"], "pending")
        updated, error = mark_paid("ORD1", processed)
        self.assertEqual(error, "")
        self.assertIsNotNone(updated)
        self.assertEqual(updated["payment_status"], "paid")

    def test_mark_paid_is_case_and_whitespace_insensitive(self):
        order = self.make_pending()
        processed = [process_order(order, self.products)]
        updated, error = mark_paid(" ord1 ", processed)
        self.assertEqual(error, "")
        self.assertIsNotNone(updated)
        self.assertEqual(updated["payment_status"], "paid")

    def test_mark_paid_rejects_already_paid_order(self):
        order = dict(self.make_pending(), payment_status="paid")
        processed = [process_order(order, self.products)]
        self.assertEqual(processed[0]["payment_status"], "paid")
        updated, error = mark_paid("ORD1", processed)
        self.assertIsNone(updated)
        self.assertEqual(error, "order already paid")

    def test_mark_paid_rejects_unknown_order_id(self):
        processed = [process_order(self.make_pending(), self.products)]
        updated, error = mark_paid("NOPE", processed)
        self.assertIsNone(updated)
        self.assertEqual(error, "order not found")

    def test_mark_paid_rejects_rejected_order(self):
        bad_order = {
            "order_id": "ORD2",
            "customer": "Ali",
            "payment_status": "paid",
            "items": [],
        }
        processed = [process_order(bad_order, self.products)]
        self.assertEqual(processed[0]["outcome"], "rejected")
        updated, error = mark_paid("ORD2", processed)
        self.assertIsNone(updated)
        self.assertEqual(error, "order not found")

    def test_mark_paid_finds_accepted_order_after_same_id_was_rejected(self):
        rejected_order = {
            "order_id": "ORD9",
            "customer": "Ali",
            "payment_status": "pending",
            "items": [{"product_id": "P001", "quantity": 50}],
        }
        accepted_order = {
            "order_id": "ORD9",
            "customer": "Ali",
            "payment_status": "pending",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        ids = set()
        first = process_order(rejected_order, self.products, ids)
        second = process_order(accepted_order, self.products, ids)
        self.assertEqual(first["outcome"], "rejected")
        self.assertEqual(second["outcome"], "accepted")
        processed = [first, second]
        updated, error = mark_paid("ORD9", processed)
        self.assertEqual(error, "")
        self.assertEqual(updated["payment_status"], "paid")

    def test_mark_paid_does_not_change_stock(self):
        processed = [process_order(self.make_pending(), self.products)]
        self.assertEqual(self.products["P001"]["stock"], 9)
        mark_paid("ORD1", processed)
        self.assertEqual(self.products["P001"]["stock"], 9)

class TestReports(unittest.TestCase):
    def test_revenue_matches_customer_spending(self):
        products = {
            "P001": {"name": "Laptop", "price": 1200, "stock": 10},
            "P002": {"name": "Mouse", "price": 25, "stock": 50},
        }
        order = {
            "order_id": "T9",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P002", "quantity": 1}],
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
            "order_id": "TA1",
            "customer": "Ali",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        order_b = {
            "order_id": "TB1",
            "customer": "Zed",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        processed = [
            process_order(
                order_a, products, apply_discount=False, include_shipping=False
            ),
            process_order(
                order_b, products, apply_discount=False, include_shipping=False
            ),
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
            "order_id": "PA1",
            "customer": "Ali",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        order_b = {
            "order_id": "PB1",
            "customer": "Zed",
            "payment_status": "paid",
            "items": [{"product_id": "P002", "quantity": 1}],
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
        products = {"P001": {"name": "Laptop", "price": 1200, "stock": 10}}
        order = {
            "order_id": "R1",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        processed_ids = set()
        first = process_order(order, products, processed_order_ids=processed_ids)
        second = process_order(order, products, processed_order_ids=processed_ids)
        report = generate_sales_report([first, second], products)
        self.assertEqual(report["rejected_orders"], 1)
        self.assertEqual(report["paid_orders"], 1)

    def test_generate_sales_report_handles_empty_orders(self):
        products = {"P001": {"name": "Laptop", "price": 1200, "stock": 10}}
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
            {
                "order_id": "U1",
                "customer": "Ali",
                "payment_status": "paid",
                "items": [{"product_id": "P001", "quantity": 1}],
            },
            {
                "order_id": "U2",
                "customer": "Bob",
                "payment_status": "paid",
                "items": [{"product_id": "UNKNOWN", "quantity": 1}],
            },
            {
                "order_id": "U3",
                "payment_status": "paid",
                "items": [{"product_id": "P001", "quantity": 1}],
            },
        ]
        processed = [process_order(o, products) for o in orders]
        self.assertEqual(get_unique_customers(processed), {"Ali"})

class TestDisplaySalesReport(unittest.TestCase):
    def test_display_sales_report_no_low_stock(self):
        report = {
            "total_orders": 0,
            "paid_orders": 0,
            "pending_orders": 0,
            "rejected_orders": 0,
            "total_revenue": 0,
            "revenue_excl_shipping": 0,
            "total_discounts": 0,
            "shipping_collected": 0,
            "top_customer": [],
            "top_selling_product": [],
            "low_stock_products": {},
        }
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            display_sales_report(report)
        output = buf.getvalue()
        self.assertIn("None", output)

    def test_display_sales_report_with_low_stock(self):
        report = {
            "total_orders": 0,
            "paid_orders": 0,
            "pending_orders": 0,
            "rejected_orders": 0,
            "total_revenue": 0,
            "revenue_excl_shipping": 0,
            "total_discounts": 0,
            "shipping_collected": 0,
            "top_customer": [],
            "top_selling_product": [],
            "low_stock_products": {"P003": {"name": "Keyboard", "stock": 4}},
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
            "order_id": "T10",
            "customer": "Test",
            "payment_status": "paid",
            "items": [{"product_id": "P001", "quantity": 1}],
        }
        processed = [process_order(order, products)]
        report = generate_sales_report(processed, products)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            display_sales_report(report)
        self.assertIn("Test", buf.getvalue())

class TestEdgeCaseFixes(unittest.TestCase):
    def setUp(self):
        self.products = {
            "P002": {
                "name": "Mouse",
                "price": 25,
                "category": "Accessories",
                "stock": 50,
            }
        }
        self.order = {
            "order_id": "ORD1",
            "customer": "Ali",
            "items": [{"product_id": "P002", "quantity": 1}],
            "payment_status": "paid",
        }

    def test_nan_price_is_rejected_not_crashed(self):
        self.products["P002"]["price"] = float("nan")
        result = process_order(self.order, self.products, set())
        self.assertEqual(result["outcome"], "rejected")
        self.assertEqual(result["reason"], "invalid price for P002")

    def test_missing_order_id_after_order_named_unknown(self):
        ids = set()
        first = dict(self.order, order_id="Unknown")
        self.assertEqual(
            process_order(first, self.products, ids)["payment_status"], "paid"
        )
        no_id = {
            "customer": "Ali",
            "items": self.order["items"],
            "payment_status": "paid",
        }
        result = process_order(no_id, self.products, ids)
        self.assertEqual(result["outcome"], "rejected")
        self.assertEqual(result["reason"], "missing order_id")

    def test_product_report_handles_missing_name(self):
        del self.products["P002"]["name"]
        result = process_order(self.order, self.products, set())
        report = generate_product_report([result], self.products)
        self.assertEqual(report["P002"]["name"], "P002")

    def test_product_report_survives_deleted_product(self):
        result = process_order(self.order, self.products, set())
        del self.products["P002"]
        report = generate_product_report([result], self.products)
        self.assertEqual(report, {"P002": {"name": "Mouse", "units_sold": 1}})
        sales = generate_sales_report([result], self.products)
        self.assertEqual(sales["top_selling_product"], ["Mouse"])

class TestRecentFixes(unittest.TestCase):
    def setUp(self):
        self.products = {
            "P002": {
                "name": "Mouse",
                "price": 25,
                "category": "Accessories",
                "stock": 50,
            }
        }

    def make(self, order_id="ORD1", customer="Ali", qty=1):
        return {
            "order_id": order_id,
            "customer": customer,
            "items": [{"product_id": "P002", "quantity": qty}],
            "payment_status": "paid",
        }

    def test_non_bool_option_is_rejected(self):
        r = process_order(self.make(), self.products, set(), apply_discount="no")
        self.assertEqual(
            (r["outcome"], r["reason"]), ("rejected", "apply_discount must be a bool")
        )
        self.assertEqual(self.products["P002"]["stock"], 50)

    def test_unknown_option_reported_before_validation_error(self):
        bad = {
            "order_id": "X",
            "customer": "Ali",
            "items": [],
            "payment_status": "paid",
        }
        r = process_order(bad, self.products, set(), apply_discout=True)
        self.assertEqual(r["reason"], "unknown option(s): apply_discout")

    def test_order_id_whitespace_and_case_are_duplicates(self):
        ids = set()
        self.assertEqual(
            process_order(self.make("ORD1"), self.products, ids)["payment_status"],
            "paid",
        )
        for dup in ("ORD1 ", "ord1"):
            r = process_order(self.make(dup), self.products, ids)
            self.assertEqual(r["reason"], "order already processed")
        self.assertEqual(self.products["P002"]["stock"], 49)

    def test_customer_names_group_ignoring_case_and_spaces(self):
        ids = set()
        results = [
            process_order(self.make(f"O{i}", c), self.products, ids)
            for i, c in enumerate(["Ali", "Ali ", "ali"])
        ]
        self.assertEqual(get_unique_customers(results), {"Ali"})
        self.assertEqual(list(generate_customer_report(results)), ["Ali"])

    def test_customer_name_keeps_original_capitalisation(self):
        r = process_order(self.make(customer=" McDonald "), self.products, set())
        self.assertEqual(r["customer"], "McDonald")

    def test_money_uses_decimal_rounding(self):
        self.products["P002"]["price"] = 0.1
        r = process_order(self.make(qty=3), self.products, set())
        self.assertEqual(r["subtotal"], Decimal("0.30"))
        self.products["P002"]["price"] = 0.333
        r = process_order(self.make("ORD2"), self.products, set())
        self.assertEqual(r["subtotal"], Decimal("0.33"))

    def test_customer_first_spelling_is_kept(self):
        ids = set()
        results = [
            process_order(self.make(f"O{i}", c), self.products, ids)
            for i, c in enumerate(["mcDonald", "McDonald ", "MCDONALD"])
        ]
        self.assertEqual(list(generate_customer_report(results)), ["mcDonald"])
        self.assertEqual(get_unique_customers(results), {"mcDonald"})

class TestValidateProducts(unittest.TestCase):
    def test_rejects_product_without_category(self):
        products = {"P1": {"name": "Mouse", "price": 25, "stock": 5}}
        with self.assertRaises(ValueError):
            validate_products(products)

if __name__ == "__main__":
    unittest.main()