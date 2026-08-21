"""LangGraph workflow definition for multi-agent code review."""

import asyncio
import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.base import BaseAgent
from src.agents.documentation_agent import DocumentationAgent
from src.agents.performance_agent import PerformanceAgent
from src.agents.quality_agent import QualityAgent
from src.agents.security_agent import SecurityAgent
from src.models.report import FinalReport
from src.orchestrator.aggregator import aggregate_results
from src.orchestrator.state import ReviewState

logger = logging.getLogger(__name__)


def _make_agent_node(agent_cls: type[BaseAgent], state_key: str, model: str | None):
    """Build a graph node that constructs and runs one agent per invocation."""

    async def node(state: ReviewState) -> dict:
        logger.info(f"Running {agent_cls.__name__}...")
        try:
            agent = agent_cls(model=model)
            result = await agent.analyze(
                code=state["code"],
                language=state["language"],
            )
            return {state_key: result}
        except Exception as e:
            logger.error(f"{agent_cls.__name__} error: {e}")
            return {"errors": [f"{agent_cls.__name__} error: {str(e)}"]}

    return node


async def aggregate_node(state: ReviewState) -> dict:
    """Aggregate results from all agents into final report."""
    logger.info("Aggregating results...")

    results = []
    if state.get("quality_result"):
        results.append(state["quality_result"])
    if state.get("security_result"):
        results.append(state["security_result"])
    if state.get("performance_result"):
        results.append(state["performance_result"])
    if state.get("documentation_result"):
        results.append(state["documentation_result"])

    final_report = aggregate_results(
        results=results,
        code=state["code"],
        language=state["language"],
        file_path=state.get("file_path"),
    )

    return {"final_report": final_report}


def create_review_graph(
    agents: list[Literal["quality", "security", "performance", "documentation"]] | None = None,
    model: str | None = None,
) -> CompiledStateGraph:
    """
    Create the multi-agent review workflow.

    Args:
        agents: List of agents to run. If None, runs all agents.
        model: Model slug to use for every selected agent. If None, each
            agent falls back to its own per-agent override, then the
            configured default.

    Flow:
    1. START -> [selected agents] (parallel)
    2. All agents -> aggregator
    3. aggregator -> END
    """
    if agents is None:
        agents = ["quality", "security", "performance", "documentation"]

    workflow = StateGraph(ReviewState)

    # Add aggregator node (always needed)
    workflow.add_node("aggregator", aggregate_node)

    # Map agent names to their node config
    agent_classes = {
        "quality": (QualityAgent, "quality_result"),
        "security": (SecurityAgent, "security_result"),
        "performance": (PerformanceAgent, "performance_result"),
        "documentation": (DocumentationAgent, "documentation_result"),
    }

    # Add selected agent nodes
    for agent_name in agents:
        if agent_name in agent_classes:
            agent_cls, state_key = agent_classes[agent_name]
            node_name = f"{agent_name}_agent"
            workflow.add_node(node_name, _make_agent_node(agent_cls, state_key, model))

            # Add edges: START -> agent -> aggregator
            workflow.add_edge(START, node_name)
            workflow.add_edge(node_name, "aggregator")

    # Aggregator produces final output
    workflow.add_edge("aggregator", END)

    return workflow.compile()


async def run_review(
    code: str,
    language: str,
    file_path: str | None = None,
    agents: list[str] | None = None,
    model: str | None = None,
) -> FinalReport:
    """
    Run a complete code review.

    Args:
        code: Source code to review
        language: Programming language
        file_path: Optional file path for context
        agents: Optional list of agents to run
        model: Model slug to use for every selected agent

    Returns:
        FinalReport with aggregated results
    """
    # Create the graph with selected agents
    graph = create_review_graph(agents, model=model)

    # Initial state
    initial_state: ReviewState = {
        "code": code,
        "language": language,
        "file_path": file_path,
        "quality_result": None,
        "security_result": None,
        "performance_result": None,
        "documentation_result": None,
        "final_report": None,
        "errors": [],
    }

    # Run the graph
    final_state = await graph.ainvoke(initial_state)

    return final_state["final_report"]


def run_review_sync(
    code: str,
    language: str,
    file_path: str | None = None,
    agents: list[str] | None = None,
    model: str | None = None,
) -> FinalReport:
    """Synchronous wrapper for run_review."""
    return asyncio.run(run_review(code, language, file_path, agents, model))
