"""Configuration loaded from environment variables at startup.

Mode is auto-detected from whichever credentials are present:

  1. AMP LLM provider (highest priority):
     LLM_PROVIDER_URL and LLM_PROVIDER_KEY are both set.
     The AMP console injects these when you bind an LLM provider to the agent
     via Configure → Add LLM Provider → Environment Variable References.
     USE_LLM_PROVIDER=true is also accepted but not required.

  2. Direct Gemini (fallback):
     GEMINI_API_KEY is set (Google AI Studio key, free tier).
     Calls Gemini via its OpenAI-compatible endpoint — no extra package needed.

If neither set of credentials is present the agent fails fast at startup
with a clear message.
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
    gemini_api_key: str
    gemini_model: str
    use_llm_provider: bool
    llm_provider_url: str
    llm_provider_key: str
    agent_name: str
    max_results: int

    @classmethod
    def from_env(cls) -> "Config":
        llm_provider_url = os.environ.get("LLM_PROVIDER_URL", "").strip()
        llm_provider_key = os.environ.get("LLM_PROVIDER_KEY", "").strip()
        gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        # Mode priority:
        #   1. Direct Gemini  — when GEMINI_API_KEY is present (always preferred;
        #      guaranteed to work with a valid Google AI Studio key).
        #   2. AMP LLM proxy  — when LLM_PROVIDER_URL + LLM_PROVIDER_KEY are both
        #      set AND GEMINI_API_KEY is absent. The proxy key must have been
        #      provisioned via AMP model config (Agent → Configure → Add LLM
        #      Provider → map "apikey" → LLM_PROVIDER_KEY). A manually-pasted
        #      Gemini key in LLM_PROVIDER_KEY will not work here.
        #
        # If you have both vars set but keep hitting 401 from the AMP gateway,
        # just add GEMINI_API_KEY to your deploy config — direct mode will take
        # over automatically.
        use_llm_provider = (
            bool(llm_provider_url and llm_provider_key) and not gemini_api_key
        )

        if not use_llm_provider and not gemini_api_key:
            raise RuntimeError(
                "No LLM credentials found. Set one of:\n"
                "  • GEMINI_API_KEY — for direct Gemini access (free tier, always works)\n"
                "  • LLM_PROVIDER_URL + LLM_PROVIDER_KEY — for AMP LLM provider\n"
                "    (these must be injected via Agent → Configure → Add LLM Provider\n"
                "    → Environment Variable References, NOT manually entered)\n"
            )

        raw_max = os.environ.get("MAX_RESULTS", "5")
        try:
            max_results = int(raw_max)
        except ValueError:
            raise RuntimeError(
                f"MAX_RESULTS must be an integer, got: {raw_max!r}"
            ) from None

        mode = "amp-llm-provider" if use_llm_provider else "gemini-direct"
        log.info("LLM mode: %s", mode)
        if use_llm_provider:
            key_preview = (llm_provider_key[:8] + "…") if len(llm_provider_key) > 8 else llm_provider_key
            log.info("LLM provider URL: %s | key prefix: %s", llm_provider_url, key_preview)

        return cls(
            gemini_api_key=gemini_api_key,
            gemini_model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
            use_llm_provider=use_llm_provider,
            llm_provider_url=llm_provider_url,
            llm_provider_key=llm_provider_key,
            agent_name=os.environ.get("AGENT_NAME", "WSO2 Support Assistant"),
            max_results=max_results,
        )
