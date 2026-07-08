"""Configuration loaded from environment variables at startup.

Direct Gemini mode (default):
  Set GEMINI_API_KEY to your Google AI Studio key.
  Model defaults to gemini-2.0-flash (free tier).

AMP LLM provider mode:
  Set USE_LLM_PROVIDER=true and provide LLM_PROVIDER_URL / LLM_PROVIDER_KEY.
  The AMP platform exposes an OpenAI-compatible proxy for any registered provider,
  so no code changes are needed when switching providers in the console.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str | None = None) -> str:
    val = os.environ.get(name, default)
    if val is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


@dataclass(frozen=True)
class Config:
    gemini_api_key: str
    gemini_model: str
    use_llm_provider: bool
    llm_provider_url: str
    llm_provider_key: str
    agent_name: str
    max_results: int

    @classmethod
    def from_env(cls) -> "Config":
        use_llm_provider = _env("USE_LLM_PROVIDER", "false").lower() == "true"
        llm_provider_url = _env("LLM_PROVIDER_URL", "")
        llm_provider_key = _env("LLM_PROVIDER_KEY", "")

        if use_llm_provider:
            if not llm_provider_url:
                raise RuntimeError(
                    "USE_LLM_PROVIDER=true but LLM_PROVIDER_URL is not set"
                )
            if not llm_provider_key:
                raise RuntimeError(
                    "USE_LLM_PROVIDER=true but LLM_PROVIDER_KEY is not set"
                )

        gemini_api_key = _env("GEMINI_API_KEY", "")
        if not use_llm_provider and not gemini_api_key:
            raise RuntimeError(
                "Either set GEMINI_API_KEY for direct Gemini access, "
                "or set USE_LLM_PROVIDER=true with LLM_PROVIDER_URL and LLM_PROVIDER_KEY"
            )

        raw_max = _env("MAX_RESULTS", "5")
        try:
            max_results = int(raw_max)
        except ValueError:
            raise RuntimeError(f"MAX_RESULTS must be an integer, got: {raw_max!r}") from None

        return cls(
            gemini_api_key=gemini_api_key,
            gemini_model=_env("GEMINI_MODEL", "gemini-2.0-flash"),
            use_llm_provider=use_llm_provider,
            llm_provider_url=llm_provider_url,
            llm_provider_key=llm_provider_key,
            agent_name=_env("AGENT_NAME", "WSO2 Support Assistant"),
            max_results=max_results,
        )
