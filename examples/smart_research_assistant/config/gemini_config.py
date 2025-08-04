"""
Gemini LLM configuration for the Smart Research Assistant.
"""
import os
from typing import Optional
from dataclasses import dataclass

from multiagents.worker_sdk.dspy_wrapper import DSPyConfig


@dataclass
class GeminiConfig:
    """Configuration for Gemini LLM integration."""
    model: str = "gemini/gemini-1.5-flash"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    retry_attempts: int = 3

    def __post_init__(self):
        """Load API key from environment if not provided."""
        if not self.api_key:
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "Google API key not found. Please set GOOGLE_API_KEY environment variable "
                    "or provide api_key parameter."
                )

    def to_dspy_config(self) -> DSPyConfig:
        """Convert to DSPy configuration."""
        return DSPyConfig(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            retry_attempts=self.retry_attempts
        )


def get_default_gemini_config() -> GeminiConfig:
    """Get default Gemini configuration."""
    return GeminiConfig()


def get_coordinator_config() -> GeminiConfig:
    """Get specialized config for Coordinator Agent."""
    return GeminiConfig(
        temperature=0.3,  # More deterministic for routing decisions
        max_tokens=1500
    )


def get_researcher_config() -> GeminiConfig:
    """Get specialized config for Research Agent."""
    return GeminiConfig(
        temperature=0.6,  # Balanced for research and clarification
        max_tokens=2500
    )


def get_analyst_config() -> GeminiConfig:
    """Get specialized config for Analyst Agent."""
    return GeminiConfig(
        temperature=0.2,  # More precise for analysis and calculations
        max_tokens=2000
    )


def get_formatter_config() -> GeminiConfig:
    """Get specialized config for Formatter Agent."""
    return GeminiConfig(
        temperature=0.4,  # Balanced for clear formatting
        max_tokens=3000
    )