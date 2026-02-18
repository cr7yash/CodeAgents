"""Shared state definitions for the LangGraph workflow."""

from typing import Annotated, TypedDict

from src.models.review import AgentResult
from src.models.report import FinalReport


def merge_results(existing: AgentResult | None, new: AgentResult) -> AgentResult:
    """Reducer to merge agent results (just use the new one)."""
    return new


def merge_errors(existing: list[str], new: list[str]) -> list[str]:
    """Reducer to accumulate errors."""
    return existing + new


class ReviewState(TypedDict, total=False):
    """
    Shared state passed between all nodes in the graph.
    """

    # Input
    code: str
    language: str
    file_path: str | None

    # Agent results (populated during execution)
    quality_result: Annotated[AgentResult | None, merge_results]
    security_result: Annotated[AgentResult | None, merge_results]
    performance_result: Annotated[AgentResult | None, merge_results]
    documentation_result: Annotated[AgentResult | None, merge_results]

    # Output
    final_report: FinalReport | None

    # Metadata
    errors: Annotated[list[str], merge_errors]
