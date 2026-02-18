"""Sample code with a mix of all issue types for testing."""

import os
import pickle

# Hardcoded secret - SECURITY
API_KEY = "sk_live_1234567890abcdef"


def process_user_data(user_id, db, options={}):  # Mutable default arg - QUALITY
    """Process user data.

    Missing parameter docs - DOCUMENTATION
    """
    # SQL injection - SECURITY
    query = f"SELECT * FROM users WHERE id = {user_id}"
    user = db.execute(query)

    if user:
        # Deep nesting - QUALITY
        if user.active:
            if user.verified:
                if options.get("include_orders"):
                    # N+1 query - PERFORMANCE
                    orders = []
                    for order_id in user.order_ids:
                        order = db.execute(f"SELECT * FROM orders WHERE id = {order_id}")
                        orders.append(order)

                    # String concat in loop - PERFORMANCE
                    summary = ""
                    for order in orders:
                        summary = summary + str(order.total) + ","

                    return {"user": user, "orders": orders, "summary": summary}

    return None


class DataManager:
    """Manages data operations."""

    def __init__(self):
        # Magic number - QUALITY
        self.max_retries = 3
        self.timeout = 30
        self.batch_size = 100

    def load_unsafe(self, data):
        # Insecure deserialization - SECURITY
        return pickle.loads(data)

    def search_items(self, items, query):
        # O(n) when could be O(1) - PERFORMANCE
        for item in items:
            if item["id"] == query:
                return item
        return None

    def find_duplicates(self, items):
        # O(n²) algorithm - PERFORMANCE
        duplicates = []
        for i in range(len(items)):
            for j in range(len(items)):
                if i != j and items[i] == items[j]:
                    if items[i] not in duplicates:
                        duplicates.append(items[i])
        return duplicates


def calculate(a, b, c, d, e, f):  # Too many params - QUALITY
    # Missing docstring - DOCUMENTATION
    result = a + b * c - d / e + f
    return result * 1.5  # Magic number - QUALITY


def run_command(cmd):
    # Command injection - SECURITY
    os.system(cmd)


# Star import warning - would be flagged
# from module import *

def long_function():
    """This function is way too long."""
    x = 1
    y = 2
    z = 3
    a = x + y
    b = y + z
    c = a + b
    d = b + c
    e = c + d
    f = d + e
    g = e + f
    h = f + g
    i = g + h
    j = h + i
    k = i + j
    l = j + k
    m = k + l
    n = l + m
    o = m + n
    p = n + o
    q = o + p
    r = p + q
    s = q + r
    t = r + s
    return t
