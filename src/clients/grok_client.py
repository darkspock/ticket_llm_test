"""Grok (xAI) LLM client."""

import os

from openai import OpenAI

from .base import BaseLLMClient
from ..prompts import SYSTEM_PROMPT, EVALUATION_TEMPLATE


class GrokClient(BaseLLMClient):
    """Grok LLM client using xAI API."""

    def __init__(self, model: str, temperature: float):
        super().__init__(model, temperature)

        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            raise ValueError("XAI_API_KEY environment variable not set")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )

    def evaluate(self, ticket: str, reply: str) -> str:
        """Send evaluation request to Grok."""
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
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("LLM returned empty response")
        return content
