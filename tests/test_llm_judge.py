#!/usr/bin/env python3
"""
LLM Judge Test - Evaluates one LLM's performance using another LLM as judge.

This test verifies that an LLM evaluator is working correctly by having
another LLM judge the quality of its evaluations.
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients import create_client
from src.clients.base import BaseLLMClient
from src.models import TicketInput
from src.evaluator import evaluate_ticket_with_retry

load_dotenv()

# =============================================================================
# Test Data - 2 sample tickets with known quality levels
# =============================================================================

TEST_TICKETS = [
    # Good reply - should score high (4-5)
    TicketInput(
        ticket="I ordered a laptop 5 days ago and haven't received any shipping confirmation. Order #12345.",
        reply="I apologize for the delay in your shipping confirmation. I've checked your order #12345 and can confirm it was shipped yesterday. Your tracking number is TRK789456. You should receive it within 2-3 business days. I've also sent the tracking details to your email.",
    ),
    # Poor reply - should score low (1-2)
    TicketInput(
        ticket="My account was hacked and someone made unauthorized purchases totaling $500. Please help urgently!",
        reply="Have you tried resetting your password?",
    ),
]

# =============================================================================
# Judge Prompt
# =============================================================================

JUDGE_SYSTEM_PROMPT = """You are a quality assurance expert evaluating the performance of an AI evaluation system.

You will be given:
1. A customer support ticket
2. An AI-generated reply to that ticket
3. An evaluation of that reply (scores and explanations)

Your task is to judge if the evaluation is CORRECT and REASONABLE.

Consider:
- Are the scores (1-5) appropriate for the quality of the reply?
- Do the explanations accurately describe the reply's strengths/weaknesses?
- Is the evaluation consistent (good reply = high scores, poor reply = low scores)?

IMPORTANT: Respond with valid JSON only:
{
    "verdict": "PASS" or "FAIL",
    "reasoning": "<brief explanation of your judgment>",
    "expected_content_score_range": [min, max],
    "expected_format_score_range": [min, max]
}"""

JUDGE_TEMPLATE = """Evaluate this AI evaluation:

---
ORIGINAL TICKET:
{ticket}

---
AI REPLY BEING EVALUATED:
{reply}

---
EVALUATION GIVEN:
- Content Score: {content_score}/5
- Content Explanation: {content_explanation}
- Format Score: {format_score}/5
- Format Explanation: {format_explanation}

---

Is this evaluation correct and reasonable? Consider if the scores match the actual quality of the reply.
For the first ticket (good detailed reply), scores should be 4-5.
For the second ticket (dismissive reply to urgent issue), scores should be 1-3.

Respond with JSON including verdict (PASS/FAIL) and reasoning."""


# =============================================================================
# Judge Logic
# =============================================================================


def judge_evaluation(
    judge_client: BaseLLMClient,
    ticket: TicketInput,
    content_score: int,
    content_explanation: str,
    format_score: int,
    format_explanation: str,
) -> dict:
    """Have the judge LLM evaluate if an evaluation is correct."""

    prompt = JUDGE_TEMPLATE.format(
        ticket=ticket.ticket,
        reply=ticket.reply,
        content_score=content_score,
        content_explanation=content_explanation,
        format_score=format_score,
        format_explanation=format_explanation,
    )

    # Get judge's verdict
    response = judge_client.client.chat.completions.create(
        model=judge_client.model,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=500,
    )

    raw_response = response.choices[0].message.content

    try:
        # Try to parse JSON from response
        # Handle case where response might have markdown code blocks
        if "```json" in raw_response:
            raw_response = raw_response.split("```json")[1].split("```")[0]
        elif "```" in raw_response:
            raw_response = raw_response.split("```")[1].split("```")[0]

        return json.loads(raw_response.strip())
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract verdict
        if "PASS" in raw_response.upper():
            return {"verdict": "PASS", "reasoning": raw_response}
        else:
            return {"verdict": "FAIL", "reasoning": raw_response}


def run_llm_judge_test(evaluator_mode: str, judge_mode: str) -> bool:
    """
    Run the LLM judge test.

    Args:
        evaluator_mode: Mode for the LLM being tested (e.g., "openai-fast")
        judge_mode: Mode for the judge LLM (e.g., "deep")

    Returns:
        True if all evaluations pass, False otherwise
    """
    print("=" * 60)
    print("LLM Judge Test")
    print("=" * 60)
    print(f"Evaluator: {evaluator_mode}")
    print(f"Judge: {judge_mode}")
    print("-" * 60)

    # Create clients
    print("\nCreating clients...")
    evaluator = create_client(evaluator_mode)
    judge = create_client(judge_mode)

    all_passed = True
    results = []

    for i, ticket in enumerate(TEST_TICKETS, start=1):
        print(f"\n--- Test Case {i}/{len(TEST_TICKETS)} ---")
        print(f"Ticket: {ticket.ticket[:50]}...")
        print(f"Reply: {ticket.reply[:50]}...")

        # Step 1: Get evaluation from the evaluator
        print(f"\n[1] Getting evaluation from {evaluator_mode}...")
        try:
            eval_result = evaluate_ticket_with_retry(
                evaluator, ticket.ticket, ticket.reply
            )
            print(
                f"    Content: {eval_result.content_score}/5 - {eval_result.content_explanation[:50]}..."
            )
            print(
                f"    Format:  {eval_result.format_score}/5 - {eval_result.format_explanation[:50]}..."
            )
        except Exception as e:
            print(f"    ERROR: Evaluation failed - {e}")
            all_passed = False
            results.append(
                {"test_case": i, "evaluator_error": str(e), "verdict": "FAIL"}
            )
            continue

        # Step 2: Have the judge evaluate the evaluation
        print(f"\n[2] Judge ({judge_mode}) reviewing evaluation...")
        try:
            judgment = judge_evaluation(
                judge,
                ticket,
                eval_result.content_score,
                eval_result.content_explanation,
                eval_result.format_score,
                eval_result.format_explanation,
            )

            verdict = judgment.get("verdict", "UNKNOWN")
            reasoning = judgment.get("reasoning", "No reasoning provided")

            print(f"    Verdict: {verdict}")
            print(f"    Reasoning: {reasoning[:100]}...")

            if verdict != "PASS":
                all_passed = False

            results.append(
                {
                    "test_case": i,
                    "content_score": eval_result.content_score,
                    "format_score": eval_result.format_score,
                    "verdict": verdict,
                    "reasoning": reasoning,
                }
            )

        except Exception as e:
            print(f"    ERROR: Judge failed - {e}")
            all_passed = False
            results.append({"test_case": i, "judge_error": str(e), "verdict": "FAIL"})

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r.get("verdict") == "PASS")
    failed = len(results) - passed

    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("-" * 60)

    for r in results:
        status = "✓" if r.get("verdict") == "PASS" else "✗"
        print(f"  {status} Test {r['test_case']}: {r.get('verdict', 'ERROR')}")

    print("=" * 60)

    if all_passed:
        print("RESULT: ALL TESTS PASSED ✓")
    else:
        print("RESULT: SOME TESTS FAILED ✗")

    print("=" * 60)

    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Test an LLM evaluator using another LLM as judge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test OpenAI with Grok as judge
  python tests/test_llm_judge.py --evaluator openai-fast --judge deep

  # Test Groq with OpenAI as judge
  python tests/test_llm_judge.py --evaluator fast --judge openai

  # Test OpenAI with Groq as judge
  python tests/test_llm_judge.py --evaluator openai --judge balanced
        """,
    )

    parser.add_argument(
        "--evaluator",
        "-e",
        type=str,
        required=True,
        help="Model mode for the evaluator being tested (e.g., openai-fast, fast, deep)",
    )

    parser.add_argument(
        "--judge",
        "-j",
        type=str,
        required=True,
        help="Model mode for the judge (e.g., deep, openai, balanced)",
    )

    args = parser.parse_args()

    success = run_llm_judge_test(args.evaluator, args.judge)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
