# Ticket Evaluator - Project Instructions

## Overview

Console script that evaluates customer support ticket replies using LLM (Groq/Grok).

## Project Structure

```
ticket-evaluator/
├── evaluate_tickets.py      # Main script
├── tickets.csv              # Input (sample in docs/)
├── tickets_evaluated.csv    # Output (generated)
├── .env                     # API keys (not committed)
├── .env.example             # Template
├── pyproject.toml           # Dependencies
├── README.md                # Setup instructions
├── tests/                   # Unit tests
└── docs/                    # Assignment docs
```

## Commands

```bash
# Run evaluation
python evaluate_tickets.py tickets.csv --model balanced

# Run tests
pytest tests/
```

## Design Reference

See `docs/working_docs/epics/initial_epic/AI Engineer Assignment.design.md`
