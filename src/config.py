"""Configuration for LLM providers and models."""

from dataclasses import dataclass
from enum import Enum


class Provider(str, Enum):
    """LLM provider."""

    GROQ = "groq"
    GROK = "grok"
    OPENAI = "openai"


@dataclass
class ModelConfig:
    """Configuration for a specific model mode."""

    provider: Provider
    model: str
    temperature: float


MODEL_CONFIGS: dict[str, ModelConfig] = {
    # Groq models (fastest)
    "groq-fast": ModelConfig(
        provider=Provider.GROQ,
        model="llama-3.3-70b-versatile",
        temperature=0.1,
    ),
    "groq-balanced": ModelConfig(
        provider=Provider.GROQ,
        model="llama-3.3-70b-versatile",
        temperature=0.3,
    ),
    # Grok models (xAI)
    "grok-deep": ModelConfig(
        provider=Provider.GROK,
        model="grok-3",
        temperature=0.2,
    ),
    # OpenAI models
    "openai-fast": ModelConfig(
        provider=Provider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.1,
    ),
    "openai-balanced": ModelConfig(
        provider=Provider.OPENAI,
        model="gpt-4o",
        temperature=0.2,
    ),
    "openai-deep": ModelConfig(
        provider=Provider.OPENAI,
        model="o1",
        temperature=1.0,  # o1 requires temperature=1
    ),
}


# Default mode
DEFAULT_MODE = "groq-balanced"


def get_available_modes() -> list[str]:
    """Get list of available model modes."""
    return list(MODEL_CONFIGS.keys())
