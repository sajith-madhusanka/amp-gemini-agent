# WSO2 Support Assistant — AMP + Gemini Agent

A [LangGraph](https://langchain-ai.github.io/langgraph/) ReAct agent that answers
WSO2 product support questions using a curated knowledge base. Built as a
**Chat Agent** for [WSO2 Agent Manager Platform (AMP)](https://wso2.github.io/agent-manager/docs/v0.18.x/).

Uses **Google Gemini** (free tier via Google AI Studio) as the LLM — no paid
OpenAI subscription required.

---

## What it does

The agent answers questions about APIM, Micro Integrator, Identity Server,
Asgardeo, and Choreo by combining:

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
My JWT token is rejected with 401 — where do I check?
```

---

## Prerequisites

- A **Google AI Studio** API key — free at https://aistudio.google.com/apikey
- WSO2 Agent Manager v0.18.x running locally or on a cluster
  ([Quick Start](https://wso2.github.io/agent-manager/docs/v0.18.x/getting-started/quick-start/))

---

## Deploy on AMP

### Step 1 — Navigate to your project
In the AMP console (`http://localhost:3000`), open a project and click
**Agents → Add Agent**.

### Step 2 — Select Platform-Hosted Agent → Source Code

### Step 3 — Fill in the configuration form

| Field | Value |
|-------|-------|
| Display Name | `WSO2 Support Assistant` |
| Description | `AI-powered WSO2 product support agent using Gemini` |
| GitHub Repository | `https://github.com/sajith-madhusanka/amp-gemini-agent` |
| Branch | `main` |
| App Path | `/` (root) |
| Language | Python |
| Language Version | `3.11` |
| Start Command | `python main.py` |

### Step 4 — Select **Chat Agent** as the agent interface

### Step 5 — Add environment variables

| Variable | Value | Required |
|----------|-------|----------|
| `GEMINI_API_KEY` | Your Google AI Studio key | Yes (direct mode) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | No (default) |
| `AGENT_NAME` | `WSO2 Support Assistant` | No |
| `MAX_RESULTS` | `5` | No |

### Step 6 — Click Deploy

Build takes ~3–5 minutes. Monitor progress in the **Builds** tab.

---

## Switch to AMP LLM Provider (optional)

If you've registered an LLM provider in the AMP console (e.g. your Gemini key
registered as an org-level provider), you can route through it to get guardrails.

1. Set `USE_LLM_PROVIDER=true` in the agent's environment variables.
2. Set `LLM_PROVIDER_URL` and `LLM_PROVIDER_KEY` (or use AMP's variable references).
3. Redeploy.

The AMP provider exposes an OpenAI-compatible proxy, so no code changes needed.

---

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export GEMINI_API_KEY=your-key-here
python main.py
```

Then test it:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "My APIM returns 900901 — what does that mean?", "session_id": "test-1"}'
```

---

## Project structure

```
amp-gemini-agent/
├── main.py            # uvicorn entrypoint (AMP start command)
├── app.py             # FastAPI app with POST /chat and GET /health
├── agent.py           # LangGraph ReAct agent (Gemini or AMP LLM provider)
├── config.py          # Environment-based configuration
├── tools.py           # LangChain tool definitions
├── knowledge_base.py  # In-memory WSO2 knowledge base (issues, errors, compat, docs)
└── requirements.txt
```

## Environment variables reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model ID |
| `USE_LLM_PROVIDER` | `false` | Route through AMP LLM provider instead |
| `LLM_PROVIDER_URL` | — | AMP provider proxy base URL |
| `LLM_PROVIDER_KEY` | — | AMP provider API key |
| `AGENT_NAME` | `WSO2 Support Assistant` | Display name |
| `MAX_RESULTS` | `5` | Max knowledge base results per tool call |
