"""Configuration loaded from environment variables at startup.

AMP injects LLM provider credentials using the mapping name as a prefix:
  {MAPPING_NAME_UPPER}_URL      e.g. WSO2_SUPPORT_ASSISTANT_1_URL
  {MAPPING_NAME_UPPER}_API_KEY  e.g. WSO2_SUPPORT_ASSISTANT_1_API_KEY

These names change whenever the agent or LLM provider mapping is renamed.
This module discovers them dynamically so the agent works regardless of the
mapping name chosen in the AMP console.

To force a specific variable name (local dev or explicit override), set:
  LLM_PROVIDER_URL=<url>
  LLM_PROVIDER_KEY=<key>

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

# AMP system vars that end in _URL but are not LLM provider endpoints.
_SYSTEM_URL_VARS = {"AMP_OTEL_ENDPOINT"}


def _env(name: str, default: str | None = None) -> str:
    val = os.environ.get(name, default)
    if val is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


def _discover_llm_credentials() -> tuple[str, str]:
    """Return ``(url, api_key)`` for the connected LLM provider.

    Resolution order:
    1. ``LLM_PROVIDER_URL`` / ``LLM_PROVIDER_KEY`` — explicit stable aliases;
       win if either is set.
    2. First ``*_URL`` / ``*_API_KEY`` pair injected by AMP.  AMP always
       injects both vars with the same prefix, so only a URL var that has a
       matching ``{PREFIX}_API_KEY`` is accepted.  This avoids accidentally
       picking up unrelated ``*_URL`` vars from the environment.
    """
    explicit_url = os.environ.get("LLM_PROVIDER_URL", "")
    explicit_key = os.environ.get("LLM_PROVIDER_KEY", "")
    if explicit_url or explicit_key:
        log.debug("LLM credentials from LLM_PROVIDER_URL / LLM_PROVIDER_KEY")
        return explicit_url, explicit_key

    for var, val in os.environ.items():
        if not var.endswith("_URL") or var in _SYSTEM_URL_VARS or not val:
            continue
        prefix = var[: -len("_URL")]
        key_var = f"{prefix}_API_KEY"
        api_key = os.environ.get(key_var, "")
        if not api_key:
            continue
        log.info("LLM credentials discovered from %s / %s", var, key_var)
        return val, api_key

    return "", ""


@dataclass(frozen=True)
class Config:
    llm_url: str
    llm_api_key: str
    gemini_model: str
    agent_name: str
    max_results: int

    @classmethod
    def from_env(cls) -> "Config":
        llm_url, llm_api_key = _discover_llm_credentials()

        if not llm_url:
            raise RuntimeError(
                "No LLM provider URL found. AMP should inject "
                "{MAPPING_NAME}_URL when an LLM provider is connected, "
                "or set LLM_PROVIDER_URL explicitly."
            )
        if not llm_api_key:
            raise RuntimeError(
                "No LLM provider API key found. AMP should inject "
                "{MAPPING_NAME}_API_KEY when an LLM provider is connected, "
                "or set LLM_PROVIDER_KEY explicitly."
            )

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
