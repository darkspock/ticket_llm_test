"""OpenAI LLM client."""

import os

from openai import OpenAI

from .base import BaseLLMClient
from ..prompts import SYSTEM_PROMPT, EVALUATION_TEMPLATE


class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client using GPT models."""

    def __init__(self, model: str, temperature: float):
        super().__init__(model, temperature)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)

    def evaluate(self, ticket: str, reply: str) -> str:
        """Send evaluation request to OpenAI."""
        # o1 models don't support system messages or temperature != 1
        # o1 uses reasoning tokens internally, needs more tokens (960+ for reasoning, ~60 for output)
        if self.model.startswith("o1"):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": SYSTEM_PROMPT
                        + "\n\n"
                        + EVALUATION_TEMPLATE.format(ticket=ticket, reply=reply),
                    },
                ],
                max_completion_tokens=2000,
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": EVALUATION_TEMPLATE.format(
                            ticket=ticket, reply=reply
                        ),
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
