"""Result aggregation logic for combining agent outputs."""

import logging
from typing import Optional

from src.models.finding import Finding, Severity
from src.models.review import AgentResult
from src.models.report import FinalReport


logger = logging.getLogger(__name__)


def aggregate_results(
    results: list[AgentResult],
    code: str,
    language: str,
    file_path: Optional[str] = None,
) -> FinalReport:
    """
    Aggregate results from all agents into a final report.

    Responsibilities:
    1. Collect results from all agents
    2. Deduplicate overlapping findings
    3. Resolve conflicts (e.g., if quality and security flag same issue)
    4. Prioritize findings by severity
    5. Generate executive summary
    6. Calculate overall code health score

    Args:
        results: List of AgentResult from all agents
        code: Original source code
        language: Programming language
        file_path: Optional file path

    Returns:
        FinalReport with aggregated and deduplicated findings
    """
    logger.info(f"Aggregating results from {len(results)} agents")

    # Deduplicate findings
    deduplicated_results = _deduplicate_findings(results)

    # Create the final report
    report = FinalReport.from_agent_results(
        results=deduplicated_results,
        code=code,
        language=language,
        file_path=file_path,
    )

    logger.info(
        f"Aggregation complete: {report.summary.total_findings} findings, "
        f"score: {report.summary.overall_score}"
    )

    return report


def _deduplicate_findings(results: list[AgentResult]) -> list[AgentResult]:
    """
    Deduplicate overlapping findings from multiple agents.

    Two findings are considered duplicates if they:
    - Reference the same line range (with some overlap tolerance)
    - Have similar categories or titles

    When duplicates are found, we keep the one with higher severity
    and merge relevant information.
    """
    if len(results) <= 1:
        return results

    # Collect all findings with their source agent
    all_findings: list[tuple[Finding, str]] = []
    for result in results:
        for finding in result.findings:
            all_findings.append((finding, result.agent_name))

    # Group findings by line number for efficient comparison
    findings_by_line: dict[int | None, list[tuple[Finding, str]]] = {}
    for finding, agent in all_findings:
        line = finding.line_start
        if line not in findings_by_line:
            findings_by_line[line] = []
        findings_by_line[line].append((finding, agent))

    # Identify duplicates
    duplicates: set[str] = set()
    merged_findings: dict[str, Finding] = {}

    for line, findings_at_line in findings_by_line.items():
        if len(findings_at_line) <= 1:
            continue

        # Compare findings at the same line
        for i, (finding1, agent1) in enumerate(findings_at_line):
            for finding2, agent2 in findings_at_line[i + 1 :]:
                if _are_similar_findings(finding1, finding2):
                    # Keep the one with higher severity
                    merged = _merge_findings(finding1, finding2)
                    merged_id = str(merged.id)
                    merged_findings[merged_id] = merged

                    # Mark originals as duplicates
                    duplicates.add(str(finding1.id))
                    duplicates.add(str(finding2.id))

    # Build deduplicated results
    deduplicated_results: list[AgentResult] = []

    for result in results:
        # Filter out duplicated findings
        filtered_findings = [
            f for f in result.findings if str(f.id) not in duplicates
        ]

        # Add merged findings that belong to this agent's categories
        for merged in merged_findings.values():
            if merged.category in [
                cat.lower().replace(" ", "_")
                for cat in _get_agent_categories(result.agent_name)
            ]:
                filtered_findings.append(merged)

        deduplicated_results.append(
            result.model_copy(update={"findings": filtered_findings})
        )

    return deduplicated_results


def _are_similar_findings(f1: Finding, f2: Finding) -> bool:
    """
    Check if two findings are similar enough to be considered duplicates.
    """
    # Check line overlap
    if f1.line_start and f2.line_start:
        line_diff = abs(f1.line_start - f2.line_start)
        if line_diff > 2:  # Allow 2 lines tolerance
            return False

    # Check title similarity (simple word overlap)
    words1 = set(f1.title.lower().split())
    words2 = set(f2.title.lower().split())

    if len(words1) == 0 or len(words2) == 0:
        return False

    overlap = len(words1 & words2)
    similarity = overlap / min(len(words1), len(words2))

    return similarity > 0.5


def _merge_findings(f1: Finding, f2: Finding) -> Finding:
    """
    Merge two similar findings, keeping the one with higher severity.
    """
    severity_order = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 2,
        Severity.LOW: 3,
        Severity.INFO: 4,
    }

    # Keep the one with higher severity (lower number)
    if severity_order.get(f1.severity, 5) <= severity_order.get(f2.severity, 5):
        primary, secondary = f1, f2
    else:
        primary, secondary = f2, f1

    # Merge descriptions if they add value
    merged_description = primary.description
    if secondary.description and secondary.description not in primary.description:
        merged_description += f"\n\nAdditional context: {secondary.description}"

    # Merge suggestions
    merged_suggestion = primary.suggestion
    if secondary.suggestion and secondary.suggestion != primary.suggestion:
        if merged_suggestion:
            merged_suggestion += f"\n\nAlternative: {secondary.suggestion}"
        else:
            merged_suggestion = secondary.suggestion

    # Merge references
    merged_refs = list(set(primary.references + secondary.references))

    return Finding(
        severity=primary.severity,
        category=primary.category,
        title=primary.title,
        description=merged_description,
        line_start=primary.line_start or secondary.line_start,
        line_end=primary.line_end or secondary.line_end,
        code_snippet=primary.code_snippet or secondary.code_snippet,
        suggestion=merged_suggestion,
        references=merged_refs,
    )


def _get_agent_categories(agent_name: str) -> list[str]:
    """Get the categories associated with an agent."""
    categories = {
        "QualityAgent": [
            "code_smell",
            "long_method",
            "deep_nesting",
            "god_class",
            "solid_violation",
            "dry_violation",
            "complexity",
            "naming",
        ],
        "SecurityAgent": [
            "sql_injection",
            "command_injection",
            "xss",
            "hardcoded_secret",
            "weak_crypto",
            "auth_flaw",
            "input_validation",
        ],
        "PerformanceAgent": [
            "time_complexity",
            "space_complexity",
            "n_plus_one",
            "inefficient_loop",
            "missing_cache",
            "blocking_call",
        ],
        "DocumentationAgent": [
            "missing_docstring",
            "incomplete_docstring",
            "missing_type_hint",
            "missing_comment",
        ],
    }
    return categories.get(agent_name, [])
