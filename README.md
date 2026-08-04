# Contract AI Legal Analyst

> **Multi-agent AI platform for automated legal contract review, risk scoring, and knowledge graph extraction — powered by IBM watsonx.ai**

A full-stack application that replaces manual contract review with a pipeline of specialist AI agents. Upload a contract, get back a structured risk report with clause-level analysis, compliance flags, and an entity relationship graph — in minutes, not days.

---

## Architecture

```
┌─────────────────────┐     ┌──────────────────────────────────────────────┐
│  React + TypeScript │────▶│  FastAPI Backend                              │
│  Carbon Design Sys  │     │                                              │
└─────────────────────┘     │  ┌──────────────┐   ┌─────────────────────┐ │
                             │  │  Ingestion    │   │  Multi-Agent Review │ │
                             │  │  Pipeline     │   │                     │ │
                             │  │  (Docling OCR)│   │  • legal_counsel    │ │
                             │  └──────┬───────┘   │  • compliance_agent │ │
                             │         │            │  • risk_manager     │ │
                             │         ▼            │  • credit_analyst   │ │
                             │  ┌──────────────┐   │  • aml_officer      │ │
                             │  │  Embeddings  │   └──────────┬──────────┘ │
                             │  │  + Chunking  │              │            │
                             │  └──────┬───────┘              ▼            │
                             └─────────┼─────────────────────────────────┘ │
                                       │                                    │
              ┌────────────────────────┼──────────────────────┐            │
              ▼                        ▼                       ▼            │
        ┌──────────┐           ┌──────────────┐        ┌──────────────┐   │
        │ AstraDB  │           │    Neo4j     │        │  PostgreSQL  │   │
        │ (vectors)│           │(knowledge    │        │  (metadata + │   │
        └──────────┘           │  graph)      │        │   contracts) │   │
                               └──────────────┘        └──────────────┘
```

## Features

| Feature | Description |
|---|---|
| **Document Ingestion** | PDF/DOCX upload → OCR → chunking → embedding (Docling + watsonx.ai) |
| **Knowledge Graph** | Extracts parties, obligations, dates, penalties into Neo4j |
| **Multi-Agent Review** | 5 specialist agents analyse clauses in parallel via IBM watsonx.ai |
| **Risk Scoring** | Aggregated contract risk score (0–100) with per-clause breakdown |
| **Vector Search** | Semantic clause retrieval across all uploaded contracts |
| **Report Generation** | Structured PDF/JSON report with agent findings and recommendations |

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Alembic, SQLAlchemy |
| Frontend | React 18, TypeScript, Vite, Carbon Design System |
| LLM / Embeddings | IBM watsonx.ai (Llama 4 Maverick + Slate-125m) |
| Knowledge Graph | Neo4j 5 |
| Relational DB | PostgreSQL 15 |
| Vector Store | DataStax AstraDB (primary) / IBM Milvus (alternative) |
| OCR | Docling |
| Container | Docker, docker-compose |

## Getting Started

### Prerequisites
- Python 3.11+, Node 18+, Docker
- IBM watsonx.ai account (API key + project ID)
- PostgreSQL + Neo4j (included in docker-compose)

### Quick start with Docker
```bash
git clone <repo>
cd 01-contract-ai-legal-analyst
cp backend/.env.example backend/.env   # fill in credentials
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Manual setup

**Backend**
```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Copy `backend/.env.example` to `backend/.env`:

| Variable | Description |
|---|---|
| `WATSONX_API_KEY` | IBM watsonx.ai API key |
| `WATSONX_PROJECT_ID` | watsonx.ai project ID |
| `WATSONX_URL` | Regional endpoint (e.g. `https://us-south.ml.cloud.ibm.com`) |
| `DATABASE_URL` | PostgreSQL connection string |
| `NEO4J_URI` / `NEO4J_PASSWORD` | Neo4j connection |
| `ASTRA_TOKEN` + `ASTRA_ENDPOINT` | DataStax AstraDB vector store |
| `LLM_PROVIDER` | `watsonx` \| `gemini` \| `ollama` (default: `watsonx`) |

See `.env.example` for the full list with descriptions.

## Project Structure

```
01-contract-ai-legal-analyst/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── api/                 # Route handlers
│   │   ├── services/            # Business logic
│   │   │   ├── ingestion.py     # Document processing pipeline
│   │   │   ├── agents/          # Specialist AI agents
│   │   │   └── graph.py         # Neo4j knowledge graph
│   │   ├── models/              # SQLAlchemy models
│   │   └── schemas/             # Pydantic schemas
│   ├── alembic/                 # DB migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/               # Contract upload, review, dashboard
│   │   ├── components/          # Reusable Carbon components
│   │   └── services/            # API client
│   └── package.json
└── docker-compose.yml
```
