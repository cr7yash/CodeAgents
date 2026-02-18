"""Cyclomatic complexity calculator."""

import re
from dataclasses import dataclass


@dataclass
class ComplexityResult:
    """Result of complexity analysis for a function."""

    name: str
    line_start: int
    line_end: int
    complexity: int
    is_complex: bool  # True if complexity > threshold


class ComplexityCalculator:
    """
    Calculate cyclomatic complexity for code.

    Uses the simplified formula:
    CC = 1 + number of decision points (if, for, while, case, catch, &&, ||)
    """

    # Default threshold for flagging complex functions
    DEFAULT_THRESHOLD = 10

    # Decision point patterns for different languages
    PYTHON_PATTERNS = [
        r"\bif\b",
        r"\belif\b",
        r"\bfor\b",
        r"\bwhile\b",
        r"\bexcept\b",
        r"\band\b",
        r"\bor\b",
        r"\bif\s+.+\s+else\b",  # ternary
        r"\bfor\s+.+\s+in\s+.+\s+if\b",  # list comprehension with condition
    ]

    JS_PATTERNS = [
        r"\bif\b",
        r"\belse\s+if\b",
        r"\bfor\b",
        r"\bwhile\b",
        r"\bcase\b",
        r"\bcatch\b",
        r"\?\?",  # nullish coalescing
        r"\?\.",  # optional chaining with condition
        r"&&",
        r"\|\|",
        r"\?[^:]+:",  # ternary operator
    ]

    def __init__(self, language: str, threshold: int = DEFAULT_THRESHOLD):
        self.language = language.lower()
        self.threshold = threshold

        if self.language == "python":
            self.patterns = [re.compile(p) for p in self.PYTHON_PATTERNS]
        elif self.language in ("javascript", "typescript"):
            self.patterns = [re.compile(p) for p in self.JS_PATTERNS]
        else:
            self.patterns = [re.compile(p) for p in self.PYTHON_PATTERNS]

    def calculate(self, code: str) -> int:
        """
        Calculate cyclomatic complexity for a code block.

        Args:
            code: Source code to analyze

        Returns:
            Cyclomatic complexity score
        """
        complexity = 1  # Base complexity

        for pattern in self.patterns:
            complexity += len(pattern.findall(code))

        return complexity

    def calculate_per_function(
        self, code: str, functions: list[dict] | None = None
    ) -> list[ComplexityResult]:
        """
        Calculate complexity for each function in the code.

        Args:
            code: Full source code
            functions: Optional list of function info dicts with
                      name, line_start, line_end

        Returns:
            List of ComplexityResult for each function
        """
        results: list[ComplexityResult] = []
        lines = code.splitlines()

        if functions is None:
            # Try to extract functions automatically
            functions = self._extract_functions(code, lines)

        for func in functions:
            name = func.get("name", "unknown")
            line_start = func.get("line_start", 1)
            line_end = func.get("line_end", len(lines))

            # Extract function body
            func_lines = lines[line_start - 1 : line_end]
            func_code = "\n".join(func_lines)

            complexity = self.calculate(func_code)

            results.append(
                ComplexityResult(
                    name=name,
                    line_start=line_start,
                    line_end=line_end,
                    complexity=complexity,
                    is_complex=complexity > self.threshold,
                )
            )

        return results

    def _extract_functions(self, code: str, lines: list[str]) -> list[dict]:
        """Extract function boundaries from code."""
        functions: list[dict] = []

        if self.language == "python":
            func_pattern = re.compile(r"^\s*def\s+(\w+)\s*\(")
            indent_tracker: dict[str, tuple[int, int, int]] = {}  # name -> (start, indent, end)

            for i, line in enumerate(lines, 1):
                match = func_pattern.match(line)
                if match:
                    name = match.group(1)
                    indent = len(line) - len(line.lstrip())

                    # Close any functions with same or higher indent
                    for fname, (start, find, _) in list(indent_tracker.items()):
                        if find >= indent:
                            functions.append(
                                {"name": fname, "line_start": start, "line_end": i - 1}
                            )
                            del indent_tracker[fname]

                    indent_tracker[name] = (i, indent, i)

            # Close remaining functions
            for name, (start, _, _) in indent_tracker.items():
                functions.append({"name": name, "line_start": start, "line_end": len(lines)})

        elif self.language in ("javascript", "typescript"):
            # Simplified JS function detection
            func_patterns = [
                re.compile(r"^\s*function\s+(\w+)\s*\("),
                re.compile(r"^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\("),
            ]

            brace_count = 0
            current_func = None
            func_start = 0

            for i, line in enumerate(lines, 1):
                for pattern in func_patterns:
                    match = pattern.match(line)
                    if match and current_func is None:
                        current_func = match.group(1)
                        func_start = i
                        brace_count = 0
                        break

                if current_func:
                    brace_count += line.count("{") - line.count("}")
                    if brace_count <= 0 and "{" in "".join(lines[func_start - 1 : i]):
                        functions.append(
                            {"name": current_func, "line_start": func_start, "line_end": i}
                        )
                        current_func = None

            if current_func:
                functions.append(
                    {"name": current_func, "line_start": func_start, "line_end": len(lines)}
                )

        return functions

    def get_file_complexity(self, code: str) -> dict:
        """
        Get overall file complexity metrics.

        Returns:
            Dict with total complexity, average per function, max, etc.
        """
        results = self.calculate_per_function(code)

        if not results:
            return {
                "total_functions": 0,
                "total_complexity": self.calculate(code),
                "average_complexity": 0,
                "max_complexity": 0,
                "complex_functions": 0,
                "complex_function_names": [],
            }

        complexities = [r.complexity for r in results]
        complex_funcs = [r for r in results if r.is_complex]

        return {
            "total_functions": len(results),
            "total_complexity": sum(complexities),
            "average_complexity": round(sum(complexities) / len(results), 2),
            "max_complexity": max(complexities),
            "complex_functions": len(complex_funcs),
            "complex_function_names": [f.name for f in complex_funcs],
        }
