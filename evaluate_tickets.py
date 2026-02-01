#!/usr/bin/env python3
"""
LLM-based Ticket Reply Evaluation System

Evaluates customer support ticket replies using Groq, Grok, or OpenAI LLMs.
"""

import argparse
import sys

from dotenv import load_dotenv

from src.config import MODEL_CONFIGS, DEFAULT_MODE, get_available_modes
from src.csv_handler import read_tickets, write_results
from src.clients import create_client
from src.evaluator import evaluate_tickets

# Load environment variables
load_dotenv()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate customer support ticket replies using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python evaluate_tickets.py tickets.csv
  python evaluate_tickets.py tickets.csv --model groq-fast
  python evaluate_tickets.py tickets.csv --model openai-balanced --output results.csv

Available modes:
  groq-fast      - Groq (llama-3.3-70b), fastest
  groq-balanced  - Groq (llama-3.3-70b), default
  grok-deep      - Grok (grok-3), thorough
  openai-fast    - OpenAI (gpt-4o-mini), quick
  openai-balanced- OpenAI (gpt-4o), balanced
  openai-deep    - OpenAI (o1), reasoning
        """,
    )

    parser.add_argument(
        "input_file",
        type=str,
        help="Path to input CSV file with 'ticket' and 'reply' columns",
    )

    parser.add_argument(
        "--model",
        "-m",
        type=str,
        choices=get_available_modes(),
        default=DEFAULT_MODE,
        help=f"Model mode (default: {DEFAULT_MODE})",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="tickets_evaluated.csv",
        help="Output file path (default: tickets_evaluated.csv)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Print configuration
    config = MODEL_CONFIGS[args.model]
    print(f"Mode: {args.model}")
    print(f"Provider: {config.provider.value}")
    print(f"Model: {config.model}")
    print(f"Input: {args.input_file}")
    print(f"Output: {args.output}")
    print("-" * 40)

    try:
        # Read input
        print("Reading tickets...")
        tickets = read_tickets(args.input_file)
        print(f"Found {len(tickets)} tickets")
        print("-" * 40)

        # Create client
        client = create_client(args.model)

        # Evaluate
        results = evaluate_tickets(tickets, client)

        # Write output
        print("-" * 40)
        print(f"Writing results to {args.output}...")
        write_results(args.output, results)

        # Summary
        successful = [r for r in results if r.content_score > 0]
        avg_content = (
            sum(r.content_score for r in successful) / len(successful)
            if successful
            else 0
        )
        avg_format = (
            sum(r.format_score for r in successful) / len(successful)
            if successful
            else 0
        )

        print("-" * 40)
        print("Summary:")
        print(f"  Total tickets: {len(results)}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(results) - len(successful)}")
        print(f"  Avg content score: {avg_content:.2f}")
        print(f"  Avg format score: {avg_format:.2f}")
        print("-" * 40)
        print("Done!")

        return 0

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
