"""Configuration loaded from environment variables at startup.

Required environment variables:
  WSO2_SUPPORT_ASSISTANT_1_URL     — base URL for the Gemini LLM provider
  WSO2_SUPPORT_ASSISTANT_1_API_KEY — API key for authenticating with the provider

Optional:
  GEMINI_MODEL   — Gemini model name (default: gemini-2.0-flash)
  AGENT_NAME     — display name logged at startup
  MAX_RESULTS    — max knowledge-base results per tool call (default: 5)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

log = logging.getLogger("wso2-support-agent")


def _env(name: str, default: str | None = None) -> str:
    val = os.environ.get(name, default)
    if val is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


@dataclass(frozen=True)
class Config:
    llm_url: str
    llm_api_key: str
    gemini_model: str
    agent_name: str
    max_results: int

    @classmethod
    def from_env(cls) -> "Config":
        llm_url = _env("WSO2_SUPPORT_ASSISTANT_1_URL")
        llm_api_key = _env("WSO2_SUPPORT_ASSISTANT_1_API_KEY")

        raw_max = os.environ.get("MAX_RESULTS", "5")
        try:
            max_results = int(raw_max)
        except ValueError:
            raise RuntimeError(
                f"MAX_RESULTS must be an integer, got: {raw_max!r}"
            ) from None

        log.info("LLM URL: %s", llm_url)

        return cls(
            llm_url=llm_url,
            llm_api_key=llm_api_key,
            gemini_model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
            agent_name=os.environ.get("AGENT_NAME", "WSO2 Support Assistant"),
            max_results=max_results,
        )
