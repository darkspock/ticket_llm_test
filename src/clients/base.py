"""Base class for LLM clients."""

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, model: str, temperature: float):
        self.model = model
        self.temperature = temperature

    @abstractmethod
    def evaluate(self, ticket: str, reply: str) -> str:
        """
        Send evaluation request to LLM.

        Args:
            ticket: Customer support ticket message
            reply: AI-generated response

        Returns:
            Raw JSON string with evaluation result
        """
        pass
