"""Base agent class for all code review agents."""

import time
import logging
from abc import ABC, abstractmethod
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from src.config.settings import get_settings
from src.models.finding import Finding, Severity
from src.models.review import AgentResult


logger = logging.getLogger(__name__)


class FindingsOutput(BaseModel):
    """Structured output for agent findings."""

    findings: list[dict[str, Any]]
    summary: str


class BaseAgent(ABC):
    """
    Base class for all code review agents.
    Each agent specializes in a specific type of analysis.
    """

    def __init__(self, model_name: str | None = None):
        settings = get_settings()
        self.model_name = model_name or settings.default_model
        self.llm = ChatGroq(
            model=self.model_name,
            temperature=settings.temperature,
            api_key=settings.groq_api_key,
        )
        self.name = self.__class__.__name__

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Define the agent's specialized system prompt."""
        pass

    @property
    @abstractmethod
    def analysis_categories(self) -> list[str]:
        """Categories this agent analyzes."""
        pass

    @abstractmethod
    def get_tools(self) -> list[Any]:
        """Return tools available to this agent."""
        pass

    def _build_analysis_prompt(self, code: str, language: str) -> str:
        """Build the analysis prompt for the agent."""
        return f"""Analyze the following {language} code and identify issues related to your expertise.

For each issue found, provide:
1. severity: One of "critical", "high", "medium", "low", or "info"
2. category: A specific category from your domain (e.g., "sql_injection", "code_smell", etc.)
3. title: A brief title for the issue
4. description: Detailed explanation of the issue
5. line_start: Starting line number (1-indexed)
6. line_end: Ending line number (1-indexed)
7. suggestion: How to fix the issue
8. code_snippet: The problematic code (optional)

Respond with a JSON object containing:
- "findings": An array of issue objects
- "summary": A brief summary of your analysis

If no issues are found, return an empty findings array with a summary stating the code looks good for your area of expertise.

CODE TO ANALYZE:
```{language}
{code}
```

Respond ONLY with valid JSON. Do not include any other text."""

    async def analyze(
        self,
        code: str,
        language: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        """
        Analyze code and return findings.

        Args:
            code: Source code to analyze
            language: Programming language
            context: Additional context (optional)

        Returns:
            AgentResult with findings and metadata
        """
        start_time = time.time()
        tokens_used = 0

        try:
            # Build messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=self._build_analysis_prompt(code, language)),
            ]

            # Run analysis with structured output
            structured_llm = self.llm.with_structured_output(FindingsOutput)
            response = await structured_llm.ainvoke(messages)

            # Track token usage from response metadata if available
            tokens_used = getattr(response, "usage_metadata", {}).get("total_tokens", 0)

            # Parse findings
            findings = self._parse_findings(response.findings)

            execution_time_ms = (time.time() - start_time) * 1000

            return AgentResult(
                agent_name=self.name,
                findings=findings,
                summary=response.summary,
                execution_time_ms=round(execution_time_ms, 2),
                tokens_used=tokens_used,
            )

        except Exception as e:
            logger.error(f"Error in {self.name} analysis: {e}")
            execution_time_ms = (time.time() - start_time) * 1000

            return AgentResult(
                agent_name=self.name,
                findings=[],
                summary=f"Analysis failed: {str(e)}",
                execution_time_ms=round(execution_time_ms, 2),
                tokens_used=tokens_used,
                error=str(e),
            )

    def _parse_findings(self, raw_findings: list[dict[str, Any]]) -> list[Finding]:
        """Parse raw findings into Finding objects."""
        findings = []

        for raw in raw_findings:
            try:
                # Map severity string to enum
                severity_str = raw.get("severity", "info").lower()
                try:
                    severity = Severity(severity_str)
                except ValueError:
                    severity = Severity.INFO

                finding = Finding(
                    severity=severity,
                    category=raw.get("category", "unknown"),
                    title=raw.get("title", "Untitled Issue"),
                    description=raw.get("description", ""),
                    line_start=raw.get("line_start"),
                    line_end=raw.get("line_end"),
                    suggestion=raw.get("suggestion"),
                    code_snippet=raw.get("code_snippet"),
                    references=raw.get("references", []),
                )
                findings.append(finding)

            except Exception as e:
                logger.warning(f"Failed to parse finding: {e}")
                continue

        return findings

    def analyze_sync(
        self,
        code: str,
        language: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        """Synchronous wrapper for analyze."""
        import asyncio

        return asyncio.run(self.analyze(code, language, context))
