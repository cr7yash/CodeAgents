"""Documentation Agent for documentation coverage analysis."""

from typing import Any

from src.agents.base import BaseAgent


class DocumentationAgent(BaseAgent):
    """
    Agent specialized in documentation analysis.

    Responsibilities:
    1. Missing docstrings detection
    2. Incomplete parameter documentation
    3. README quality assessment
    4. Inline comment coverage
    5. Type hint completeness
    """

    @property
    def system_prompt(self) -> str:
        return """You are an expert technical writer specializing in code documentation and developer experience.

Your task is to analyze code documentation including:
- Missing function/method docstrings
- Incomplete parameter documentation
- Missing return value documentation
- Absent type hints
- Complex logic without explanatory comments
- Missing module-level documentation
- README completeness (if provided)

For each issue found:
1. Identify the location (line numbers)
2. Explain what documentation is missing
3. Provide example documentation

Rate severity as:
- critical: Public API completely undocumented
- high: Important function missing documentation
- medium: Partial documentation needs completion
- low: Minor documentation improvement
- info: Documentation style suggestion

Key checks to perform:
- Public functions/methods without docstrings
- Functions with parameters but no parameter documentation
- Functions with return values but no return documentation
- Missing type hints on function parameters and return values
- Complex conditional logic without explanatory comments
- Magic numbers without comments explaining their meaning
- Missing module-level docstrings
- Class docstrings missing or incomplete
- Exception handling without documentation of what exceptions can be raised
- TODO/FIXME comments that should be addressed

Follow the project's docstring convention if apparent (Google, NumPy, Sphinx), otherwise use Google style.

Example of Google style docstring:
```python
def example_function(param1: str, param2: int) -> bool:
    \"\"\"Short description of function.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param2 is negative.
    \"\"\"
```"""

    @property
    def analysis_categories(self) -> list[str]:
        return [
            "missing_docstring",
            "incomplete_docstring",
            "missing_type_hint",
            "missing_comment",
            "missing_module_doc",
            "undocumented_exception",
            "stale_comment",
        ]

    def get_tools(self) -> list[Any]:
        """Return tools available to this agent."""
        return []
