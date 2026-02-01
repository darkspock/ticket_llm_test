"""Factory for creating LLM clients."""

from ..config import MODEL_CONFIGS, Provider
from .base import BaseLLMClient
from .groq_client import GroqClient
from .grok_client import GrokClient
from .openai_client import OpenAIClient


def create_client(mode: str) -> BaseLLMClient:
    """
    Create LLM client based on mode.

    Args:
        mode: Model mode (fast, balanced, deep, openai-fast, openai, openai-deep)

    Returns:
        Configured LLM client instance

    Raises:
        ValueError: If mode is unknown or provider is not supported
    """
    if mode not in MODEL_CONFIGS:
        raise ValueError(f"Unknown mode: {mode}")

    config = MODEL_CONFIGS[mode]

    if config.provider == Provider.GROQ:
        return GroqClient(model=config.model, temperature=config.temperature)
    elif config.provider == Provider.GROK:
        return GrokClient(model=config.model, temperature=config.temperature)
    elif config.provider == Provider.OPENAI:
        return OpenAIClient(model=config.model, temperature=config.temperature)
    else:
        raise ValueError(f"Unknown provider: {config.provider}")
