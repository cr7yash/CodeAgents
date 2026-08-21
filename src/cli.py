"""CLI for running code reviews."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown

from src.config.settings import get_settings
from src.orchestrator.graph import run_review
from src.models.report import FinalReport
from src.providers.portkey_catalog import FAMILY_LABELS, all_models, families, find_any, models_for_family


console = Console()


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def detect_language(file_path: Path) -> str:
    """Detect programming language from file extension."""
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
    }
    return extension_map.get(file_path.suffix.lower(), "unknown")


def format_severity_color(severity: str) -> str:
    """Get color for severity level."""
    colors = {
        "critical": "red bold",
        "high": "red",
        "medium": "yellow",
        "low": "blue",
        "info": "dim",
    }
    return colors.get(severity, "white")


def print_report_text(report: FinalReport) -> None:
    """Print report in text format with rich formatting."""
    # Header
    console.print()
    console.print(
        Panel.fit(
            f"[bold]Code Review Report[/bold]\n"
            f"Score: [{'green' if report.summary.overall_score >= 70 else 'yellow' if report.summary.overall_score >= 40 else 'red'}]"
            f"{report.summary.overall_score:.1f}/100[/]",
            title="CodeAgents",
            border_style="blue",
        )
    )

    # Summary table
    summary_table = Table(title="Summary", show_header=True, header_style="bold")
    summary_table.add_column("Severity", style="dim")
    summary_table.add_column("Count", justify="right")

    summary_table.add_row(
        "[red bold]Critical[/]", str(report.summary.critical)
    )
    summary_table.add_row("[red]High[/]", str(report.summary.high))
    summary_table.add_row("[yellow]Medium[/]", str(report.summary.medium))
    summary_table.add_row("[blue]Low[/]", str(report.summary.low))
    summary_table.add_row("[dim]Info[/]", str(report.summary.info))
    summary_table.add_row(
        "[bold]Total[/]", f"[bold]{report.summary.total_findings}[/]"
    )

    console.print(summary_table)
    console.print()

    # Executive summary
    console.print(
        Panel(
            report.summary.executive_summary,
            title="Executive Summary",
            border_style="green",
        )
    )
    console.print()

    # Findings by agent
    if report.findings:
        findings_table = Table(
            title="Findings",
            show_header=True,
            header_style="bold",
            show_lines=True,
        )
        findings_table.add_column("Severity", width=10)
        findings_table.add_column("Line", width=8, justify="right")
        findings_table.add_column("Category", width=20)
        findings_table.add_column("Title", width=40)
        findings_table.add_column("Description")

        for finding in report.findings:
            severity_style = format_severity_color(finding.severity.value)
            line = (
                str(finding.line_start) if finding.line_start else "-"
            )

            findings_table.add_row(
                f"[{severity_style}]{finding.severity.value.upper()}[/]",
                line,
                finding.category,
                finding.title,
                finding.description[:100] + "..."
                if len(finding.description) > 100
                else finding.description,
            )

        console.print(findings_table)
    else:
        console.print("[green]No issues found! Your code looks good.[/]")

    # Metadata
    console.print()
    cost_str = (
        f"${report.metadata.total_cost_usd:.4f}"
        if report.metadata.pricing_known
        else "unpriced"
    )
    console.print(
        f"[dim]Agents: {', '.join(report.metadata.agents_used)} | "
        f"Time: {report.metadata.total_execution_time_ms:.0f}ms | "
        f"Tokens: {report.metadata.tokens_used} "
        f"({report.metadata.input_tokens} in / {report.metadata.output_tokens} out) | "
        f"Cost: {cost_str}[/]"
    )
    if report.metadata.models_used:
        models_str = ", ".join(
            f"{agent}={model}" for agent, model in report.metadata.models_used.items()
        )
        console.print(f"[dim]Models: {models_str}[/]")
    if report.metadata.warnings:
        console.print()
        for warning in report.metadata.warnings:
            console.print(f"[yellow]Warning: {warning}[/]")


def format_report_json(report: FinalReport) -> str:
    """Format report as JSON."""
    return json.dumps(report.to_dict(), indent=2, default=str)


def format_report_markdown(report: FinalReport) -> str:
    """Format report as Markdown."""
    lines = [
        "# Code Review Report",
        "",
        f"**Overall Score:** {report.summary.overall_score:.1f}/100",
        "",
        "## Summary",
        "",
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| Critical | {report.summary.critical} |",
        f"| High | {report.summary.high} |",
        f"| Medium | {report.summary.medium} |",
        f"| Low | {report.summary.low} |",
        f"| Info | {report.summary.info} |",
        f"| **Total** | **{report.summary.total_findings}** |",
        "",
        "## Executive Summary",
        "",
        report.summary.executive_summary,
        "",
    ]

    if report.findings:
        lines.extend([
            "## Findings",
            "",
        ])

        for finding in report.findings:
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🔵",
                "info": "ℹ️",
            }.get(finding.severity.value, "")

            lines.extend([
                f"### {severity_emoji} {finding.title}",
                "",
                f"**Severity:** {finding.severity.value.upper()}  ",
                f"**Category:** {finding.category}  ",
                f"**Line:** {finding.line_start or 'N/A'}",
                "",
                finding.description,
                "",
            ])

            if finding.suggestion:
                lines.extend([
                    "**Suggestion:**",
                    "",
                    finding.suggestion,
                    "",
                ])

            if finding.code_snippet:
                lines.extend([
                    "```",
                    finding.code_snippet,
                    "```",
                    "",
                ])

    cost_str = (
        f"${report.metadata.total_cost_usd:.4f}"
        if report.metadata.pricing_known
        else "unpriced"
    )
    lines.extend([
        "---",
        "",
        f"*Agents: {', '.join(report.metadata.agents_used)} | "
        f"Time: {report.metadata.total_execution_time_ms:.0f}ms | "
        f"Tokens: {report.metadata.tokens_used} "
        f"({report.metadata.input_tokens} in / {report.metadata.output_tokens} out) | "
        f"Cost: {cost_str}*",
    ])

    if report.metadata.models_used:
        models_str = ", ".join(
            f"{agent}={model}" for agent, model in report.metadata.models_used.items()
        )
        lines.append(f"*Models: {models_str}*")

    if report.metadata.warnings:
        lines.extend(["", "**Warnings:**", ""])
        lines.extend(f"- {w}" for w in report.metadata.warnings)

    return "\n".join(lines)


@click.group()
@click.version_option(version="0.2.0")
def main():
    """CodeAgents: Multi-agent code review system."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-l",
    "--language",
    help="Programming language (auto-detect if not specified)",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file path",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format",
)
@click.option(
    "--agents",
    help="Comma-separated list of agents to run (quality,security,performance,documentation)",
)
@click.option(
    "-m",
    "--model",
    help="Model slug to use for every agent (run `codeagents models` to list options)",
)
@click.option(
    "--severity",
    type=click.Choice(["critical", "high", "medium", "low", "info"]),
    help="Minimum severity to report",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show detailed progress",
)
def review(
    path: str,
    language: Optional[str],
    output: Optional[str],
    output_format: str,
    agents: Optional[str],
    model: Optional[str],
    severity: Optional[str],
    verbose: bool,
):
    """Run a code review on a file or directory."""
    setup_logging(verbose)

    if model and find_any(model) is None:
        console.print(
            f"[red]Error: unknown model '{model}'. "
            f"Run `codeagents models` to see available models.[/]"
        )
        sys.exit(1)

    file_path = Path(path)

    # Read code
    if file_path.is_file():
        code = file_path.read_text()
        lang = language or detect_language(file_path)
    else:
        console.print(f"[red]Error: {path} is not a valid file[/]")
        sys.exit(1)

    if lang == "unknown" and not language:
        console.print(
            "[yellow]Warning: Could not detect language. "
            "Use --language to specify.[/]"
        )
        lang = "python"  # Default to Python

    # Parse agents
    agent_list = None
    if agents:
        agent_list = [a.strip() for a in agents.split(",")]

    # Check for Portkey gateway key
    settings = get_settings()
    if not settings.portkey_api_key:
        console.print(
            "[red]Error: PORTKEY_API_KEY not set. "
            "Please set PORTKEY_API_KEY in .env or environment.[/]"
        )
        sys.exit(1)

    # Run review with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running code review...", total=None)

        try:
            report = asyncio.run(
                run_review(
                    code=code,
                    language=lang,
                    file_path=str(file_path),
                    agents=agent_list,
                    model=model,
                )
            )
        except Exception as e:
            progress.stop()
            console.print(f"[red]Error during review: {e}[/]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            sys.exit(1)

        progress.update(task, completed=True)

    # Filter by severity if specified
    if severity and report.findings:
        severity_order = ["critical", "high", "medium", "low", "info"]
        min_index = severity_order.index(severity)
        allowed_severities = set(severity_order[: min_index + 1])
        report.findings = [
            f for f in report.findings if f.severity.value in allowed_severities
        ]

    # Output
    if output_format == "json":
        result = format_report_json(report)
    elif output_format == "markdown":
        result = format_report_markdown(report)
    else:
        result = None  # Will use rich printing

    if output:
        output_path = Path(output)
        if result:
            output_path.write_text(result)
        else:
            # For text format, write a simplified version
            output_path.write_text(format_report_markdown(report))
        console.print(f"[green]Report saved to {output}[/]")
    else:
        if result and output_format != "text":
            if output_format == "markdown":
                console.print(Markdown(result))
            else:
                console.print(result)
        else:
            print_report_text(report)


@main.command()
def agents():
    """List available agents."""
    table = Table(title="Available Agents", show_header=True)
    table.add_column("Agent", style="bold")
    table.add_column("Description")
    table.add_column("Categories")

    table.add_row(
        "quality",
        "Code quality analysis (smells, complexity, SOLID)",
        "code_smell, complexity, naming, ...",
    )
    table.add_row(
        "security",
        "Security vulnerability detection (OWASP, secrets)",
        "sql_injection, xss, secrets, ...",
    )
    table.add_row(
        "performance",
        "Performance analysis (Big O, inefficiencies)",
        "time_complexity, n_plus_one, ...",
    )
    table.add_row(
        "documentation",
        "Documentation coverage (docstrings, types)",
        "missing_docstring, type_hints, ...",
    )

    console.print(table)


@main.command()
def models():
    """List every model reachable through the Portkey gateway."""
    table = Table(title="Available Models", show_header=True, show_lines=False)
    table.add_column("Family", style="bold")
    table.add_column("Slug")
    table.add_column("Temp", justify="center")
    table.add_column("Top P", justify="center")
    table.add_column("Stop", justify="center")
    table.add_column("Reasoning", justify="center")
    table.add_column("Priced", justify="center")

    def _mark(value: bool) -> str:
        return "[green]yes[/]" if value else "[dim]no[/]"

    for family in families():
        for spec in models_for_family(family):
            table.add_row(
                FAMILY_LABELS[family],
                spec.slug,
                _mark(spec.caps.temperature),
                _mark(spec.caps.top_p),
                _mark(spec.caps.stop),
                _mark(spec.caps.reasoning_effort),
                _mark(spec.pricing is not None),
            )

    console.print(table)
    console.print(f"\n[dim]{len(all_models())} models across {len(families())} families[/]")


if __name__ == "__main__":
    main()
