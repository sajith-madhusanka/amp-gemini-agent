# WSO2 Support Assistant — AMP + Gemini Agent

A [LangGraph](https://langchain-ai.github.io/langgraph/) ReAct agent that answers
WSO2 product support questions using a curated knowledge base. Built as a
**Chat Agent** for [WSO2 Agent Manager Platform (AMP)](https://wso2.github.io/agent-manager/docs/v0.18.x/).

Uses **Google Gemini** as the LLM, routed through AMP's built-in LLM proxy
gateway. The proxy handles authentication and injects the Gemini API key
upstream — the agent never holds the actual Gemini key.

---

## How it works

```
POST /chat
   │
   ▼
LangGraph ReAct agent (GeminiAMPChat)
   │
   │  API-Key: {gateway_key}
   ▼
AMP LLM Proxy Gateway  ──── injects x-goog-api-key: {gemini_key} ────►  Gemini API
(gateway.localhost)         /v1beta/models/gemini-2.0-flash:generateContent
```

The agent uses the **native Gemini generateContent API** (not the OpenAI-compatible
endpoint). This is required because AMP's Gemini provider template injects upstream
auth via `x-goog-api-key`, which only the native API accepts. AMP automatically injects the LLM provider credentials at runtime using the
mapping name as a prefix:

| Variable pattern | Description |
|-----------------|-------------|
| `{MAPPING_NAME_UPPER}_URL` | AMP gateway context URL for the LLM proxy |
| `{MAPPING_NAME_UPPER}_API_KEY` | Gateway API key for authenticating to the proxy |

For example, if the LLM provider mapping is named **WSO2 Support Assistant 1**,
AMP injects `WSO2_SUPPORT_ASSISTANT_1_URL` and `WSO2_SUPPORT_ASSISTANT_1_API_KEY`.
The agent discovers these automatically regardless of the mapping name, so
renaming the agent or the LLM provider connection does not require any code changes.

---

## Tools

The agent answers questions about APIM, Micro Integrator, Identity Server,
Asgardeo, and Choreo by combining five tools:

| Tool | Description |
|------|-------------|
| `search_known_issues` | Searches a curated DB of known bugs and their fixes |
| `lookup_error_code` | Decodes error codes from logs/API responses |
| `check_product_compatibility` | Checks whether two product versions work together |
| `find_documentation` | Returns the right docs URL for a product + topic |
| `get_product_overview` | Explains what a WSO2 product does |

### Example queries
```
My APIM 4.2.0 returns error 900901 — what's wrong?
Is WSO2 APIM 4.3.0 compatible with Identity Server 7.1.0?
How do I configure an external key manager in APIM?
What is Asgardeo and when should I use it instead of IS?
```

---

## Prerequisites

- WSO2 Agent Manager v0.18.x running locally
  ([Quick Start](https://wso2.github.io/agent-manager/docs/v0.18.x/getting-started/quick-start/))
- A **Gemini LLM provider** registered in the AMP console (Org → LLM Providers →
  Add Provider → Gemini) with your Google AI Studio API key

---

## Deploy on AMP

### Step 1 — Register a Gemini LLM provider (if not already done)

In the AMP console, go to **Org Settings → LLM Providers → Add Provider**:
- Template: **Gemini**
- API Key: your Google AI Studio key (free at https://aistudio.google.com/apikey)

### Step 2 — Create the agent

In your project, go to **Agents → Add Agent → Platform-Hosted → Source Code**.

| Field | Value |
|-------|-------|
| Display Name | `WSO2 Support Assistant` |
| GitHub Repository | `https://github.com/sajith-madhusanka/amp-gemini-agent` |
| Branch | `main` |
| App Path | `/` |
| **Build Type** | **Docker** |
| **Dockerfile Path** | `Dockerfile` |
| Start Command | `python main.py` |

> **Important:** Select **Docker** as the build type, not Buildpack.
> Google's buildpack CDN intermittently fails to serve Python 3.11 patch
> releases. The Dockerfile uses `python:3.11.9-slim` from Docker Hub which
> is always available.

### Step 3 — Select Chat Agent as the agent interface

### Step 4 — Add a model configuration

Under **Model Configuration**, link the agent to the Gemini LLM provider you
registered in Step 1. AMP will automatically inject the gateway URL and API
key — no manual secret management needed.

### Step 5 — Optional environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model ID. Use `gemini-flash-lite-latest` if you are a new user — it has a generous free quota and lower latency. |
| `AGENT_NAME` | `WSO2 Support Assistant` | Display name logged at startup |
| `MAX_RESULTS` | `5` | Max knowledge base results per tool call |

### Step 6 — Deploy

Build takes ~3–5 minutes. Monitor progress in the **Builds** tab.

### Step 7 — Get the endpoint URL

Once the build completes, deploy from the **Deploy** tab:

1. In the AMP console, open your agent and click the **Deploy** tab.
2. Expand the environment card (e.g. **Development**) and click **Deploy** if not already deployed.
3. Wait for the status badge to show **Active**.
4. The agent's invoke URL appears in a read-only **URL** field with a copy button. It looks like:
   ```
   https://<gateway-host>/orgs/<org>/projects/<project>/agents/<agent>/v1
   ```
5. Copy that URL — append `/chat` for the chat endpoint, e.g.:
   ```
   POST https://<gateway-host>/orgs/<org>/projects/<project>/agents/<agent>/v1/chat
   ```

> **Tip:** If the URL field is missing or the Deploy tab shows "Not deployed", make sure your build completed successfully in the **Builds** tab first. The URL only appears after the first successful deployment.

---

## Project structure

```
amp-gemini-agent/
├── Dockerfile         # Docker build (python:3.11.9-slim from Docker Hub)
├── openapi.yaml       # OpenAPI spec — OpenChoreo uses this to register endpoints
├── main.py            # uvicorn entrypoint
├── app.py             # FastAPI app: POST /chat, GET /health
├── agent.py           # LangGraph ReAct agent — wires GeminiAMPChat + tools
├── gemini_amp.py      # Custom BaseChatModel: native Gemini API via AMP gateway
├── config.py          # Dynamic LLM credential discovery at startup
├── tools.py           # Five LangChain tool definitions
├── knowledge_base.py  # In-memory WSO2 knowledge base (issues, errors, compat, docs)
├── requirements.txt   # langchain, langgraph, fastapi, httpx — no langchain-openai
└── .python-version    # 3.11.9 (buildpack fallback, not used with Docker build)
```

### Key design notes

**`gemini_amp.py` — `GeminiAMPChat`**  
A custom `BaseChatModel` that calls `POST {gateway_url}/v1beta/models/{model}:generateContent`
with `API-Key: {gateway_key}` for gateway auth. Implements `bind_tools()` using
Gemini's `functionDeclarations` format. Groups consecutive `ToolMessage` objects into
a single user message, as Gemini requires all function responses for a model turn to
arrive in one request. Retries on `429 Too Many Requests` with exponential backoff
(5 s → 10 s → 20 s, up to 3 retries), respecting the `Retry-After` header.

**`config.py`**  
Discovers LLM provider credentials at startup by scanning for the `*_URL` /
`*_API_KEY` pair that AMP injects (pattern: `{MAPPING_NAME_UPPER}_URL` and
`{MAPPING_NAME_UPPER}_API_KEY`). Only a pair where both vars exist is accepted,
avoiding false positives from other `*_URL` vars in the environment. Set
`LLM_PROVIDER_URL` / `LLM_PROVIDER_KEY` to override discovery explicitly.

---

## Chat API

The agent implements AMP's chat agent contract:

```
POST /chat
Content-Type: application/json

{ "message": "string", "session_id": "string (optional)", "context": {} }
```

```json
{ "response": "string", "session_id": "string" }
```

```
GET /health  →  { "status": "ok", "agent": "WSO2 Support Assistant" }
```

---

## Local development

The agent requires an AMP LLM proxy URL and gateway key to call Gemini. For local
testing, run AMP locally and obtain the injected values from the agent's
environment, or set the stable override vars directly:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Option A — use the stable override vars (recommended for local dev):
export LLM_PROVIDER_URL=<gateway-context-url>
export LLM_PROVIDER_KEY=<gateway-api-key>

# Option B — set the AMP-style vars with whatever mapping name was used:
export WSO2_SUPPORT_ASSISTANT_1_URL=<gateway-context-url>
export WSO2_SUPPORT_ASSISTANT_1_API_KEY=<gateway-api-key>

# Optional: override the Gemini model (use gemini-flash-lite-latest for free-tier accounts):
export GEMINI_MODEL=gemini-flash-lite-latest

python main.py
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "My APIM returns 900901 — what does that mean?", "session_id": "test-1"}'
```
