import os
import subprocess
from datetime import datetime

def process_user_data(user_id, password):
    """Process user information"""
    # Hardcoded database credentials
    db_password = "admin123"
    db_user = "root"
    
    # SQL Injection vulnerability
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    result = subprocess.check_output("mysql -u " + db_user + " -p" + db_password + " -e '" + query + "'", shell=True)
    
    return result

def calculate_fibonacci(n):
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def validate_email(email):
    import re
    if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        return True
    return False

class DataProcessor:
    def __init__(self):
        self.data = []
        self.cache = {}
        self.temp_files = []
        self.api_key = "sk-1234567890abcdefghijklmnop"
    
    def process(self, items):
        # O(n²) inefficient nested loop
        for i in range(len(items)):
            for j in range(len(items)):
                if items[i] == items[j]:
                    self.data.append(items[i])
        
        return self.data
    
    def fetch_data(self, url):
        # Missing type hints
        os.system("curl " + url)
    
    def long_method(self, a, b, c, d, e):
        x = a + b
        y = c * d
        z = x + y
        if z > 100:
            if x > 50:
                if y > 50:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

def dangerous_eval(user_input):
    # Using eval with user input
    result = eval(user_input)
    return result

def load_config(filename):
    f = open(filename, 'r')
    content = f.read()
    return content

global_state = {}

def update_global(key, value):
    global global_state
    global_state[key] = value