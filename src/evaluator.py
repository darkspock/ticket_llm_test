"""Ticket evaluation logic."""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .clients.base import BaseLLMClient
from .models import TicketInput, TicketEvaluated, EvaluationResult
from .parser import parse_response


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=True,
)
def evaluate_ticket_with_retry(
    client: BaseLLMClient,
    ticket: str,
    reply: str,
) -> EvaluationResult:
    """Evaluate a single ticket with retry logic."""
    raw_response = client.evaluate(ticket, reply)
    return parse_response(raw_response)


def evaluate_tickets(
    tickets: list[TicketInput],
    client: BaseLLMClient,
) -> list[TicketEvaluated]:
    """Evaluate all tickets."""
    results = []
    total = len(tickets)

    for i, ticket_input in enumerate(tickets, start=1):
        print(f"Evaluating ticket {i}/{total}...", end=" ")

        try:
            result = evaluate_ticket_with_retry(
                client,
                ticket_input.ticket,
                ticket_input.reply,
            )

            evaluated = TicketEvaluated(
                ticket=ticket_input.ticket,
                reply=ticket_input.reply,
                content_score=result.content_score,
                content_explanation=result.content_explanation,
                format_score=result.format_score,
                format_explanation=result.format_explanation,
            )
            results.append(evaluated)
            print(
                f"Done (Content: {result.content_score}, Format: {result.format_score})"
            )

        except Exception as e:
            print(f"Failed after retries: {e}")
            # Add with default scores on failure
            evaluated = TicketEvaluated(
                ticket=ticket_input.ticket,
                reply=ticket_input.reply,
                content_score=0,
                content_explanation=f"Evaluation failed: {e}",
                format_score=0,
                format_explanation=f"Evaluation failed: {e}",
            )
            results.append(evaluated)

    return results
