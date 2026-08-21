"""Final report model."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.finding import Finding
from src.models.review import AgentResult


class InputInfo(BaseModel):
    """Information about the input code."""

    file_path: Optional[str] = None
    language: str
    lines_of_code: int


class ReviewSummary(BaseModel):
    """Summary statistics for the review."""

    overall_score: float
    total_findings: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    executive_summary: str = ""


class AgentSummary(BaseModel):
    """Summary for a single agent's results."""

    score: float
    findings_count: int
    execution_time_ms: float


class ReviewMetadata(BaseModel):
    """Metadata about the review process."""

    agents_used: list[str] = Field(default_factory=list)
    total_execution_time_ms: float = 0.0
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    models_used: dict[str, str] = Field(default_factory=dict)
    total_cost_usd: float = 0.0
    pricing_known: bool = True
    warnings: list[str] = Field(default_factory=list)


class FinalReport(BaseModel):
    """Complete review report aggregating all agent results."""

    review_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input: InputInfo
    summary: ReviewSummary
    agents: dict[str, AgentSummary] = Field(default_factory=dict)
    findings: list[Finding] = Field(default_factory=list)
    metadata: ReviewMetadata = Field(default_factory=ReviewMetadata)

    @classmethod
    def from_agent_results(
        cls,
        results: list[AgentResult],
        code: str,
        language: str,
        file_path: Optional[str] = None,
    ) -> "FinalReport":
        """Create a final report from agent results."""
        # Collect all findings
        all_findings: list[Finding] = []
        agents_summary: dict[str, AgentSummary] = {}
        total_tokens = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_time_ms = 0.0
        models_used: dict[str, str] = {}
        total_cost_usd = 0.0
        pricing_known = True
        warnings: list[str] = []

        for result in results:
            all_findings.extend(result.findings)
            agents_summary[result.agent_name] = AgentSummary(
                score=result.calculate_score(),
                findings_count=result.findings_count,
                execution_time_ms=result.execution_time_ms,
            )
            total_tokens += result.tokens_used
            total_input_tokens += result.input_tokens
            total_output_tokens += result.output_tokens
            total_time_ms += result.execution_time_ms
            models_used[result.agent_name] = result.model
            total_cost_usd += result.cost_usd
            pricing_known = pricing_known and result.pricing_known
            warnings.extend(result.warnings)
            if result.error:
                warnings.append(f"{result.agent_name} failed: {result.error}")

        # Sort findings by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        all_findings.sort(key=lambda f: severity_order.get(f.severity.value, 5))

        # Count by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in all_findings:
            severity_counts[finding.severity.value] = (
                severity_counts.get(finding.severity.value, 0) + 1
            )

        # Calculate overall score
        if agents_summary:
            overall_score = sum(a.score for a in agents_summary.values()) / len(
                agents_summary
            )
        else:
            overall_score = 100.0

        # Generate executive summary
        executive_summary = cls._generate_executive_summary(
            all_findings, severity_counts, overall_score
        )

        lines_of_code = len(code.splitlines())

        return cls(
            input=InputInfo(
                file_path=file_path,
                language=language,
                lines_of_code=lines_of_code,
            ),
            summary=ReviewSummary(
                overall_score=round(overall_score, 1),
                total_findings=len(all_findings),
                critical=severity_counts["critical"],
                high=severity_counts["high"],
                medium=severity_counts["medium"],
                low=severity_counts["low"],
                info=severity_counts["info"],
                executive_summary=executive_summary,
            ),
            agents=agents_summary,
            findings=all_findings,
            metadata=ReviewMetadata(
                agents_used=[r.agent_name for r in results],
                total_execution_time_ms=round(total_time_ms, 2),
                tokens_used=total_tokens,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                models_used=models_used,
                total_cost_usd=round(total_cost_usd, 6),
                pricing_known=pricing_known,
                warnings=warnings,
            ),
        )

    @staticmethod
    def _generate_executive_summary(
        findings: list[Finding],
        counts: dict[str, int],
        score: float,
    ) -> str:
        """Generate an executive summary of the review."""
        if not findings:
            return "No issues found. The code appears to be well-written."

        parts = []

        if counts["critical"] > 0:
            parts.append(
                f"{counts['critical']} critical issue(s) require immediate attention"
            )
        if counts["high"] > 0:
            parts.append(f"{counts['high']} high-priority issue(s) should be addressed")
        if counts["medium"] + counts["low"] > 0:
            parts.append(
                f"{counts['medium'] + counts['low']} moderate/low priority improvements suggested"
            )

        if score >= 80:
            quality = "good overall quality"
        elif score >= 60:
            quality = "acceptable quality with room for improvement"
        elif score >= 40:
            quality = "several areas needing attention"
        else:
            quality = "significant issues requiring remediation"

        return f"Code review found {len(findings)} total issues indicating {quality}. " + ". ".join(parts) + "."

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = self.model_dump()
        data["review_id"] = str(self.review_id)
        data["timestamp"] = self.timestamp.isoformat()
        data["findings"] = [f.to_dict() for f in self.findings]
        return data
