"""Sample code with high cyclomatic complexity for testing."""


def process_order(order, user, payment, shipping, discount_code, loyalty_points,
                  gift_wrap, expedited, insurance, signature_required):
    """God method with too many parameters and high complexity."""
    result = {"status": "pending", "total": 0, "messages": []}

    # Deep nesting - BAD
    if order:
        if order.items:
            for item in order.items:
                if item.available:
                    if item.quantity > 0:
                        if item.price > 0:
                            for i in range(item.quantity):
                                if user.is_premium:
                                    if discount_code:
                                        if discount_code.is_valid():
                                            if discount_code.applies_to(item):
                                                item.price *= 0.9
                                            else:
                                                result["messages"].append("Discount not applicable")
                                        else:
                                            result["messages"].append("Invalid discount")
                                    else:
                                        pass
                                else:
                                    pass
                            result["total"] += item.price * item.quantity
                        else:
                            result["messages"].append("Invalid price")
                    else:
                        result["messages"].append("Invalid quantity")
                else:
                    result["messages"].append("Item not available")
        else:
            result["messages"].append("No items in order")
    else:
        result["messages"].append("No order provided")

    # Magic numbers - BAD
    if result["total"] > 100:
        result["total"] *= 0.95
    if result["total"] > 500:
        result["total"] *= 0.9
    if result["total"] > 1000:
        result["total"] *= 0.85

    # Long method continues...
    if payment:
        if payment.type == "credit":
            if payment.card_number:
                if len(payment.card_number) == 16:
                    if payment.cvv:
                        if len(payment.cvv) == 3:
                            result["payment_status"] = "valid"
                        else:
                            result["payment_status"] = "invalid_cvv"
                    else:
                        result["payment_status"] = "missing_cvv"
                else:
                    result["payment_status"] = "invalid_card"
            else:
                result["payment_status"] = "missing_card"
        elif payment.type == "debit":
            result["payment_status"] = "debit_processing"
        elif payment.type == "paypal":
            result["payment_status"] = "paypal_redirect"
        elif payment.type == "crypto":
            result["payment_status"] = "crypto_processing"
        else:
            result["payment_status"] = "unknown_type"
    else:
        result["payment_status"] = "no_payment"

    return result


def calculate_something(a, b, c, d, e, f, g, h):
    """Too many parameters - code smell."""
    return a + b + c + d + e + f + g + h


class GodClass:
    """Class doing too many things - violates Single Responsibility."""

    def __init__(self):
        self.db = None
        self.cache = None
        self.logger = None
        self.email_service = None
        self.payment_processor = None
        self.notification_service = None

    def create_user(self, data):
        pass

    def update_user(self, user_id, data):
        pass

    def delete_user(self, user_id):
        pass

    def send_email(self, to, subject, body):
        pass

    def process_payment(self, amount, card):
        pass

    def generate_report(self, type, params):
        pass

    def export_data(self, format):
        pass

    def import_data(self, file):
        pass

    def backup_database(self):
        pass

    def send_notification(self, user_id, message):
        pass

    def log_activity(self, action, details):
        pass

    def validate_input(self, data, schema):
        pass
