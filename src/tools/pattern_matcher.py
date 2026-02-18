"""Pattern matcher for detecting anti-patterns and code issues."""

import re
from dataclasses import dataclass
from typing import Callable


@dataclass
class PatternMatch:
    """A matched anti-pattern in code."""

    pattern_name: str
    description: str
    line_number: int
    line_content: str
    severity: str
    suggestion: str


class PatternMatcher:
    """
    Match code against known anti-patterns.

    Supports language-specific patterns for Python and JavaScript.
    """

    def __init__(self, language: str):
        self.language = language.lower()
        self.patterns = self._get_patterns_for_language()

    def _get_patterns_for_language(self) -> list[dict]:
        """Get patterns for the current language."""
        if self.language == "python":
            return self._python_patterns()
        elif self.language in ("javascript", "typescript"):
            return self._javascript_patterns()
        return []

    def _python_patterns(self) -> list[dict]:
        """Python-specific anti-patterns."""
        return [
            {
                "name": "bare_except",
                "pattern": re.compile(r"^\s*except\s*:\s*$"),
                "description": "Bare except clause catches all exceptions including KeyboardInterrupt",
                "severity": "medium",
                "suggestion": "Use 'except Exception:' or catch specific exceptions",
            },
            {
                "name": "mutable_default_arg",
                "pattern": re.compile(r"def\s+\w+\([^)]*=\s*(\[\]|\{\}|\set\(\))"),
                "description": "Mutable default argument can cause unexpected behavior",
                "severity": "high",
                "suggestion": "Use None as default and initialize inside function",
            },
            {
                "name": "eval_usage",
                "pattern": re.compile(r"\beval\s*\("),
                "description": "eval() is dangerous and can execute arbitrary code",
                "severity": "critical",
                "suggestion": "Use ast.literal_eval() for data or avoid eval entirely",
            },
            {
                "name": "exec_usage",
                "pattern": re.compile(r"\bexec\s*\("),
                "description": "exec() is dangerous and can execute arbitrary code",
                "severity": "critical",
                "suggestion": "Avoid exec() - find alternative approaches",
            },
            {
                "name": "hardcoded_password",
                "pattern": re.compile(r'password\s*=\s*["\'][^"\']+["\']', re.I),
                "description": "Hardcoded password detected",
                "severity": "critical",
                "suggestion": "Use environment variables or secure vault",
            },
            {
                "name": "star_import",
                "pattern": re.compile(r"from\s+\w+\s+import\s+\*"),
                "description": "Star import pollutes namespace and hides dependencies",
                "severity": "low",
                "suggestion": "Import specific names or use module prefix",
            },
            {
                "name": "assert_usage",
                "pattern": re.compile(r"^\s*assert\s+(?!.*#.*test)", re.I),
                "description": "assert statements are removed with -O flag",
                "severity": "low",
                "suggestion": "Use explicit if/raise for non-test assertions",
            },
            {
                "name": "global_usage",
                "pattern": re.compile(r"^\s*global\s+\w+"),
                "description": "Global variable usage makes code harder to test and reason about",
                "severity": "medium",
                "suggestion": "Pass values as parameters or use class attributes",
            },
            {
                "name": "string_format_sql",
                "pattern": re.compile(r'(?:execute|query)\s*\(\s*["\'].*%[sd]', re.I),
                "description": "Potential SQL injection via string formatting",
                "severity": "critical",
                "suggestion": "Use parameterized queries",
            },
            {
                "name": "pickle_load",
                "pattern": re.compile(r"pickle\.loads?\s*\("),
                "description": "pickle.load is unsafe with untrusted data",
                "severity": "high",
                "suggestion": "Use JSON or other safe serialization formats",
            },
            {
                "name": "yaml_unsafe_load",
                "pattern": re.compile(r"yaml\.load\s*\([^)]*\)(?!\s*,\s*Loader\s*=\s*yaml\.SafeLoader)"),
                "description": "yaml.load without SafeLoader is vulnerable to code execution",
                "severity": "critical",
                "suggestion": "Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader)",
            },
            {
                "name": "subprocess_shell",
                "pattern": re.compile(r"subprocess\.\w+\([^)]*shell\s*=\s*True"),
                "description": "shell=True is vulnerable to command injection",
                "severity": "high",
                "suggestion": "Use shell=False and pass arguments as list",
            },
            {
                "name": "md5_usage",
                "pattern": re.compile(r"(?:hashlib\.)?md5\s*\("),
                "description": "MD5 is cryptographically weak",
                "severity": "medium",
                "suggestion": "Use SHA-256 or stronger for security purposes",
            },
            {
                "name": "sha1_usage",
                "pattern": re.compile(r"(?:hashlib\.)?sha1\s*\("),
                "description": "SHA-1 is cryptographically weak",
                "severity": "low",
                "suggestion": "Use SHA-256 or stronger for security purposes",
            },
            {
                "name": "insecure_random",
                "pattern": re.compile(r"\brandom\.(?:random|randint|choice)\s*\("),
                "description": "random module is not cryptographically secure",
                "severity": "info",
                "suggestion": "Use secrets module for security-sensitive randomness",
            },
        ]

    def _javascript_patterns(self) -> list[dict]:
        """JavaScript/TypeScript-specific anti-patterns."""
        return [
            {
                "name": "eval_usage",
                "pattern": re.compile(r"\beval\s*\("),
                "description": "eval() is dangerous and can execute arbitrary code",
                "severity": "critical",
                "suggestion": "Use JSON.parse() for data or find alternative approaches",
            },
            {
                "name": "innerhtml_xss",
                "pattern": re.compile(r"\.innerHTML\s*="),
                "description": "innerHTML assignment can lead to XSS",
                "severity": "high",
                "suggestion": "Use textContent or sanitize input",
            },
            {
                "name": "document_write",
                "pattern": re.compile(r"document\.write\s*\("),
                "description": "document.write can be exploited for XSS",
                "severity": "medium",
                "suggestion": "Use DOM manipulation methods instead",
            },
            {
                "name": "var_declaration",
                "pattern": re.compile(r"^\s*var\s+\w+"),
                "description": "var has function scope, can lead to bugs",
                "severity": "low",
                "suggestion": "Use const or let for block scoping",
            },
            {
                "name": "console_log",
                "pattern": re.compile(r"console\.log\s*\("),
                "description": "console.log should be removed in production",
                "severity": "info",
                "suggestion": "Remove or use proper logging framework",
            },
            {
                "name": "hardcoded_url",
                "pattern": re.compile(r'(?:http|https)://(?:localhost|127\.0\.0\.1)'),
                "description": "Hardcoded localhost URL",
                "severity": "low",
                "suggestion": "Use environment variables for URLs",
            },
            {
                "name": "sql_concat",
                "pattern": re.compile(r'(?:query|execute|sql)\s*[\(=].*\+.*(?:req\.|params\.|input)', re.I),
                "description": "Potential SQL injection via string concatenation",
                "severity": "critical",
                "suggestion": "Use parameterized queries",
            },
            {
                "name": "password_in_code",
                "pattern": re.compile(r'password\s*[:=]\s*["\'][^"\']+["\']', re.I),
                "description": "Hardcoded password detected",
                "severity": "critical",
                "suggestion": "Use environment variables",
            },
            {
                "name": "new_function",
                "pattern": re.compile(r"new\s+Function\s*\("),
                "description": "new Function() is similar to eval() and unsafe",
                "severity": "critical",
                "suggestion": "Use regular function definitions",
            },
            {
                "name": "setTimeout_string",
                "pattern": re.compile(r"setTimeout\s*\(\s*[\"']"),
                "description": "setTimeout with string argument acts like eval",
                "severity": "high",
                "suggestion": "Pass a function reference instead of string",
            },
        ]

    def match(self, code: str) -> list[PatternMatch]:
        """
        Match code against all patterns.

        Args:
            code: Source code to analyze

        Returns:
            List of PatternMatch objects
        """
        matches: list[PatternMatch] = []
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            for pattern_def in self.patterns:
                if pattern_def["pattern"].search(line):
                    matches.append(
                        PatternMatch(
                            pattern_name=pattern_def["name"],
                            description=pattern_def["description"],
                            line_number=line_num,
                            line_content=line.strip(),
                            severity=pattern_def["severity"],
                            suggestion=pattern_def["suggestion"],
                        )
                    )

        return matches

    def match_custom(
        self,
        code: str,
        pattern: re.Pattern,
        name: str,
        description: str,
        severity: str,
        suggestion: str,
    ) -> list[PatternMatch]:
        """Match code against a custom pattern."""
        matches: list[PatternMatch] = []
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            if pattern.search(line):
                matches.append(
                    PatternMatch(
                        pattern_name=name,
                        description=description,
                        line_number=line_num,
                        line_content=line.strip(),
                        severity=severity,
                        suggestion=suggestion,
                    )
                )

        return matches

    def get_severity_counts(self, matches: list[PatternMatch]) -> dict[str, int]:
        """Get count of matches by severity."""
        counts: dict[str, int] = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

        for match in matches:
            if match.severity in counts:
                counts[match.severity] += 1

        return counts
