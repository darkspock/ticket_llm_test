# Ticket Evaluator

[![CI](https://github.com/darkspock/ticket_llm_test/actions/workflows/ci.yml/badge.svg)](https://github.com/darkspock/ticket_llm_test/actions/workflows/ci.yml)

LLM-based evaluation system for customer support ticket replies.

## Requirements

- Python 3.10+

## Architecture

```
tickets.csv → CSV Reader → LLM Client → Parser → tickets_evaluated.csv
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
             Groq            Grok           OpenAI
         (fast/balanced)    (deep)    (fast/balanced/deep)
```

## Documentation

- [Requirements](docs/01-requirements.md) - Original assignment
- [Analysis](docs/02-analysis.md) - Requirements analysis
- [Solution Design](docs/03-solution-design.md) - Architecture and EU AI Act compliance
- [Model Comparison](docs/04-model-comparison.md) - Benchmark results and price/quality analysis

## Functionality

The goal of this project is to demonstrate skills in calling LLM models, properly defining prompts, analyzing results, and storing them correctly.

It's important to note that models sometimes return corrupted JSON. Functionality has been added to attempt to recover the response by parsing the JSON with regex fallback.

Multiple models have been included to demonstrate the use of abstraction, inheritance, and factory patterns.

Additionally, a test has been included that evaluates one model using another as a judge, to demonstrate evaluation quality. This is important to ensure service level and comply with EU AI Act regulations.

## The Code
The code is structured in a modular way, with separate components for configuration, prompts, CSV handling, response parsing, evaluation logic, and LLM clients. This structure promotes maintainability and extensibility.

GitHub Actions CI is used for mypy and ruff validation.

Tests are not included in CI due to token costs. With Groq it's cheap and could be automated, but it's not an EU-approved model - we would need to use Mistral for that.


## Setup

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install groq openai python-dotenv tenacity pytest
   ```
4. Copy `.env.example` to `.env` and add your API keys:
   ```bash
   cp .env.example .env
   ```

## Usage

```bash
# Default mode (groq-balanced)
python evaluate_tickets.py tickets.csv

# Groq modes
python evaluate_tickets.py tickets.csv --model groq-fast
python evaluate_tickets.py tickets.csv --model groq-balanced

# Grok mode
python evaluate_tickets.py tickets.csv --model grok-deep

# OpenAI modes
python evaluate_tickets.py tickets.csv --model openai-fast
python evaluate_tickets.py tickets.csv --model openai-balanced
python evaluate_tickets.py tickets.csv --model openai-deep

# Custom output file
python evaluate_tickets.py tickets.csv --output results.csv
```

## Model Modes

| Mode | Provider | Model | Speed | Thinking |
|------|----------|-------|-------|----------|
| `groq-fast` | Groq | llama-3.3-70b-versatile | ⚡⚡⚡ | ⭐⭐ |
| `groq-balanced` | Groq | llama-3.3-70b-versatile | ⚡⚡ | ⭐⭐⭐ |
| `grok-deep` | Grok | grok-3 | ⚡ | ⭐⭐⭐⭐⭐ |
| `openai-fast` | OpenAI | gpt-4o-mini | ⚡⚡⚡ | ⭐⭐ |
| `openai-balanced` | OpenAI | gpt-4o | ⚡⚡ | ⭐⭐⭐⭐ |
| `openai-deep` | OpenAI | o1 | ⚡ | ⭐⭐⭐⭐⭐ |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key ([console.groq.com](https://console.groq.com)) |
| `XAI_API_KEY` | xAI/Grok API key ([console.x.ai](https://console.x.ai)) |
| `OPENAI_API_KEY` | OpenAI API key ([platform.openai.com](https://platform.openai.com)) |

## Project Structure

```
ticket-evaluator/
├── evaluate_tickets.py          # CLI entry point
├── src/
│   ├── config.py                # Model configurations
│   ├── prompts.py               # LLM prompts
│   ├── csv_handler.py           # CSV read/write
│   ├── parser.py                # Response parsing
│   ├── evaluator.py             # Evaluation logic
│   ├── models/
│   │   ├── ticket_input.py      # TicketInput
│   │   ├── evaluation_result.py # EvaluationResult
│   │   └── ticket_evaluated.py  # TicketEvaluated
│   └── clients/
│       ├── base.py              # BaseLLMClient (abstract)
│       ├── factory.py           # create_client()
│       ├── groq_client.py       # GroqClient
│       ├── grok_client.py       # GrokClient
│       └── openai_client.py     # OpenAIClient
├── tests/
│   ├── test_evaluate.py         # Unit tests (29 tests)
│   └── test_llm_judge.py        # LLM judge test
├── .env.example
└── pyproject.toml
```

## Running Tests

```bash
# Unit tests
pytest tests/test_evaluate.py -v

# LLM Judge test (evaluates one LLM using another as judge)
python tests/test_llm_judge.py --evaluator openai-fast --judge grok-deep
python tests/test_llm_judge.py --evaluator groq-fast --judge openai-balanced
```

## Output Format

Input CSV (`tickets.csv`):
```csv
ticket,reply
"Customer message...","AI response..."
```

Output CSV (`tickets_evaluated.csv`):
```csv
ticket,reply,content_score,content_explanation,format_score,format_explanation
"Customer message...","AI response...",4,"Good response.",5,"Well formatted."
```

Scores are 1-5:
- **Content**: relevance, correctness, completeness
- **Format**: clarity, structure, grammar/spelling
