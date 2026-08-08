# Solution Architecture — Contract AI Legal Analyst
### Multi-agent contract review · Risk scoring · Knowledge graph extraction
**Stack:** FastAPI · React/TypeScript · Neo4j · AstraDB · IBM watsonx.ai · LangGraph · Docling OCR

---

## 1. Full System Architecture

```mermaid
graph TB
    subgraph USERS["👥 Users"]
        LA[Legal Analyst\nContract Review]
        CO[Compliance Officer\nRisk Oversight]
    end

    subgraph SEC["🔒 Security Perimeter"]
        CIS[IBM CIS WAF\nDDoS · CDN · TLS termination]
        APPID[IBM App ID\nOIDC · OAuth2 · MFA]
    end

    subgraph CE["☁️ IBM Cloud Code Engine — Frontend"]
        FE[React SPA\nContract Upload · Clause Viewer\nRisk Report · AI Chat\nauto-scale 0→N replicas]
    end

    subgraph OCP["🔴 Red Hat OpenShift ROKS — Backend"]
        API[FastAPI\n3 replicas · HPA]
        LGW[LangGraph Workers\n2–6 replicas · auto-scale]
        NEO[Neo4j 5.x\nStatefulSet · PVC 50Gi]
        PG[PostgreSQL 16\nStatefulSet · PVC 20Gi]
    end

    subgraph AI["🤖 IBM AI Services"]
        WXA[watsonx.ai\nGranite-3-8b · Llama 4 Scout]
        WXO[watsonx Orchestrate\n5 specialist agents]
        WXG[watsonx.governance\nGuardrails · Audit]
    end

    subgraph STORE["💾 Storage"]
        ASTRA[AstraDB\nVector embeddings]
        COS[IBM COS\nDocument storage]
        VAULT[HashiCorp Vault\nSecrets]
    end

    USERS --> SEC --> CE --> API
    API --> LGW --> WXO
    WXO --> WXA
    WXA --> WXG
    LGW --> NEO
    LGW --> ASTRA
    API --> PG
    API --> COS
    VAULT --> OCP
```

---

## 2. Agent Pipeline Flow

```mermaid
sequenceDiagram
    actor User as Legal Analyst
    participant FE as React SPA
    participant API as FastAPI
    participant LG as LangGraph
    participant WXO as watsonx Orchestrate
    participant WXA as watsonx.ai
    participant NEO as Neo4j
    participant ASTRA as AstraDB

    User->>FE: Upload contract PDF
    FE->>API: POST /api/documents
    API->>LG: trigger pipeline

    LG->>LG: ① PDF extract (Docling OCR)
    LG->>LG: ② Chunk into 18 clause types
    LG->>NEO: ③ Build knowledge graph
    LG->>ASTRA: ④ Store embeddings

    LG->>WXO: ⑤ Dispatch to 5 specialist agents
    WXO->>WXA: LLM reasoning per agent
    WXA-->>WXO: clause analysis + risk scores
    WXO-->>LG: consolidated findings

    LG->>WXA: ⑥ Synthesise final report
    WXA-->>API: risk report JSON
    API-->>FE: stream SSE results
    FE-->>User: Risk dashboard + recommendations
```

---

## 3. Data Pipeline

```mermaid
flowchart LR
    subgraph INPUT["📄 Input"]
        PDF[Contract PDF\nProcurement · Loan · B2B]
    end

    subgraph EXTRACT["🔍 Extraction"]
        OCR[Docling OCR\nPDF → structured text]
        CHUNK[LangChain Splitter\n18 clause types]
    end

    subgraph ENRICH["🧠 Enrichment"]
        EMBED[watsonx.ai Embeddings\nslate-125m-english-rtrvr]
        KG[Neo4j Knowledge Graph\nentities · relationships · clauses]
    end

    subgraph STORE["💾 Storage"]
        ASTRA[AstraDB\nvector search]
        PG[PostgreSQL\nmetadata · audit log]
    end

    subgraph OUTPUT["📊 Output"]
        REPORT[Risk Report\nclause analysis · scores · flags]
        CHAT[AI Chat\ngrounded Q&A on contract]
    end

    PDF --> OCR --> CHUNK --> EMBED --> ASTRA
    CHUNK --> KG --> PG
    ASTRA --> REPORT
    KG --> REPORT
    ASTRA --> CHAT
    REPORT --> OUTPUT
```

---

## 4. Deployment Topology

```mermaid
graph TB
    subgraph IBM_CLOUD["☁️ IBM Cloud"]
        subgraph CE["IBM Cloud Code Engine — Serverless"]
            FE_APP[React SPA\nicr.io/ns/contract-ai-fe:latest\n0→N replicas · auto-scale]
        end

        subgraph ROKS["Red Hat OpenShift ROKS"]
            subgraph NS["contract-ai namespace"]
                API_POD[FastAPI\nDeployment · 3 replicas\nHPA cpu>70% · PDB min1]
                LG_POD[LangGraph Workers\nDeployment · 2–6 replicas]
                NEO_POD[Neo4j\nStatefulSet · PVC 50Gi]
                PG_POD[PostgreSQL\nStatefulSet · PVC 20Gi]
            end
            NETPOL[NetworkPolicy\ndefault-deny · allowlist]
            CERTMGR[cert-manager\nTLS auto-renew]
        end

        subgraph MANAGED["IBM Managed Services"]
            ASTRA_SVC[AstraDB\nvector store]
            COS_SVC[IBM COS\ndocument storage]
            KP[IBM Key Protect\nBYOK AES-256]
            VAULT_SVC[HashiCorp Vault\ndynamic secrets]
        end
    end

    CE -- "private HTTPS" --> ROKS
    ROKS --> MANAGED
```

---

## 5. Security Architecture

```mermaid
graph TB
    subgraph PERIMETER["Perimeter"]
        WAF[IBM CIS WAF\nOWASP Top 10 · DDoS · CDN]
        APIGW[API Gateway\nRate limit · JWT validation]
    end

    subgraph IDENTITY["Identity"]
        APPID[IBM App ID\nOAuth2 · OIDC · MFA]
        IAM[IBM Cloud IAM\nRBAC · service accounts]
        VAULT[HashiCorp Vault\n90-day secret rotation]
    end

    subgraph DATA["Data Security"]
        KP[IBM Key Protect\nBYOK AES-256 at rest]
        TLS[TLS 1.3 mTLS\nall service-to-service]
        NETPOL[OpenShift NetworkPolicy\ndefault-deny egress/ingress]
    end

    subgraph AI_SEC["AI Security"]
        GUARD[Granite Guard\nprompt injection detection]
        PII[PII NER Redactor\npre + post LLM]
        SQL_G[SELECT-only guard\nforbidden keyword blocklist]
    end

    subgraph AUDIT["Audit"]
        LEDGER[Iceberg Audit Ledger\n7-year immutable retention]
        SIEM[IBM QRadar\nreal-time threat detection]
    end

    WAF --> APIGW --> IDENTITY --> DATA --> AI_SEC --> AUDIT
```

---

## 6. AI Guardrails & Governance

```mermaid
flowchart TD
    INPUT([User Query / Document]) --> PII_IN[PII NER Scan\ndetect PII in input]
    PII_IN --> INJECT[Granite Guard\nprompt injection check]
    INJECT -->|clean| LLM[watsonx.ai Granite-3-8b\nclause analysis + risk scoring]
    INJECT -->|blocked| REJECT1([Reject + log])

    LLM --> HALL[Hallucination Monitor\nwatsonx.governance\nanswer grounded in contract?]
    HALL -->|grounded| PII_OUT[PII Post-scan\nstrip residual PII in output]
    HALL -->|hallucinated| FALLBACK[Return raw extraction\nno LLM synthesis]

    PII_OUT --> BIAS[Bias & Fairness Monitor\nequitable across contract types?]
    BIAS --> LEDGER[Iceberg Audit Ledger\nquery · caller · result · ts]
    LEDGER --> OUTPUT([Risk Report to User])

    style REJECT1 fill:#c0392b,color:#fff
    style FALLBACK fill:#e67e22,color:#fff
    style OUTPUT fill:#27ae60,color:#fff
```

---

## 7. Data Model

```mermaid
erDiagram
    CONTRACT {
        varchar contract_id PK
        varchar title
        varchar type
        varchar status
        timestamp uploaded_at
        varchar uploaded_by
    }

    CLAUSE {
        varchar clause_id PK
        varchar contract_id FK
        varchar clause_type
        text content
        decimal risk_score
        varchar risk_level
    }

    RISK_FLAG {
        varchar flag_id PK
        varchar clause_id FK
        varchar flag_type
        varchar severity
        text description
        varchar recommendation
    }

    PARTY {
        varchar party_id PK
        varchar contract_id FK
        varchar name
        varchar role
        varchar jurisdiction
    }

    AUDIT_LOG {
        varchar log_id PK
        varchar contract_id FK
        varchar user_id
        varchar action
        timestamp created_at
        text result_summary
    }

    CONTRACT ||--o{ CLAUSE : "contains"
    CLAUSE ||--o{ RISK_FLAG : "triggers"
    CONTRACT ||--o{ PARTY : "involves"
    CONTRACT ||--o{ AUDIT_LOG : "logged in"
```
