"""Tests for base agent functionality."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.base import BaseAgent
from src.models.finding import Severity
from src.models.review import AgentResult
from src.providers.base import GenerationResult


class ConcreteAgent(BaseAgent):
    """Concrete implementation for testing."""

    @property
    def system_prompt(self) -> str:
        return "You are a test agent."

    @property
    def analysis_categories(self) -> list[str]:
        return ["test_category"]

    def get_tools(self) -> list:
        return []


class TestBaseAgent:
    """Tests for BaseAgent."""

    def test_cannot_instantiate_abstract(self):
        """Test that BaseAgent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAgent()

    def test_concrete_agent_creation(self):
        """Test creating a concrete agent."""
        agent = ConcreteAgent()

        assert agent.name == "ConcreteAgent"
        assert agent.system_prompt == "You are a test agent."
        assert "test_category" in agent.analysis_categories

    def test_parse_findings_valid(self):
        """Test parsing valid findings."""
        agent = ConcreteAgent()

        raw_findings = [
            {
                "severity": "high",
                "category": "security",
                "title": "Test Issue",
                "description": "A test description",
                "line_start": 10,
                "line_end": 15,
                "suggestion": "Fix it",
            }
        ]

        findings = agent._parse_findings(raw_findings)

        assert len(findings) == 1
        assert findings[0].severity == Severity.HIGH
        assert findings[0].title == "Test Issue"
        assert findings[0].line_start == 10

    def test_parse_findings_invalid_severity(self):
        """Test parsing findings with invalid severity."""
        agent = ConcreteAgent()

        raw_findings = [
            {
                "severity": "invalid_severity",
                "category": "test",
                "title": "Test",
                "description": "Test",
            }
        ]

        findings = agent._parse_findings(raw_findings)

        assert len(findings) == 1
        assert findings[0].severity == Severity.INFO  # Falls back to INFO

    def test_parse_findings_missing_fields(self):
        """Test parsing findings with missing optional fields."""
        agent = ConcreteAgent()

        raw_findings = [
            {
                "severity": "medium",
                "category": "quality",
                "title": "Minimal Finding",
                "description": "Just required fields",
            }
        ]

        findings = agent._parse_findings(raw_findings)

        assert len(findings) == 1
        assert findings[0].line_start is None
        assert findings[0].suggestion is None

    def test_build_analysis_prompt(self):
        """Test building the analysis prompt."""
        agent = ConcreteAgent()

        prompt = agent._build_analysis_prompt(
            code="def hello():\n    print('hi')",
            language="python",
        )

        assert "python" in prompt.lower()
        assert "def hello()" in prompt
        assert "JSON" in prompt

    @pytest.mark.asyncio
    async def test_analyze_success(self):
        """Test successful analysis."""
        agent = ConcreteAgent()

        response_text = json.dumps(
            {
                "findings": [
                    {
                        "severity": "high",
                        "category": "test",
                        "title": "Test Issue",
                        "description": "Test description",
                        "line_start": 1,
                    }
                ],
                "summary": "Found 1 issue",
            }
        )
        mock_result = GenerationResult(
            text=response_text,
            input_tokens=100,
            output_tokens=50,
            latency_ms=10.0,
            model=agent.model,
            finish_reason="stop",
        )

        with patch.object(agent.provider, "generate", AsyncMock(return_value=mock_result)):
            result = await agent.analyze("x = 1", "python")

            assert isinstance(result, AgentResult)
            assert result.agent_name == "ConcreteAgent"
            assert len(result.findings) == 1
            assert result.summary == "Found 1 issue"
            assert result.tokens_used == 150
            assert result.input_tokens == 100
            assert result.output_tokens == 50

    @pytest.mark.asyncio
    async def test_analyze_error_handling(self):
        """Test error handling during analysis."""
        agent = ConcreteAgent()

        with patch.object(
            agent.provider, "generate", AsyncMock(side_effect=Exception("API Error"))
        ):
            result = await agent.analyze("x = 1", "python")

            assert isinstance(result, AgentResult)
            assert result.error is not None
            assert "API Error" in result.error
            assert len(result.findings) == 0

    @pytest.mark.asyncio
    async def test_analyze_retries_once_on_malformed_json(self):
        """A malformed first response triggers exactly one retry."""
        agent = ConcreteAgent()

        bad_result = GenerationResult(
            text="not json at all",
            input_tokens=10,
            output_tokens=5,
            latency_ms=5.0,
            model=agent.model,
            finish_reason="stop",
        )
        good_result = GenerationResult(
            text=json.dumps({"findings": [], "summary": "clean"}),
            input_tokens=10,
            output_tokens=5,
            latency_ms=5.0,
            model=agent.model,
            finish_reason="stop",
        )

        mock_generate = AsyncMock(side_effect=[bad_result, good_result])
        with patch.object(agent.provider, "generate", mock_generate):
            result = await agent.analyze("x = 1", "python")

            assert mock_generate.await_count == 2
            assert result.summary == "clean"
            assert result.error is None

    @pytest.mark.asyncio
    async def test_analyze_flags_empty_reasoning_response(self):
        """An empty first response (all output spent on hidden reasoning) should
        warn even though the retry recovers valid findings."""
        agent = ConcreteAgent()

        empty_result = GenerationResult(
            text="",
            input_tokens=10,
            output_tokens=0,
            latency_ms=5.0,
            model=agent.model,
            finish_reason="stop",
        )
        recovered_result = GenerationResult(
            text=json.dumps({"findings": [], "summary": "no issues"}),
            input_tokens=10,
            output_tokens=5,
            latency_ms=5.0,
            model=agent.model,
            finish_reason="stop",
        )

        mock_generate = AsyncMock(side_effect=[empty_result, recovered_result])
        with patch.object(agent.provider, "generate", mock_generate):
            result = await agent.analyze("x = 1", "python")

            assert mock_generate.await_count == 2
            assert any("empty response" in w for w in result.warnings)
            assert result.error is None

    @pytest.mark.asyncio
    async def test_analyze_reports_error_when_retry_also_empty(self):
        """If a reasoning model exhausts its budget on both attempts, the
        result must carry both the warning and the error — never silently
        look like a clean pass with 0 findings."""
        agent = ConcreteAgent()

        empty_result = GenerationResult(
            text="",
            input_tokens=10,
            output_tokens=0,
            latency_ms=5.0,
            model=agent.model,
            finish_reason="stop",
        )

        mock_generate = AsyncMock(side_effect=[empty_result, empty_result])
        with patch.object(agent.provider, "generate", mock_generate):
            result = await agent.analyze("x = 1", "python")

            assert mock_generate.await_count == 2
            assert result.error is not None
            assert any("empty response" in w for w in result.warnings)
            assert result.input_tokens == 20
