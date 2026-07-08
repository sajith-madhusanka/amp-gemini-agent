"""LangGraph ReAct agent construction.

Two operating modes:
  - Direct Gemini: uses ChatGoogleGenerativeAI with GEMINI_API_KEY.
  - AMP LLM Provider: uses ChatOpenAI pointed at the AMP provider proxy
    (OpenAI-compatible endpoint). Switch by setting USE_LLM_PROVIDER=true
    in the agent's environment variables on the AMP console.
"""

from __future__ import annotations

import os
from typing import Any

from langgraph.prebuilt import create_react_agent

from config import Config
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
    if cfg.use_llm_provider:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="default",
            temperature=0,
            base_url=cfg.llm_provider_url,
            api_key="not-used",
            default_headers={
                "API-Key": cfg.llm_provider_key,
                "Authorization": "",
            },
        )
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI
        os.environ.setdefault("GOOGLE_API_KEY", cfg.gemini_api_key)
        llm = ChatGoogleGenerativeAI(
            model=cfg.gemini_model,
            temperature=0,
            google_api_key=cfg.gemini_api_key,
        )

    tools = build_tools(cfg)
    return create_react_agent(model=llm, tools=tools, prompt=SYSTEM_PROMPT)
