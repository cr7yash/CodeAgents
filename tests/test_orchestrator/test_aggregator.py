"""Tests for result aggregation."""

import pytest

from src.models.finding import Finding, Severity
from src.models.review import AgentResult
from src.orchestrator.aggregator import (
    aggregate_results,
    _are_similar_findings,
    _merge_findings,
)


class TestAggregator:
    """Tests for aggregation logic."""

    def test_aggregate_empty_results(self):
        """Test aggregating empty results."""
        report = aggregate_results(
            results=[],
            code="x = 1",
            language="python",
        )

        assert report.summary.total_findings == 0
        assert report.summary.overall_score == 100.0

    def test_aggregate_single_result(self):
        """Test aggregating single agent result."""
        findings = [
            Finding(
                severity=Severity.HIGH,
                category="security",
                title="SQL Injection",
                description="Vulnerable query",
                line_start=10,
            )
        ]

        result = AgentResult(
            agent_name="SecurityAgent",
            findings=findings,
            summary="Found 1 issue",
            execution_time_ms=100,
        )

        report = aggregate_results(
            results=[result],
            code="x = 1\n" * 20,
            language="python",
        )

        assert report.summary.total_findings == 1
        assert report.summary.high == 1
        assert "SecurityAgent" in report.metadata.agents_used

    def test_aggregate_multiple_results(self):
        """Test aggregating multiple agent results."""
        security_result = AgentResult(
            agent_name="SecurityAgent",
            findings=[
                Finding(
                    severity=Severity.CRITICAL,
                    category="sql_injection",
                    title="SQL Injection",
                    description="Vulnerable",
                    line_start=10,
                )
            ],
            summary="Security issues found",
        )

        quality_result = AgentResult(
            agent_name="QualityAgent",
            findings=[
                Finding(
                    severity=Severity.MEDIUM,
                    category="code_smell",
                    title="Long Method",
                    description="Method too long",
                    line_start=50,
                )
            ],
            summary="Quality issues found",
        )

        report = aggregate_results(
            results=[security_result, quality_result],
            code="x = 1\n" * 100,
            language="python",
        )

        assert report.summary.total_findings == 2
        assert report.summary.critical == 1
        assert report.summary.medium == 1
        assert len(report.metadata.agents_used) == 2

    def test_findings_sorted_by_severity(self):
        """Test that findings are sorted by severity."""
        findings = [
            Finding(severity=Severity.LOW, category="a", title="Low", description="d"),
            Finding(severity=Severity.CRITICAL, category="b", title="Critical", description="d"),
            Finding(severity=Severity.MEDIUM, category="c", title="Medium", description="d"),
        ]

        result = AgentResult(
            agent_name="TestAgent",
            findings=findings,
            summary="Test",
        )

        report = aggregate_results(
            results=[result],
            code="x = 1",
            language="python",
        )

        # Check findings are ordered by severity
        assert report.findings[0].severity == Severity.CRITICAL
        assert report.findings[-1].severity == Severity.LOW


class TestFindingSimilarity:
    """Tests for finding similarity detection."""

    def test_similar_same_line(self):
        """Test findings on same line are similar."""
        f1 = Finding(
            severity=Severity.HIGH,
            category="security",
            title="SQL injection vulnerability",
            description="Desc 1",
            line_start=10,
        )

        f2 = Finding(
            severity=Severity.CRITICAL,
            category="sql_injection",
            title="SQL injection in query",
            description="Desc 2",
            line_start=10,
        )

        assert _are_similar_findings(f1, f2)

    def test_not_similar_different_lines(self):
        """Test findings on different lines are not similar."""
        f1 = Finding(
            severity=Severity.HIGH,
            category="security",
            title="Issue 1",
            description="Desc 1",
            line_start=10,
        )

        f2 = Finding(
            severity=Severity.HIGH,
            category="security",
            title="Issue 2",
            description="Desc 2",
            line_start=50,
        )

        assert not _are_similar_findings(f1, f2)

    def test_not_similar_different_titles(self):
        """Test findings with different titles are not similar."""
        f1 = Finding(
            severity=Severity.HIGH,
            category="security",
            title="SQL Injection",
            description="Desc 1",
            line_start=10,
        )

        f2 = Finding(
            severity=Severity.HIGH,
            category="quality",
            title="Code Smell",
            description="Desc 2",
            line_start=10,
        )

        # Different enough titles should not be similar
        # (depends on word overlap threshold)
        assert not _are_similar_findings(f1, f2)


class TestFindingMerge:
    """Tests for finding merge logic."""

    def test_merge_keeps_higher_severity(self):
        """Test merged finding keeps higher severity."""
        f1 = Finding(
            severity=Severity.HIGH,
            category="security",
            title="Issue",
            description="Desc 1",
        )

        f2 = Finding(
            severity=Severity.CRITICAL,
            category="security",
            title="Issue",
            description="Desc 2",
        )

        merged = _merge_findings(f1, f2)

        assert merged.severity == Severity.CRITICAL

    def test_merge_combines_descriptions(self):
        """Test merged finding combines descriptions."""
        f1 = Finding(
            severity=Severity.HIGH,
            category="security",
            title="Issue",
            description="First description",
        )

        f2 = Finding(
            severity=Severity.HIGH,
            category="security",
            title="Issue",
            description="Second description",
        )

        merged = _merge_findings(f1, f2)

        assert "First description" in merged.description
        assert "Second description" in merged.description

    def test_merge_combines_references(self):
        """Test merged finding combines references."""
        f1 = Finding(
            severity=Severity.HIGH,
            category="security",
            title="Issue",
            description="Desc",
            references=["CWE-89"],
        )

        f2 = Finding(
            severity=Severity.HIGH,
            category="security",
            title="Issue",
            description="Desc",
            references=["OWASP-A1"],
        )

        merged = _merge_findings(f1, f2)

        assert "CWE-89" in merged.references
        assert "OWASP-A1" in merged.references
