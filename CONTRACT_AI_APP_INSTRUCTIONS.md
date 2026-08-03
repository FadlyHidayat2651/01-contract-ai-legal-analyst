# Contract Management & Analysis AI Application — Build Instructions

> **Purpose**: This document is a comprehensive specification for AI-assisted code generation tools (Cursor, Claude Code, Windsurf, Copilot, etc.) to build a full-stack Contract Management and Analysis AI application. Feed this entire file as context/instructions to your AI coding tool.

---

## 1. Project Overview

### 1.1 What We're Building

A web-based **Contract Lifecycle Management (CLM) platform** powered by AI that enables users to:

- Upload, parse, and store contracts (PDF, DOCX, scanned images)
- Automatically extract key metadata, clauses, obligations, and dates
- Analyze risk, flag non-standard terms, and score contract health
- Compare contracts against playbooks, templates, and regulatory standards
- Track obligations, milestones, renewals, and expirations
- Generate summaries, redlines, and amendment suggestions
- Provide a conversational AI assistant for contract Q&A
- Manage the full contract lifecycle: Draft → Review → Negotiate → Execute → Monitor → Renew/Terminate

### 1.2 Target Users

- Legal teams and in-house counsel
- Procurement and vendor management teams
- Compliance and risk officers
- Business stakeholders who need contract visibility

### 1.3 Design Principles

- **Accuracy over speed**: Contract analysis must prioritize precision — surface confidence scores and always allow human override
- **Auditability**: Every AI-generated insight must be traceable to the source clause/paragraph with page and section references
- **Security-first**: Contracts are sensitive — encrypt at rest and in transit, enforce RBAC, maintain audit logs
- **Modular architecture**: Each AI capability (extraction, risk scoring, Q&A) should be an independent service/module
- **Human-in-the-loop**: AI assists but never auto-executes legal decisions without user confirmation

---

## 2. Tech Stack

### 2.1 Recommended Stack

```
Frontend:       Next.js 14+ (App Router) + TypeScript + Tailwind CSS + shadcn/ui
Backend:        Python 3.11+ (FastAPI) — handles AI pipelines, document processing
Database:       PostgreSQL 16 (structured data) + pgvector extension (embeddings)
Object Storage: MinIO or S3-compatible (contract file storage)
Cache/Queue:    Redis (caching + task queue via Celery or BullMQ)
AI/LLM:        OpenAI GPT-4o / Anthropic Claude API (configurable provider)
Embeddings:     OpenAI text-embedding-3-large or sentence-transformers (local)
OCR:            Tesseract + pdf2image (for scanned contracts)
PDF Parsing:    PyMuPDF (fitz) + pdfplumber (tables) + python-docx (DOCX)
Search:         PostgreSQL full-text search + pgvector similarity search
Auth:           NextAuth.js or Clerk (JWT + RBAC)
Deployment:     Docker Compose (dev) / Kubernetes (prod)
```

### 2.2 Alternative/Swappable Components

| Component | Alternative Options |
|-----------|-------------------|
| LLM Provider | Azure OpenAI, AWS Bedrock, local Ollama (Llama 3), IBM watsonx |
| Vector DB | Qdrant, ChromaDB, Pinecone, Weaviate (if separating from pgvector) |
| Task Queue | Celery + Redis, Temporal, or BullMQ (Node) |
| OCR | AWS Textract, Google Document AI, Azure Form Recognizer |
| Frontend | React + Vite if not using Next.js SSR features |

---

## 3. Data Model & Database Schema

### 3.1 Core Entities

```sql
-- Organizations / Tenants
CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    settings        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id),
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(255),
    role            VARCHAR(50) NOT NULL DEFAULT 'viewer',
        -- roles: admin, legal_lead, reviewer, contributor, viewer
    avatar_url      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Contracts (core entity)
CREATE TABLE contracts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id),
    title           VARCHAR(500) NOT NULL,
    contract_type   VARCHAR(100),
        -- e.g., NDA, MSA, SaaS Agreement, Employment, Lease, SOW, Amendment
    status          VARCHAR(50) NOT NULL DEFAULT 'draft',
        -- draft, under_review, pending_approval, negotiation,
        -- executed, active, expired, terminated, renewed
    version         INTEGER DEFAULT 1,
    parent_id       UUID REFERENCES contracts(id),  -- for amendments/versions

    -- Parties
    party_a_name    VARCHAR(255),
    party_a_type    VARCHAR(50),   -- e.g., 'us', 'counterparty'
    party_b_name    VARCHAR(255),
    party_b_type    VARCHAR(50),

    -- Key Dates
    effective_date  DATE,
    expiration_date DATE,
    execution_date  DATE,
    renewal_date    DATE,
    notice_period_days INTEGER,

    -- Financial
    total_value     DECIMAL(15,2),
    currency        VARCHAR(3) DEFAULT 'USD',
    payment_terms   VARCHAR(255),

    -- Classification
    risk_score      DECIMAL(3,2),  -- 0.00 to 1.00 (AI-generated)
    risk_level      VARCHAR(20),   -- low, medium, high, critical
    tags            TEXT[],
    department      VARCHAR(100),
    governing_law   VARCHAR(100),

    -- File references
    original_file_key   TEXT,       -- S3/MinIO key for original upload
    processed_file_key  TEXT,       -- S3/MinIO key for processed/OCR'd version
    file_type           VARCHAR(10), -- pdf, docx, image
    page_count          INTEGER,

    -- AI processing status
    extraction_status   VARCHAR(20) DEFAULT 'pending',
        -- pending, processing, completed, failed, needs_review
    extraction_confidence DECIMAL(3,2),
    last_analyzed_at    TIMESTAMPTZ,

    -- Metadata
    uploaded_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Extracted Clauses
CREATE TABLE clauses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id     UUID REFERENCES contracts(id) ON DELETE CASCADE,
    clause_type     VARCHAR(100) NOT NULL,
        -- indemnification, limitation_of_liability, termination,
        -- confidentiality, ip_ownership, non_compete, force_majeure,
        -- data_protection, warranty, dispute_resolution, assignment,
        -- governing_law, payment_terms, auto_renewal, exclusivity,
        -- non_solicitation, insurance, audit_rights, change_of_control
    clause_title    VARCHAR(500),
    clause_text     TEXT NOT NULL,
    summary         TEXT,           -- AI-generated plain-English summary
    page_number     INTEGER,
    section_ref     VARCHAR(50),    -- e.g., "Section 4.2(a)"
    start_offset    INTEGER,        -- character offset in full text
    end_offset      INTEGER,

    -- Risk assessment per clause
    risk_flag       BOOLEAN DEFAULT FALSE,
    risk_reason     TEXT,
    risk_severity   VARCHAR(20),    -- low, medium, high, critical
    standard_deviation TEXT,        -- how it deviates from standard playbook

    -- Embedding for semantic search
    embedding       vector(1536),

    confidence      DECIMAL(3,2),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Obligations & Milestones
CREATE TABLE obligations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id     UUID REFERENCES contracts(id) ON DELETE CASCADE,
    clause_id       UUID REFERENCES clauses(id),
    obligation_type VARCHAR(50) NOT NULL,
        -- payment, delivery, reporting, compliance, renewal_notice,
        -- performance, insurance, audit, notification
    description     TEXT NOT NULL,
    responsible_party VARCHAR(100),  -- party_a, party_b, both
    due_date        DATE,
    recurrence      VARCHAR(50),    -- one_time, monthly, quarterly, annually
    status          VARCHAR(30) DEFAULT 'upcoming',
        -- upcoming, in_progress, completed, overdue, waived
    reminder_days   INTEGER[],      -- e.g., {30, 14, 7, 1}
    assigned_to     UUID REFERENCES users(id),
    completed_at    TIMESTAMPTZ,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Contract Comparisons / Redlines
CREATE TABLE comparisons (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_a_id   UUID REFERENCES contracts(id),
    contract_b_id   UUID REFERENCES contracts(id),  -- or playbook template
    comparison_type VARCHAR(50),    -- version_diff, playbook_check, benchmark
    differences     JSONB,          -- structured diff output
    summary         TEXT,
    risk_delta      DECIMAL(3,2),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Approval Workflows
CREATE TABLE approval_workflows (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id     UUID REFERENCES contracts(id),
    step_order      INTEGER NOT NULL,
    approver_id     UUID REFERENCES users(id),
    status          VARCHAR(30) DEFAULT 'pending',
        -- pending, approved, rejected, skipped
    comments        TEXT,
    decided_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Playbook Templates (standard clause libraries)
CREATE TABLE playbook_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id),
    name            VARCHAR(255) NOT NULL,
    contract_type   VARCHAR(100),
    clauses         JSONB NOT NULL,
        -- Array of { clause_type, preferred_language, fallback_language,
        --            must_have: bool, risk_threshold, notes }
    created_by      UUID REFERENCES users(id),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id),
    user_id         UUID REFERENCES users(id),
    entity_type     VARCHAR(50) NOT NULL,   -- contract, clause, obligation, etc.
    entity_id       UUID NOT NULL,
    action          VARCHAR(50) NOT NULL,
        -- created, updated, deleted, viewed, downloaded,
        -- analyzed, approved, rejected, exported
    changes         JSONB,
    ip_address      INET,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Chat / Q&A History
CREATE TABLE chat_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    contract_id     UUID REFERENCES contracts(id),  -- nullable for general Q&A
    messages        JSONB NOT NULL DEFAULT '[]',
        -- Array of { role, content, sources: [{clause_id, page, excerpt}], timestamp }
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_contracts_org ON contracts(org_id);
CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_contracts_expiration ON contracts(expiration_date);
CREATE INDEX idx_clauses_contract ON clauses(contract_id);
CREATE INDEX idx_clauses_type ON clauses(clause_type);
CREATE INDEX idx_obligations_due ON obligations(due_date, status);
CREATE INDEX idx_obligations_contract ON obligations(contract_id);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);

-- pgvector index for semantic search
CREATE INDEX idx_clauses_embedding ON clauses
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 4. AI Pipeline Architecture

### 4.1 Document Ingestion Pipeline

```
Upload → File Validation → Text Extraction → OCR (if needed)
    → Chunking → Embedding Generation → Storage

Pipeline Steps:
1. UPLOAD & VALIDATE
   - Accept PDF, DOCX, PNG/JPG (scanned)
   - Validate file size (max 50MB), type, virus scan
   - Store original in object storage

2. TEXT EXTRACTION
   - PDF: PyMuPDF for text-native PDFs; pdfplumber for table extraction
   - DOCX: python-docx for structured extraction preserving headings
   - Scanned/Image: Tesseract OCR with pdf2image preprocessing
   - Detect if PDF is text-native or scanned (check character count per page)

3. DOCUMENT STRUCTURING
   - Identify document sections using heading detection and regex patterns
   - Preserve section hierarchy (Article > Section > Subsection > Clause)
   - Detect and label: preamble/recitals, definitions, operative clauses,
     schedules/exhibits, signature blocks
   - Output: structured JSON with section tree

4. CHUNKING STRATEGY
   - Primary: Chunk by clause/section boundaries (semantic chunking)
   - Fallback: Sliding window (1000 tokens, 200 overlap) for unstructured text
   - Preserve metadata per chunk: page number, section reference, clause type
   - Never split mid-sentence

5. EMBEDDING & INDEXING
   - Generate embeddings for each chunk
   - Store in pgvector with metadata
   - Build full-text search index on raw text
```

### 4.2 Contract Analysis Pipeline

```
Extracted Text → Metadata Extraction → Clause Classification
    → Risk Analysis → Obligation Detection → Summary Generation

Each step uses LLM calls with structured output (JSON mode).
```

#### 4.2.1 Metadata Extraction Prompt Template

```
You are a contract analysis AI. Extract the following metadata from this
contract text. Return ONLY valid JSON.

Required fields:
{
  "title": "string — contract title or descriptive name",
  "contract_type": "string — one of: NDA, MSA, SaaS_Agreement, Employment,
      Lease, SOW, Amendment, License, Services_Agreement, Supply_Agreement,
      Partnership, Other",
  "parties": [
    {
      "name": "string — full legal entity name",
      "role": "string — e.g., Licensor, Licensee, Employer, Contractor, Buyer, Seller",
      "type": "string — corporation, individual, government, llc, partnership"
    }
  ],
  "effective_date": "YYYY-MM-DD or null",
  "expiration_date": "YYYY-MM-DD or null",
  "auto_renewal": {
    "enabled": true/false,
    "term_length": "string or null",
    "notice_period": "string or null"
  },
  "total_value": { "amount": number or null, "currency": "string" },
  "payment_terms": "string or null",
  "governing_law": "string — jurisdiction",
  "confidentiality_term": "string or null",
  "termination_notice_period": "string or null"
}

Contract text:
---
{contract_text}
---
```

#### 4.2.2 Clause Classification Prompt Template

```
You are a legal AI specializing in contract clause identification.

Analyze the following contract section and classify it. For each clause found,
provide:

{
  "clauses": [
    {
      "clause_type": "string — from the standardized list below",
      "clause_title": "string — section heading if present",
      "text": "string — exact text of the clause",
      "summary": "string — 1-2 sentence plain-English explanation",
      "section_ref": "string — e.g., Section 4.2(a)",
      "page_number": number,
      "key_terms": ["string — important defined terms used"],
      "confidence": number (0.0-1.0)
    }
  ]
}

Standardized clause types:
- indemnification
- limitation_of_liability
- termination_for_convenience
- termination_for_cause
- confidentiality
- non_disclosure
- ip_ownership
- ip_license
- non_compete
- non_solicitation
- force_majeure
- data_protection
- warranty
- disclaimer_of_warranty
- dispute_resolution (arbitration / litigation / mediation)
- governing_law
- assignment
- change_of_control
- payment_terms
- late_payment
- auto_renewal
- exclusivity
- most_favored_nation
- insurance
- audit_rights
- representations_and_warranties
- survival
- entire_agreement
- amendment
- severability
- notice
- waiver

Contract section:
---
{section_text}
---
```

#### 4.2.3 Risk Analysis Prompt Template

```
You are a senior legal risk analyst AI. Evaluate the following contract clause
for risk to our organization (we are "{our_party_name}").

Analyze against these risk factors:
1. ONE-SIDED TERMS: Does the clause disproportionately favor the counterparty?
2. UNLIMITED LIABILITY: Is there uncapped liability exposure?
3. BROAD INDEMNIFICATION: Are indemnification obligations too broad?
4. WEAK TERMINATION RIGHTS: Are our termination rights limited?
5. IP RISK: Could we lose IP rights or have them too broadly licensed?
6. DATA/PRIVACY RISK: Insufficient data protection or processing obligations?
7. AUTO-RENEWAL TRAP: Auto-renewal with short/no notice windows?
8. NON-STANDARD LANGUAGE: Significant deviation from market-standard terms?
9. MISSING PROTECTIONS: Key protective clauses absent?
10. REGULATORY RISK: Terms that may conflict with applicable regulations?

Return:
{
  "risk_score": number (0.0-1.0, where 1.0 is highest risk),
  "risk_level": "low|medium|high|critical",
  "risk_factors": [
    {
      "factor": "string — which risk factor",
      "severity": "low|medium|high|critical",
      "description": "string — specific concern",
      "recommendation": "string — suggested change or negotiation point",
      "source_text": "string — exact clause text triggering this flag"
    }
  ],
  "overall_assessment": "string — 2-3 sentence summary",
  "negotiation_priority": "string — what to address first"
}

Our standard position (playbook):
---
{playbook_standard_if_available}
---

Clause to analyze:
---
{clause_text}
---
```

#### 4.2.4 Obligation Extraction Prompt Template

```
You are a contract obligations analyst. Extract all obligations, deadlines,
and action items from this contract.

For each obligation, return:
{
  "obligations": [
    {
      "description": "string — clear description of what must be done",
      "obligation_type": "payment|delivery|reporting|compliance|
          renewal_notice|performance|insurance|audit|notification",
      "responsible_party": "string — which party must perform",
      "due_date": "YYYY-MM-DD or null",
      "due_description": "string — e.g., 'within 30 days of effective date'",
      "recurrence": "one_time|monthly|quarterly|annually|ongoing",
      "consequence_of_breach": "string — what happens if not met",
      "source_section": "string — section reference",
      "source_text": "string — exact text"
    }
  ]
}

Contract text:
---
{contract_text}
---
```

### 4.3 Conversational Q&A (RAG Pipeline)

```
User Question → Query Embedding → Retrieve Relevant Chunks
    → Rerank → Construct Prompt with Context → LLM Response
    → Citation Mapping → Response with Source References

Implementation:
1. RETRIEVAL
   - Embed user question
   - Hybrid search: pgvector cosine similarity + PostgreSQL full-text search
   - Retrieve top-k chunks (k=10 initial, rerank to top-5)
   - Filter by contract scope (if user is asking about a specific contract)

2. RERANKING
   - Use cross-encoder reranker (e.g., ms-marco-MiniLM) or LLM-based reranking
   - Score relevance of each chunk to the question
   - Select top-5 most relevant

3. ANSWER GENERATION
   System prompt:
   "You are a contract analysis assistant. Answer the user's question based
   ONLY on the provided contract excerpts. For every claim, cite the source
   using [Section X.X, Page Y] format. If the answer is not in the provided
   context, say so clearly. Never fabricate contract terms."

4. CITATION MAPPING
   - Map each citation back to clause_id, page_number, section_ref
   - Return clickable references that navigate to the source in the document viewer
```

---

## 5. API Design

### 5.1 REST API Endpoints

```
BASE: /api/v1

── Authentication ──
POST   /auth/login
POST   /auth/register
POST   /auth/refresh
POST   /auth/logout

── Contracts ──
GET    /contracts                    # List (paginated, filterable, sortable)
POST   /contracts                    # Create new (metadata only)
GET    /contracts/:id                # Get details + extracted data
PUT    /contracts/:id                # Update metadata
DELETE /contracts/:id                # Soft delete
POST   /contracts/:id/upload         # Upload file and trigger processing
GET    /contracts/:id/download       # Download original file
GET    /contracts/:id/text           # Get extracted full text
GET    /contracts/:id/status         # Get processing status

── AI Analysis ──
POST   /contracts/:id/analyze        # Trigger full AI analysis pipeline
GET    /contracts/:id/clauses        # Get all extracted clauses
GET    /contracts/:id/clauses/:cid   # Get specific clause with risk detail
GET    /contracts/:id/obligations    # Get all obligations
GET    /contracts/:id/risks          # Get risk assessment summary
GET    /contracts/:id/summary        # Get AI-generated executive summary
POST   /contracts/:id/compare        # Compare against another contract or playbook

── Chat / Q&A ──
POST   /chat                         # Send message (streaming SSE response)
GET    /chat/sessions                # List chat sessions
GET    /chat/sessions/:id            # Get session history
DELETE /chat/sessions/:id            # Delete session

── Obligations & Alerts ──
GET    /obligations                   # List all across contracts (filterable)
PUT    /obligations/:id              # Update status
GET    /obligations/upcoming          # Dashboard: upcoming deadlines
GET    /obligations/overdue           # Dashboard: overdue items

── Playbooks ──
GET    /playbooks                     # List playbook templates
POST   /playbooks                     # Create playbook
PUT    /playbooks/:id                 # Update playbook
POST   /playbooks/:id/check/:contractId  # Check contract against playbook

── Approvals ──
GET    /contracts/:id/approvals       # Get approval workflow status
POST   /contracts/:id/approvals       # Create/trigger approval workflow
PUT    /approvals/:id                 # Approve or reject

── Dashboard & Reports ──
GET    /dashboard/stats               # Aggregate stats (counts, values, risk dist)
GET    /dashboard/expiring            # Contracts expiring in next N days
GET    /dashboard/risk-overview       # Risk distribution across portfolio
GET    /reports/export                # Export contracts/obligations (CSV, Excel)

── Admin ──
GET    /admin/audit-logs              # Audit trail (paginated)
GET    /admin/users                   # Manage users
PUT    /admin/settings                # Organization settings
```

### 5.2 Query Parameters Convention

```
# Pagination
?page=1&per_page=25

# Sorting
?sort_by=expiration_date&sort_order=asc

# Filtering
?status=active&contract_type=NDA&risk_level=high
?expiration_before=2025-12-31&department=engineering
?search=confidentiality+clause    # full-text search
?tags=vendor,renewal

# Date ranges
?created_after=2024-01-01&created_before=2024-12-31
```

---

## 6. Frontend Architecture

### 6.1 Page Structure

```
/                           → Dashboard (overview, stats, alerts)
/contracts                  → Contract list (table with filters/search)
/contracts/upload           → Upload wizard (drag-drop, bulk upload)
/contracts/:id              → Contract detail view
    /contracts/:id/overview     → Summary, metadata, key dates, risk score
    /contracts/:id/document     → Document viewer with clause highlights
    /contracts/:id/clauses      → Clause list with risk flags
    /contracts/:id/obligations  → Obligation tracker
    /contracts/:id/compare      → Comparison / redline view
    /contracts/:id/history      → Version history and audit log
    /contracts/:id/chat         → Contract-specific AI Q&A
/obligations                → Cross-contract obligation dashboard
/playbooks                  → Playbook template management
/chat                       → General AI assistant (cross-contract Q&A)
/reports                    → Analytics and reporting
/settings                   → Organization and user settings
```

### 6.2 Key UI Components

```
ContractTable
├── FilterBar (status, type, risk level, date range, department, tags)
├── SearchInput (full-text + semantic toggle)
├── SortableColumns
├── BulkActions (export, tag, assign, delete)
└── Pagination

ContractDetail
├── MetadataCard (parties, dates, value, status badge, risk score gauge)
├── KeyDatesTimeline (effective → expiration with milestones)
├── DocumentViewer
│   ├── PDF/DOCX renderer (react-pdf or pdfjs)
│   ├── ClauseHighlightOverlay (color-coded by risk level)
│   ├── AnnotationPanel (AI insights per highlighted section)
│   └── PageNavigation
├── ClausePanel
│   ├── ClauseCard (type badge, summary, risk indicator, expand for full text)
│   ├── RiskBadge (color-coded: green/yellow/orange/red)
│   └── PlaybookDeviation indicator
├── ObligationTracker
│   ├── ObligationCard (description, due date, responsible party, status)
│   ├── CalendarView (obligations on calendar)
│   └── KanbanView (upcoming / in-progress / completed / overdue)
└── ChatSidebar (contract-scoped AI assistant)

Dashboard
├── StatsCards (total contracts, active, expiring soon, high-risk count)
├── RiskDistributionChart (donut chart by risk level)
├── ExpirationTimeline (bar chart: contracts expiring by month)
├── ObligationAlerts (upcoming/overdue list)
├── RecentActivity feed
└── ContractValueByType (stacked bar or treemap)

ComparisonView
├── SideBySideViewer (two documents synced scroll)
├── DiffHighlights (added/removed/changed with color coding)
├── DeviationList (list of differences from playbook)
└── RiskDelta indicator

ChatInterface
├── MessageList (user + AI messages with citations)
├── CitationPopover (click citation → see source clause, link to document)
├── ContractScopeSelector (filter AI answers to specific contract)
├── SuggestedQuestions (contextual quick prompts)
└── MessageInput (with file attachment for new contract questions)
```

### 6.3 Design System Notes

```
- Use shadcn/ui component library for consistent, accessible UI
- Color coding for risk levels:
    Low     → green-500  (#22c55e)
    Medium  → yellow-500 (#eab308)
    High    → orange-500 (#f97316)
    Critical→ red-500    (#ef4444)
- Contract status badges with distinct colors per status
- Dark mode support from the start
- Responsive: desktop-first but usable on tablet
- Skeleton loading states for all async data
- Toast notifications for async operations (analysis complete, etc.)
- Empty states with clear CTAs
```

---

## 7. Backend Service Architecture

### 7.1 Service Modules

```
app/
├── main.py                      # FastAPI app entry point
├── config.py                    # Environment config, secrets
├── dependencies.py              # Dependency injection
│
├── api/                         # API route handlers
│   ├── contracts.py
│   ├── analysis.py
│   ├── chat.py
│   ├── obligations.py
│   ├── playbooks.py
│   ├── approvals.py
│   ├── dashboard.py
│   └── admin.py
│
├── services/                    # Business logic layer
│   ├── contract_service.py      # CRUD + orchestration
│   ├── ingestion_service.py     # File processing pipeline
│   ├── extraction_service.py    # Text extraction (PDF, DOCX, OCR)
│   ├── analysis_service.py      # AI analysis orchestrator
│   ├── clause_classifier.py     # Clause identification + classification
│   ├── risk_analyzer.py         # Risk scoring engine
│   ├── obligation_extractor.py  # Obligation/deadline detection
│   ├── comparison_service.py    # Contract diff + playbook checking
│   ├── summary_service.py       # Executive summary generation
│   ├── chat_service.py          # RAG pipeline for Q&A
│   ├── embedding_service.py     # Embedding generation + vector ops
│   ├── notification_service.py  # Email/Slack alerts for deadlines
│   └── export_service.py        # CSV/Excel/PDF report generation
│
├── models/                      # SQLAlchemy ORM models
│   ├── contract.py
│   ├── clause.py
│   ├── obligation.py
│   ├── user.py
│   └── ...
│
├── schemas/                     # Pydantic request/response schemas
│   ├── contract.py
│   ├── analysis.py
│   ├── chat.py
│   └── ...
│
├── workers/                     # Background task workers
│   ├── analysis_worker.py       # Async contract analysis pipeline
│   ├── reminder_worker.py       # Obligation deadline reminders
│   └── embedding_worker.py      # Batch embedding generation
│
├── prompts/                     # LLM prompt templates (Jinja2 or string)
│   ├── metadata_extraction.py
│   ├── clause_classification.py
│   ├── risk_analysis.py
│   ├── obligation_extraction.py
│   ├── summary_generation.py
│   ├── comparison.py
│   └── chat_system.py
│
└── utils/
    ├── llm_client.py            # Abstraction over OpenAI/Anthropic/etc.
    ├── pdf_utils.py
    ├── docx_utils.py
    ├── ocr_utils.py
    ├── chunking.py              # Smart text chunking strategies
    ├── security.py              # Encryption, sanitization
    └── date_parser.py           # Flexible date extraction
```

### 7.2 LLM Client Abstraction

```python
# utils/llm_client.py — implement this interface
# so the LLM provider is swappable via config

class LLMClient:
    """
    Unified interface for LLM calls.
    Configure provider via LLM_PROVIDER env var: 'openai', 'anthropic', 'azure', 'local'
    """

    async def complete(
        self,
        messages: list[dict],
        model: str = None,          # override per-call if needed
        temperature: float = 0.0,   # low temp for extraction accuracy
        max_tokens: int = 4096,
        response_format: str = "json",  # "json" or "text"
        timeout: int = 120
    ) -> dict:
        """Returns parsed JSON or text response."""
        pass

    async def embed(
        self,
        texts: list[str],
        model: str = None
    ) -> list[list[float]]:
        """Returns embedding vectors."""
        pass

    async def stream(
        self,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        """Yields streaming text chunks for chat responses."""
        pass
```

---

## 8. Key Implementation Details

### 8.1 Document Processing Pipeline (Detailed)

```python
# services/ingestion_service.py — pseudocode

async def process_contract(contract_id: str, file_path: str) -> None:
    """
    Full ingestion pipeline. Runs as background task.
    Updates contract.extraction_status throughout.
    """
    try:
        # 1. Detect file type and extract text
        update_status(contract_id, "processing")
        file_type = detect_file_type(file_path)

        if file_type == "pdf":
            text, pages = extract_pdf_text(file_path)  # PyMuPDF
            if is_scanned_pdf(text, pages):
                text = ocr_pdf(file_path)               # Tesseract
            tables = extract_tables(file_path)           # pdfplumber
        elif file_type == "docx":
            text, structure = extract_docx(file_path)    # python-docx
        elif file_type in ("png", "jpg"):
            text = ocr_image(file_path)                  # Tesseract

        # 2. Structure the document
        sections = identify_sections(text)
        # Returns: [{ heading, level, text, page, start_offset, end_offset }]

        # 3. Store full text
        store_full_text(contract_id, text)

        # 4. Run AI extraction (can parallelize)
        metadata = await extract_metadata(text)
        clauses = await classify_clauses(sections)
        obligations = await extract_obligations(text)

        # 5. Risk analysis (depends on clauses)
        playbook = get_playbook_for_type(metadata.contract_type)
        risk_results = await analyze_risks(clauses, playbook)

        # 6. Generate summary
        summary = await generate_summary(text, metadata, risk_results)

        # 7. Generate embeddings for all chunks
        chunks = create_chunks(sections, clauses)
        embeddings = await embed_chunks(chunks)

        # 8. Store everything
        store_analysis_results(
            contract_id, metadata, clauses,
            obligations, risk_results, summary, embeddings
        )

        update_status(contract_id, "completed")

    except Exception as e:
        update_status(contract_id, "failed", error=str(e))
        log_error(contract_id, e)
```

### 8.2 Smart Chunking Strategy

```python
# utils/chunking.py

def chunk_contract(sections: list, max_tokens: int = 1000, overlap: int = 200):
    """
    Hybrid chunking strategy:
    1. Try clause-boundary chunking first (preserves semantic units)
    2. Fall back to sliding window for long unstructured sections
    3. Never split mid-sentence
    4. Always preserve metadata per chunk
    """
    chunks = []

    for section in sections:
        token_count = count_tokens(section.text)

        if token_count <= max_tokens:
            # Section fits in one chunk
            chunks.append({
                "text": section.text,
                "page": section.page,
                "section_ref": section.heading,
                "start_offset": section.start_offset,
                "end_offset": section.end_offset,
                "chunk_type": "section"
            })
        else:
            # Split by paragraph boundaries, respecting sentence integrity
            paragraphs = split_into_paragraphs(section.text)
            current_chunk = ""
            current_start = section.start_offset

            for para in paragraphs:
                if count_tokens(current_chunk + para) > max_tokens:
                    if current_chunk:
                        chunks.append({
                            "text": current_chunk.strip(),
                            "page": section.page,
                            "section_ref": section.heading,
                            "start_offset": current_start,
                            "end_offset": current_start + len(current_chunk),
                            "chunk_type": "sliding_window"
                        })
                    # Overlap: keep last N tokens of previous chunk
                    overlap_text = get_last_n_tokens(current_chunk, overlap)
                    current_chunk = overlap_text + para
                    current_start = current_start + len(current_chunk) - len(overlap_text)
                else:
                    current_chunk += para

            if current_chunk.strip():
                chunks.append({
                    "text": current_chunk.strip(),
                    "page": section.page,
                    "section_ref": section.heading,
                    "start_offset": current_start,
                    "end_offset": section.end_offset,
                    "chunk_type": "sliding_window"
                })

    return chunks
```

### 8.3 Risk Scoring Algorithm

```python
# services/risk_analyzer.py

CLAUSE_RISK_WEIGHTS = {
    "indemnification":          0.15,
    "limitation_of_liability":  0.15,
    "termination_for_convenience": 0.10,
    "termination_for_cause":    0.08,
    "ip_ownership":             0.10,
    "data_protection":          0.10,
    "confidentiality":          0.07,
    "auto_renewal":             0.05,
    "non_compete":              0.05,
    "governing_law":            0.03,
    "dispute_resolution":       0.04,
    "force_majeure":            0.03,
    "insurance":                0.02,
    "audit_rights":             0.02,
    "assignment":               0.01,
}
# Remaining weight distributed to "missing clause" penalties

MISSING_CLAUSE_PENALTIES = {
    # If these clauses are expected but absent, add penalty
    "limitation_of_liability": 0.25,
    "termination_for_convenience": 0.15,
    "data_protection": 0.20,
    "indemnification": 0.15,
    "force_majeure": 0.10,
}

def calculate_contract_risk_score(clause_risks: list, contract_type: str) -> dict:
    """
    Composite risk score combining:
    1. Per-clause AI risk scores (weighted)
    2. Missing clause penalties
    3. Contract-type-specific adjustments
    """
    weighted_score = 0.0
    found_types = set()

    for clause in clause_risks:
        weight = CLAUSE_RISK_WEIGHTS.get(clause.clause_type, 0.02)
        weighted_score += clause.risk_score * weight
        found_types.add(clause.clause_type)

    # Penalty for missing critical clauses
    expected = get_expected_clauses(contract_type)
    for clause_type in expected:
        if clause_type not in found_types:
            penalty = MISSING_CLAUSE_PENALTIES.get(clause_type, 0.05)
            weighted_score += penalty

    # Normalize to 0-1
    final_score = min(1.0, weighted_score)

    risk_level = (
        "low" if final_score < 0.25 else
        "medium" if final_score < 0.50 else
        "high" if final_score < 0.75 else
        "critical"
    )

    return {
        "risk_score": round(final_score, 2),
        "risk_level": risk_level,
        "clause_scores": clause_risks,
        "missing_clauses": [c for c in expected if c not in found_types],
    }
```

---

## 9. Security & Compliance Requirements

### 9.1 Mandatory Security Controls

```
AUTHENTICATION & AUTHORIZATION
- JWT-based authentication with refresh token rotation
- Role-Based Access Control (RBAC):
    admin         → full access, user management, settings
    legal_lead    → all contracts, approve/reject, manage playbooks
    reviewer      → view + annotate assigned contracts
    contributor   → upload + edit own contracts
    viewer        → read-only access to assigned contracts
- Organization-level data isolation (multi-tenant)
- API rate limiting per user/org

ENCRYPTION
- TLS 1.3 for all API communication
- AES-256 encryption at rest for stored contracts
- Encrypt sensitive fields in database (party names, values)
- Signed URLs for file downloads (time-limited)

AUDIT & COMPLIANCE
- Immutable audit log for all actions (who, what, when, from where)
- Log all AI analysis runs with model version, prompt hash, and timestamp
- Data retention policies (configurable per org)
- GDPR-ready: support data export and deletion requests
- SOC 2 alignment: access controls, monitoring, incident response

INPUT VALIDATION
- Sanitize all file uploads (virus scan, file type validation)
- Validate and sanitize all user inputs
- Prevent prompt injection in chat inputs
- Rate-limit AI API calls per user

AI-SPECIFIC SECURITY
- Never send contract data to LLM providers without org consent
- Support for on-premise / private LLM deployment
- Prompt injection protection: validate LLM outputs against expected schema
- Confidence thresholds: flag low-confidence extractions for human review
- Model version pinning for reproducible analysis
```

---

## 10. Background Jobs & Notifications

### 10.1 Async Task Queue

```
TASKS (via Celery/Redis or similar):

1. contract.process          — Full ingestion pipeline (triggered on upload)
2. contract.analyze          — AI analysis pipeline (triggered after ingestion)
3. contract.embed            — Generate/update embeddings
4. contract.compare          — Run comparison analysis
5. obligation.check_due      — Cron: daily scan for upcoming/overdue obligations
6. obligation.send_reminder  — Send email/Slack reminders
7. report.generate           — Generate scheduled reports (weekly/monthly)
8. batch.analyze             — Bulk analysis for contract portfolio

CRON SCHEDULE:
- Every day 08:00:  Check obligations due in reminder windows
- Every day 09:00:  Send obligation reminder digests
- Every Monday:     Weekly portfolio risk summary email
- Every 1st:        Monthly contract expiration report
```

### 10.2 Notification Events

```
- Contract uploaded and processing started
- Analysis complete (with risk score summary)
- High-risk clause detected
- Obligation deadline approaching (at configured intervals)
- Obligation overdue
- Contract expiring soon (30, 14, 7, 1 days)
- Approval requested / approved / rejected
- Playbook deviation detected in new contract

Channels: in-app notification center, email digest, Slack/Teams webhook
```

---

## 11. Testing Strategy

### 11.1 Test Categories

```
UNIT TESTS
- Chunking logic (boundary detection, overlap, metadata preservation)
- Risk score calculation (weighted scoring, missing clause penalties)
- Date parsing (various date formats in contracts)
- Section identification regex patterns
- Pydantic schema validation

INTEGRATION TESTS
- Full ingestion pipeline (upload → extract → store)
- AI analysis pipeline (mock LLM responses, verify structured output parsing)
- RAG pipeline (embed → retrieve → rerank → answer)
- Database queries (complex filters, pagination, full-text search)
- File storage (upload → download → delete)

E2E TESTS
- Upload a real NDA → verify metadata extraction accuracy
- Upload a complex MSA → verify all clause types detected
- Chat Q&A → verify citations link to correct source locations
- Obligation tracking → verify reminders trigger at correct times
- Approval workflow → verify state transitions

AI EVALUATION TESTS
- Maintain a test set of 50+ annotated contracts with ground truth:
    - Known clause types and locations
    - Known risk levels
    - Known obligations and dates
- Run extraction pipeline on test set, measure:
    - Precision / Recall for clause classification
    - Accuracy of metadata extraction
    - Risk score correlation with human assessment
- Track these metrics across model/prompt changes (regression testing)
```

---

## 12. Environment Variables

```env
# Application
APP_ENV=development
APP_PORT=8000
APP_SECRET_KEY=<random-256-bit-key>
FRONTEND_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/contract_ai
REDIS_URL=redis://localhost:6379/0

# Object Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=contracts

# AI / LLM
LLM_PROVIDER=openai                    # openai | anthropic | azure | local
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=gpt-4o                       # default model for analysis
LLM_EMBEDDING_MODEL=text-embedding-3-large
LLM_TEMPERATURE=0.0                    # keep deterministic for extraction
LLM_MAX_RETRIES=3

# OCR (optional, for cloud OCR)
OCR_PROVIDER=tesseract                  # tesseract | aws_textract | google_docai

# Auth
NEXTAUTH_SECRET=<random-key>
NEXTAUTH_URL=http://localhost:3000

# Notifications
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASS=<password>
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Feature Flags
ENABLE_OCR=true
ENABLE_CHAT=true
ENABLE_NOTIFICATIONS=true
MAX_FILE_SIZE_MB=50
ANALYSIS_CONFIDENCE_THRESHOLD=0.7       # flag for review if below this
```

---

## 13. Deployment

### 13.1 Docker Compose (Development)

```yaml
version: "3.9"
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on: [backend]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [db, redis, minio]
    volumes:
      - ./backend:/app

  worker:
    build: ./backend
    command: celery -A app.workers worker --loglevel=info
    env_file: .env
    depends_on: [db, redis, backend]

  scheduler:
    build: ./backend
    command: celery -A app.workers beat --loglevel=info
    env_file: .env
    depends_on: [redis, worker]

  db:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: contract_ai
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  minio:
    image: minio/minio
    ports: ["9000:9000", "9001:9001"]
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

volumes:
  pgdata:
  minio_data:
```

---

## 14. MVP Scope & Phasing

### Phase 1 — Core (Weeks 1–4)

- [ ] Project scaffolding (Next.js + FastAPI + PostgreSQL + pgvector)
- [ ] User authentication and RBAC
- [ ] Contract upload (PDF, DOCX) with file storage
- [ ] Text extraction pipeline (PyMuPDF + python-docx + basic OCR)
- [ ] AI metadata extraction (parties, dates, type, value)
- [ ] AI clause classification (top 10 clause types)
- [ ] Basic risk scoring
- [ ] Contract list view with search and filters
- [ ] Contract detail page with metadata and clause list

### Phase 2 — Analysis & Intelligence (Weeks 5–8)

- [ ] Full clause type library (30+ types)
- [ ] Obligation extraction and tracking
- [ ] Playbook template management
- [ ] Contract vs. playbook comparison
- [ ] RAG-based chat Q&A with citations
- [ ] Risk detail view with per-clause breakdown
- [ ] Executive summary generation
- [ ] Dashboard with stats, charts, and alerts

### Phase 3 — Workflow & Collaboration (Weeks 9–12)

- [ ] Approval workflows
- [ ] Notification system (email + in-app + Slack)
- [ ] Obligation reminders and calendar view
- [ ] Contract version history and amendment tracking
- [ ] Document viewer with clause highlighting overlay
- [ ] Bulk upload and batch analysis
- [ ] Export (CSV, Excel, PDF reports)
- [ ] Audit log viewer

### Phase 4 — Advanced (Weeks 13+)

- [ ] Side-by-side redline comparison view
- [ ] AI-suggested clause amendments
- [ ] Contract drafting assistant (generate from template)
- [ ] Multi-language contract support
- [ ] Advanced analytics (portfolio risk trends, clause benchmarking)
- [ ] API integrations (DocuSign, Salesforce, SharePoint)
- [ ] On-premise LLM support
- [ ] Mobile-responsive refinement

---

## 15. Prompt Engineering Best Practices

```
1. ALWAYS use JSON mode / structured output for extraction tasks
   - Prevents hallucinated prose in metadata fields
   - Makes parsing deterministic

2. SET temperature=0.0 for extraction, 0.3 for chat/summaries
   - Extraction needs determinism
   - Chat benefits from slight creativity

3. CHAIN prompts rather than mega-prompts
   - Step 1: Extract metadata
   - Step 2: Classify clauses (per section)
   - Step 3: Risk-analyze each clause
   - Step 4: Synthesize summary
   This improves accuracy over a single "do everything" prompt

4. INCLUDE examples in prompts (few-shot)
   - Show 2-3 examples of correct extraction output
   - Especially for clause classification edge cases

5. VALIDATE LLM output against Pydantic schemas
   - If output doesn't parse, retry with error feedback (max 2 retries)
   - Log all validation failures for prompt tuning

6. USE system prompts for role-setting
   - "You are a senior legal analyst specializing in {contract_type} contracts"
   - Improves domain-specific accuracy

7. HANDLE long documents with map-reduce
   - Split into sections, analyze each, then aggregate
   - Don't try to fit entire contracts in one context window

8. ALWAYS ground answers in source text
   - For chat: "Answer based ONLY on the provided excerpts"
   - For extraction: "Quote the exact text that supports each field"
   - For risk: "Cite the specific clause language creating the risk"
```

---

## 16. Contract Analysis Best Practices (Domain Knowledge)

### 16.1 Standard Clause Checklist by Contract Type

```
NDA:
  Must have: confidentiality_definition, exclusions, term, return_of_info
  Watch for: overly_broad_definition, unlimited_term, no_exclusions

MSA / Services Agreement:
  Must have: scope, payment, liability_cap, indemnification, termination,
             ip_ownership, confidentiality, warranty, governing_law
  Watch for: unlimited_liability, auto_renewal_without_notice, broad_assignment

SaaS Agreement:
  Must have: service_levels (SLA), data_protection, uptime_guarantee,
             data_portability, security_obligations, termination_rights
  Watch for: no_SLA, unilateral_price_changes, data_lock_in, broad_license_grant

Employment Agreement:
  Must have: compensation, benefits, termination_provisions, non_compete,
             non_solicitation, ip_assignment, confidentiality
  Watch for: overly_broad_non_compete, no_severance, weak_termination_protections

Lease:
  Must have: rent, term, maintenance, insurance, subletting, termination,
             renewal_options, default_remedies
  Watch for: uncapped_CAM_charges, unlimited_rent_escalation, no_early_termination
```

### 16.2 Common Red Flags

```
CRITICAL RED FLAGS (auto-flag):
- Unlimited or uncapped liability
- Indemnification with no carve-outs for gross negligence
- Unilateral amendment rights by counterparty
- Auto-renewal with <30 day notice window
- Assignment rights without consent
- Governing law in unfavorable jurisdiction
- No termination for convenience
- Perpetual license grant with no reversion
- Data ownership ambiguity
- Waiver of jury trial without arbitration alternative
- No force majeure clause (post-COVID essential)

HIGH-RISK PATTERNS:
- "Including but not limited to" in liability clauses (unbounded scope)
- "Sole and exclusive remedy" (limits available recourse)
- "Material breach" without definition of materiality
- Cure periods longer than 60 days
- Survival clauses extending beyond 3 years
- Insurance requirements without standard market minimums
```

---

*End of Instructions. This document provides complete specifications for an AI code IDE tool to generate a production-grade Contract Management & Analysis AI application. Feed the entire file as project context and implement phase by phase.*
