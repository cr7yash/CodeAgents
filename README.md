# CodeAgents: Multi-Agent Code Review System

A multi-agent AI system where **4 specialized agents** collaborate via **LangGraph** to perform comprehensive, parallel code reviews. Each agent analyzes code from a different perspective (quality, security, performance, documentation), and an orchestrator aggregates their findings into a unified report with deduplication and severity-based scoring.

Built with **LangGraph** and the **Portkey AI gateway** — one gateway key reaches 46 models across OpenAI, Anthropic, Google, Mistral, and others, so every agent (or each one individually) can run on whichever model fits.

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
$ uv run codeagents review ./sample_review.py --model gpt-4o-mini

╭──── CodeAgents ────╮
│ Code Review Report │
│ Score: 39.2/100    │
╰────────────────────╯
      Summary
┏━━━━━━━━━━┳━━━━━━━┓
┃ Severity ┃ Count ┃
┡━━━━━━━━━━╇━━━━━━━┩
│ Critical │     4 │
│ High     │     8 │
│ Medium   │     4 │
│ Low      │     3 │
│ Info     │     1 │
│ Total    │    20 │
└──────────┴───────┘

╭──────────────────────────── Executive Summary ─────────────────────────────╮
│ Code review found 20 total issues indicating significant issues requiring │
│ remediation. 4 critical issue(s) require immediate attention. 8           │
│ high-priority issue(s) should be addressed. 7 moderate/low priority       │
│ improvements suggested.                                                   │
╰───────────────────────────────────────────────────────────────────────────╯

                                   Findings
┏━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Severity   ┃  Line ┃ Category             ┃ Title                                   ┃
┡━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ CRITICAL   │    10 │ command_injection     │ Command Injection Vulnerability          │
│ CRITICAL   │    47 │ eval_usage            │ Usage of eval with User Input            │
│ CRITICAL   │     7 │ sql_injection         │ SQL Injection Vulnerability              │
│ CRITICAL   │     8 │ sql_injection         │ SQL Injection Vulnerability              │
│ HIGH       │    41 │ code_smell            │ Long Method                              │
│ HIGH       │    30 │ code_smell            │ Inefficient Nested Loop in process        │
│ HIGH       │     5 │ hardcoded_secrets     │ Hardcoded Database Credentials           │
│ HIGH       │    13 │ inefficient_algorithm │ Inefficient Fibonacci Calculation        │
│ ...        │       │                       │ (12 more)                                │
└────────────┴───────┴──────────────────────┴─────────────────────────────────────────┘

Agents: QualityAgent, SecurityAgent, PerformanceAgent, DocumentationAgent |
Time: 38711ms | Tokens: 7513 (4074 in / 3439 out) | Cost: $0.0027
Models: QualityAgent=gpt-4o-mini, SecurityAgent=gpt-4o-mini,
PerformanceAgent=gpt-4o-mini, DocumentationAgent=gpt-4o-mini
```

The system detected **20 issues** across multiple categories — command injection, hardcoded secrets, O(n²) loops, missing docstrings, and more — scoring the file **39.2/100**, in this run for **$0.0027** and 7,513 tokens.

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
| Agent Framework | LangGraph |
| LLM Access | Portkey AI gateway (via the `openai` SDK) |
| Code Parsing | tree-sitter |
| Data Validation | Pydantic v2 |
| CLI | Click + Rich |
| Testing | pytest + pytest-asyncio |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A [Portkey](https://portkey.ai) API key (one key reaches every catalogued model)

### Installation

```bash
# Clone the repo
git clone https://github.com/<your-username>/codeagents.git
cd codeagents

# Install dependencies (pick one)
uv sync --extra dev      # using uv (recommended)
pip install -e ".[dev]"  # using pip

# Set up environment
cp .env.example .env
# Edit .env and add your PORTKEY_API_KEY
```

### Run a Review

```bash
# Review a Python file (uses DEFAULT_MODEL from .env)
uv run codeagents review ./sample_review.py

# Pick a specific model for this run
uv run codeagents review ./sample_review.py --model claude-opus-5

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

# List every model reachable through the gateway
uv run codeagents models
```

Per-agent model overrides (e.g. `SECURITY_MODEL=claude-opus-5`) can also be set in `.env` — see `.env.example`.

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
|   |   |-- base.py              # BaseAgent ABC; JSON extraction + validation
|   |   |-- quality_agent.py     # SOLID, code smells, complexity
|   |   |-- security_agent.py    # OWASP, injection, secrets
|   |   |-- performance_agent.py # Big O, inefficient patterns
|   |   +-- documentation_agent.py
|   |
|   |-- providers/               # LLM access via the Portkey gateway
|   |   |-- base.py              # LLMProvider ABC, GenerationConfig/Result
|   |   |-- portkey_catalog.py   # 46-model catalog + per-model param profiles
|   |   +-- portkey_provider.py  # AsyncOpenAI client wired to the gateway
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
|   |   |-- test_base.py         # BaseAgent ABC, parsing, prompt building
|   |   +-- test_json_extraction.py  # Tolerant JSON parsing of model output
|   |-- test_providers/
|   |   |-- test_catalog.py      # Catalog integrity checks
|   |   +-- test_portkey_provider.py # Per-model request shaping
|   +-- test_orchestrator/
|       |-- test_aggregator.py   # Aggregation, dedup, similarity, merging
|       +-- test_graph.py        # Graph wiring, model selection
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

Each agent reaches its model through the Portkey gateway (`PortkeyProvider`), which speaks the OpenAI chat-completions protocol for every upstream vendor. The `BaseAgent` class handles:
- Prompt construction with code and language context
- Tolerant JSON extraction from the response (handles fenced, prose-wrapped, or plain output), with one retry on a malformed response
- Structured validation into `Finding` objects
- Error handling (agents never crash -- errors are captured in the result and surfaced as report warnings)
- Severity validation with fallback to INFO
- Reasoning-model safety: an empty or truncated response (the model spent its whole budget on hidden reasoning) is flagged as a warning rather than silently scored as a clean pass

Requests are shaped per model: reasoning models (e.g. `gpt-5.5`, `o4-mini`) reject `temperature`/`top_p`/`stop` and need `max_completion_tokens` with an output-token floor, while others accept full sampling control. See `src/providers/portkey_catalog.py` for the measured parameter matrix per model.

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
| `PORTKEY_API_KEY` | Yes | -- | Portkey gateway key for all LLM calls |
| `PORTKEY_BASE_URL` | No | `https://api.portkey.ai/v1` | Gateway endpoint |
| `DEFAULT_MODEL` | No | `claude-sonnet-4-5` | Model slug used by every agent unless overridden |
| `QUALITY_MODEL` / `SECURITY_MODEL` / `PERFORMANCE_MODEL` / `DOCUMENTATION_MODEL` | No | -- | Per-agent model override |
| `MAX_OUTPUT_TOKENS` | No | `4000` | Max tokens requested per agent call |
| `REASONING_EFFORT` | No | -- | Reasoning budget hint, only sent to models that accept it |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `MAX_CODE_LENGTH` | No | `50000` | Max code length (chars) |

Run `codeagents models` to see every model slug, its family, and which parameters it supports.

## Supported Models

46 models are reachable through the Portkey gateway, grouped by vendor family:

| Family | Count | Examples |
|--------|-------|----------|
| OpenAI | 19 | `gpt-5.5`, `gpt-4.1`, `gpt-4o-mini`, `o4-mini` |
| Anthropic | 10 | `claude-opus-5`, `claude-sonnet-5`, `claude-sonnet-4-5` |
| Google | 11 | `gemini-2.5-pro`, `gemini-3.7-flash`, `gemma-4-31b` |
| Mistral | 3 | `mistral-large-3`, `mixtral-8x7b` |
| Other | 3 | `deepseek-r1`, `kimi-k2.5` |

Pricing is recorded for the mainstream models only; `codeagents models` marks unpriced models, and the report shows `Cost: unpriced` rather than a misleading `$0.00` when it runs one.

## Output Formats

**Text** (default) -- Rich terminal output with colored severity indicators and tables

**JSON** -- Structured report with all findings, scores, and metadata

**Markdown** -- Formatted report suitable for PRs or documentation

## Key Design Decisions

1. **One gateway, many vendors**: Portkey speaks the OpenAI protocol for every upstream provider, so a single `AsyncOpenAI` client covers all 46 catalogued models.
2. **Per-model request shaping**: Parameter support is not uniform across models (reasoning models reject `max_tokens`, `temperature`, `stop`), so each model declares its capabilities in `portkey_catalog.py` and requests are built to match.
3. **Parallel Execution**: LangGraph's fan-out pattern runs all agents concurrently; each agent is constructed per invocation, so a `--model` flag or per-agent override reaches every node.
4. **Tolerant JSON parsing**: Model output is extracted from fences/prose and validated against Pydantic models, with one retry on a malformed response -- more robust than any single model's native JSON mode across 46 heterogeneous routes.
5. **Graceful Degradation**: If one agent fails, the others still complete. Errors and reasoning-model warnings are captured on the result and surfaced in the report, never silently scored as a clean pass.
6. **Deduplication**: When multiple agents flag the same issue (e.g., security + quality both flag `eval()`), findings are merged intelligently.
7. **Abstract Base Class**: `BaseAgent` enforces a consistent interface -- adding a new agent requires implementing 3 abstract methods.

## Future Enhancements

- FastAPI backend with SSE for real-time progress
- Celery + Redis for background job processing
- PostgreSQL persistence for review history
- React dashboard for visualization
- GitHub webhook / PR integration
- Docker deployment

## License

MIT
