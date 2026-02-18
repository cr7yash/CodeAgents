"""LangGraph workflow definition for multi-agent code review."""

import asyncio
import logging
from typing import Literal

from langgraph.graph import StateGraph, START, END

from src.agents.quality_agent import QualityAgent
from src.agents.security_agent import SecurityAgent
from src.agents.performance_agent import PerformanceAgent
from src.agents.documentation_agent import DocumentationAgent
from src.orchestrator.state import ReviewState
from src.orchestrator.aggregator import aggregate_results
from src.models.report import FinalReport


logger = logging.getLogger(__name__)

# Agent instances (created once)
quality_agent = QualityAgent()
security_agent = SecurityAgent()
performance_agent = PerformanceAgent()
documentation_agent = DocumentationAgent()


async def run_quality_agent(state: ReviewState) -> dict:
    """Run the quality agent on the code."""
    logger.info("Running Quality Agent...")
    try:
        result = await quality_agent.analyze(
            code=state["code"],
            language=state["language"],
        )
        return {"quality_result": result}
    except Exception as e:
        logger.error(f"Quality agent error: {e}")
        return {"errors": [f"Quality agent error: {str(e)}"]}


async def run_security_agent(state: ReviewState) -> dict:
    """Run the security agent on the code."""
    logger.info("Running Security Agent...")
    try:
        result = await security_agent.analyze(
            code=state["code"],
            language=state["language"],
        )
        return {"security_result": result}
    except Exception as e:
        logger.error(f"Security agent error: {e}")
        return {"errors": [f"Security agent error: {str(e)}"]}


async def run_performance_agent(state: ReviewState) -> dict:
    """Run the performance agent on the code."""
    logger.info("Running Performance Agent...")
    try:
        result = await performance_agent.analyze(
            code=state["code"],
            language=state["language"],
        )
        return {"performance_result": result}
    except Exception as e:
        logger.error(f"Performance agent error: {e}")
        return {"errors": [f"Performance agent error: {str(e)}"]}


async def run_documentation_agent(state: ReviewState) -> dict:
    """Run the documentation agent on the code."""
    logger.info("Running Documentation Agent...")
    try:
        result = await documentation_agent.analyze(
            code=state["code"],
            language=state["language"],
        )
        return {"documentation_result": result}
    except Exception as e:
        logger.error(f"Documentation agent error: {e}")
        return {"errors": [f"Documentation agent error: {str(e)}"]}


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
) -> StateGraph:
    """
    Create the multi-agent review workflow.

    Args:
        agents: List of agents to run. If None, runs all agents.

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

    # Map agent names to their node functions
    agent_nodes = {
        "quality": ("quality_agent", run_quality_agent),
        "security": ("security_agent", run_security_agent),
        "performance": ("performance_agent", run_performance_agent),
        "documentation": ("documentation_agent", run_documentation_agent),
    }

    # Add selected agent nodes
    for agent_name in agents:
        if agent_name in agent_nodes:
            node_name, node_func = agent_nodes[agent_name]
            workflow.add_node(node_name, node_func)

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
) -> FinalReport:
    """
    Run a complete code review.

    Args:
        code: Source code to review
        language: Programming language
        file_path: Optional file path for context
        agents: Optional list of agents to run

    Returns:
        FinalReport with aggregated results
    """
    # Create the graph with selected agents
    graph = create_review_graph(agents)

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
) -> FinalReport:
    """Synchronous wrapper for run_review."""
    return asyncio.run(run_review(code, language, file_path, agents))
