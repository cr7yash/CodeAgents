"""Tests for LangGraph orchestration."""

import json
import subprocess
import sys
from unittest.mock import patch

import pytest

from src.orchestrator.graph import create_review_graph, run_review
from src.providers.base import GenerationResult


def _make_result(model: str) -> GenerationResult:
    return GenerationResult(
        text=json.dumps({"findings": [], "summary": "clean"}),
        input_tokens=5,
        output_tokens=5,
        latency_ms=1.0,
        model=model,
        finish_reason="stop",
    )


class _StubProvider:
    """Echoes back whichever model each agent was constructed with."""

    async def generate(self, **kwargs):
        return _make_result(kwargs["model"])

    def estimate_cost(self, *args, **kwargs):
        return 0.0, True


class TestGraphImport:
    def test_importing_graph_constructs_no_client(self):
        """Regression guard: agents used to be built at import time, which
        required a valid PORTKEY_API_KEY just to `import graph`."""
        code = (
            "import os\n"
            "os.environ.pop('PORTKEY_API_KEY', None)\n"
            "import src.orchestrator.graph\n"
            "print('ok')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=str(__file__.rsplit("/tests/", 1)[0]),
        )
        assert result.returncode == 0, result.stderr
        assert "ok" in result.stdout


class TestCreateReviewGraph:
    def test_default_includes_all_four_agents(self):
        graph = create_review_graph()
        nodes = set(graph.get_graph().nodes.keys())
        for name in ("quality_agent", "security_agent", "performance_agent", "documentation_agent"):
            assert name in nodes

    def test_subset_selection_excludes_others(self):
        graph = create_review_graph(agents=["quality", "security"])
        nodes = set(graph.get_graph().nodes.keys())
        assert "quality_agent" in nodes
        assert "security_agent" in nodes
        assert "performance_agent" not in nodes
        assert "documentation_agent" not in nodes


class TestModelSelection:
    @pytest.mark.asyncio
    async def test_model_override_reaches_every_agent(self):
        """A --model value passed to run_review must reach every agent node."""
        with patch("src.agents.base.get_provider", return_value=_StubProvider()):
            report = await run_review(
                code="x = 1",
                language="python",
                agents=["quality", "security"],
                model="claude-opus-5",
            )

            assert report.metadata.models_used["QualityAgent"] == "claude-opus-5"
            assert report.metadata.models_used["SecurityAgent"] == "claude-opus-5"
