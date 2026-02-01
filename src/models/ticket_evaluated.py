"""Evaluated ticket model."""

from dataclasses import dataclass


@dataclass
class TicketEvaluated:
    """Complete evaluated ticket."""

    ticket: str
    reply: str
    content_score: int
    content_explanation: str
    format_score: int
    format_explanation: str
