"""Base agent class for all code review agents."""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ValidationError

from src.config.settings import get_settings
from src.models.finding import Finding, Severity
from src.models.review import AgentResult
from src.providers import GenerationConfig, get_provider


logger = logging.getLogger(__name__)

# Maps each concrete agent's class name to its per-agent settings override.
_MODEL_OVERRIDE_FIELDS = {
    "QualityAgent": "quality_model",
    "SecurityAgent": "security_model",
    "PerformanceAgent": "performance_model",
    "DocumentationAgent": "documentation_model",
}

_JSON_RETRY_NUDGE = (
    "\n\nYour previous response was not valid JSON. "
    "Respond with the JSON object only — no prose, no markdown fences."
)


class FindingsOutput(BaseModel):
    """Structured output for agent findings."""

    findings: list[dict[str, Any]]
    summary: str


class BaseAgent(ABC):
    """
    Base class for all code review agents.
    Each agent specializes in a specific type of analysis.
    """

    def __init__(self, model: str | None = None):
        settings = get_settings()
        override_field = _MODEL_OVERRIDE_FIELDS.get(self.__class__.__name__)
        override = getattr(settings, override_field, None) if override_field else None
        self.model = model or override or settings.default_model
        self.provider = get_provider()
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

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """Extract a JSON object from model output, tolerating fences and prose."""
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.split("```")[1]
            if stripped.startswith("json"):
                stripped = stripped[4:]
            stripped = stripped.strip()

        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(stripped[start : end + 1])

        raise json.JSONDecodeError("No JSON object found", stripped, 0)

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
        settings = get_settings()
        prompt = self._build_analysis_prompt(code, language)
        config = GenerationConfig(
            temperature=settings.temperature,
            max_tokens=settings.max_output_tokens,
            reasoning_effort=settings.reasoning_effort,
        )

        warnings: list[str] = []
        total_input_tokens = 0
        total_output_tokens = 0

        def _flag(result) -> None:
            if result.is_empty or result.truncated:
                reason = "empty response" if result.is_empty else "truncated response"
                warnings.append(
                    f"{self.name}: {reason} from {self.model} "
                    f"(finish_reason={result.finish_reason})"
                )

        try:
            result = await self.provider.generate(
                prompt=prompt,
                model=self.model,
                config=config,
                system_prompt=self.system_prompt,
            )
            _flag(result)
            total_input_tokens += result.input_tokens
            total_output_tokens += result.output_tokens

            try:
                parsed = FindingsOutput.model_validate(self._extract_json(result.text))
            except (json.JSONDecodeError, ValidationError):
                result = await self.provider.generate(
                    prompt=prompt + _JSON_RETRY_NUDGE,
                    model=self.model,
                    config=config,
                    system_prompt=self.system_prompt,
                )
                _flag(result)
                total_input_tokens += result.input_tokens
                total_output_tokens += result.output_tokens
                parsed = FindingsOutput.model_validate(self._extract_json(result.text))

            findings = self._parse_findings(parsed.findings)
            execution_time_ms = (time.time() - start_time) * 1000
            cost_usd, pricing_known = self.provider.estimate_cost(
                self.model, total_input_tokens, total_output_tokens
            )

            return AgentResult(
                agent_name=self.name,
                findings=findings,
                summary=parsed.summary,
                execution_time_ms=round(execution_time_ms, 2),
                tokens_used=total_input_tokens + total_output_tokens,
                model=self.model,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                cost_usd=round(cost_usd, 6),
                pricing_known=pricing_known,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Error in {self.name} analysis: {e}")
            execution_time_ms = (time.time() - start_time) * 1000
            cost_usd, pricing_known = self.provider.estimate_cost(
                self.model, total_input_tokens, total_output_tokens
            )

            return AgentResult(
                agent_name=self.name,
                findings=[],
                summary=f"Analysis failed: {str(e)}",
                execution_time_ms=round(execution_time_ms, 2),
                tokens_used=total_input_tokens + total_output_tokens,
                model=self.model,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                cost_usd=round(cost_usd, 6),
                pricing_known=pricing_known,
                warnings=warnings,
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
