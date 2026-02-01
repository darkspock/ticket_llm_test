"""Input ticket model."""

from dataclasses import dataclass


@dataclass
class TicketInput:
    """Input ticket/reply pair."""

    ticket: str
    reply: str
