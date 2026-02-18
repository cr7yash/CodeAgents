"""Sample code with known security vulnerabilities for testing."""

import pickle
import subprocess
import yaml

# Hardcoded credentials - SECURITY ISSUE
API_KEY = "AKIA1234567890ABCDEF"
DATABASE_PASSWORD = "super_secret_password_123"
SECRET_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"


def get_user_unsafe(user_id):
    """SQL injection vulnerability - string concatenation."""
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)


def run_command_unsafe(user_input):
    """Command injection vulnerability."""
    subprocess.run("echo " + user_input, shell=True)


def load_data_unsafe(data):
    """Insecure deserialization with pickle."""
    return pickle.loads(data)


def load_yaml_unsafe(yaml_string):
    """Insecure YAML loading."""
    return yaml.load(yaml_string)


def execute_code_unsafe(code_string):
    """Dangerous eval usage."""
    return eval(code_string)


def exec_code_unsafe(code_string):
    """Dangerous exec usage."""
    exec(code_string)


def get_random_token():
    """Insecure random number generation for security purposes."""
    import random
    return random.randint(100000, 999999)


def read_file_unsafe(filename):
    """Path traversal vulnerability."""
    with open("/data/" + filename, "r") as f:
        return f.read()
