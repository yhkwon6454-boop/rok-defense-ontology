"""Runtime configuration, resolved from environment variables.

All knobs live here so the rest of the codebase never reads ``os.environ``
directly. ``Settings.from_env()`` is the single entry point.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Default to the latest, most capable Claude model. Override with ROK_ONTO_MODEL.
DEFAULT_MODEL = "claude-opus-4-8"


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings for a pipeline run."""

    model: str = DEFAULT_MODEL
    api_key: str | None = None
    top_k: int = 5
    max_tokens: int = 16000
    effort: str = "high"  # low | medium | high | max

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from environment variables, falling back to defaults."""
        return cls(
            model=os.environ.get("ROK_ONTO_MODEL", DEFAULT_MODEL),
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            top_k=int(os.environ.get("ROK_ONTO_TOP_K", "5")),
            max_tokens=int(os.environ.get("ROK_ONTO_MAX_TOKENS", "16000")),
            effort=os.environ.get("ROK_ONTO_EFFORT", "high"),
        )
