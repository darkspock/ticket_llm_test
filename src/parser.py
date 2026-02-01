"""Response parsing utilities."""

import json
import re

from .models import EvaluationResult


def clamp_score(score: int) -> int:
    """Clamp score to valid range 1-5."""
    return max(1, min(5, score))


def parse_response_json(raw_response: str) -> EvaluationResult:
    """Parse JSON response from LLM."""
    data = json.loads(raw_response)

    return EvaluationResult(
        content_score=clamp_score(int(data["content_score"])),
        content_explanation=str(data["content_explanation"]),
        format_score=clamp_score(int(data["format_score"])),
        format_explanation=str(data["format_explanation"]),
    )


def parse_response_regex(raw_response: str) -> EvaluationResult:
    """Fallback regex parser for malformed JSON."""
    # Extract scores
    content_score_match = re.search(r'"?content_score"?\s*:\s*(\d+)', raw_response)
    format_score_match = re.search(r'"?format_score"?\s*:\s*(\d+)', raw_response)

    # Extract explanations
    content_exp_match = re.search(
        r'"?content_explanation"?\s*:\s*"([^"]*)"', raw_response
    )
    format_exp_match = re.search(
        r'"?format_explanation"?\s*:\s*"([^"]*)"', raw_response
    )

    content_score = int(content_score_match.group(1)) if content_score_match else 3
    format_score = int(format_score_match.group(1)) if format_score_match else 3
    content_exp = (
        content_exp_match.group(1)
        if content_exp_match
        else "Unable to parse explanation"
    )
    format_exp = (
        format_exp_match.group(1) if format_exp_match else "Unable to parse explanation"
    )

    return EvaluationResult(
        content_score=clamp_score(content_score),
        content_explanation=content_exp,
        format_score=clamp_score(format_score),
        format_explanation=format_exp,
    )


def parse_response(raw_response: str) -> EvaluationResult:
    """Parse LLM response with fallback."""
    try:
        return parse_response_json(raw_response)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        print(f"Warning: JSON parse failed ({e}), using regex fallback")
        return parse_response_regex(raw_response)
