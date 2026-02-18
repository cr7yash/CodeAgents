"""Tests for analysis tools."""

import pytest

from src.tools.secret_scanner import SecretScanner
from src.tools.complexity import ComplexityCalculator
from src.tools.pattern_matcher import PatternMatcher


class TestSecretScanner:
    """Tests for SecretScanner."""

    def test_detect_aws_key(self):
        """Test detection of AWS access key."""
        scanner = SecretScanner()
        code = 'AWS_KEY = "AKIA1234567890ABCDEF"'

        findings = scanner.scan(code)

        assert len(findings) == 1
        assert findings[0].secret_type == "aws_access_key"
        assert findings[0].confidence == "high"

    def test_detect_password(self):
        """Test detection of hardcoded password."""
        scanner = SecretScanner()
        code = 'password = "super_secret_123"'

        findings = scanner.scan(code)

        assert len(findings) == 1
        assert findings[0].secret_type == "password"

    def test_detect_jwt(self):
        """Test detection of JWT token."""
        scanner = SecretScanner()
        code = 'token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"'

        findings = scanner.scan(code)

        assert len(findings) == 1
        assert findings[0].secret_type == "jwt_token"

    def test_exclude_env_variables(self):
        """Test that environment variable patterns are excluded."""
        scanner = SecretScanner()
        code = 'password = os.environ.get("PASSWORD")'

        findings = scanner.scan(code)

        assert len(findings) == 0

    def test_exclude_placeholders(self):
        """Test that placeholder values are excluded."""
        scanner = SecretScanner()
        code = 'password = "your_password_here"'

        findings = scanner.scan(code)

        assert len(findings) == 0

    def test_mask_secret(self):
        """Test secret masking."""
        scanner = SecretScanner()

        masked = scanner._mask_secret("AKIA1234567890ABCDEF")
        assert masked.startswith("AKIA")
        assert "*" in masked
        assert len(masked) == len("AKIA1234567890ABCDEF")


class TestComplexityCalculator:
    """Tests for ComplexityCalculator."""

    def test_simple_function(self):
        """Test complexity of simple function."""
        calc = ComplexityCalculator("python")
        code = """
def hello():
    print("hello")
"""
        complexity = calc.calculate(code)
        assert complexity == 1  # Base complexity only

    def test_function_with_if(self):
        """Test complexity with if statement."""
        calc = ComplexityCalculator("python")
        code = """
def check(x):
    if x > 0:
        return True
    return False
"""
        complexity = calc.calculate(code)
        assert complexity == 2  # 1 base + 1 if

    def test_function_with_loops(self):
        """Test complexity with loops."""
        calc = ComplexityCalculator("python")
        code = """
def process(items):
    for item in items:
        while item.active:
            item.process()
"""
        complexity = calc.calculate(code)
        assert complexity == 3  # 1 base + 1 for + 1 while

    def test_complex_function(self):
        """Test high complexity function."""
        calc = ComplexityCalculator("python")
        code = """
def complex(x, y, z):
    if x > 0:
        if y > 0:
            for i in range(z):
                if i % 2 == 0:
                    continue
                elif i % 3 == 0:
                    break
    elif x < 0:
        while y > 0:
            y -= 1
"""
        complexity = calc.calculate(code)
        assert complexity > 5

    def test_is_complex_flag(self):
        """Test is_complex threshold."""
        calc = ComplexityCalculator("python", threshold=5)
        code = """
def simple():
    if True:
        pass
"""
        results = calc.calculate_per_function(code)
        # Should find the function and it should not be flagged as complex
        if results:
            assert not results[0].is_complex

    def test_file_complexity(self):
        """Test file-level complexity metrics."""
        calc = ComplexityCalculator("python")
        code = """
def func1():
    if True:
        pass

def func2():
    for i in range(10):
        if i > 5:
            print(i)
"""
        metrics = calc.get_file_complexity(code)

        assert metrics["total_functions"] >= 1
        assert metrics["average_complexity"] > 0


class TestPatternMatcher:
    """Tests for PatternMatcher."""

    def test_detect_eval(self):
        """Test detection of eval usage."""
        matcher = PatternMatcher("python")
        code = 'result = eval(user_input)'

        matches = matcher.match(code)

        assert len(matches) == 1
        assert matches[0].pattern_name == "eval_usage"
        assert matches[0].severity == "critical"

    def test_detect_exec(self):
        """Test detection of exec usage."""
        matcher = PatternMatcher("python")
        code = 'exec(code_string)'

        matches = matcher.match(code)

        assert len(matches) == 1
        assert matches[0].pattern_name == "exec_usage"

    def test_detect_mutable_default(self):
        """Test detection of mutable default argument."""
        matcher = PatternMatcher("python")
        code = 'def func(items=[]):'

        matches = matcher.match(code)

        assert len(matches) == 1
        assert matches[0].pattern_name == "mutable_default_arg"

    def test_detect_pickle(self):
        """Test detection of pickle.load."""
        matcher = PatternMatcher("python")
        code = 'data = pickle.loads(untrusted_data)'

        matches = matcher.match(code)

        assert len(matches) == 1
        assert matches[0].pattern_name == "pickle_load"

    def test_detect_yaml_unsafe(self):
        """Test detection of unsafe yaml.load."""
        matcher = PatternMatcher("python")
        code = 'data = yaml.load(yaml_string)'

        matches = matcher.match(code)

        assert len(matches) == 1
        assert matches[0].pattern_name == "yaml_unsafe_load"

    def test_javascript_eval(self):
        """Test JavaScript eval detection."""
        matcher = PatternMatcher("javascript")
        code = 'result = eval(userInput);'

        matches = matcher.match(code)

        assert len(matches) == 1
        assert matches[0].pattern_name == "eval_usage"

    def test_javascript_innerhtml(self):
        """Test innerHTML detection."""
        matcher = PatternMatcher("javascript")
        code = 'element.innerHTML = userContent;'

        matches = matcher.match(code)

        assert len(matches) == 1
        assert matches[0].pattern_name == "innerhtml_xss"

    def test_severity_counts(self):
        """Test severity counting."""
        matcher = PatternMatcher("python")
        code = """
eval(x)
exec(y)
def func(items=[]):
    pass
"""
        matches = matcher.match(code)
        counts = matcher.get_severity_counts(matches)

        assert counts["critical"] >= 2
        assert counts["high"] >= 1
