"""LangGraph ReAct agent construction.

Two operating modes:
  - Direct Gemini: uses langchain-openai pointed at Google's OpenAI-compatible
    endpoint (https://generativelanguage.googleapis.com/v1beta/openai/).
    Requires only GEMINI_API_KEY — no extra package needed.
  - AMP LLM Provider: uses the same ChatOpenAI class pointed at the AMP provider
    proxy. Switch by setting USE_LLM_PROVIDER=true in the AMP console.

Using the OpenAI-compatible Gemini endpoint avoids the langchain-google-genai
package, which currently requires langchain-core<0.4 and conflicts with the
langchain-core 1.x series used by langchain and langgraph.
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from config import Config
from tools import build_tools

GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

SYSTEM_PROMPT = """\
You are a knowledgeable WSO2 technical support assistant. You help WSO2 customers
and partner engineers troubleshoot issues, understand products, and find the right
documentation.

You have access to these tools:
- search_known_issues: find known bugs, misconfigurations, and their solutions
- lookup_error_code: decode error codes from logs or API responses
- check_product_compatibility: verify whether two product versions work together
- find_documentation: locate the right WSO2 docs page for a topic
- get_product_overview: explain what a WSO2 product does

GUIDELINES:
1. DIAGNOSE BEFORE ADVISING: When a user reports a problem, always call
   search_known_issues or lookup_error_code first. Don't guess without checking.
2. BE SPECIFIC: Include version numbers, configuration keys, and file names
   when they're available. Vague advice isn't useful.
3. CITE YOUR SOURCES: When you suggest a fix, mention whether it came from
   the knowledge base or your general knowledge. Point to docs URLs.
4. KNOW YOUR LIMITS: If the knowledge base has no match, say so clearly and
   suggest escalation paths (raise a support ticket at support.wso2.com).
5. STAY ON TOPIC: Only answer questions about WSO2 products and integrations.
   For unrelated requests, politely redirect.

Tone: professional, concise, and technically precise.
"""


def build_agent(cfg: Config) -> Any:
    if cfg.use_llm_provider:
        # The AMP LLM proxy gateway authenticates via Authorization: Bearer {key}.
        # Pass the key as api_key so the OpenAI SDK sets that header correctly.
        # The model name is forwarded to the provider as-is; use the same model
        # name configured in the AMP LLM provider (e.g. gemini-2.0-flash).
        llm = ChatOpenAI(
            model=cfg.gemini_model,
            temperature=0,
            base_url=cfg.llm_provider_url,
            api_key=cfg.llm_provider_key,
        )
    else:
        # Gemini's OpenAI-compatible endpoint — no extra package required.
        # See: https://ai.google.dev/gemini-api/docs/openai
        llm = ChatOpenAI(
            model=cfg.gemini_model,
            temperature=0,
            base_url=GEMINI_OPENAI_BASE_URL,
            api_key=cfg.gemini_api_key,
        )

    tools = build_tools(cfg)
    return create_react_agent(model=llm, tools=tools, prompt=SYSTEM_PROMPT)
