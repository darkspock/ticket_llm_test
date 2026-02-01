"""Evaluation result model."""

from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """Evaluation result from LLM."""

    content_score: int
    content_explanation: str
    format_score: int
    format_explanation: str
