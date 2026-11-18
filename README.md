# AI Support Agent

A multi-agent customer support system ("Destekçi") for a fictional e-commerce company, built with [Google ADK](https://google.github.io/adk-docs/) and Gemini. A hub agent classifies each customer message and delegates it to a specialist agent; specialists answer only from typed Python tools backed by validated data, and report "not found" instead of guessing.

This repository is being built incrementally toward a production deployment on Google Cloud (see [Roadmap](#roadmap)).

## Current capabilities

- **Hub-and-spoke orchestration:** `support_agent` handles greetings and off-topic requests itself and transfers domain questions to the right specialist (`order_agent` or `policy_agent`) using ADK's LLM-driven agent transfer.
- **Description-based routing:** Each specialist declares its responsibility in its `description`; the hub uses these, together with explicit routing rules in its instruction, to choose a sub-agent.
- **Tool calling:** Specialists invoke Python functions (`siparis_durumu_getir`, `politikalari_getir`) selected by the model from their signatures and docstrings.
- **Grounded answers:** Order lookups return an explicit error payload for unknown IDs, and the policy agent is instructed to answer only from the policy document, so the system reports missing information rather than hallucinating.
- **Scope control:** Off-topic queries (e.g. weather) are declined by the hub.
- **Resilience:** Every agent's Gemini model is configured with up to 5 automatic retries to absorb transient `503 UNAVAILABLE` / `504 DEADLINE_EXCEEDED` responses.

## Architecture

```
                        User
                         │
                         ▼
                ┌─────────────────┐
                │  support_agent  │  hub: greets, declines off-topic,
                │      (hub)      │  routes via sub-agent descriptions
                └────────┬────────┘
             transfer    │    transfer
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌───────────────────┐         ┌───────────────────┐
│    order_agent    │         │   policy_agent    │
│ order status and  │         │ returns, shipping │
│ cargo tracking    │         │ fees, delivery,   │
│                   │         │ cancellation      │
└─────────┬─────────┘         └─────────┬─────────┘
          │ tool call                   │ tool call
          ▼                             ▼
 siparis_durumu_getir()          politikalari_getir()
          │                             │
          ▼                             ▼
  OrderRepository                data/policies.md
          │
          ▼
  data/orders.json ──► Order (Pydantic)
```

| Component | Responsibility |
|---|---|
| `agents/support_agent/` | Hub agent. No tools; owns the conversation and delegates via `sub_agents=[order_agent, policy_agent]`. |
| `agents/order_agent/` | Specialist for order status and cargo tracking. Tool: `siparis_durumu_getir(siparis_no)`. |
| `agents/policy_agent/` | Specialist for store policies. Tool: `politikalari_getir()` returns the policy document. |
| `models.py` | `Order` Pydantic model. `status` is constrained with a `Literal` type, so invalid values fail validation at load time. |
| `repository.py` | `OrderRepository`: loads and validates orders, exposes `get_by_id` and `list_by_customer`. |
| `chat.py` | Week 1 single-agent prototype using the google-genai SDK directly (kept for reference). |

### Design decisions

- **One folder per agent:** Each agent lives in its own package exposing `root_agent`, following ADK's convention. Every specialist can be run and tested in isolation with `adk run`, and the hub composes them by import.
- **Hub without tools:** The hub only routes. Keeping data access inside specialists gives each agent a small, focused instruction and tool set, which makes routing and answers more reliable and lets new specialists be added without changing existing ones.
- **Repository pattern:** Data access is isolated behind `OrderRepository`. Swapping the JSON source for BigQuery later requires a new repository implementation only; agents and tools stay unchanged.
- **Validation at the boundary:** Every record is parsed into an `Order` on load. During development this caught a malformed status value (`"İade edildi."`) in the source data that would otherwise have silently broken status-based queries.
- **Explicit "not found" contract:** Tools return structured error objects rather than empty results, giving the model an unambiguous signal and reducing hallucination risk.
- **Whole-document policy context (for now):** The policy tool returns the full document, which is sufficient at its current size. It is the planned insertion point for retrieval (RAG) in week 3.

## Tech stack

- Python 3.11, [uv](https://docs.astral.sh/uv/) for dependency and environment management
- [Google ADK](https://pypi.org/project/google-adk/) for agent definition, orchestration and the dev runner
- [google-genai](https://pypi.org/project/google-genai/) SDK, model `gemini-3.5-flash-lite`
- Pydantic v2 for data modeling and validation
- pytest for testing, ruff for linting and formatting, mypy for static type checking

## Getting started

**Prerequisites:** [uv](https://docs.astral.sh/uv/) and a Gemini API key from [Google AI Studio](https://aistudio.google.com/).

```bash
git clone <repo-url>
cd ai-support-agent
uv sync
```

Create a `.env` file in the project root (it is git-ignored):

```
GEMINI_API_KEY=your_api_key
```

Run the multi-agent system:

```bash
uv run --env-file .env adk run src/ai_support_agent/agents/support_agent
```

Example session (the bracketed name shows which agent produced the reply):

```
[user]: Merhaba
[support_agent]: Merhaba! Destekçi'ye hoş geldiniz. Size nasıl yardımcı olabilirim?
[user]: SP-1003 nerede?
[order_agent]: SP-1003 numaralı siparişiniz şu anda hazırlanıyor aşamasındadır.
[user]: Hava nasıl?
[support_agent]: Üzgünüm, hava durumu gibi konu dışı konularda yardımcı olamıyorum. ...
```

```
[user]: Açılmış protein tozunu iade edebilir miyim?
[policy_agent]: Hijyen nedeniyle açılmış protein tozu gibi gıda ve takviye ürünleri iade edilemez.
```

A single specialist can also be run on its own, e.g.:

```bash
uv run --env-file .env adk run src/ai_support_agent/agents/order_agent
```

## Development

```bash
uv run pytest            # run tests
uv run ruff check .      # lint
uv run ruff format .     # format
```

## Project structure

```
ai-support-agent/
├── data/
│   ├── orders.json              # sample order data
│   └── policies.md              # store policies (returns, shipping, delivery, cancellation)
├── src/ai_support_agent/
│   ├── agents/
│   │   ├── support_agent/       # hub agent
│   │   ├── order_agent/         # order status specialist
│   │   └── policy_agent/        # store policy specialist
│   ├── models.py                # Pydantic domain models
│   ├── repository.py            # data access layer
│   └── chat.py                  # week 1 single-agent prototype
├── tests/
│   └── test_repository.py       # unit tests for the repository
└── pyproject.toml
```

## Roadmap

- [x] **Week 1:** Single agent with function calling, validated data layer, unit tests
- [x] **Week 2:** Hub-and-spoke multi-agent system with Google ADK (hub + order and policy specialists)
- [ ] **Week 3:** RAG over policy documents with Vertex AI Search, grounding and citations
- [ ] **Week 4:** MCP server for refund/shipping operations, input/output guardrails
- [ ] **Week 5:** FastAPI service with REST, SSE and WebSocket streaming
- [ ] **Week 6:** Evaluation suite (golden set, LLM-as-judge) with regression runs in CI
- [ ] **Week 7:** Deployment to Google Cloud (Agent Engine, GKE, BigQuery, Secret Manager)
- [ ] **Week 8:** Agent Engine Sessions, Memory Bank and context caching
