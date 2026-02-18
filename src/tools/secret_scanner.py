"""Secret scanner for detecting hardcoded credentials."""

import re
from dataclasses import dataclass
from typing import Pattern


@dataclass
class SecretFinding:
    """A detected secret in code."""

    secret_type: str
    line_number: int
    line_content: str
    masked_value: str
    confidence: str  # "high", "medium", "low"


class SecretScanner:
    """
    Detect hardcoded secrets using regex patterns.

    Detects:
    - AWS keys
    - Generic API keys
    - Passwords
    - Private keys
    - JWT tokens
    - Generic secrets
    - Database connection strings
    """

    # Secret patterns with their types and confidence
    SECRET_PATTERNS: list[tuple[str, Pattern[str], str]] = [
        # AWS Access Key ID
        ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}"), "high"),
        # AWS Secret Access Key (usually follows access key)
        (
            "aws_secret_key",
            re.compile(r'(?:aws_secret|aws_secret_key|secret_key)\s*[=:]\s*["\']?([A-Za-z0-9/+=]{40})["\']?', re.I),
            "high",
        ),
        # Generic API key patterns
        (
            "api_key",
            re.compile(r'(?:api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', re.I),
            "high",
        ),
        # Password assignments
        (
            "password",
            re.compile(r'(?:password|passwd|pwd)\s*[=:]\s*["\']([^"\']+)["\']', re.I),
            "high",
        ),
        # Private keys
        (
            "private_key",
            re.compile(r"-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY-----"),
            "high",
        ),
        # JWT tokens
        (
            "jwt_token",
            re.compile(r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*"),
            "high",
        ),
        # Generic secret patterns
        (
            "secret",
            re.compile(r'(?:secret|token)\s*[=:]\s*["\']([^"\']{8,})["\']', re.I),
            "medium",
        ),
        # Database URLs with credentials
        (
            "database_url",
            re.compile(r'(?:postgres|mysql|mongodb|redis)://\w+:[^@]+@', re.I),
            "high",
        ),
        # GitHub tokens
        (
            "github_token",
            re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"),
            "high",
        ),
        # Slack tokens
        (
            "slack_token",
            re.compile(r"xox[baprs]-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24}"),
            "high",
        ),
        # Google API keys
        (
            "google_api_key",
            re.compile(r"AIza[0-9A-Za-z_-]{35}"),
            "high",
        ),
        # Stripe keys
        (
            "stripe_key",
            re.compile(r"(?:sk|pk)_(?:test|live)_[0-9a-zA-Z]{24,}"),
            "high",
        ),
        # Bearer tokens
        (
            "bearer_token",
            re.compile(r'["\']Bearer\s+[a-zA-Z0-9_\-\.]+["\']', re.I),
            "medium",
        ),
        # Hardcoded IPs (internal)
        (
            "internal_ip",
            re.compile(r'["\'](?:10\.|172\.(?:1[6-9]|2[0-9]|3[01])\.|192\.168\.)\d+\.\d+["\']'),
            "low",
        ),
        # Basic auth in URLs
        (
            "basic_auth_url",
            re.compile(r"https?://[^:]+:[^@]+@"),
            "high",
        ),
    ]

    # Patterns to exclude (false positives)
    EXCLUSION_PATTERNS = [
        re.compile(r"password\s*[=:]\s*[\"']?\$\{"),  # Environment variable placeholder
        re.compile(r"password\s*[=:]\s*[\"']?<"),  # Placeholder like <password>
        re.compile(r"password\s*[=:]\s*[\"']?your[_-]?password", re.I),  # Example values
        re.compile(r"password\s*[=:]\s*[\"']?xxx+", re.I),  # Redacted
        re.compile(r"password\s*[=:]\s*[\"']?password", re.I),  # Default/example
        re.compile(r"[\"']?placeholder[\"']?", re.I),  # Placeholder
        re.compile(r"process\.env\.", re.I),  # Environment variables
        re.compile(r"os\.environ", re.I),  # Python env vars
        re.compile(r"getenv\(", re.I),  # Getting env vars
    ]

    def __init__(self):
        pass

    def scan(self, code: str) -> list[SecretFinding]:
        """
        Scan code for potential secrets.

        Args:
            code: Source code to scan

        Returns:
            List of SecretFinding objects
        """
        findings: list[SecretFinding] = []
        lines = code.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Skip if line matches exclusion patterns
            if self._is_excluded(line):
                continue

            # Check each secret pattern
            for secret_type, pattern, confidence in self.SECRET_PATTERNS:
                match = pattern.search(line)
                if match:
                    # Get the matched value
                    matched_text = match.group(0)

                    # Create masked version
                    masked = self._mask_secret(matched_text)

                    findings.append(
                        SecretFinding(
                            secret_type=secret_type,
                            line_number=line_num,
                            line_content=line.strip(),
                            masked_value=masked,
                            confidence=confidence,
                        )
                    )
                    # Only one finding per line per type
                    break

        return findings

    def _is_excluded(self, line: str) -> bool:
        """Check if line should be excluded (likely false positive)."""
        for pattern in self.EXCLUSION_PATTERNS:
            if pattern.search(line):
                return True
        return False

    def _mask_secret(self, secret: str) -> str:
        """Mask a secret value for safe display."""
        if len(secret) <= 8:
            return "*" * len(secret)

        # Show first 4 and last 4 characters
        return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"

    def scan_file(self, file_path: str) -> list[SecretFinding]:
        """
        Scan a file for potential secrets.

        Args:
            file_path: Path to file to scan

        Returns:
            List of SecretFinding objects
        """
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        return self.scan(code)

    def get_summary(self, findings: list[SecretFinding]) -> dict:
        """
        Get a summary of findings.

        Returns:
            Dict with counts by type and confidence
        """
        by_type: dict[str, int] = {}
        by_confidence: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

        for finding in findings:
            by_type[finding.secret_type] = by_type.get(finding.secret_type, 0) + 1
            by_confidence[finding.confidence] += 1

        return {
            "total": len(findings),
            "by_type": by_type,
            "by_confidence": by_confidence,
            "high_confidence_count": by_confidence["high"],
        }
