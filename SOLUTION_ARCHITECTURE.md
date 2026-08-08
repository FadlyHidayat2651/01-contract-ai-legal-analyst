# Contract AI Legal Analyst — Solution Architecture

> **Platform**: Multi-agent AI platform for automated legal contract review, risk scoring, and knowledge graph extraction
> **Stack**: FastAPI · React/TypeScript · PostgreSQL · Neo4j · AstraDB · IBM watsonx.ai · Docling OCR · LangGraph
> **Deployment**: IBM Cloud Code Engine (frontend) + Red Hat OpenShift ROKS (backend) + IBM Managed Services

---

## 1. Full System Architecture

```mermaid
flowchart TB
    %% ─────────────────────────────────────────
    %% USER CHANNELS
    %% ─────────────────────────────────────────
    subgraph UC["👥 User Channels"]
        LA["Legal Analyst\n(Contract Review)"]
        CO["Compliance Officer\n(Risk Oversight)"]
    end

    %% ─────────────────────────────────────────
    %% SECURITY PERIMETER
    %% ─────────────────────────────────────────
    subgraph SP["🔒 Security Perimeter"]
        CIS["IBM CIS WAF\nOWASP Top 10 · DDoS · CDN"]
        APPID["IBM App ID\nOIDC · OAuth2 · MFA · JWT RS256"]
        TLS["TLS 1.3\nEnd-to-End · mTLS Pod-to-Pod"]
    end

    %% ─────────────────────────────────────────
    %% FRONTEND TIER — IBM Cloud Code Engine
    %% ─────────────────────────────────────────
    subgraph CE["☁️ IBM Cloud Code Engine — Frontend Tier"]
        FE["React SPA\n• Contract Upload\n• Clause Viewer\n• Risk Report Dashboard\n• AI Chat Interface\nauto-scale 0 → N replicas"]
    end

    %% ─────────────────────────────────────────
    %% BACKEND TIER — Red Hat OpenShift ROKS
    %% ─────────────────────────────────────────
    subgraph OCP["🔴 Red Hat OpenShift ROKS — Backend Tier"]
        API["FastAPI\n3 replicas · HPA CPU>70%\nPython 3.11 · Uvicorn"]
        LGW["LangGraph Workers\n2–6 replicas · auto-scale\nAgent Orchestration"]
        NEO["Neo4j 5.15 + APOC\nStatefulSet · PVC 50Gi\nibmc-block-gold"]
        PG["PostgreSQL 16\nStatefulSet · PVC 20Gi\n1+1 HA · ibmc-block-gold"]
    end

    %% ─────────────────────────────────────────
    %% AI GUARDRAILS
    %% ─────────────────────────────────────────
    subgraph GR["🛡️ AI Guardrails — IBM watsonx.governance"]
        IGR["Input Guardrails\n• PII Detection KTP/NPWP/NIK NER\n• Prompt Injection — Granite Guard\n• Input Length/Format Validation\n• Harmful Content Filter"]
        OGR["Output Guardrails\n• Hallucination Groundedness Check\n• Bias Fairness — Demographic Parity\n• Output PII Scrub\n• Regulatory Citation Check"]
    end

    %% ─────────────────────────────────────────
    %% LLM LAYER
    %% ─────────────────────────────────────────
    subgraph LLM["🤖 LLM Layer"]
        WX["IBM watsonx.ai PRIMARY\n• Llama 4 (reasoning)\n• Granite-3-8b (agents)\n• Slate-125m (embeddings)"]
        OLL["Ollama LOCAL\ngemma3:4b\n(dev/fallback)"]
    end

    %% ─────────────────────────────────────────
    %% IBM CLOUD MANAGED SERVICES
    %% ─────────────────────────────────────────
    subgraph MS["☁️ IBM Cloud Managed Services"]
        ADB["AstraDB Vector Store\n3 collections:\n• legal_chunks\n• legal_graph\n• legal_chat"]
        PGMS["PostgreSQL\n(IBM Cloud Databases)"]
        COS["IBM Cloud Object Storage\nContract PDFs · Reports"]
        KP["IBM Key Protect\nBYOK · AES-256"]
    end

    %% ─────────────────────────────────────────
    %% 5 SPECIALIST AI AGENTS
    %% ─────────────────────────────────────────
    subgraph AG["⚖️ 5 Specialist AI Agents (Parallel)"]
        A1["Legal Counsel\n• Liability Clauses\n• IP Rights\n• Exit Conditions"]
        A2["Compliance Officer\n• Regulatory OJK/BI\n• Indonesian Law\n• UU PDP"]
        A3["Risk Manager\n• Concentration Risk\n• Counterparty Risk\n• Covenant Analysis"]
        A4["Credit Analyst\n• DSCR / DTI / LTV\n• Financial Covenants\n• Credit Triggers"]
        A5["AML Officer\n• UBO Identification\n• SLIK Check\n• PPATK Compliance"]
    end

    %% ─────────────────────────────────────────
    %% CONNECTIONS
    %% ─────────────────────────────────────────
    LA & CO --> CIS --> APPID --> TLS --> FE
    FE -->|REST/SSE| API
    API --> IGR --> WX
    API --> LGW
    LGW --> AG
    AG --> OGR --> WX
    WX <-->|fallback| OLL
    LGW --> NEO
    LGW --> ADB
    API --> PG
    WX -.->|governed by| GR
    COS -.->|contract storage| API
    KP -.->|encrypt at rest| NEO & PG & COS
```

---

## 2. Deployment Topology

```mermaid
flowchart LR
    %% ─────────────────────────────────────────
    %% IBM CLOUD CODE ENGINE
    %% ─────────────────────────────────────────
    subgraph CCE["☁️ IBM Cloud Code Engine"]
        FEA["bob-contract-frontend app\nicr.io/bob/contract-frontend:latest\nCPU: 0.5 · RAM: 1Gi\nReplicas: 0–10 (auto-scale)\nCustom Domain: contract.ibm-bob.com\nHTTPS via IBM CIS"]
    end

    %% ─────────────────────────────────────────
    %% RED HAT OPENSHIFT ROKS
    %% ─────────────────────────────────────────
    subgraph ROKS["🔴 Red Hat OpenShift ROKS — Namespace: bob-contract"]
        direction TB
        subgraph COMPUTE["Compute Workloads"]
            APID["FastAPI Deployment\n3 replicas · HPA CPU>70%\nRequests: 500m/1Gi\nLimits: 2CPU/4Gi\nicr.io/bob/contract-backend:latest"]
            LGD["LangGraph Workers Deployment\n2–6 replicas · HPA CPU>60%\nRequests: 1CPU/2Gi\nLimits: 4CPU/8Gi"]
        end
        subgraph STATEFUL["Stateful Services"]
            NEO4["Neo4j 5.15 StatefulSet\nPVC: 50Gi ibmc-block-gold\nAPOC + GDS plugins\nBolt: 7687 · HTTP: 7474"]
            PGS["PostgreSQL 16 StatefulSet\n1+1 HA Streaming Replication\nPVC: 20Gi ibmc-block-gold\nPort: 5432"]
        end
        subgraph OBS["Observability Stack"]
            PROM["Prometheus\nMetrics Scraping"]
            GRAF["Grafana\nDashboards"]
            LOKI["Loki\nLog Aggregation"]
            JAE["Jaeger\nDistributed Tracing"]
        end
        subgraph SEC["Security Stack"]
            VAULT["HashiCorp Vault\nDynamic Credentials\nSecret Injection"]
            CM["cert-manager\nTLS Certificate Lifecycle"]
            OPA["OPA Gatekeeper\nPolicy Enforcement"]
            NP["NetworkPolicy\nDefault-Deny + Allow Rules"]
        end
    end

    %% ─────────────────────────────────────────
    %% IBM CLOUD MANAGED
    %% ─────────────────────────────────────────
    subgraph IBM["☁️ IBM Cloud Managed Services"]
        WXA["watsonx.ai\nLlama4 · Granite · Slate"]
        ASTDB["AstraDB\nlegal_chunks · legal_graph · legal_chat"]
        IAPPID["IBM App ID\nOIDC · MFA · JWT"]
        ICOS["IBM Cloud Object Storage"]
        ICIS["IBM CIS WAF"]
    end

    %% ─────────────────────────────────────────
    %% CI/CD PIPELINE
    %% ─────────────────────────────────────────
    subgraph CICD["🔧 CI/CD Pipeline"]
        GH["GitHub\nmain branch"]
        TEK["Tekton Pipelines\nBuild · Test · Scan"]
        ICR["IBM Container Registry\nicr.io/bob/"]
        ACD["ArgoCD\nGitOps Sync"]
    end

    GH -->|push/PR| TEK
    TEK -->|push image| ICR
    ICR -->|pull| ACD
    ACD -->|deploy manifests| ROKS
    ACD -->|deploy app| CCE

    FEA -->|API calls| APID
    APID --> LGD
    APID --> NEO4 & PGS
    LGD --> WXA & ASTDB
    FEA --> IAPPID
    ICIS -->|proxy| FEA
    VAULT -.->|inject secrets| APID & LGD
    NP -.->|enforce| COMPUTE & STATEFUL
```

---

## 3. Security Architecture

```mermaid
flowchart TB
    %% ─────────────────────────────────────────
    %% IDENTITY & ACCESS
    %% ─────────────────────────────────────────
    subgraph IAM["🪪 Identity & Access Management"]
        CIAM["IBM Cloud IAM\nService IDs · API Keys\nResource-level RBAC"]
        APPID2["IBM App ID OIDC\nMFA (TOTP/SMS)\nJWT RS256 · Token Refresh"]
        OCPRBAC["OpenShift RBAC\nServiceAccount per workload\nLeast-privilege ClusterRoles"]
        HVAULT["HashiCorp Vault\nDynamic DB credentials\nAuto-rotation 24h TTL\nKubernetes Auth backend"]
    end

    %% ─────────────────────────────────────────
    %% NETWORK SECURITY
    %% ─────────────────────────────────────────
    subgraph NET["🌐 Network Security"]
        WAF["IBM CIS WAF\nOWASP Top 10 Rules\nRate Limiting · Bot Management\nDDoS L3/L4/L7 Protection"]
        NPS["NetworkPolicy\nDefault-deny all ingress/egress\nExplicit allow rules per pod\nNamespace isolation"]
        PSE["Private Service Endpoints\nNo public internet exposure\nfor backend services"]
        VPC["VPC Security Groups\nStateful firewall rules\nPort allowlisting"]
    end

    %% ─────────────────────────────────────────
    %% ENCRYPTION
    %% ─────────────────────────────────────────
    subgraph ENC["🔐 Encryption"]
        KPS["IBM Key Protect BYOK\nAES-256-GCM\nCustomer-managed root keys\nKey rotation 90-day policy"]
        TLSE["TLS 1.3 Everywhere\nCertificate pinning\nmTLS pod-to-pod (Istio/cert-manager)\nPFS — Perfect Forward Secrecy"]
        ETCD["etcd Encryption at Rest\nOpenShift managed\nAES-CBC + HMAC-SHA256"]
    end

    %% ─────────────────────────────────────────
    %% COMPLIANCE & AUDIT
    %% ─────────────────────────────────────────
    subgraph COMP["📋 Compliance & Audit"]
        AT["IBM Cloud Activity Tracker\nAll API calls logged\nImmutable audit trail\nCOS archival"]
        PDP["Indonesian UU PDP\nData residency: Jakarta region\nPII data classification\nRight-to-erasure workflow"]
        VA["Container Registry VA\nDaily CVE scan\nCVSS score gating\nImage signing (Notary v2)"]
        SIEM["IBM QRadar SIEM\nReal-time threat detection\nCorrelation rules\nSOC integration"]
    end

    IAM -->|authenticates| NET
    NET -->|encrypted by| ENC
    ENC -->|audited by| COMP
    HVAULT -->|injects| TLSE
    WAF -->|feeds events| SIEM
    AT -->|feeds events| SIEM
```

---

## 4. AI Guardrails & Governance

```mermaid
flowchart LR
    %% ─────────────────────────────────────────
    %% INPUT GUARDRAILS
    %% ─────────────────────────────────────────
    subgraph IN["🛡️ Input Guardrails"]
        PII["PII Detection\n• KTP number NER\n• NPWP tax ID NER\n• NIK national ID NER\n• Phone/email masking"]
        PI["Prompt Injection Guard\n• Granite Guard model\n• Jailbreak pattern detection\n• Instruction override detection\n• Adversarial suffix filter"]
        IVL["Input Validation\n• Max token length: 32k\n• Format: PDF/DOCX/TXT only\n• Encoding validation UTF-8\n• Malware scan ClamAV"]
        HC["Harmful Content Filter\n• Violence / hate speech\n• CSAM detection\n• Extremist content\n• Threshold: 0.85"]
    end

    %% ─────────────────────────────────────────
    %% LLM CORE
    %% ─────────────────────────────────────────
    subgraph LLM2["🤖 LLM Core — IBM watsonx.ai"]
        LL4["Llama 4\nComplex legal reasoning\nLong-context synthesis"]
        GR3["Granite-3-8b\nAgent task execution\nTool use / function calling"]
        SL["Slate-125m\nDense vector embeddings\n768-dim cosine similarity"]
    end

    %% ─────────────────────────────────────────
    %% OUTPUT GUARDRAILS
    %% ─────────────────────────────────────────
    subgraph OUT["🔍 Output Guardrails"]
        HAL["Hallucination Check\n• Groundedness score ≥ 0.80\n• Source citation required\n• NLI entailment verification\n• ROUGE-L coherence check"]
        BIAS["Bias & Fairness Monitor\n• Demographic parity check\n• Disparate impact ratio\n• Protected attributes audit\n• Threshold: ±5% deviation"]
        PIOS["Output PII Scrub\n• Replace before response\n• Pseudonymisation\n• Audit log of redactions"]
        REG["Regulatory Citation\n• OJK regulation lookup\n• BI circular check\n• UU citation validation\n• Broken citation alert"]
    end

    %% ─────────────────────────────────────────
    %% GOVERNANCE LIFECYCLE
    %% ─────────────────────────────────────────
    subgraph GOV["📊 watsonx.governance Lifecycle"]
        MR["Model Registry\n• Versioned approvals\n• Model cards\n• Lineage tracking"]
        DD["Drift Detection\n• Weekly PSI monitoring\n• Daily accuracy check\n• Auto-retrain trigger\n• Champion/challenger"]
        QD["Quality Dashboard\n• Precision/recall per agent\n• F1 per clause type\n• Latency p50/p95/p99\n• Cost per inference"]
        AL["Audit Ledger\n• Apache Iceberg tables\n• 7-year retention\n• Tamper-proof hash chain\n• eDiscovery export"]
        HRQ["Human Review Queue\n• Low-confidence flagging\n• Lawyer-in-the-loop\n• Override capture\n• Feedback loop training"]
    end

    PII & PI & IVL & HC -->|validated input| LLM2
    LLM2 -->|raw output| HAL & BIAS & PIOS & REG
    HAL & BIAS & PIOS & REG -->|governed output| GOV
    GOV -->|retrain signals| LLM2
```

---

## 5. Agent Mesh & Contract Analysis Pipeline

```mermaid
flowchart TB
    %% ─────────────────────────────────────────
    %% INPUT
    %% ─────────────────────────────────────────
    DOC["📄 Document Input\nPDF · DOCX · TXT\nMax 200 pages · 50MB"]

    %% ─────────────────────────────────────────
    %% STAGE 1: EXTRACTION
    %% ─────────────────────────────────────────
    subgraph S1["Stage 1 — Document Extraction"]
        MUP["PyMuPDF\nNative PDF text\nLayout preservation"]
        DCL["Docling OCR\nScanned documents\nTable extraction\nHandwriting support"]
    end

    %% ─────────────────────────────────────────
    %% STAGE 2: CHUNKING
    %% ─────────────────────────────────────────
    subgraph S2["Stage 2 — Clause Chunking (18 Clause Types)"]
        CH["Semantic Chunker\nMax 1024 tokens/chunk\nClause boundary detection\nTypes: Parties · Definitions · Term · Payment\nLiability · IP · Confidentiality · Termination\nForce Majeure · Dispute · Governing Law · SLA\nWarranty · Indemnity · Amendment · Assignment\nData Protection · Compliance"]
    end

    %% ─────────────────────────────────────────
    %% STAGE 3: KNOWLEDGE GRAPH
    %% ─────────────────────────────────────────
    subgraph S3["Stage 3 — Knowledge Graph (Neo4j)"]
        EN["14 Entity Types\nPARTY · OBLIGATION · AMOUNT · RATIO\nASSET · COVENANT · PENALTY · SLA_METRIC\nDATE · REGULATION · RISK_FLAG · CONDITION\nIP · JURISDICTION"]
        RL["12 Relationship Types\nOWES_TO · TRIGGERS · SECURES · REFERENCES\nGOVERNS · MODIFIES · EXCLUDES · REQUIRES\nASSIGNS · TERMINATES · INDEMNIFIES · AUDITS"]
    end

    %% ─────────────────────────────────────────
    %% STAGE 4: CLASSIFY
    %% ─────────────────────────────────────────
    subgraph S4["Stage 4 — Document Classification"]
        CL["Contract Type Classifier\nGranite-3-8b zero-shot\nTypes: Loan · Vendor · Employment\nLease · Partnership · NDA · M&A"]
    end

    %% ─────────────────────────────────────────
    %% STAGE 5: PARALLEL AGENTS
    %% ─────────────────────────────────────────
    subgraph S5["Stage 5 — 5 Specialist AI Agents (Parallel LangGraph)"]
        AG1["⚖️ Legal Counsel\n• Liability clause analysis\n• IP rights & ownership\n• Exit conditions & penalties\n• Jurisdiction enforceability"]
        AG2["📋 Compliance Officer\n• OJK regulatory alignment\n• Bank Indonesia circulars\n• UU PDP data protection\n• AML/CFT requirements"]
        AG3["⚠️ Risk Manager\n• Concentration risk score\n• Counterparty credit risk\n• Covenant sensitivity analysis\n• Cross-default triggers"]
        AG4["💳 Credit Analyst\n• DSCR calculation\n• DTI ratio assessment\n• LTV covenant check\n• Amortisation schedule risk"]
        AG5["🔍 AML Officer\n• UBO identification\n• SLIK credit history\n• PPATK transaction flags\n• Beneficial ownership graph"]
    end

    %% ─────────────────────────────────────────
    %% AGGREGATION
    %% ─────────────────────────────────────────
    AGG["📊 Findings Aggregation\nSeverity: CRITICAL → HIGH → MEDIUM → LOW\nDeduplication · Conflict resolution\nConsensus scoring across agents"]

    %% ─────────────────────────────────────────
    %% STAGE 6: REPORT
    %% ─────────────────────────────────────────
    subgraph S6["Stage 6 — Report Generation"]
        RPT["Executive Summary\nRisk Score 0–100\nVerdict: APPROVE / REVIEW / REJECT\nPDF + JSON export\nSSE stream to frontend"]
    end

    DOC --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    S5 --> AGG
    AGG --> S6
```

---

## 6. Data Flow Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 User
    participant CIS as IBM CIS WAF
    participant AppID as IBM App ID
    participant FE as Code Engine Frontend
    participant BE as OpenShift Backend (FastAPI)
    participant GRD as AI Guardrails
    participant WX as IBM watsonx.ai
    participant NEO as Neo4j
    participant ADB as AstraDB
    participant AGT as 5 Agents (Parallel)
    participant PG as PostgreSQL

    User->>CIS: HTTPS request + JWT token
    CIS->>CIS: WAF rule evaluation (OWASP Top 10)
    CIS->>AppID: Token introspection
    AppID-->>CIS: Token valid + user claims
    CIS->>FE: Forward authenticated request
    FE->>BE: POST /api/v1/contracts/analyze (multipart PDF)
    BE->>GRD: Input guardrail check (PII, injection, format)
    GRD-->>BE: Input cleared / PII masked
    BE->>WX: Entity extraction (Granite-3-8b NER)
    WX-->>BE: Extracted entities + clause classifications
    BE->>NEO: Store knowledge graph (entities + relationships)
    NEO-->>BE: Graph persisted (node IDs)
    BE->>WX: Generate embeddings (Slate-125m)
    WX-->>BE: Dense vectors 768-dim
    BE->>ADB: Upsert vectors → legal_chunks collection
    ADB-->>BE: Vectors stored (upsert count)
    BE->>AGT: Dispatch 5 agents in parallel (LangGraph)

    par Legal Counsel analysis
        AGT->>WX: Liability/IP/exit clause reasoning (Llama4)
        WX-->>AGT: Legal findings
        AGT->>GRD: Output guardrail (hallucination + PII scrub)
    and Compliance Officer analysis
        AGT->>WX: Regulatory alignment check (Granite-3-8b)
        WX-->>AGT: Compliance findings
        AGT->>GRD: Output guardrail
    and Risk Manager analysis
        AGT->>WX: Concentration + counterparty risk (Llama4)
        WX-->>AGT: Risk findings
        AGT->>GRD: Output guardrail
    and Credit Analyst analysis
        AGT->>WX: DSCR/DTI/LTV computation (Granite-3-8b)
        WX-->>AGT: Credit findings
        AGT->>GRD: Output guardrail
    and AML Officer analysis
        AGT->>WX: UBO/SLIK/PPATK check (Granite-3-8b)
        WX-->>AGT: AML findings
        AGT->>GRD: Output guardrail
    end

    AGT-->>BE: All 5 agent results aggregated
    BE->>WX: Report synthesis (Llama4 — executive summary)
    WX-->>BE: Final report draft
    GRD->>GRD: Final output hallucination + bias check
    BE->>ADB: Store report → legal_chat collection
    ADB-->>BE: Stored
    BE->>PG: Persist contract record + verdict + metadata
    PG-->>BE: Contract ID committed
    BE-->>FE: SSE stream (report chunks + risk score + verdict)
    FE-->>User: Render Risk Dashboard (APPROVE/REVIEW/REJECT)
```

---

## Tech Stack Reference

| Layer | Technology | Runtime | Notes |
|---|---|---|---|
| **Frontend** | React 18 + Vite + Tailwind CSS | IBM Cloud Code Engine | Auto-scale 0→10 replicas · CPU 0.5 · RAM 1Gi |
| **API Gateway** | FastAPI + Uvicorn | OpenShift 3 replicas | HPA CPU>70% · Limits 2CPU/4Gi · Python 3.11 |
| **Agent Orchestration** | LangGraph + LangChain | OpenShift workers 2–6 | Parallel agent execution · StateGraph |
| **Primary LLM** | IBM watsonx.ai — Llama 4 | IBM Cloud SaaS | Complex reasoning · 128k context |
| **Agent LLM** | IBM watsonx.ai — Granite-3-8b | IBM Cloud SaaS | Tool use · function calling · low latency |
| **Embeddings** | IBM watsonx.ai — Slate-125m | IBM Cloud SaaS | 768-dim dense vectors · cosine similarity |
| **Local LLM** | Ollama — gemma3:4b | Local / dev | Dev fallback · no internet required |
| **OCR / Extraction** | Docling OCR + PyMuPDF | OpenShift | Scanned PDF · tables · handwriting |
| **Knowledge Graph** | Neo4j 5.15 + APOC + GDS | OpenShift StatefulSet | 14 entity types · 12 rel types · PVC 50Gi |
| **Vector Store** | AstraDB (DataStax) | IBM Cloud SaaS | 3 collections: legal_chunks · legal_graph · legal_chat |
| **Relational DB** | PostgreSQL 16 | OpenShift StatefulSet | 1+1 HA · PVC 20Gi · ibmc-block-gold |
| **Auth / SSO** | IBM App ID OAuth2 / OIDC | IBM Cloud SaaS | MFA · JWT RS256 · token introspection |
| **Secrets** | HashiCorp Vault | OpenShift | Dynamic credentials · K8s auth · 24h TTL |
| **WAF / CDN** | IBM Cloud Internet Services (CIS) | IBM Cloud | OWASP Top 10 · DDoS · rate limiting |
| **AI Governance** | IBM watsonx.governance | IBM Cloud SaaS | Drift · bias · hallucination · audit ledger |
| **Observability** | Prometheus + Grafana + Loki + Jaeger | OpenShift | Metrics · logs · traces · dashboards |
| **CI/CD** | Tekton Pipelines + ArgoCD | OpenShift | GitOps · image scanning · auto-deploy |
| **Container Registry** | IBM Container Registry (ICR) | IBM Cloud | Vulnerability Advisor · image signing |
| **Key Management** | IBM Key Protect | IBM Cloud | BYOK · AES-256 · 90-day rotation |
| **Object Storage** | IBM Cloud Object Storage (COS) | IBM Cloud | Contract PDFs · report archives |
| **Policy Engine** | OPA Gatekeeper | OpenShift | Admission control · policy-as-code |
| **TLS Certs** | cert-manager | OpenShift | ACME · auto-renewal · mTLS |
| **Data Governance** | Apache Iceberg + Audit Ledger | OpenShift | 7-year immutable retention · eDiscovery |

---

## Architecture Decision Records (ADR)

| # | Decision | Rationale |
|---|---|---|
| ADR-001 | IBM watsonx.ai over OpenAI GPT-4 | Data residency, IBM Cloud SLA, BYOK encryption, no training on customer data |
| ADR-002 | Neo4j Knowledge Graph for contract entities | Relationship traversal for cross-clause risk detection outperforms relational joins |
| ADR-003 | LangGraph over LangChain LCEL for orchestration | Cyclic graph support, parallel branch execution, built-in state checkpointing |
| ADR-004 | Code Engine for frontend, OpenShift for backend | Stateless frontend benefits from scale-to-zero; stateful AI/DB workloads need persistent pods |
| ADR-005 | AstraDB for vector store | Serverless scaling, multi-collection isolation, native LangChain integration |
| ADR-006 | 5 specialist agents over monolithic LLM | Reduced hallucination per domain, parallel execution 5× speedup, domain-specific prompts |
| ADR-007 | HashiCorp Vault for secrets | Dynamic credential rotation eliminates static secrets; K8s auth backend avoids root tokens |
| ADR-008 | IBM watsonx.governance for AI lifecycle | Regulatory compliance (Indonesian OJK/BI AI governance guidelines), drift alerting, audit ledger |
