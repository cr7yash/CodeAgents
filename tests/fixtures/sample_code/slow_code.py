"""Sample code with performance issues for testing."""


def find_duplicates_slow(items):
    """O(n²) algorithm that could be O(n)."""
    duplicates = []
    for i, item in enumerate(items):
        for j, other in enumerate(items):
            if i != j and item == other and item not in duplicates:
                duplicates.append(item)
    return duplicates


def search_slow(data, query):
    """O(n) search that could use a set/dict for O(1)."""
    for item in data:
        if item["id"] == query:
            return item
    return None


def process_with_n_plus_one(users):
    """N+1 query pattern - fetches related data in loop."""
    results = []
    for user in users:
        # This would hit the database N times
        orders = db.query(f"SELECT * FROM orders WHERE user_id = {user.id}")
        user_data = {
            "user": user,
            "orders": orders,
            "total_spent": sum(o.amount for o in orders),
        }
        results.append(user_data)
    return results


def inefficient_string_concat(items):
    """String concatenation in loop - should use join."""
    result = ""
    for item in items:
        result = result + str(item) + ", "
    return result


def repeated_computation(data):
    """Repeated expensive operation in loop."""
    results = []
    for item in data:
        # len(data) is called every iteration
        normalized = item / len(data)
        results.append(normalized)
    return results


def list_in_list_check(items, valid_items):
    """O(n*m) when it could be O(n) with a set."""
    filtered = []
    for item in items:
        if item in valid_items:  # O(m) lookup each time
            filtered.append(item)
    return filtered


def create_objects_in_loop(count):
    """Creating objects inside loop that could be reused."""
    results = []
    for i in range(count):
        config = {"setting1": "value1", "setting2": "value2"}  # Created each time
        processor = DataProcessor(config)  # New instance each time
        results.append(processor.process(i))
    return results


def sync_blocking_in_async():
    """Blocking call in what should be async context."""
    import time
    time.sleep(1)  # Blocks the event loop
    return "done"


def load_entire_file(filepath):
    """Loading entire file when streaming would be better."""
    with open(filepath, "r") as f:
        content = f.read()  # Loads entire file into memory

    lines = content.split("\n")
    results = []
    for line in lines:
        if "important" in line:
            results.append(line)
    return results


def nested_loops_cubic(matrix):
    """O(n³) nested loops."""
    n = len(matrix)
    result = 0
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result += matrix[i][j] * matrix[j][k]
    return result


def bubble_sort(arr):
    """Using bubble sort O(n²) when better algorithms exist."""
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
