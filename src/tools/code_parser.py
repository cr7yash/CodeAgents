"""Code parser using tree-sitter for AST analysis."""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """Information about a function/method."""

    name: str
    line_start: int
    line_end: int
    parameters: list[str]
    body_lines: int
    docstring: str | None = None


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    line_start: int
    line_end: int
    methods: list[FunctionInfo]
    docstring: str | None = None


class CodeParser:
    """
    Parse source code using tree-sitter for AST analysis.

    Supports Python and JavaScript/TypeScript.
    """

    SUPPORTED_LANGUAGES = {"python", "javascript", "typescript"}

    def __init__(self, language: str):
        self.language = language.lower()
        self._parser = None
        self._tree = None

        if self.language not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language: {language}. Falling back to basic parsing.")

    def parse(self, code: str) -> dict[str, Any]:
        """
        Parse code and return structured information.

        Returns a dictionary with:
        - functions: List of FunctionInfo
        - classes: List of ClassInfo
        - imports: List of import statements
        - lines: Total line count
        """
        lines = code.splitlines()

        # Try tree-sitter parsing first
        try:
            return self._parse_with_tree_sitter(code, lines)
        except Exception as e:
            logger.debug(f"Tree-sitter parsing failed: {e}. Using fallback parser.")
            return self._parse_basic(code, lines)

    def _parse_with_tree_sitter(self, code: str, lines: list[str]) -> dict[str, Any]:
        """Parse using tree-sitter (if available)."""
        try:
            import tree_sitter_python as tspython
            from tree_sitter import Language, Parser

            if self.language == "python":
                PY_LANGUAGE = Language(tspython.language())
                parser = Parser(PY_LANGUAGE)
                tree = parser.parse(bytes(code, "utf8"))
                return self._extract_python_info(tree.root_node, code, lines)
            else:
                # Fallback for other languages
                return self._parse_basic(code, lines)

        except ImportError:
            return self._parse_basic(code, lines)

    def _extract_python_info(
        self, root_node: Any, code: str, lines: list[str]
    ) -> dict[str, Any]:
        """Extract information from Python AST."""
        functions: list[FunctionInfo] = []
        classes: list[ClassInfo] = []
        imports: list[str] = []

        def traverse(node: Any) -> None:
            if node.type == "function_definition":
                func_info = self._extract_function_info(node, lines)
                if func_info:
                    functions.append(func_info)

            elif node.type == "class_definition":
                class_info = self._extract_class_info(node, lines)
                if class_info:
                    classes.append(class_info)

            elif node.type in ("import_statement", "import_from_statement"):
                import_text = code[node.start_byte : node.end_byte]
                imports.append(import_text)

            for child in node.children:
                traverse(child)

        traverse(root_node)

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "lines": len(lines),
        }

    def _extract_function_info(self, node: Any, lines: list[str]) -> FunctionInfo | None:
        """Extract function information from AST node."""
        try:
            name = ""
            parameters: list[str] = []
            docstring = None

            for child in node.children:
                if child.type == "identifier":
                    name = child.text.decode("utf8")
                elif child.type == "parameters":
                    for param in child.children:
                        if param.type == "identifier":
                            parameters.append(param.text.decode("utf8"))
                        elif param.type in ("typed_parameter", "default_parameter"):
                            for p in param.children:
                                if p.type == "identifier":
                                    parameters.append(p.text.decode("utf8"))
                                    break
                elif child.type == "block":
                    # Check for docstring
                    for stmt in child.children:
                        if stmt.type == "expression_statement":
                            for expr in stmt.children:
                                if expr.type == "string":
                                    docstring = expr.text.decode("utf8")
                            break

            line_start = node.start_point[0] + 1
            line_end = node.end_point[0] + 1
            body_lines = line_end - line_start

            return FunctionInfo(
                name=name,
                line_start=line_start,
                line_end=line_end,
                parameters=parameters,
                body_lines=body_lines,
                docstring=docstring,
            )
        except Exception as e:
            logger.debug(f"Failed to extract function info: {e}")
            return None

    def _extract_class_info(self, node: Any, lines: list[str]) -> ClassInfo | None:
        """Extract class information from AST node."""
        try:
            name = ""
            methods: list[FunctionInfo] = []
            docstring = None

            for child in node.children:
                if child.type == "identifier":
                    name = child.text.decode("utf8")
                elif child.type == "block":
                    for stmt in child.children:
                        if stmt.type == "function_definition":
                            func_info = self._extract_function_info(stmt, lines)
                            if func_info:
                                methods.append(func_info)
                        elif stmt.type == "expression_statement":
                            for expr in stmt.children:
                                if expr.type == "string" and docstring is None:
                                    docstring = expr.text.decode("utf8")

            line_start = node.start_point[0] + 1
            line_end = node.end_point[0] + 1

            return ClassInfo(
                name=name,
                line_start=line_start,
                line_end=line_end,
                methods=methods,
                docstring=docstring,
            )
        except Exception as e:
            logger.debug(f"Failed to extract class info: {e}")
            return None

    def _parse_basic(self, code: str, lines: list[str]) -> dict[str, Any]:
        """Basic parsing without tree-sitter (fallback)."""
        functions: list[FunctionInfo] = []
        classes: list[ClassInfo] = []
        imports: list[str] = []

        if self.language == "python":
            return self._parse_python_basic(lines)
        elif self.language in ("javascript", "typescript"):
            return self._parse_js_basic(lines)

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "lines": len(lines),
        }

    def _parse_python_basic(self, lines: list[str]) -> dict[str, Any]:
        """Basic Python parsing using regex."""
        import re

        functions: list[FunctionInfo] = []
        classes: list[ClassInfo] = []
        imports: list[str] = []

        func_pattern = re.compile(r"^\s*def\s+(\w+)\s*\(([^)]*)\)")
        class_pattern = re.compile(r"^\s*class\s+(\w+)")
        import_pattern = re.compile(r"^(import\s+.+|from\s+.+\s+import\s+.+)")

        current_func_start = None
        current_func_name = None
        current_func_params: list[str] = []
        indent_level = 0

        for i, line in enumerate(lines, 1):
            # Check imports
            import_match = import_pattern.match(line)
            if import_match:
                imports.append(import_match.group(1))
                continue

            # Check function definitions
            func_match = func_pattern.match(line)
            if func_match:
                # Close previous function if any
                if current_func_start is not None:
                    functions.append(
                        FunctionInfo(
                            name=current_func_name or "",
                            line_start=current_func_start,
                            line_end=i - 1,
                            parameters=current_func_params,
                            body_lines=i - 1 - current_func_start,
                        )
                    )

                current_func_start = i
                current_func_name = func_match.group(1)
                params_str = func_match.group(2)
                current_func_params = [
                    p.strip().split(":")[0].split("=")[0].strip()
                    for p in params_str.split(",")
                    if p.strip() and p.strip() != "self"
                ]
                indent_level = len(line) - len(line.lstrip())

            # Check class definitions
            class_match = class_pattern.match(line)
            if class_match:
                classes.append(
                    ClassInfo(
                        name=class_match.group(1),
                        line_start=i,
                        line_end=i,  # Will be updated later
                        methods=[],
                    )
                )

        # Close last function if any
        if current_func_start is not None:
            functions.append(
                FunctionInfo(
                    name=current_func_name or "",
                    line_start=current_func_start,
                    line_end=len(lines),
                    parameters=current_func_params,
                    body_lines=len(lines) - current_func_start,
                )
            )

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "lines": len(lines),
        }

    def _parse_js_basic(self, lines: list[str]) -> dict[str, Any]:
        """Basic JavaScript/TypeScript parsing using regex."""
        import re

        functions: list[FunctionInfo] = []
        imports: list[str] = []

        # Match various function patterns
        func_patterns = [
            re.compile(r"^\s*function\s+(\w+)\s*\(([^)]*)\)"),
            re.compile(r"^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
            re.compile(r"^\s*(?:const|let|var)\s+(\w+)\s*=\s*function"),
            re.compile(r"^\s*(\w+)\s*\([^)]*\)\s*{"),  # method shorthand
        ]
        import_pattern = re.compile(r"^import\s+.+")

        for i, line in enumerate(lines, 1):
            if import_pattern.match(line):
                imports.append(line.strip())
                continue

            for pattern in func_patterns:
                match = pattern.match(line)
                if match:
                    functions.append(
                        FunctionInfo(
                            name=match.group(1),
                            line_start=i,
                            line_end=i,  # Simplified
                            parameters=[],
                            body_lines=1,
                        )
                    )
                    break

        return {
            "functions": functions,
            "classes": [],
            "imports": imports,
            "lines": len(lines),
        }

    def get_functions(self, parsed: dict[str, Any]) -> list[FunctionInfo]:
        """Get all functions from parsed result."""
        return parsed.get("functions", [])

    def get_classes(self, parsed: dict[str, Any]) -> list[ClassInfo]:
        """Get all classes from parsed result."""
        return parsed.get("classes", [])
