"""LangGraph ReAct agent construction.

Uses GeminiAMPChat — a custom BaseChatModel that calls the native Gemini
generateContent API through the AMP LLM proxy gateway.

AMP injects LLM provider credentials as {MAPPING_NAME_UPPER}_URL and
{MAPPING_NAME_UPPER}_API_KEY. config.py discovers these dynamically so the
agent works regardless of how the LLM provider mapping is named.

The gateway validates the API-Key header, then proxies the request to
https://generativelanguage.googleapis.com and injects the actual Gemini
API key as x-goog-api-key. The native generateContent endpoint accepts
x-goog-api-key (unlike the OpenAI-compatible endpoint which requires Bearer).
"""

from __future__ import annotations

from typing import Any

from langgraph.prebuilt import create_react_agent

from config import Config
from gemini_amp import GeminiAMPChat
from tools import build_tools


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
    llm = GeminiAMPChat(
        gateway_url=cfg.llm_url,
        gateway_api_key=cfg.llm_api_key,
        model_name=cfg.gemini_model,
        temperature=0,
    )
    tools = build_tools(cfg)
    return create_react_agent(model=llm, tools=tools, prompt=SYSTEM_PROMPT)
