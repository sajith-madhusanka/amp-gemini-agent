"""FastAPI application — implements the AMP Chat Agent contract.

AMP expects:
  POST /chat  →  { message, session_id?, context? }  →  { response, session_id? }
  GET  /health (optional but recommended)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from agent import build_agent
from config import Config

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("wso2-support-agent")

CONFIG = Config.from_env()
AGENT = build_agent(CONFIG)
log.info(
    "WSO2 Support Agent ready | model=%s",
    CONFIG.gemini_model,
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    context: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str | None = None


app = FastAPI(
    title="WSO2 Support Assistant",
    description="LangGraph + Gemini agent for WSO2 product support, deployed on AMP",
    version="1.0.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "agent": CONFIG.agent_name}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    log.info("chat | session=%s | message=%.80s", req.session_id, req.message)
    try:
        result = await AGENT.ainvoke({"messages": [HumanMessage(content=req.message)]})
    except Exception as exc:
        log.exception("agent invocation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    final: Any = None
    for m in reversed(result.get("messages", [])):
        if isinstance(m, AIMessage):
            final = m.content
            break

    if final is None:
        final = "(no response)"
    if isinstance(final, list):
        final = "\n".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in final
        )

    return ChatResponse(response=str(final), session_id=req.session_id)
