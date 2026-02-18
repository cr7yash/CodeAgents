"""Agent result model."""

from pydantic import BaseModel, Field

from src.models.finding import Finding


class AgentResult(BaseModel):
    """Result from a single agent's analysis."""

    agent_name: str
    findings: list[Finding] = Field(default_factory=list)
    summary: str = ""
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    error: str | None = None

    @property
    def findings_count(self) -> int:
        """Total number of findings."""
        return len(self.findings)

    @property
    def critical_count(self) -> int:
        """Number of critical findings."""
        return sum(1 for f in self.findings if f.severity.value == "critical")

    @property
    def high_count(self) -> int:
        """Number of high severity findings."""
        return sum(1 for f in self.findings if f.severity.value == "high")

    @property
    def medium_count(self) -> int:
        """Number of medium severity findings."""
        return sum(1 for f in self.findings if f.severity.value == "medium")

    @property
    def low_count(self) -> int:
        """Number of low severity findings."""
        return sum(1 for f in self.findings if f.severity.value == "low")

    @property
    def info_count(self) -> int:
        """Number of info findings."""
        return sum(1 for f in self.findings if f.severity.value == "info")

    def calculate_score(self) -> float:
        """Calculate a score out of 100 based on findings."""
        if not self.findings:
            return 100.0

        # Deduct points based on severity
        deductions = {
            "critical": 25,
            "high": 15,
            "medium": 8,
            "low": 3,
            "info": 1,
        }

        total_deduction = sum(
            deductions.get(f.severity.value, 0) for f in self.findings
        )

        return max(0.0, 100.0 - total_deduction)
