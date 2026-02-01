# Ticket Evaluator - Solution Design

## Overview

Console application that evaluates customer support ticket replies using multiple LLM providers (Groq, Grok, OpenAI) with configurable model selection based on speed vs reasoning depth trade-offs.

---

## Usage

```bash
# Default mode (groq-balanced)
python evaluate_tickets.py tickets.csv

# Fast modes - optimized for speed
python evaluate_tickets.py tickets.csv --model groq-fast
python evaluate_tickets.py tickets.csv --model openai-fast

# Balanced modes - speed/quality trade-off
python evaluate_tickets.py tickets.csv --model groq-balanced
python evaluate_tickets.py tickets.csv --model openai-balanced

# Deep modes - optimized for reasoning quality
python evaluate_tickets.py tickets.csv --model grok-deep
python evaluate_tickets.py tickets.csv --model openai-deep

# Custom output file
python evaluate_tickets.py tickets.csv --model groq-fast --output results.csv
```

---

## Project Structure

```
ticket-evaluator/
├── evaluate_tickets.py          # CLI entry point
├── src/
│   ├── __init__.py
│   ├── config.py                # Model configurations
│   ├── prompts.py               # LLM prompts
│   ├── csv_handler.py           # CSV read/write
│   ├── parser.py                # Response parsing
│   ├── evaluator.py             # Evaluation orchestration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ticket_input.py      # Input data model
│   │   ├── evaluation_result.py # Parsed LLM response
│   │   └── ticket_evaluated.py  # Final output model
│   └── clients/
│       ├── __init__.py
│       ├── base.py              # Abstract base client
│       ├── groq_client.py       # Groq provider
│       ├── grok_client.py       # Grok/xAI provider
│       └── openai_client.py     # OpenAI provider
├── tests/
│   ├── test_evaluate.py         # Unit tests (29 tests)
│   └── test_llm_judge.py        # LLM-as-Judge validation
├── docs/
│   ├── 01-requirements.md       # Original assignment
│   ├── 02-analysis.md           # Requirements analysis
│   └── 03-solution-design.md    # This document
├── .env.example                 # API key template
├── .github/workflows/ci.yml     # CI pipeline
├── pyproject.toml               # Project configuration
└── README.md                    # Setup instructions
```

---

## Model Configuration

| Mode | Provider | Model | Temperature | Speed | Reasoning |
|------|----------|-------|-------------|-------|-----------|
| `groq-fast` | Groq | llama-3.3-70b-versatile | 0.1 | ⚡⚡⚡ | ⭐⭐ |
| `groq-balanced` | Groq | llama-3.3-70b-versatile | 0.3 | ⚡⚡ | ⭐⭐⭐ |
| `grok-deep` | Grok (xAI) | grok-3 | 0.2 | ⚡ | ⭐⭐⭐⭐⭐ |
| `openai-fast` | OpenAI | gpt-4o-mini | 0.1 | ⚡⚡⚡ | ⭐⭐ |
| `openai-balanced` | OpenAI | gpt-4o | 0.2 | ⚡⚡ | ⭐⭐⭐⭐ |
| `openai-deep` | OpenAI | o1 | 1.0 | ⚡ | ⭐⭐⭐⭐⭐ |

---

## Data Flow

```
tickets.csv → Read CSV → LLM Evaluation → Parse Response → tickets_evaluated.csv
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
            Groq            Grok           OpenAI
        (fast/balanced)    (deep)    (fast/balanced/deep)
```

---

## Input/Output Format

**Input** (`tickets.csv`):
```csv
ticket,reply
"Customer message...","AI response..."
```

**Output** (`tickets_evaluated.csv`):
```csv
ticket,reply,content_score,content_explanation,format_score,format_explanation
"Customer message...","AI response...",4,"Good response addressing the issue.",5,"Well structured and clear."
```

---

## Core Components

### LLM Client Architecture

```python
class BaseLLMClient(ABC):
    def __init__(self, model: str, temperature: float)

    @abstractmethod
    def evaluate(self, ticket: str, reply: str) -> str

class GroqClient(BaseLLMClient):     # Uses groq library
class GrokClient(BaseLLMClient):     # Uses openai library with xAI base_url
class OpenAIClient(BaseLLMClient):   # Uses openai library (handles o1 model special case)
```

### Factory Pattern

```python
def create_client(mode: str) -> BaseLLMClient:
    config = MODEL_CONFIGS[mode]
    match config.provider:
        case Provider.GROQ:   return GroqClient(config.model, config.temperature)
        case Provider.GROK:   return GrokClient(config.model, config.temperature)
        case Provider.OPENAI: return OpenAIClient(config.model, config.temperature)
```

---

## Error Handling

| Error | Action |
|-------|--------|
| API failure | Retry 3x with exponential backoff (tenacity) |
| Invalid JSON response | Regex fallback parser |
| Score out of range | Clamp to 1-5 |
| Empty CSV row | Skip with warning |
| Missing API key | Raise ValueError with clear message |

---

## Dependencies

```
groq>=0.4.0          # Groq API client
openai>=1.0.0        # OpenAI & Grok API client
python-dotenv>=1.0.0 # Environment variables
tenacity>=8.2.0      # Retry logic
ruff>=0.1.0          # Linting & formatting
mypy>=1.0.0          # Type checking
pytest>=7.0.0        # Testing
```

---

## Environment Variables

```env
GROQ_API_KEY=gsk_xxx      # For groq-fast, groq-balanced
XAI_API_KEY=xai-xxx       # For grok-deep
OPENAI_API_KEY=sk-xxx     # For openai-fast, openai-balanced, openai-deep
```

---

## Quality Assurance

### Static Analysis
- **ruff**: Linting and code formatting (PEP-8 compliance)
- **mypy**: Static type checking

### Testing
- **Unit tests**: 29 tests covering all components
- **LLM Judge**: Meta-evaluation for AI Act compliance

### CI Pipeline
GitHub Actions workflow validates:
- `ruff check` - Linting
- `ruff format --check` - Formatting
- `mypy` - Type checking

---

## LLM-as-Judge: EU AI Act Compliance

### Regulatory Context

The **EU AI Act** (Regulation 2024/1689) establishes requirements for AI systems, particularly those that interact with humans or make automated decisions. Article 14 mandates **human oversight** and Article 9 requires **risk management systems** that include validation and testing of AI outputs.

### Why LLM-as-Judge is Necessary

When using AI to evaluate customer support responses, we are essentially deploying an **AI system that assesses other AI systems**. This creates a chain of automated decisions that requires validation mechanisms:

1. **Output Quality Assurance**: The evaluator LLM must produce consistent, accurate assessments
2. **Bias Detection**: Systematic biases in evaluation must be identified
3. **Drift Monitoring**: Model behavior changes over time must be detected
4. **Audit Trail**: Regulatory compliance requires documented validation

### Implementation: `test_llm_judge.py`

The LLM Judge test validates our evaluator by using a **separate, more capable LLM** to assess whether evaluations are reasonable:

```python
@pytest.mark.llm_judge
class TestLLMJudge:
    """
    Meta-evaluation: Use an LLM to validate that our evaluator
    produces reasonable scores for known good/bad responses.
    """

    def test_good_reply_scores_high(self):
        # A clearly excellent response should score 4-5

    def test_poor_reply_scores_low(self):
        # A clearly inadequate response should score 1-2
```

### Compliance Benefits

| EU AI Act Requirement | LLM Judge Solution |
|-----------------------|-------------------|
| Art. 9 - Risk Management | Automated validation of AI output quality |
| Art. 14 - Human Oversight | Documented test results for human review |
| Art. 15 - Accuracy | Quantifiable accuracy metrics through judge validation |
| Art. 17 - Quality Management | Continuous monitoring via CI/CD integration |
| Art. 61 - Post-market Monitoring | Regression tests detect model drift |

### Running the LLM Judge

```bash
# Requires OPENAI_API_KEY or GROQ_API_KEY set
pytest tests/test_llm_judge.py -v -m llm_judge
```

**Note**: LLM Judge tests are excluded from CI pipeline as they require API access and incur costs. They should be run:
- Before major releases
- When changing evaluation prompts
- As part of periodic quality audits
- When switching LLM providers or models

---

## Future Enhancements

1. **Async Processing**: Parallel API calls for large CSV files
2. **Caching**: Store evaluations to avoid re-processing
3. **Streaming**: Handle very large files with chunked processing
4. **Web Interface**: REST API or Gradio UI for non-technical users
5. **Multi-language**: Support for non-English tickets
