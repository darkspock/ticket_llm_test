"""CSV read/write operations."""

import csv

from .models import TicketInput, TicketEvaluated


def read_tickets(file_path: str) -> list[TicketInput]:
    """Read tickets from CSV file."""
    tickets = []

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate columns
        if reader.fieldnames is None:
            raise ValueError(f"Empty CSV file: {file_path}")

        required_cols = {"ticket", "reply"}
        missing = required_cols - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        for row_num, row in enumerate(reader, start=2):
            ticket = row.get("ticket", "").strip()
            reply = row.get("reply", "").strip()

            if not ticket or not reply:
                print(f"Warning: Skipping empty row {row_num}")
                continue

            tickets.append(TicketInput(ticket=ticket, reply=reply))

    if not tickets:
        raise ValueError("No valid tickets found in CSV")

    return tickets


def write_results(file_path: str, results: list[TicketEvaluated]) -> None:
    """Write evaluation results to CSV file."""
    fieldnames = [
        "ticket",
        "reply",
        "content_score",
        "content_explanation",
        "format_score",
        "format_explanation",
    ]

    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    "ticket": result.ticket,
                    "reply": result.reply,
                    "content_score": result.content_score,
                    "content_explanation": result.content_explanation,
                    "format_score": result.format_score,
                    "format_explanation": result.format_explanation,
                }
            )
