"""Groq LLM client."""

import os

from groq import Groq

from .base import BaseLLMClient
from ..prompts import SYSTEM_PROMPT, EVALUATION_TEMPLATE


class GroqClient(BaseLLMClient):
    """Groq LLM client using Llama models."""

    def __init__(self, model: str, temperature: float):
        super().__init__(model, temperature)

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        self.client = Groq(api_key=api_key)

    def evaluate(self, ticket: str, reply: str) -> str:
        """Send evaluation request to Groq."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": EVALUATION_TEMPLATE.format(ticket=ticket, reply=reply),
                },
            ],
            temperature=self.temperature,
            max_tokens=500,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("LLM returned empty response")
        return content
