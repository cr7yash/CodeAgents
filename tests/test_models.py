"""Tests for data models."""

import pytest

from src.models.finding import Finding, Severity, Location
from src.models.review import AgentResult
from src.models.report import FinalReport, ReviewSummary, InputInfo


class TestFinding:
    """Tests for Finding model."""

    def test_finding_creation(self):
        """Test creating a finding with required fields."""
        finding = Finding(
            severity=Severity.HIGH,
            category="sql_injection",
            title="SQL Injection Vulnerability",
            description="User input is concatenated into SQL query",
        )

        assert finding.severity == Severity.HIGH
        assert finding.category == "sql_injection"
        assert finding.id is not None

    def test_finding_with_location(self):
        """Test finding with location information."""
        finding = Finding(
            severity=Severity.CRITICAL,
            category="hardcoded_secret",
            title="Hardcoded API Key",
            description="API key is hardcoded in source",
            line_start=5,
            line_end=5,
            code_snippet='API_KEY = "AKIA..."',
        )

        assert finding.line_start == 5
        assert finding.code_snippet is not None

    def test_finding_to_dict(self):
        """Test finding serialization."""
        finding = Finding(
            severity=Severity.MEDIUM,
            category="code_smell",
            title="Long Method",
            description="Method exceeds 20 lines",
        )

        data = finding.to_dict()
        assert "id" in data
        assert data["severity"] == "medium"
        assert isinstance(data["id"], str)


class TestAgentResult:
    """Tests for AgentResult model."""

    def test_empty_result(self):
        """Test agent result with no findings."""
        result = AgentResult(
            agent_name="QualityAgent",
            findings=[],
            summary="No issues found",
        )

        assert result.findings_count == 0
        assert result.calculate_score() == 100.0

    def test_result_with_findings(self):
        """Test agent result with findings."""
        findings = [
            Finding(
                severity=Severity.HIGH,
                category="security",
                title="Issue 1",
                description="Desc 1",
            ),
            Finding(
                severity=Severity.MEDIUM,
                category="quality",
                title="Issue 2",
                description="Desc 2",
            ),
        ]

        result = AgentResult(
            agent_name="SecurityAgent",
            findings=findings,
            summary="Found 2 issues",
            execution_time_ms=150.5,
            tokens_used=500,
        )

        assert result.findings_count == 2
        assert result.high_count == 1
        assert result.medium_count == 1
        assert result.calculate_score() < 100.0

    def test_severity_counts(self):
        """Test counting findings by severity."""
        findings = [
            Finding(severity=Severity.CRITICAL, category="a", title="t", description="d"),
            Finding(severity=Severity.CRITICAL, category="b", title="t", description="d"),
            Finding(severity=Severity.HIGH, category="c", title="t", description="d"),
            Finding(severity=Severity.LOW, category="d", title="t", description="d"),
        ]

        result = AgentResult(
            agent_name="Test",
            findings=findings,
            summary="Test",
        )

        assert result.critical_count == 2
        assert result.high_count == 1
        assert result.low_count == 1
        assert result.medium_count == 0


class TestFinalReport:
    """Tests for FinalReport model."""

    def test_report_from_empty_results(self):
        """Test creating report from empty results."""
        report = FinalReport.from_agent_results(
            results=[],
            code="print('hello')",
            language="python",
        )

        assert report.summary.total_findings == 0
        assert report.summary.overall_score == 100.0

    def test_report_from_agent_results(self):
        """Test creating report from agent results."""
        findings = [
            Finding(
                severity=Severity.HIGH,
                category="security",
                title="Security Issue",
                description="A security vulnerability",
                line_start=10,
            ),
        ]

        result = AgentResult(
            agent_name="SecurityAgent",
            findings=findings,
            summary="Found 1 issue",
            execution_time_ms=100,
            tokens_used=200,
        )

        report = FinalReport.from_agent_results(
            results=[result],
            code="x = 1\n" * 10,
            language="python",
            file_path="test.py",
        )

        assert report.summary.total_findings == 1
        assert report.summary.high == 1
        assert report.input.lines_of_code == 10
        assert "SecurityAgent" in report.metadata.agents_used

    def test_report_surfaces_agent_errors_as_warnings(self):
        """An agent that failed outright must not fail silently in the report."""
        result = AgentResult(
            agent_name="DocumentationAgent",
            findings=[],
            summary="Analysis failed: No JSON object found",
            error="No JSON object found: line 1 column 1 (char 0)",
        )

        report = FinalReport.from_agent_results(
            results=[result],
            code="x = 1",
            language="python",
        )

        assert any("DocumentationAgent failed" in w for w in report.metadata.warnings)

    def test_report_aggregates_tokens_and_cost(self):
        """Metadata must reflect real usage, not the pre-migration always-zero value."""
        result = AgentResult(
            agent_name="QualityAgent",
            findings=[],
            summary="clean",
            tokens_used=150,
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.001,
            pricing_known=True,
        )

        report = FinalReport.from_agent_results(
            results=[result],
            code="x = 1",
            language="python",
        )

        assert report.metadata.tokens_used == 150
        assert report.metadata.input_tokens == 100
        assert report.metadata.output_tokens == 50
        assert report.metadata.total_cost_usd == pytest.approx(0.001)
        assert report.metadata.models_used["QualityAgent"] == "gpt-4o-mini"

    def test_report_to_dict(self):
        """Test report serialization."""
        report = FinalReport.from_agent_results(
            results=[],
            code="x = 1",
            language="python",
        )

        data = report.to_dict()
        assert "review_id" in data
        assert "timestamp" in data
        assert isinstance(data["review_id"], str)
