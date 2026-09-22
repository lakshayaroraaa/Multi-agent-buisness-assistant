# Multi-Agent Business Assistant

**AI-103 Group Project — Chitkara University, September 2026**

**Made By:Navyam Jain , Lakshay Arora**

A conversational AI assistant that answers employee questions and handles simple
business tasks across departments — finance, sales, HR, and internal knowledge —
through a single chat interface, built on Microsoft Azure AI Foundry.

---

## Table of contents

- [Problem statement](#problem-statement)
- [Solution overview](#solution-overview)
- [Architecture](#architecture)
- [AI-103 concepts applied](#ai-103-concepts-applied)
- [Technology stack](#technology-stack)
- [Project structure](#project-structure)
- [Setup instructions](#setup-instructions)
- [Running it](#running-it)
- [Testing and results](#testing-and-results)
- [Responsible AI](#responsible-ai)
- [Known limitations and future improvements](#known-limitations-and-future-improvements)
- [Acknowledgments](#acknowledgments)

---

## Problem statement

Employees routinely need answers that live in different systems — invoice
status, deal stage, PTO balance, company policy — and today that means logging
into several different tools or waiting on a colleague. There is no single
place to ask a plain-language business question and get a grounded answer.

## Solution overview

Instead of one large model trying to do everything, the assistant uses a
**multi-agent architecture**. An **orchestrator agent** interprets each
request and delegates to one or more **specialist agents**, then merges their
answers into a single response. For example:

> "What's our Q3 marketing budget, and is the Acme deal still open?"

is answered by calling both the Finance and Sales agents and combining their
results — the person asking never has to know which system the answer came
from.

## Architecture

```
User (Teams / Web / CLI)
        │
        ▼
Azure API Management  (auth via Microsoft Entra ID)   [target for full deployment]
        │
        ▼
Orchestrator Agent  (Azure AI Foundry Agent Service)
  — decides which specialist(s) apply via function calling
  — runs a full thread/run/tool-submission cycle against each one it selects
   ┌────┼────┬────────────┐
   ▼    ▼    ▼            ▼
Finance Sales HR      Knowledge
Agent   Agent Agent   Agent (RAG)
   │    │    │            │
   ▼    ▼    ▼            ▼
Mock APIs (integration seam for Finance system / Dataverse / SharePoint)   Azure AI Search
```

Conversation state and session history are persisted in **Cosmos DB** per
`session_id`. See [Known limitations](#known-limitations-and-future-improvements)
for why the orchestrator does not use Azure's Connected Agents feature for
*execution*, even though it's the natural-sounding fit for this kind of system.

## AI-103 concepts applied

| Concept | Where |
|---|---|
| **Generative AI agents** | Every specialist and the orchestrator are Azure AI Foundry agents with their own instructions and model deployment |
| **Function calling / tools** | Each specialist exposes typed, Pydantic-validated tool functions (`get_invoice_status`, `draft_quote`, etc.); the orchestrator's own tools call specialists directly |
| **Multi-agent orchestration** | The orchestrator agent decides — via its own reasoning, not hardcoded if/else — which specialist(s) a request needs, including calling more than one and merging results |
| **RAG (retrieval-augmented generation)** | The Knowledge agent retrieves cited chunks from Azure AI Search (hybrid keyword + vector) over indexed policy documents, with a local fallback for development |
| **Responsible AI** | Data-privacy enforcement, no-fabrication instructions, mandatory citations, and human escalation — see [Responsible AI](#responsible-ai) |

## Technology stack

- **Azure AI Foundry Agent Service** (`azure-ai-agents`, `azure-ai-projects`) — hosts every agent
- **Azure OpenAI** — underlying language model and embeddings
- **Azure AI Search** (`azure-search-documents`) — vector + keyword hybrid index for the Knowledge agent
- **Azure Cosmos DB** (`azure-cosmos`) — conversation state and session history
- **Microsoft Entra ID** (`azure-identity`) — planned identity layer (see limitations)
- Python 3.11, **Pydantic** for every tool's input/output contract, **pytest** for testing

## Project structure

```
agents/
  orchestrator_agent.py    # routing + real thread/run execution loop
  finance_agent.py
  sales_agent.py
  hr_agent.py
  knowledge_agent.py
tools/
  finance_tools.py          # mock tool functions (see "Replace a mock integration")
  sales_tools.py
  hr_tools.py
  knowledge_tools.py        # Azure AI Search + local sample-doc fallback
shared/
  agent_base.py             # Foundry agent factory helper
  schemas.py                 # Pydantic models for every tool's input/output
  conversation_store.py      # Cosmos DB wrapper + in-memory test double
data/sample_docs/            # sample policy documents indexed by the Knowledge agent
scripts/
  ingest_knowledge_base.py   # chunks, embeds, and uploads docs to Azure AI Search
  offline_preview.py         # demo with zero Azure credentials — see below
  live_demo.py                # demo against real Azure resources
tests/                        # 29 tests covering tools, schemas, HR privacy, and routing
frontend/                     # React application built with Vite
static/                       # Production build of the React app served by FastAPI
app.py                        # FastAPI web server that hosts the UI and orchestrates agents
requirements.txt
.env.example
```

## Setup instructions

**Prerequisites:** Python 3.11+, an Azure AI Foundry project with a model
deployment, an Azure AI Search resource, and a Cosmos DB account (all coverable
by the Azure for Students $100 credit).

```bash
git clone <your-repo-url>
cd <repo-name>
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # then fill in your real values
```

See `.env.example` for the full list of required variables
(`AZURE_AI_PROJECT_CONNECTION_STRING`, `MODEL_DEPLOYMENT_NAME`,
`COSMOS_*`, `AZURE_SEARCH_*`, `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT`).

## Running it

**Web Application (FastAPI + React UI):**
You can run the full web experience which includes the orchestrator agent and a modern React UI:
```bash
# Start the FastAPI backend
uvicorn app:app --reload
```
Then navigate to `http://localhost:8000` in your browser.

*(For frontend developers: The React source code lives in the `frontend/` directory. You can run `npm run dev` there for live UI development, and `npm run build` to update the production bundle served by FastAPI in the `static/` directory).*

**CLI Fallbacks:**
If you don't have Azure credentials yet, you can run an offline CLI preview:
```bash
PYTHONPATH=. python scripts/offline_preview.py
```

Optionally, you can index the sample knowledge base once, then run the live CLI demo:
```bash
python scripts/ingest_knowledge_base.py   # optional — Knowledge agent falls back to local search without this
PYTHONPATH=. python scripts/live_demo.py
```

## Testing and results

```
$ pytest
.............................                                            [100%]
29 passed in 0.12s
```

Tests cover: every tool function's output against its Pydantic schema, the
HR agent's refusal to return another employee's data, the Knowledge agent's
citation and no-match behavior, and the orchestrator's routing decisions
(single-agent, multi-agent, and ambiguous-message clarification cases).
Azure-dependent code paths are exercised through mocks/fakes — see
`shared/conversation_store.py`'s `InMemoryConversationStore` — so the full
suite runs without any Azure credentials.

## Responsible AI

- **Privacy.** The HR agent's tools enforce, in code — not just in the
  prompt — that an employee can only retrieve their own HR data
  (`tools/hr_tools.py::_require_employee`); requests for someone else's
  information are refused with an explanation, not silently filtered.
- **Transparency.** The Knowledge agent must cite the source document for
  every claim and is instructed to say "I couldn't find that in our
  documentation" rather than answer from general knowledge when nothing
  relevant is retrieved. Every specialist's system prompt requires it to
  name the `source_system` behind any figure or status it reports.
- **Reliability.** Every tool input and output is validated against a
  Pydantic schema with `extra="forbid"`, so malformed data fails loudly
  instead of silently propagating. Specialist calls run with a timeout and
  surface failures explicitly rather than hanging or fabricating a result.
- **Human oversight.** No agent takes an action with real-world effect: the
  Finance agent never approves or rejects anything, the Sales agent's quotes
  are always drafts that are never sent, and discounts above 15% are flagged
  for manager approval rather than granted. The HR agent escalates
  harassment, discrimination, and other sensitive matters to a human HR
  representative instead of attempting to resolve them.
- **Fairness.** All specialist responses are grounded in tool data rather
  than the model's own judgment, which limits (though does not eliminate)
  the risk of the assistant giving inconsistent answers to similar requests
  from different employees.
- **Security.** No credentials are stored in code or committed to the
  repository; all secrets are read from environment variables via `.env`
  (excluded from Git — see `.gitignore`).

## Known limitations and future improvements

- **Connected Agents workaround.** Azure AI Foundry's Connected Agents
  feature is the natural way to build this kind of system, but as of this
  writing it has no mechanism for the client to answer a *child* agent's
  function-tool calls during a nested run. Since every specialist here uses
  local Python function tools, we could not use Connected Agents for
  execution and instead built the orchestrator's own tools to run a full
  thread/run cycle against each specialist directly (see the top of
  `agents/orchestrator_agent.py`). This is worth revisiting against a newer
  SDK release, or by moving tools to OpenAPI/Azure Functions, which
  Connected Agents can call natively.
- **Mock data.** All tool functions currently return mock data from an
  in-memory dictionary (`_mock_*` functions). Each has a single, clearly
  marked integration seam for swapping in a real backend call without
  changing the tool's public interface or schema.
- **Single channel.** The assistant currently runs via a local CLI
  (`scripts/live_demo.py`). A Teams or web channel, fronted by Azure API
  Management and Microsoft Entra ID, is the next step for a production
  deployment.
- **No Content Safety filtering yet.** Azure AI Content Safety on inputs and
  outputs is planned but not yet wired in.
- **Manual routing telemetry.** Specialist call logging currently records
  duration and a generic reason; capturing the orchestrator's actual
  reasoning per call (where the SDK exposes it) would make debugging
  routing decisions easier.

## Acknowledgments

Built with the `azure-ai-agents`, `azure-ai-projects`, `azure-identity`,
`azure-cosmos`, and `azure-search-documents` SDKs from Microsoft, `pydantic`
for data validation, and `pytest` for testing. Sample policy documents in
`data/sample_docs/` are original placeholder content written for this
project, not sourced from a real company.
