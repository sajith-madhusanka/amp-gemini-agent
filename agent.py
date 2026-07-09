"""LangGraph ReAct agent construction.

Uses langchain-openai pointed at the Gemini LLM provider URL injected by
the AMP platform (WSO2_SUPPORT_ASSISTANT_1_URL / WSO2_SUPPORT_ASSISTANT_1_API_KEY).

The AMP LLM proxy gateway authenticates via an 'API-Key' header (confirmed
in llm_proxy_provisioner.go: Security.APIKey.Key == "API-Key"). The OpenAI
SDK always adds 'Authorization: Bearer {api_key}' and this overrides any
attempt to clear it via default_headers. _StripAuthTransport removes the
Bearer header at the httpx transport layer so only API-Key reaches the gateway.
"""

from __future__ import annotations

from typing import Any

import httpx
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from config import Config
from tools import build_tools


class _StripAuthTransport(httpx.HTTPTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        try:
            del request.headers["authorization"]
        except KeyError:
            pass
        return super().handle_request(request)


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
    # AMP injects the gateway context URL (e.g. http://host:port/{uuid}).
    # Gemini's OpenAI-compatible endpoint lives at /v1beta/openai relative to
    # the bare domain, so we append that path so the SDK resolves
    # {base_url}/chat/completions correctly through the gateway.
    base_url = cfg.llm_url.rstrip("/") + "/v1beta/openai"
    llm = ChatOpenAI(
        model=cfg.gemini_model,
        temperature=0,
        base_url=base_url,
        api_key="not-used",
        http_client=httpx.Client(transport=_StripAuthTransport()),
        default_headers={"API-Key": cfg.llm_api_key},
    )
    tools = build_tools(cfg)
    return create_react_agent(model=llm, tools=tools, prompt=SYSTEM_PROMPT)
