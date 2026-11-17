# Destekçi

An LLM-powered customer support agent for a fictional e-commerce company, built with Google Gemini and function calling. The agent answers order-status questions by calling typed Python tools backed by a validated data layer, and declines to answer when no data is found.

This repository is being built incrementally toward a multi-agent, hub-and-spoke architecture on Google Cloud (see [Roadmap](#roadmap)).

## Current capabilities

- **Tool calling:** Gemini autonomously decides when to invoke `siparis_durumu_getir` (order lookup) based on the tool's signature and docstring.
- **Grounded answers:** When an order does not exist, the tool returns an explicit error payload instead of `None`, so the model reports "not found" rather than hallucinating.
- **Conversation memory:** Multi-turn context is preserved within a chat session (`client.chats`), so follow-up questions resolve against earlier turns.
- **Scope control:** The system instruction constrains the agent to customer-support topics; off-topic queries are declined.
- **Resilience:** HTTP client configured with a 60 s timeout and up to 5 automatic retries to handle transient `503 UNAVAILABLE` / `504 DEADLINE_EXCEEDED` responses.

## Architecture

```
User ──► chat loop (chat.py) ──► Gemini (chat session + system instruction)
                                     │
                                     │ function call
                                     ▼
                         siparis_durumu_getir(siparis_no)
                                     │
                                     ▼
                     OrderRepository ──► data/orders.json
                           │
                           ▼
                   Order (Pydantic model)
```

| Module | Responsibility |
|---|---|
| `models.py` | `Order` Pydantic model. `status` is constrained with a `Literal` type, so invalid values fail validation at load time. |
| `repository.py` | `OrderRepository`: loads and validates orders, exposes `get_by_id` and `list_by_customer`. |
| `chat.py` | Tool definition, Gemini client configuration, and the interactive chat loop. |

### Design decisions

- **Repository pattern:** Data access is isolated behind `OrderRepository`. Swapping the JSON source for BigQuery later requires a new repository implementation only; the agent and tools stay unchanged.
- **Validation at the boundary:** Every record is parsed into an `Order` on load. During development this caught a malformed status value (`"İade edildi."`) in the source data that would otherwise have silently broken status-based queries.
- **Explicit "not found" contract:** Tools return structured error objects rather than empty results, giving the model an unambiguous signal and reducing hallucination risk.

## Tech stack

- Python 3.11, [uv](https://docs.astral.sh/uv/) for dependency and environment management
- [google-genai](https://pypi.org/project/google-genai/) SDK, model `gemini-3.5-flash-lite`
- Pydantic v2 for data modeling and validation
- pytest for testing, ruff for linting and formatting, mypy for static type checking

## Getting started

**Prerequisites:** [uv](https://docs.astral.sh/uv/) and a Gemini API key from [Google AI Studio](https://aistudio.google.com/).

```bash
git clone <repo-url>
cd destekci
uv sync
```

Create a `.env` file in the project root (it is git-ignored):

```
GEMINI_API_KEY=your_api_key
```

Run the agent:

```bash
uv run --env-file .env python -m destekci.chat
```

Example session:

```
Destekçi: Merhaba! Size nasıl yardımcı olabilirim? (Çıkmak için 'çıkış' yazın)
Siz: SP-1003 nerede?
  [araç çağrıldı: SP-1003]
Destekçi: SP-1003 numaralı siparişiniz şu anda hazırlanmaktadır.
Siz: SP-9999 nerede?
  [araç çağrıldı: SP-9999]
Destekçi: SP-9999 numaralı sisteme ait bir sipariş bulunamadı. ...
Siz: Hava nasıl?
Destekçi: Üzgünüm, hava durumu hakkında bilgi verecek bir yetkim yok. ...
```

## Development

```bash
uv run pytest            # run tests
uv run ruff check .      # lint
uv run ruff format .     # format
```

## Project structure

```
destekci/
├── data/
│   └── orders.json          # sample order data
├── src/destekci/
│   ├── models.py            # Pydantic domain models
│   ├── repository.py        # data access layer
│   └── chat.py              # agent, tools, chat loop
├── tests/
│   └── test_repository.py   # unit tests for the repository
└── pyproject.toml
```

## Roadmap

- [x] **Week 1:** Single agent with function calling, validated data layer, unit tests
- [ ] **Week 2:** Hub-and-spoke multi-agent system with Google ADK (orchestrator + specialist agents)
- [ ] **Week 3:** RAG over policy documents with Vertex AI Search, grounding and citations
- [ ] **Week 4:** MCP server for refund/shipping operations, input/output guardrails
- [ ] **Week 5:** FastAPI service with REST, SSE and WebSocket streaming
- [ ] **Week 6:** Evaluation suite (golden set, LLM-as-judge) with regression runs in CI
- [ ] **Week 7:** Deployment to Google Cloud (Agent Engine, GKE, BigQuery, Secret Manager)
- [ ] **Week 8:** Agent Engine Sessions, Memory Bank and context caching
