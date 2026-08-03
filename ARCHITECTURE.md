# Contract Analysis App - Architecture Overview

## System Architecture

```mermaid
graph TB
    subgraph "Frontend - React App"
        UI[User Interface]
        Upload[Upload Component]
        List[Contract List]
        Detail[Contract Detail]
        Compare[Comparison View]
        Dashboard[Dashboard]
    end
    
    subgraph "Backend - FastAPI"
        API[REST API Layer]
        ContractSvc[Contract Service]
        DoclingProc[Docling Processor]
        ClauseExt[Clause Extractor]
        StorageSvc[Storage Service]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL)]
        FS[Local File System]
    end
    
    subgraph "External"
        Docling[IBM Docling Library]
    end
    
    UI --> API
    Upload --> API
    List --> API
    Detail --> API
    Compare --> API
    Dashboard --> API
    
    API --> ContractSvc
    API --> ClauseExt
    
    ContractSvc --> DoclingProc
    ContractSvc --> StorageSvc
    ContractSvc --> DB
    
    DoclingProc --> Docling
    DoclingProc --> DB
    
    ClauseExt --> DB
    
    StorageSvc --> FS
    StorageSvc --> DB
    
    style Docling fill:#e1f5ff
    style DB fill:#ffe1e1
    style FS fill:#ffe1e1
```

## Document Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant DoclingProc
    participant Docling
    participant DB
    participant FileSystem
    
    User->>Frontend: Upload Contract File
    Frontend->>API: POST /api/contracts
    API->>FileSystem: Save Original File
    API->>DB: Create Contract Record
    API->>DoclingProc: Process Document
    
    DoclingProc->>Docling: Convert Document
    Docling-->>DoclingProc: Structured Data
    
    DoclingProc->>DoclingProc: Extract Text
    DoclingProc->>DoclingProc: Extract Sections
    DoclingProc->>DoclingProc: Extract Tables
    DoclingProc->>DoclingProc: Extract Metadata
    
    DoclingProc->>DB: Store Full Text
    DoclingProc->>DB: Store Sections
    DoclingProc->>DB: Store Metadata
    
    DoclingProc->>API: Processing Complete
    API->>Frontend: Return Contract Data
    Frontend->>User: Show Contract Details
```

## Clause Extraction Flow

```mermaid
flowchart TD
    Start[Document Processed] --> GetSections[Get Document Sections]
    GetSections --> Loop{For Each Section}
    
    Loop --> Analyze[Analyze Title & Content]
    Analyze --> Match{Pattern Match?}
    
    Match -->|Yes| Classify[Classify Clause Type]
    Match -->|No| General[Mark as General]
    
    Classify --> Store[Store Clause in DB]
    General --> Store
    
    Store --> Loop
    Loop -->|Done| End[Clauses Extracted]
    
    style Start fill:#e1ffe1
    style End fill:#e1ffe1
    style Match fill:#ffe1e1
```

## Data Model

```mermaid
erDiagram
    CONTRACTS ||--o{ CLAUSES : contains
    CONTRACTS ||--o{ DOCUMENT_SECTIONS : has
    DOCUMENT_SECTIONS ||--o{ DOCUMENT_SECTIONS : parent-child
    
    CONTRACTS {
        uuid id PK
        string title
        string file_name
        string file_path
        bigint file_size
        string mime_type
        timestamp upload_date
        string contract_type
        text[] parties
        date effective_date
        date expiration_date
        string status
        string processing_status
        text full_text
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }
    
    CLAUSES {
        uuid id PK
        uuid contract_id FK
        string clause_type
        string title
        text content
        integer page_number
        integer position_start
        integer position_end
        float confidence_score
        jsonb metadata
        timestamp created_at
    }
    
    DOCUMENT_SECTIONS {
        uuid id PK
        uuid contract_id FK
        string section_type
        string title
        text content
        integer page_number
        integer order_index
        uuid parent_section_id FK
        jsonb metadata
        timestamp created_at
    }
```

## Component Interaction

```mermaid
graph LR
    subgraph "React Components"
        A[ContractUpload]
        B[ContractList]
        C[ContractDetail]
        D[ClauseViewer]
        E[ContractCompare]
        F[Dashboard]
    end
    
    subgraph "API Hooks"
        G[useContracts]
        H[useContract]
        I[useClauses]
        J[useSearch]
    end
    
    subgraph "API Service"
        K[api.ts]
    end
    
    A --> G
    B --> G
    C --> H
    C --> I
    D --> I
    E --> H
    F --> G
    
    G --> K
    H --> K
    I --> K
    J --> K
    
    K --> L[FastAPI Backend]
    
    style L fill:#e1f5ff
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Compose"
        subgraph "Frontend Container"
            React[React + Vite<br/>Port 3000]
        end
        
        subgraph "Backend Container"
            FastAPI[FastAPI + Uvicorn<br/>Port 8000]
            Docling[Docling Library]
        end
        
        subgraph "Database Container"
            Postgres[(PostgreSQL<br/>Port 5432)]
        end
        
        subgraph "Volumes"
            UploadsVol[uploads_data]
            DBVol[postgres_data]
        end
    end
    
    User[User Browser] --> React
    React --> FastAPI
    FastAPI --> Docling
    FastAPI --> Postgres
    FastAPI --> UploadsVol
    Postgres --> DBVol
    
    style User fill:#e1ffe1
    style React fill:#ffe1e1
    style FastAPI fill:#e1f5ff
    style Postgres fill:#ffe1ff
```

## API Endpoint Structure

```mermaid
graph TD
    API[FastAPI Application]
    
    API --> Contracts[/api/contracts]
    API --> Clauses[/api/clauses]
    API --> Search[/api/search]
    
    Contracts --> C1[POST / - Upload]
    Contracts --> C2[GET / - List All]
    Contracts --> C3[GET /:id - Get One]
    Contracts --> C4[DELETE /:id - Delete]
    Contracts --> C5[PATCH /:id - Update]
    Contracts --> C6[GET /:id/clauses]
    Contracts --> C7[POST /:id/process]
    Contracts --> C8[GET /:id/download]
    
    Clauses --> CL1[GET /types - Statistics]
    
    Search --> S1[GET / - Search Contracts]
    
    style API fill:#e1f5ff
    style Contracts fill:#ffe1e1
    style Clauses fill:#ffe1e1
    style Search fill:#ffe1e1
```

## Technology Stack Overview

```mermaid
mindmap
  root((Contract App))
    Frontend
      React 18
      TypeScript
      Vite
      TailwindCSS
      React Query
      React Router
    Backend
      Python 3.11+
      FastAPI
      SQLAlchemy
      Alembic
      Pydantic
    Document Processing
      IBM Docling
      Pattern Matching
      Text Extraction
    Data Storage
      PostgreSQL
      Local File System
      JSONB for Metadata
    Infrastructure
      Docker
      Docker Compose
      Uvicorn
      Nginx optional
```

## Key Design Decisions

### 1. Offline-First Architecture
- All data stored locally (PostgreSQL + file system)
- No external API dependencies
- Can run completely disconnected from internet

### 2. IBM Docling for Extraction
- Replaces LLM-based extraction
- Provides structured document parsing
- Extracts text, tables, sections, metadata
- More reliable and faster than LLM calls

### 3. Rule-Based Clause Classification
- Pattern matching on section titles and content
- Predefined clause type patterns
- Confidence scoring based on match quality
- Extensible pattern dictionary

### 4. Simple REST API
- Standard CRUD operations
- JSON request/response
- File upload via multipart/form-data
- Pagination for list endpoints

### 5. React + TypeScript Frontend
- Type-safe development
- Component-based architecture
- React Query for server state
- TailwindCSS for rapid styling

### 6. Docker Compose for Development
- Single command to start all services
- Consistent development environment
- Easy onboarding for new developers
- Production-ready containerization

## Security Considerations

Even for local development, basic security is implemented:

1. **File Upload Validation**
   - File type checking (PDF, DOCX, TXT only)
   - File size limits (50MB default)
   - Sanitized file names

2. **SQL Injection Prevention**
   - SQLAlchemy ORM (parameterized queries)
   - Input validation with Pydantic

3. **Path Traversal Prevention**
   - Restricted upload directory
   - UUID-based file naming

4. **CORS Configuration**
   - Restricted to localhost origins
   - Configurable for production

## Performance Considerations

1. **Database Indexing**
   - Indexes on frequently queried fields
   - Full-text search on contract content
   - JSONB indexing for metadata queries

2. **File Storage**
   - Original files stored separately
   - Extracted text in database for fast search
   - Lazy loading of large content

3. **Frontend Optimization**
   - Code splitting with React Router
   - React Query caching
   - Virtualized lists for large datasets

4. **Processing Pipeline**
   - Async document processing
   - Progress tracking
   - Error recovery

## Future Enhancements

When ready to expand beyond MVP:

1. **LLM Integration**
   - Advanced clause analysis
   - Risk assessment
   - Semantic search
   - Contract summarization

2. **Cloud Storage**
   - IBM COS integration
   - S3-compatible storage
   - Backup and archival

3. **Authentication & Authorization**
   - User management
   - Role-based access control
   - Multi-tenant support

4. **Advanced Features**
   - Contract templates
   - Workflow automation
   - Email notifications
   - Audit logging
   - Version control

5. **Analytics**
   - Contract insights
   - Trend analysis
   - Compliance reporting
   - Custom dashboards