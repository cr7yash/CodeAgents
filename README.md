# CodeAgents: Multi-Agent Code Review System

A multi-agent AI system where **4 specialized agents** collaborate via **LangGraph** to perform comprehensive, parallel code reviews. Each agent analyzes code from a different perspective (quality, security, performance, documentation), and an orchestrator aggregates their findings into a unified report with deduplication and severity-based scoring.

Built with **LangChain**, **LangGraph**, and **Groq** (LLaMA 3.3 70B).

## Architecture

```
User Input (Code + Language)
           |
           v
    +--------------+
    | Orchestrator  |  (LangGraph StateGraph)
    +------+-------+
           |
    +------+------+--------------+--------------+
    v             v              v              v
+--------+  +--------+   +-----------+  +-------------+
|Quality |  |Security|   |Performance|  |Documentation|
| Agent  |  | Agent  |   |  Agent    |  |   Agent     |
+---+----+  +---+----+   +-----+-----+  +------+------+
    |           |              |               |
    +-----------+------+-------+---------------+
                       v
              +----------------+
              |   Aggregator   |
              | (Dedupe/Score) |
              +-------+--------+
                      v
               Final Report
```

All 4 agents run **in parallel** via LangGraph's fan-out pattern, then results are aggregated, deduplicated, and scored.

## Demo

Running `codeagents review ./sample_review.py` on a file with intentional security, quality, and performance issues:

```
$ uv run codeagents review ./sample_review.py

╭──── CodeAgents ────╮
│ Code Review Report │
│ Score: 25.0/100    │
╰────────────────────╯
      Summary
┏━━━━━━━━━━┳━━━━━━━┓
┃ Severity ┃ Count ┃
┡━━━━━━━━━━╇━━━━━━━┩
│ Critical │     2 │
│ High     │     3 │
│ Medium   │     6 │
│ Low      │     2 │
│ Info     │     1 │
│ Total    │    14 │
└──────────┴───────┘

╭──────────────────────────── Executive Summary ─────────────────────────────╮
│ Code review found 14 total issues indicating significant issues requiring │
│ remediation. 2 critical issue(s) require immediate attention. 3           │
│ high-priority issue(s) should be addressed. 8 moderate/low priority       │
│ improvements suggested.                                                   │
╰───────────────────────────────────────────────────────────────────────────╯

                                   Findings
┏━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Severity   ┃  Line ┃ Category             ┃ Title                                   ┃
┡━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ CRITICAL   │    10 │ command_injection     │ Command Injection Vulnerability          │
│ CRITICAL   │    73 │ code_injection        │ Code Injection Vulnerability             │
│ HIGH       │    93 │ security_vulnerabil.. │ Using eval with User Input               │
│ HIGH       │     7 │ code_smell            │ Hardcoded Database Credentials           │
│ HIGH       │    43 │ hardcoded_secrets     │ Hardcoded API Key                        │
│ MEDIUM     │    44 │ performance_issue     │ Inefficient Nested Loop                  │
│ MEDIUM     │    54 │ code_smell            │ Long Method                              │
│ MEDIUM     │    50 │ security_vulnerabil.. │ Missing Type Hints                       │
│ MEDIUM     │    49 │ inefficient_code      │ Inefficient Nested Loop                  │
│ MEDIUM     │    55 │ missing_type_hints    │ Missing Type Hints                       │
│ MEDIUM     │    85 │ global_state          │ Global State Modification                │
│ LOW        │    97 │ code_smell            │ Global Variable                          │
│ LOW        │    79 │ file_handling         │ Insecure File Handling                   │
│ INFO       │     1 │ best_practice         │ Unused Import                            │
└────────────┴───────┴──────────────────────┴─────────────────────────────────────────┘

Agents: QualityAgent, SecurityAgent | Time: 5290ms | Tokens: 0
```

The system detected **14 issues** across multiple categories -- command injection, hardcoded secrets, O(n^2) loops, missing type hints, and more -- scoring the file **25/100**.

## What Each Agent Does

| Agent | Focus | Key Checks |
|-------|-------|------------|
| **Quality** | Clean code, design | Code smells, SOLID violations, cyclomatic complexity >10, deep nesting, god classes |
| **Security** | Vulnerability detection | OWASP Top 10, SQL/command injection, XSS, hardcoded secrets, insecure crypto |
| **Performance** | Efficiency analysis | O(n^2) algorithms, N+1 queries, blocking I/O, missing caching, memory leaks |
| **Documentation** | Documentation coverage | Missing docstrings, incomplete param docs, missing type hints, module docs |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | LangChain + LangGraph |
| LLM Provider | Groq (LLaMA 3.3 70B) |
| Code Parsing | tree-sitter |
| Data Validation | Pydantic v2 |
| CLI | Click + Rich |
| Testing | pytest + pytest-asyncio |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A free [Groq API key](https://console.groq.com)

### Installation

```bash
# Clone the repo
git clone https://github.com/<your-username>/codeagents.git
cd codeagents

# Install dependencies (pick one)
uv sync                 # using uv (recommended)
pip install -e ".[dev]" # using pip

# Set up environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Run a Review

```bash
# Review a Python file
uv run codeagents review ./sample_review.py

# JSON output
uv run codeagents review ./sample_review.py --format json -o report.json

# Markdown output
uv run codeagents review ./sample_review.py --format markdown

# Run specific agents only
uv run codeagents review ./sample_review.py --agents security,quality

# Filter by minimum severity
uv run codeagents review ./sample_review.py --severity high

# List available agents
uv run codeagents agents
```

### Python API

```python
import asyncio
from src.orchestrator import run_review

code = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)
'''

report = asyncio.run(run_review(code, "python"))

print(f"Score: {report.summary.overall_score}/100")
print(f"Findings: {report.summary.total_findings}")

for finding in report.findings:
    print(f"[{finding.severity.value}] {finding.title}")
    print(f"  Line {finding.line_start}: {finding.description}")
```

## Project Structure

```
codeagents/
|-- src/
|   |-- agents/                  # Specialized review agents
|   |   |-- base.py              # BaseAgent ABC with structured LLM output
|   |   |-- quality_agent.py     # SOLID, code smells, complexity
|   |   |-- security_agent.py    # OWASP, injection, secrets
|   |   |-- performance_agent.py # Big O, inefficient patterns
|   |   +-- documentation_agent.py
|   |
|   |-- orchestrator/            # LangGraph workflow
|   |   |-- graph.py             # StateGraph with parallel fan-out
|   |   |-- state.py             # ReviewState TypedDict
|   |   +-- aggregator.py        # Deduplication, scoring, merging
|   |
|   |-- tools/                   # Static analysis utilities
|   |   |-- code_parser.py       # tree-sitter AST parsing
|   |   |-- complexity.py        # Cyclomatic complexity calculator
|   |   |-- secret_scanner.py    # Regex-based secret detection (15+ patterns)
|   |   +-- pattern_matcher.py   # Anti-pattern detection (Python/JS)
|   |
|   |-- models/                  # Pydantic data models
|   |   |-- finding.py           # Finding + Severity enum
|   |   |-- review.py            # AgentResult
|   |   +-- report.py            # FinalReport with scoring
|   |
|   |-- config/
|   |   +-- settings.py          # Pydantic Settings (env-based config)
|   |
|   +-- cli.py                   # Click CLI with Rich output
|
|-- tests/
|   |-- conftest.py              # Shared fixtures
|   |-- test_models.py           # Finding, AgentResult, FinalReport tests
|   |-- test_tools.py            # SecretScanner, Complexity, PatternMatcher
|   |-- test_agents/
|   |   +-- test_base.py         # BaseAgent ABC, parsing, prompt building
|   +-- test_orchestrator/
|       +-- test_aggregator.py   # Aggregation, dedup, similarity, merging
|
|-- tests/fixtures/sample_code/  # Test fixtures with intentional issues
|   |-- vulnerable_code.py       # SQL injection, hardcoded secrets, eval
|   |-- complex_code.py          # Deep nesting, god class, magic numbers
|   |-- slow_code.py             # O(n^2), N+1 queries, string concat in loops
|   |-- undocumented_code.py     # Missing docstrings, no type hints
|   |-- clean_code.py            # Well-written code (minimal findings)
|   +-- mixed_issues.py          # Combination of all issue types
|
|-- sample_review.py             # Sample file to try a review on
|-- pyproject.toml
|-- .env.example
+-- LICENSE
```

## How It Works

### 1. Orchestration (LangGraph)

The orchestrator builds a `StateGraph` where all selected agents run as parallel nodes. Each agent receives the same code and returns an `AgentResult`. The graph topology:

```
START --> [quality_agent, security_agent, performance_agent, documentation_agent] --> aggregator --> END
```

### 2. Agent Analysis

Each agent uses `ChatGroq.with_structured_output()` to get reliable JSON from the LLM. The `BaseAgent` class handles:
- Prompt construction with code and language context
- Structured output parsing into `Finding` objects
- Error handling (agents never crash -- errors are captured in the result)
- Severity validation with fallback to INFO

### 3. Aggregation and Scoring

The aggregator:
- Collects results from all agents
- **Deduplicates** overlapping findings using line proximity + title word overlap
- **Merges** similar findings (keeps higher severity, combines descriptions)
- **Scores** code on a 0-100 scale using weighted severity penalties:

```
Severity Weights: Critical=25, High=15, Medium=8, Low=3, Info=1
Score = max(0, 100 - total_penalty / max(lines_of_code / 10, 1))
```

### 4. Static Analysis Tools

These tools run locally without LLM calls:
- **CodeParser**: tree-sitter AST parsing with regex fallback for Python/JS
- **ComplexityCalculator**: McCabe cyclomatic complexity per function
- **SecretScanner**: 15+ regex patterns (AWS keys, JWT, Stripe, Slack, etc.)
- **PatternMatcher**: 17+ Python patterns, 10+ JavaScript anti-patterns

## Running Tests

```bash
# Run all tests (no API key needed -- tests use mocks)
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_tools.py -v

# Lint and type check
uv run ruff check src/
uv run mypy src/
```

## Configuration

All configuration is via environment variables (or `.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | -- | Groq API key for LLM calls |
| `DEFAULT_MODEL` | No | `llama-3.3-70b-versatile` | LLM model to use |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `MAX_CODE_LENGTH` | No | `50000` | Max code length (chars) |

## Output Formats

**Text** (default) -- Rich terminal output with colored severity indicators and tables

**JSON** -- Structured report with all findings, scores, and metadata

**Markdown** -- Formatted report suitable for PRs or documentation

## Key Design Decisions

1. **Parallel Execution**: LangGraph's fan-out pattern runs all agents concurrently, reducing total review time vs sequential execution.
2. **Structured Output**: `with_structured_output()` ensures LLM responses are valid JSON matching Pydantic models -- no fragile regex parsing.
3. **Graceful Degradation**: If one agent fails, the others still complete. Errors are captured in `AgentResult.error`, never crash the system.
4. **Deduplication**: When multiple agents flag the same issue (e.g., security + quality both flag `eval()`), findings are merged intelligently.
5. **Abstract Base Class**: `BaseAgent` enforces a consistent interface -- adding a new agent requires implementing 3 abstract methods.

## Future Enhancements

- FastAPI backend with SSE for real-time progress
- Celery + Redis for background job processing
- PostgreSQL persistence for review history
- React dashboard for visualization
- GitHub webhook / PR integration
- Docker deployment

## License

MIT
