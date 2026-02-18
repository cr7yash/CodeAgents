"""Tests for base agent functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.base import BaseAgent, FindingsOutput
from src.models.finding import Finding, Severity
from src.models.review import AgentResult


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

        mock_response = FindingsOutput(
            findings=[
                {
                    "severity": "high",
                    "category": "test",
                    "title": "Test Issue",
                    "description": "Test description",
                    "line_start": 1,
                }
            ],
            summary="Found 1 issue",
        )

        with patch.object(agent, "llm") as mock_llm:
            mock_structured = MagicMock()
            mock_structured.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm.with_structured_output.return_value = mock_structured

            result = await agent.analyze("x = 1", "python")

            assert isinstance(result, AgentResult)
            assert result.agent_name == "ConcreteAgent"
            assert len(result.findings) == 1
            assert result.summary == "Found 1 issue"

    @pytest.mark.asyncio
    async def test_analyze_error_handling(self):
        """Test error handling during analysis."""
        agent = ConcreteAgent()

        with patch.object(agent, "llm") as mock_llm:
            mock_llm.with_structured_output.side_effect = Exception("API Error")

            result = await agent.analyze("x = 1", "python")

            assert isinstance(result, AgentResult)
            assert result.error is not None
            assert "API Error" in result.error
            assert len(result.findings) == 0
