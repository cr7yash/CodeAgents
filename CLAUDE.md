# CodeAgents: Multi-Agent Code Review System
## Claude Code Implementation Guide

---

## Project Context

You are building **CodeAgents**, a multi-agent code review system where specialized AI agents collaborate to perform comprehensive code reviews. This project demonstrates expertise in agentic AI, LangChain/LangGraph, and multi-agent orchestration for a software engineering internship portfolio.

**Target Role Context:** AI & Modeling Center of Excellence internship requiring experience with "autonomous AI agents and multi-agent workflows" and "Agentic AI tools (LangChain, AutoGen)."

---

## Implementation Status

This file is the original design spec. The build has diverged from it in ways worth knowing before trusting anything below at face value:

- **LLM access is the Portkey AI gateway**, not direct Anthropic/OpenAI SDKs. `src/providers/` wraps a single `AsyncOpenAI` client pointed at Portkey's OpenAI-compatible endpoint, reaching 46 models across OpenAI, Anthropic, Google, Mistral, and others behind one `PORTKEY_API_KEY`. Agents use `provider.generate()` + tolerant JSON parsing, not `ChatAnthropic`/`ChatOpenAI`/`with_structured_output()`. See `src/providers/portkey_catalog.py` for the model catalog and per-model parameter matrix, and the README's "Supported Models" section.
- **Implemented**: `src/agents/` (all 4 agents), `src/orchestrator/` (LangGraph graph + aggregator), `src/tools/` (parser, complexity, pattern matcher, secret scanner — not yet wired into any agent's `get_tools()`, which all return `[]`), `src/models/`, `src/config/`, `src/cli.py` (Click + Rich, including `review`, `agents`, and `models` commands).
- **Not implemented**: `src/api/` (FastAPI app — only empty package stubs exist), `frontend/` (React dashboard), `scripts/`, Celery/Redis background jobs, PostgreSQL persistence, Docker deployment. Phases 5 and 6 below, and any FastAPI/Celery/PostgreSQL/React code shown in this file, are aspirational — nothing under those phases has been built.
- The system prompts, agent responsibilities, key checks, and output format specification below are still accurate and in effect.

---

## System Overview

### What We're Building

A system where 4 specialized AI agents analyze code from different perspectives:

1. **Quality Agent** - Code smells, complexity, SOLID violations
2. **Security Agent** - OWASP vulnerabilities, injection risks, secrets detection
3. **Performance Agent** - Time/space complexity, inefficient patterns
4. **Documentation Agent** - Missing docstrings, README quality

An **Orchestrator** coordinates these agents, runs them in parallel where possible, and aggregates their findings into a unified report.

### Architecture

```
                    ┌─────────────────────┐
                    │   User Input        │
                    │   (Code + Config)   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Orchestrator      │
                    │   (LangGraph)       │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │ Quality   │       │ Security  │       │Performance│
    │ Agent     │       │ Agent     │       │ Agent     │
    └─────┬─────┘       └─────┬─────┘       └─────┬─────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Aggregator        │
                    │   (Final Report)    │
                    └─────────────────────┘
```

---

## Technical Requirements

### Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Agent Framework | LangGraph | Latest |
| LLM Access | Portkey AI gateway (via `openai` SDK) | Latest |
| Code Parsing | tree-sitter | Latest |
| API Framework | FastAPI (not yet implemented) | Latest |
| Task Queue | Celery + Redis (not yet implemented) | Latest |
| Database | PostgreSQL (not yet implemented) | 15+ |
| Frontend | React + TypeScript | 18+ |
| Containerization | Docker + docker-compose | Latest |

### Project Structure

```
codeagents/
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── .env.example
│
├── src/
│   ├── __init__.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py              # Base agent class
│   │   ├── quality_agent.py     # Code quality analysis
│   │   ├── security_agent.py    # Security vulnerability detection
│   │   ├── performance_agent.py # Performance analysis
│   │   └── documentation_agent.py # Documentation coverage
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── graph.py             # LangGraph workflow definition
│   │   ├── state.py             # Shared state definitions
│   │   └── aggregator.py        # Result aggregation logic
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── code_parser.py       # tree-sitter parsing
│   │   ├── complexity.py        # Cyclomatic complexity calculator
│   │   ├── pattern_matcher.py   # Anti-pattern detection
│   │   └── secret_scanner.py    # Hardcoded secrets detection
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── review.py            # Review result models
│   │   ├── finding.py           # Individual finding model
│   │   └── report.py            # Final report model
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── routes/
│   │   │   ├── review.py        # Review endpoints
│   │   │   └── health.py        # Health check
│   │   └── dependencies.py      # DI containers
│   │
│   └── config/
│       ├── __init__.py
│       └── settings.py          # Pydantic settings
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_agents/
│   ├── test_orchestrator/
│   └── fixtures/
│       └── sample_code/         # Test code samples
│
├── frontend/                    # React dashboard (Phase 3)
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   └── pages/
│   └── ...
│
└── scripts/
    ├── run_review.py            # CLI entry point
    └── seed_db.py               # Database seeding
```

---

## Implementation Phases

### Phase 1: Core Agent Framework (Priority: HIGH)

#### Task 1.1: Project Setup

```bash
# Initialize project with uv or poetry
# Set up pyproject.toml with dependencies:
# - langgraph
# - openai            (Portkey speaks the OpenAI-compatible protocol)
# - tree-sitter
# - tree-sitter-python
# - tree-sitter-javascript
# - pydantic
# - rich (for CLI output)
```

**Acceptance Criteria:**
- [ ] Project initializes without errors
- [ ] All dependencies install correctly
- [ ] Basic CLI runs: `python -m codeagents --help`

#### Task 1.2: Base Agent Implementation

> As built, `BaseAgent` resolves its model from settings/per-agent overrides, calls a shared `PortkeyProvider.generate()`, and parses the response with tolerant JSON extraction rather than `with_structured_output()`. See `src/agents/base.py` and `src/providers/` for the actual implementation; the sketch below is the original design intent and predates the Portkey migration.

Create the base agent class that all specialized agents inherit from:

```python
# src/agents/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel

class Finding(BaseModel):
    """Individual code review finding"""
    severity: str  # "critical", "high", "medium", "low", "info"
    category: str  # e.g., "security", "quality", "performance"
    title: str
    description: str
    line_start: int | None = None
    line_end: int | None = None
    suggestion: str | None = None
    code_snippet: str | None = None

class AgentResult(BaseModel):
    """Result from a single agent's analysis"""
    agent_name: str
    findings: List[Finding]
    summary: str
    execution_time_ms: float
    tokens_used: int

class BaseAgent(ABC):
    """
    Base class for all code review agents.
    Each agent specializes in a specific type of analysis.
    """
    
    def __init__(self, model: str | None = None):
        # Resolves to a per-agent override, then DEFAULT_MODEL, then reaches
        # the model through the shared Portkey gateway provider.
        self.model = model or ...
        self.provider = get_provider()
        self.name = self.__class__.__name__
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Define the agent's specialized system prompt"""
        pass
    
    @property
    @abstractmethod
    def analysis_categories(self) -> List[str]:
        """Categories this agent analyzes"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Any]:
        """Return tools available to this agent"""
        pass
    
    async def analyze(self, code: str, language: str, context: Dict[str, Any] = None) -> AgentResult:
        """
        Analyze code and return findings.
        Implement the core analysis logic here.
        """
        pass
```

**Acceptance Criteria:**
- [ ] BaseAgent class is abstract and cannot be instantiated directly
- [ ] Finding and AgentResult models validate correctly
- [ ] Subclasses must implement all abstract methods

#### Task 1.3: Quality Agent

```python
# src/agents/quality_agent.py

"""
Quality Agent responsibilities:
1. Detect code smells (long methods, deep nesting, god classes)
2. Check SOLID principle violations
3. Calculate cyclomatic complexity
4. Identify code duplication patterns
5. Suggest refactoring opportunities

Tools to use:
- tree-sitter for AST analysis
- Custom complexity calculator
- Pattern matcher for anti-patterns
"""
```

**System Prompt Requirements:**
- Expert in clean code principles
- Familiar with SOLID, DRY, KISS
- Provides actionable refactoring suggestions
- References specific line numbers

**Key Checks:**
- Methods longer than 20 lines
- Nesting deeper than 3 levels
- Cyclomatic complexity > 10
- Classes with more than 5 public methods
- Duplicate code blocks

#### Task 1.4: Security Agent

```python
# src/agents/security_agent.py

"""
Security Agent responsibilities:
1. OWASP Top 10 vulnerability detection
2. SQL injection patterns
3. XSS vulnerability identification
4. Hardcoded secrets/credentials
5. Insecure dependencies (if package info provided)

Tools to use:
- Regex patterns for common vulnerabilities
- Secret pattern matcher (API keys, passwords)
- Known vulnerable pattern database
"""
```

**System Prompt Requirements:**
- Expert in application security
- Familiar with OWASP, CWE, CVE
- Explains attack vectors clearly
- Provides secure alternatives

**Key Checks:**
- SQL string concatenation
- `eval()`, `exec()` usage
- Hardcoded passwords/API keys
- Insecure random number generation
- Missing input validation

#### Task 1.5: Performance Agent

```python
# src/agents/performance_agent.py

"""
Performance Agent responsibilities:
1. Time complexity analysis (Big O)
2. Memory leak patterns
3. N+1 query detection (if DB code)
4. Inefficient loop patterns
5. Caching opportunities

Tools to use:
- AST analysis for loop detection
- Pattern matcher for known inefficiencies
"""
```

**System Prompt Requirements:**
- Expert in algorithm optimization
- Explains Big O notation
- Identifies memory issues
- Suggests concrete optimizations

**Key Checks:**
- Nested loops over collections
- Repeated expensive operations
- Missing early returns
- Inefficient data structures
- Synchronous blocking calls

#### Task 1.6: Documentation Agent

```python
# src/agents/documentation_agent.py

"""
Documentation Agent responsibilities:
1. Missing docstrings detection
2. Incomplete parameter documentation
3. README quality assessment
4. Inline comment coverage
5. Type hint completeness

Tools to use:
- AST for docstring extraction
- Type hint parser
"""
```

**System Prompt Requirements:**
- Expert in technical documentation
- Understands docstring conventions (Google, NumPy, Sphinx)
- Values clarity over verbosity

**Key Checks:**
- Public functions without docstrings
- Missing parameter descriptions
- No return type documentation
- Complex logic without comments
- Missing type hints

---

### Phase 2: LangGraph Orchestration (Priority: HIGH)

#### Task 2.1: State Definition

```python
# src/orchestrator/state.py

from typing import TypedDict, List, Annotated
from langgraph.graph.message import add_messages

class ReviewState(TypedDict):
    """
    Shared state passed between all nodes in the graph.
    """
    # Input
    code: str
    language: str
    file_path: str | None
    
    # Agent results (populated during execution)
    quality_result: AgentResult | None
    security_result: AgentResult | None
    performance_result: AgentResult | None
    documentation_result: AgentResult | None
    
    # Output
    final_report: FinalReport | None
    
    # Metadata
    messages: Annotated[list, add_messages]
    errors: List[str]
```

#### Task 2.2: Graph Definition

```python
# src/orchestrator/graph.py

from langgraph.graph import StateGraph, START, END

def create_review_graph() -> StateGraph:
    """
    Create the multi-agent review workflow.
    
    Flow:
    1. START -> [quality, security, performance, docs] (parallel)
    2. All agents -> aggregator
    3. aggregator -> END
    
    Use add_conditional_edges if you need dynamic routing.
    """
    
    workflow = StateGraph(ReviewState)
    
    # Add agent nodes
    workflow.add_node("quality_agent", run_quality_agent)
    workflow.add_node("security_agent", run_security_agent)
    workflow.add_node("performance_agent", run_performance_agent)
    workflow.add_node("documentation_agent", run_documentation_agent)
    workflow.add_node("aggregator", aggregate_results)
    
    # Parallel execution from START
    workflow.add_edge(START, "quality_agent")
    workflow.add_edge(START, "security_agent")
    workflow.add_edge(START, "performance_agent")
    workflow.add_edge(START, "documentation_agent")
    
    # All agents feed into aggregator
    workflow.add_edge("quality_agent", "aggregator")
    workflow.add_edge("security_agent", "aggregator")
    workflow.add_edge("performance_agent", "aggregator")
    workflow.add_edge("documentation_agent", "aggregator")
    
    # Aggregator produces final output
    workflow.add_edge("aggregator", END)
    
    return workflow.compile()
```

#### Task 2.3: Result Aggregation

```python
# src/orchestrator/aggregator.py

"""
Aggregator responsibilities:
1. Collect results from all agents
2. Deduplicate overlapping findings
3. Resolve conflicts (e.g., if quality and security flag same issue)
4. Prioritize findings by severity
5. Generate executive summary
6. Calculate overall code health score

Output format:
- Executive summary (2-3 sentences)
- Critical findings (must fix)
- High priority findings
- Medium/low findings
- Overall score (0-100)
- Metrics (lines analyzed, issues found, etc.)
"""
```

---

### Phase 3: Tools Implementation (Priority: MEDIUM)

#### Task 3.1: Code Parser (tree-sitter)

```python
# src/tools/code_parser.py

"""
Implement tree-sitter based code parsing.

Features needed:
1. Parse Python and JavaScript/TypeScript
2. Extract function definitions with line numbers
3. Extract class definitions
4. Get AST for complexity analysis
5. Find all function calls

Example usage:
    parser = CodeParser("python")
    ast = parser.parse(code)
    functions = parser.get_functions(ast)
"""
```

#### Task 3.2: Complexity Calculator

```python
# src/tools/complexity.py

"""
Calculate cyclomatic complexity.

McCabe's formula:
CC = E - N + 2P
Where:
- E = number of edges in the control flow graph
- N = number of nodes
- P = number of connected components

Simpler approximation:
CC = 1 + number of decision points (if, for, while, case, catch, &&, ||)

Return:
- Per-function complexity scores
- File-level aggregate
- Flag functions with CC > 10
"""
```

#### Task 3.3: Secret Scanner

```python
# src/tools/secret_scanner.py

"""
Detect hardcoded secrets using regex patterns.

Patterns to detect:
- AWS keys: AKIA[0-9A-Z]{16}
- Generic API keys: api[_-]?key[_-]?[=:]["']?[a-zA-Z0-9]{20,}
- Passwords: password[_-]?[=:]["']?[^\s"']{8,}
- Private keys: -----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----
- JWT tokens: eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*
- Generic secrets: secret[_-]?[=:]["']?[^\s"']{8,}

Return line numbers and masked versions of detected secrets.
"""
```

---

### Phase 4: CLI Interface (Priority: MEDIUM)

#### Task 4.1: CLI Implementation

```python
# scripts/run_review.py

"""
CLI for running code reviews.

Usage:
    codeagents review <file_or_directory> [options]
    codeagents review ./src/main.py
    codeagents review ./src --language python
    codeagents review ./src -o report.json --format json

Options:
    -l, --language    Language (auto-detect if not specified)
    -o, --output      Output file path
    -f, --format      Output format: text, json, markdown, html
    --agents          Comma-separated list of agents to run
    --severity        Minimum severity to report: critical, high, medium, low
    --verbose         Show detailed progress

Use 'rich' library for beautiful terminal output with:
- Progress bars during analysis
- Colored severity indicators
- Tables for findings summary
- Syntax-highlighted code snippets
"""
```

---

### Phase 5: FastAPI Backend (Priority: MEDIUM)

#### Task 5.1: API Endpoints

```python
# src/api/routes/review.py

"""
REST API endpoints:

POST /api/v1/review
    - Submit code for review
    - Body: { "code": str, "language": str, "options": {...} }
    - Returns: { "job_id": str }

GET /api/v1/review/{job_id}
    - Get review status/results
    - Returns: { "status": str, "result": {...} | null }

POST /api/v1/review/file
    - Upload file for review
    - Multipart form with file

GET /api/v1/review/{job_id}/stream
    - SSE endpoint for real-time progress updates

WebSocket /api/v1/ws/review
    - Real-time bidirectional for interactive reviews
"""
```

#### Task 5.2: Background Jobs

```python
# Use Celery for async job processing

"""
Job flow:
1. API receives review request
2. Create job record in PostgreSQL
3. Queue job to Celery
4. Worker picks up job, runs LangGraph
5. Store results in PostgreSQL
6. Notify via WebSocket/SSE
"""
```

---

### Phase 6: React Dashboard (Priority: LOW)

#### Task 6.1: Dashboard Features

```
Dashboard pages:
1. Home - Submit new review, paste code or upload file
2. Results - View review findings with filters
3. History - Past reviews with search
4. Analytics - Trends over time (if implementing)

Components needed:
- CodeEditor (Monaco or CodeMirror)
- FindingCard - Display individual finding
- SeverityBadge - Color-coded severity
- AgentProgress - Show which agents are running
- ReportView - Full report display
```

---

## Agent System Prompts

### Quality Agent System Prompt

```
You are an expert code quality analyst specializing in clean code principles, design patterns, and software craftsmanship.

Your task is to analyze code for quality issues including:
- Code smells (long methods, deep nesting, god classes, feature envy)
- SOLID principle violations
- DRY violations (code duplication)
- Complex conditional logic
- Poor naming conventions
- Missing abstractions

For each issue found:
1. Identify the specific location (line numbers)
2. Explain why it's a problem
3. Suggest a concrete refactoring

Rate severity as:
- critical: Major architectural issue affecting maintainability
- high: Significant code smell that should be addressed
- medium: Moderate issue worth fixing
- low: Minor improvement opportunity
- info: Suggestion or best practice note

Be specific and actionable. Reference line numbers. Provide code examples for suggestions when helpful.
```

### Security Agent System Prompt

```
You are an expert application security analyst specializing in identifying vulnerabilities in source code.

Your task is to analyze code for security issues including:
- Injection vulnerabilities (SQL, Command, LDAP, XPath)
- Cross-Site Scripting (XSS) risks
- Hardcoded secrets and credentials
- Insecure cryptographic practices
- Authentication/authorization flaws
- Input validation issues
- Insecure deserialization
- Security misconfiguration

For each vulnerability found:
1. Identify the exact location (line numbers)
2. Explain the attack vector
3. Assess the potential impact
4. Provide a secure alternative

Rate severity based on:
- critical: Exploitable vulnerability with severe impact
- high: Significant security risk
- medium: Moderate risk requiring attention
- low: Minor security consideration
- info: Security best practice recommendation

Reference OWASP, CWE, or CVE identifiers when applicable. Always provide secure code alternatives.
```

### Performance Agent System Prompt

```
You are an expert performance analyst specializing in code optimization and efficiency.

Your task is to analyze code for performance issues including:
- Inefficient algorithms (poor time complexity)
- Memory leaks and excessive allocations
- N+1 query patterns
- Blocking operations in async contexts
- Inefficient data structure choices
- Missing caching opportunities
- Redundant computations
- I/O bottlenecks

For each issue found:
1. Identify the location (line numbers)
2. Explain the performance impact with Big O notation when relevant
3. Estimate the magnitude of impact (e.g., "O(n²) becomes problematic above 1000 items")
4. Suggest optimized alternatives

Rate severity as:
- critical: Causes system degradation or crashes at scale
- high: Significant performance impact
- medium: Noticeable performance issue
- low: Minor optimization opportunity
- info: Performance best practice

Provide concrete optimization suggestions with example code when helpful.
```

### Documentation Agent System Prompt

```
You are an expert technical writer specializing in code documentation and developer experience.

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

Follow the project's docstring convention if apparent (Google, NumPy, Sphinx), otherwise use Google style.
```

---

## Output Format Specification

### JSON Output Schema

```json
{
  "review_id": "uuid",
  "timestamp": "ISO8601",
  "input": {
    "file_path": "string | null",
    "language": "string",
    "lines_of_code": "number"
  },
  "summary": {
    "overall_score": "number (0-100)",
    "total_findings": "number",
    "critical": "number",
    "high": "number",
    "medium": "number",
    "low": "number",
    "info": "number",
    "executive_summary": "string"
  },
  "agents": {
    "quality": {
      "score": "number",
      "findings_count": "number",
      "execution_time_ms": "number"
    },
    "security": { ... },
    "performance": { ... },
    "documentation": { ... }
  },
  "findings": [
    {
      "id": "uuid",
      "agent": "string",
      "severity": "critical|high|medium|low|info",
      "category": "string",
      "title": "string",
      "description": "string",
      "location": {
        "line_start": "number",
        "line_end": "number",
        "column_start": "number | null",
        "column_end": "number | null"
      },
      "code_snippet": "string | null",
      "suggestion": "string | null",
      "references": ["string"]
    }
  ],
  "metadata": {
    "agents_used": ["string"],
    "total_execution_time_ms": "number",
    "tokens_used": "number"
  }
}
```

---

## Testing Requirements

### Test Cases to Implement

```python
# tests/fixtures/sample_code/

# 1. vulnerable_code.py - Code with known security issues
# 2. complex_code.py - High cyclomatic complexity
# 3. undocumented_code.py - Missing all documentation
# 4. slow_code.py - O(n²) algorithms, N+1 patterns
# 5. clean_code.py - Well-written code (should have minimal findings)
# 6. mixed_issues.py - Combination of all issue types
```

### Test Structure

```python
# tests/test_agents/test_security_agent.py

async def test_detects_sql_injection():
    """Security agent should flag SQL string concatenation"""
    code = '''
    def get_user(user_id):
        query = "SELECT * FROM users WHERE id = " + user_id
        return db.execute(query)
    '''
    result = await security_agent.analyze(code, "python")
    assert any(f.category == "sql_injection" for f in result.findings)

async def test_detects_hardcoded_secrets():
    """Security agent should flag hardcoded API keys"""
    code = '''
    API_KEY = "AKIA1234567890ABCDEF"
    '''
    result = await security_agent.analyze(code, "python")
    assert any(f.category == "hardcoded_secret" for f in result.findings)
```

---

## Environment Setup

### Required Environment Variables

```bash
# .env.example — as actually implemented; see the real file for the full list

# LLM Access (Portkey AI gateway — one key reaches all 46 catalogued models)
PORTKEY_API_KEY=your_portkey_api_key_here
PORTKEY_BASE_URL=https://api.portkey.ai/v1

# Model settings
DEFAULT_MODEL=claude-sonnet-4-5
MAX_OUTPUT_TOKENS=4000
# Per-agent overrides: QUALITY_MODEL, SECURITY_MODEL, PERFORMANCE_MODEL, DOCUMENTATION_MODEL

# Database (for Phase 5+, not yet implemented)
DATABASE_URL=postgresql://user:pass@localhost:5432/codeagents

# Redis (for Phase 5+, not yet implemented)
REDIS_URL=redis://localhost:6379/0

# Optional
LOG_LEVEL=INFO
MAX_CODE_LENGTH=50000
```

### Docker Compose (for Phase 5+)

```yaml
# docker-compose.yml

version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/codeagents
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: celery -A src.worker worker --loglevel=info
    depends_on:
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=codeagents
      - POSTGRES_PASSWORD=postgres

  redis:
    image: redis:7-alpine
```

---

## Implementation Checklist

### MVP (Weeks 1-2)
- [ ] Project setup with dependencies
- [ ] BaseAgent class implementation
- [ ] Quality Agent (basic)
- [ ] Security Agent (basic)
- [ ] LangGraph orchestration with 2 agents
- [ ] CLI that accepts a file and outputs JSON
- [ ] Basic tests for both agents

### Full Agent Suite (Weeks 3-4)
- [ ] Performance Agent
- [ ] Documentation Agent
- [ ] Parallel execution in LangGraph
- [ ] Result aggregation and scoring
- [ ] Markdown and HTML output formats
- [ ] tree-sitter integration for better parsing
- [ ] Comprehensive test suite

### Production Features (Weeks 5-6)
- [ ] FastAPI backend
- [ ] Celery background jobs
- [ ] PostgreSQL persistence
- [ ] React dashboard (basic)
- [ ] GitHub webhook integration (optional)
- [ ] Docker deployment

---

## Success Metrics

Track these to include in resume bullet points:

1. **Accuracy**: % of true positives in findings
2. **Coverage**: Types of issues detected
3. **Speed**: Time to analyze 500 lines of code
4. **Agent Agreement**: How often agents flag same issues
5. **False Positive Rate**: % of incorrect findings

Target metrics:
- Process 500 LOC in < 30 seconds
- 85%+ accuracy on security findings
- < 10% false positive rate
- Support Python + JavaScript

---

## Commands Reference

```bash
# Development
uv run python -m codeagents review ./sample.py
uv run pytest tests/ -v
uv run python -m codeagents review ./src --format markdown -o report.md

# With Docker (Phase 5+)
docker-compose up -d
curl -X POST http://localhost:8000/api/v1/review -d '{"code": "...", "language": "python"}'
```

---

## Notes for Claude Code

1. **Start simple**: Get 2 agents working end-to-end before adding more
2. **Test early**: Write tests alongside implementation
3. **Use structured output**: LangChain's `with_structured_output()` for reliable JSON
4. **Handle errors gracefully**: Agents should not crash on malformed code
5. **Log everything**: Use Python logging for debugging
6. **Type hints everywhere**: Makes the code self-documenting

When stuck, focus on getting one complete vertical slice working (submit code → run agents → get report) before expanding horizontally.