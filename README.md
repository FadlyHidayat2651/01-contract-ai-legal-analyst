# Contract AI Legal Analyst

AI-powered contract analysis platform that uses a multi-agent pipeline to review legal documents, extract risk factors, build knowledge graphs, and generate compliance reports.

## What it does
- Ingests PDF/Word contracts and extracts structured data via OCR (Docling)
- Builds a Neo4j knowledge graph of entities, clauses, and relationships
- Routes documents through specialist AI agents (legal counsel, compliance officer, risk manager, credit analyst, AML officer) powered by IBM watsonx.ai
- Scores contract risk and generates a detailed review report
- Stores embeddings in AstraDB (vector store) for semantic search

## Tech Stack
| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Alembic |
| Frontend | React, TypeScript, Vite, Carbon Design System |
| LLM | IBM watsonx.ai (Llama 4), Google Gemini, Ollama |
| Graph DB | Neo4j |
| Relational DB | PostgreSQL |
| Vector Store | DataStax AstraDB / IBM Milvus |
| Container | Docker, docker-compose |

## How to Run

### Prerequisites
- Python 3.11+, Node 18+, Docker
- PostgreSQL running locally (or update `DATABASE_URL`)
- Neo4j running locally (or via Docker)

### Backend
```bash
cd backend
cp .env.example .env        # fill in your credentials
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                  # runs on http://localhost:3000
```

### Docker (full stack)
```bash
docker-compose up --build
```

## Environment Variables
Copy `backend/.env.example` to `backend/.env`. Required variables:
- `WATSONX_API_KEY` / `WATSONX_PROJECT_ID` — IBM watsonx.ai credentials
- `DATABASE_URL` — PostgreSQL connection string
- `NEO4J_PASSWORD` — Neo4j password
- `ASTRA_TOKEN` + `ASTRA_ENDPOINT` — AstraDB vector store

See `.env.example` for full list with descriptions.
