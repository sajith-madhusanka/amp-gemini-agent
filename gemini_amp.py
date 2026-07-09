"""Custom LangChain chat model that calls Gemini's native API through an AMP LLM proxy.

The AMP gateway for Gemini providers uses x-goog-api-key for upstream auth
(not Authorization: Bearer), which is compatible with Gemini's native
generateContent endpoint but NOT with the OpenAI-compatible endpoint.
This module calls the native endpoint directly, routing through the gateway
with the API-Key header that the gateway validates.

Flow:
  agent → POST {gateway_url}/v1beta/models/{model}:generateContent
           API-Key: {gateway_key}               ← gateway auth
  gateway → x-goog-api-key: {actual_gemini_key} ← injected upstream by AMP
  gemini ← accepts x-goog-api-key ✓
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence, Union

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field


class GeminiAMPChat(BaseChatModel):
    """Native Gemini API chat model routed through the AMP LLM proxy gateway."""

    gateway_url: str
    gateway_api_key: str
    model_name: str
    temperature: float = 0.0
    bound_tools: List[dict] = Field(default_factory=list)

    def bind_tools(
        self,
        tools: Sequence[Any],
        tool_choice: Optional[str] = None,
        **kwargs: Any,
    ) -> "GeminiAMPChat":
        tool_defs = []
        for tool in tools:
            if isinstance(tool, dict):
                tool_defs.append(tool)
            elif hasattr(tool, "name") and hasattr(tool, "description"):
                schema: dict = {}
                if getattr(tool, "args_schema", None) is not None:
                    raw = tool.args_schema.model_json_schema()
                    schema = _json_schema_to_gemini(raw)
                tool_defs.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": schema,
                })
        return self.model_copy(update={"bound_tools": tool_defs})

    @staticmethod
    def _text_parts(content: Any) -> list:
        if isinstance(content, str):
            return [{"text": content}] if content else []
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append({"text": item})
                elif isinstance(item, dict) and item.get("type") == "text":
                    parts.append({"text": item["text"]})
            return parts
        return [{"text": str(content)}] if content else []

    def _to_gemini(
        self, messages: List[BaseMessage]
    ) -> tuple[Optional[dict], list]:
        system_instruction = None
        contents: list = []
        i = 0

        while i < len(messages):
            msg = messages[i]

            if isinstance(msg, SystemMessage):
                parts = self._text_parts(msg.content) or [{"text": ""}]
                system_instruction = {"parts": parts}
                i += 1

            elif isinstance(msg, HumanMessage):
                contents.append({
                    "role": "user",
                    "parts": self._text_parts(msg.content) or [{"text": ""}],
                })
                i += 1

            elif isinstance(msg, AIMessage):
                parts = self._text_parts(msg.content)
                for tc in (msg.tool_calls or []):
                    parts.append({
                        "functionCall": {
                            "name": tc["name"],
                            "args": tc.get("args", {}),
                        }
                    })
                if parts:
                    contents.append({"role": "model", "parts": parts})
                i += 1

            elif isinstance(msg, ToolMessage):
                # Gemini requires all functionResponses for a model turn to be
                # grouped in a single user message — collect consecutive ones.
                fn_parts: list = []
                while i < len(messages) and isinstance(messages[i], ToolMessage):
                    tm = messages[i]
                    fn_parts.append({
                        "functionResponse": {
                            "name": tm.name or "tool",
                            "response": {"output": str(tm.content)},
                        }
                    })
                    i += 1
                contents.append({"role": "user", "parts": fn_parts})

            else:
                i += 1

        return system_instruction, contents

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        system_instruction, contents = self._to_gemini(messages)

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": self.temperature},
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        if self.bound_tools:
            payload["tools"] = [{"functionDeclarations": self.bound_tools}]

        url = (
            f"{self.gateway_url.rstrip('/')}"
            f"/v1beta/models/{self.model_name}:generateContent"
        )
        resp = httpx.post(
            url,
            json=payload,
            headers={
                "API-Key": self.gateway_api_key,
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )
        resp.raise_for_status()

        data = resp.json()
        candidate = data["candidates"][0]
        raw_parts = candidate["content"]["parts"]

        text_parts: list[str] = []
        tool_calls: list[dict] = []

        for part in raw_parts:
            if "text" in part:
                text_parts.append(part["text"])
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append({
                    "name": fc["name"],
                    "args": fc.get("args", {}),
                    "id": f"call_{fc['name']}_{len(tool_calls)}",
                    "type": "tool_call",
                })

        ai_msg = AIMessage(
            content="".join(text_parts),
            tool_calls=tool_calls,
        )
        return ChatResult(generations=[ChatGeneration(message=ai_msg)])

    @property
    def _llm_type(self) -> str:
        return "gemini-amp-gateway"


def _json_schema_to_gemini(schema: dict) -> dict:
    """Recursively convert a Pydantic v2 JSON Schema to Gemini parameter schema."""
    _type_map = {
        "string": "STRING",
        "integer": "INTEGER",
        "number": "NUMBER",
        "boolean": "BOOLEAN",
        "array": "ARRAY",
        "object": "OBJECT",
    }

    def _convert(s: dict) -> dict:
        result: dict[str, Any] = {}
        if "type" in s:
            result["type"] = _type_map.get(s["type"], "STRING")
        if "description" in s:
            result["description"] = s["description"]
        if "enum" in s:
            result["enum"] = s["enum"]
        if s.get("type") == "array" and "items" in s:
            result["items"] = _convert(s["items"])
        if s.get("type") == "object":
            if "properties" in s:
                result["properties"] = {
                    k: _convert(v) for k, v in s["properties"].items()
                }
            if "required" in s:
                result["required"] = s["required"]
        return result

    top: dict[str, Any] = {"type": "OBJECT"}
    if "properties" in schema:
        top["properties"] = {k: _convert(v) for k, v in schema["properties"].items()}
    if "required" in schema:
        top["required"] = schema["required"]
    return top
