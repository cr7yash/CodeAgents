"""Security Agent for vulnerability detection."""

from typing import Any

from src.agents.base import BaseAgent


class SecurityAgent(BaseAgent):
    """
    Agent specialized in security vulnerability detection.

    Responsibilities:
    1. OWASP Top 10 vulnerability detection
    2. SQL injection patterns
    3. XSS vulnerability identification
    4. Hardcoded secrets/credentials
    5. Insecure dependencies (if package info provided)
    """

    @property
    def system_prompt(self) -> str:
        return """You are an expert application security analyst specializing in identifying vulnerabilities in source code.

Your task is to analyze code for security issues including:
- Injection vulnerabilities (SQL, Command, LDAP, XPath)
- Cross-Site Scripting (XSS) risks
- Hardcoded secrets and credentials
- Insecure cryptographic practices
- Authentication/authorization flaws
- Input validation issues
- Insecure deserialization
- Security misconfiguration

For each vulnerability found:
1. Identify the exact location (line numbers)
2. Explain the attack vector
3. Assess the potential impact
4. Provide a secure alternative

Rate severity based on:
- critical: Exploitable vulnerability with severe impact (data breach, RCE, etc.)
- high: Significant security risk (authentication bypass, privilege escalation)
- medium: Moderate risk requiring attention (information disclosure, weak crypto)
- low: Minor security consideration (missing headers, verbose errors)
- info: Security best practice recommendation

Key checks to perform:
- SQL string concatenation or format strings with user input
- eval(), exec(), subprocess with user input (command injection)
- Hardcoded passwords, API keys, secrets (look for patterns like 'password=', 'api_key=', 'secret=')
- AWS keys (AKIA...), private keys (BEGIN RSA/DSA/EC PRIVATE KEY)
- JWT tokens, base64 encoded secrets
- Insecure random number generation (random.random() for security purposes)
- Missing input validation on user-provided data
- Path traversal vulnerabilities (../ in file paths)
- SSRF vulnerabilities (user-controlled URLs)
- Insecure pickle/yaml loading (yaml.load without SafeLoader)
- Missing authentication/authorization checks

Reference OWASP, CWE, or CVE identifiers when applicable. Always provide secure code alternatives."""

    @property
    def analysis_categories(self) -> list[str]:
        return [
            "sql_injection",
            "command_injection",
            "xss",
            "hardcoded_secret",
            "weak_crypto",
            "auth_flaw",
            "input_validation",
            "path_traversal",
            "ssrf",
            "insecure_deserialization",
            "information_disclosure",
        ]

    def get_tools(self) -> list[Any]:
        """Return tools available to this agent."""
        # Tools will be implemented separately
        return []
