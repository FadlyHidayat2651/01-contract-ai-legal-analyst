# Contract Analysis App - Simplified Development Plan

## Overview
This is a streamlined development plan focusing on building a working contract analysis application using IBM Docling for document extraction, running completely offline with local storage and database.

## Key Simplifications
- ✅ **No LLM Integration** - Using IBM Docling for document parsing and extraction
- ✅ **Offline First** - Local PostgreSQL database and local file storage
- ✅ **No Cloud Dependencies** - No IBM COS, no external APIs
- ✅ **Development Focus** - Build working code, skip formal testing phase
- ✅ **Core Features Only** - Essential contract management functionality

## Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **IBM Docling** - Document parsing and text extraction
- **PostgreSQL** - Local database
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations

### Frontend
- **React 18** with TypeScript
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **React Query** - Data fetching
- **React Router** - Navigation

### Infrastructure
- **Docker & Docker Compose** - Local development environment
- **Local File System** - Document storage

## Architecture

```
┌─────────────────┐
│  React Frontend │
│   (Port 3000)   │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│  FastAPI Backend│
│   (Port 8000)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────────┐
│ IBM  │  │PostgreSQL │
│Docling│  │ Database  │
└───┬──┘  └───────────┘
    │
┌───▼──────────┐
│ Local Files  │
│  /uploads    │
└──────────────┘
```

## Database Schema

### Core Tables

```sql
-- Contracts table
CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    contract_type VARCHAR(100),
    parties TEXT[],
    effective_date DATE,
    expiration_date DATE,
    status VARCHAR(50) DEFAULT 'uploaded',
    processing_status VARCHAR(50) DEFAULT 'pending',
    full_text TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clauses table
CREATE TABLE clauses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID REFERENCES contracts(id) ON DELETE CASCADE,
    clause_type VARCHAR(100),
    title VARCHAR(500),
    content TEXT NOT NULL,
    page_number INTEGER,
    position_start INTEGER,
    position_end INTEGER,
    confidence_score FLOAT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document sections table
CREATE TABLE document_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID REFERENCES contracts(id) ON DELETE CASCADE,
    section_type VARCHAR(100),
    title VARCHAR(500),
    content TEXT,
    page_number INTEGER,
    order_index INTEGER,
    parent_section_id UUID REFERENCES document_sections(id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_contracts_type ON contracts(contract_type);
CREATE INDEX idx_contracts_upload_date ON contracts(upload_date);
CREATE INDEX idx_clauses_contract_id ON clauses(contract_id);
CREATE INDEX idx_clauses_type ON clauses(clause_type);
CREATE INDEX idx_sections_contract_id ON document_sections(contract_id);
```

## IBM Docling Integration

### Installation
```bash
pip install docling
```

### Document Processing Pipeline

```python
from docling.document_converter import DocumentConverter

class DoclingProcessor:
    def __init__(self):
        self.converter = DocumentConverter()
    
    def process_document(self, file_path: str):
        """
        Process document using Docling
        Returns structured document data
        """
        result = self.converter.convert(file_path)
        
        return {
            'text': result.document.export_to_text(),
            'markdown': result.document.export_to_markdown(),
            'tables': self._extract_tables(result),
            'sections': self._extract_sections(result),
            'metadata': self._extract_metadata(result)
        }
    
    def _extract_tables(self, result):
        """Extract tables from document"""
        tables = []
        for table in result.document.tables:
            tables.append({
                'data': table.export_to_dataframe(),
                'page': table.page_number,
                'caption': table.caption
            })
        return tables
    
    def _extract_sections(self, result):
        """Extract document sections"""
        sections = []
        for section in result.document.sections:
            sections.append({
                'title': section.title,
                'content': section.text,
                'level': section.level,
                'page': section.page_number
            })
        return sections
    
    def _extract_metadata(self, result):
        """Extract document metadata"""
        return {
            'title': result.document.title,
            'author': result.document.author,
            'pages': result.document.page_count,
            'creation_date': result.document.creation_date
        }
```

## API Endpoints

### Contract Management
```
POST   /api/contracts              - Upload new contract
GET    /api/contracts              - List all contracts
GET    /api/contracts/{id}         - Get contract details
DELETE /api/contracts/{id}         - Delete contract
PATCH  /api/contracts/{id}         - Update contract metadata
GET    /api/contracts/{id}/clauses - Get contract clauses
GET    /api/contracts/{id}/download - Download original file
```

### Search & Analysis
```
GET    /api/contracts/search       - Search contracts
POST   /api/contracts/compare      - Compare multiple contracts
GET    /api/clauses/types          - Get clause type statistics
```

### Processing
```
POST   /api/contracts/{id}/process - Trigger document processing
GET    /api/contracts/{id}/status  - Get processing status
```

## Development Workflow

### Phase 1: Foundation (Days 1-3)
1. Set up project structure
2. Configure Docker Compose with PostgreSQL
3. Initialize FastAPI backend with basic routes
4. Set up React frontend with Vite
5. Create database schema and migrations

### Phase 2: Document Processing (Days 4-6)
6. Integrate IBM Docling
7. Build file upload endpoint
8. Implement document processing pipeline
9. Store extracted text and metadata in database
10. Create document storage system (local filesystem)

### Phase 3: Clause Extraction (Days 7-9)
11. Build clause identification logic using Docling sections
12. Implement clause classification (basic pattern matching)
13. Store clauses in database with references
14. Create clause retrieval endpoints

### Phase 4: Frontend UI (Days 10-14)
15. Build contract upload interface
16. Create contract list view with filters
17. Develop contract detail page showing clauses
18. Implement search functionality
19. Build contract comparison view (side-by-side)
20. Create simple dashboard with statistics

### Phase 5: Polish & Docker (Days 15-16)
21. Refine UI/UX
22. Add error handling and validation
23. Complete Docker Compose setup
24. Write README with setup instructions

## Project Structure

```
contract-analysis-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Configuration
│   │   ├── database.py             # Database connection
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── contract.py
│   │   │   ├── clause.py
│   │   │   └── section.py
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── contract.py
│   │   │   └── clause.py
│   │   ├── api/                    # API routes
│   │   │   ├── __init__.py
│   │   │   ├── contracts.py
│   │   │   ├── clauses.py
│   │   │   └── search.py
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── docling_processor.py
│   │   │   ├── contract_service.py
│   │   │   ├── clause_extractor.py
│   │   │   └── storage_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── alembic/                    # Database migrations
│   ├── uploads/                    # Local file storage
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ContractUpload.tsx
│   │   │   ├── ContractList.tsx
│   │   │   ├── ContractDetail.tsx
│   │   │   ├── ClauseViewer.tsx
│   │   │   ├── ContractCompare.tsx
│   │   │   └── Dashboard.tsx
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── ContractsPage.tsx
│   │   │   ├── ContractDetailPage.tsx
│   │   │   └── ComparePage.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── hooks/
│   │   │   └── useContracts.ts
│   │   ├── types/
│   │   │   └── contract.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Docker Compose Configuration

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: contract_db
      POSTGRES_USER: contract_user
      POSTGRES_PASSWORD: contract_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U contract_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://contract_user:contract_pass@postgres:5432/contract_db
      UPLOAD_DIR: /app/uploads
    volumes:
      - ./backend:/app
      - uploads_data:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0

volumes:
  postgres_data:
  uploads_data:
```

## Environment Variables

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://contract_user:contract_pass@localhost:5432/contract_db

# File Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=52428800  # 50MB

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# CORS
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
```

## Clause Extraction Logic

Since we're not using LLMs, we'll use rule-based extraction with Docling's structured output:

```python
class ClauseExtractor:
    """Extract clauses using Docling sections and pattern matching"""
    
    CLAUSE_PATTERNS = {
        'payment': [
            r'payment\s+terms?',
            r'compensation',
            r'fees?\s+and\s+charges',
            r'invoice',
        ],
        'termination': [
            r'termination',
            r'cancellation',
            r'end\s+of\s+agreement',
        ],
        'liability': [
            r'liability',
            r'indemnification',
            r'limitation\s+of\s+liability',
        ],
        'confidentiality': [
            r'confidential',
            r'non-disclosure',
            r'proprietary\s+information',
        ],
        'intellectual_property': [
            r'intellectual\s+property',
            r'copyright',
            r'patent',
            r'trademark',
        ],
        'warranty': [
            r'warrant(y|ies)',
            r'guarantee',
            r'representation',
        ],
        'dispute_resolution': [
            r'dispute\s+resolution',
            r'arbitration',
            r'governing\s+law',
            r'jurisdiction',
        ],
    }
    
    def extract_clauses(self, sections: list) -> list:
        """Extract and classify clauses from document sections"""
        clauses = []
        
        for section in sections:
            clause_type = self._classify_section(section['title'], section['content'])
            
            if clause_type:
                clauses.append({
                    'type': clause_type,
                    'title': section['title'],
                    'content': section['content'],
                    'page': section.get('page'),
                    'confidence': 0.8  # Rule-based confidence
                })
        
        return clauses
    
    def _classify_section(self, title: str, content: str) -> str:
        """Classify section into clause type using pattern matching"""
        text = f"{title} {content}".lower()
        
        for clause_type, patterns in self.CLAUSE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return clause_type
        
        return 'general'
```

## Quick Start Commands

```bash
# Clone and setup
git clone <repo-url>
cd contract-analysis-app

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Key Features

### 1. Document Upload & Processing
- Drag-and-drop file upload
- Support for PDF, DOCX, TXT
- Automatic processing with Docling
- Progress indication

### 2. Contract Management
- List view with filters (type, date, status)
- Search across contract content
- View contract details with metadata
- Download original files

### 3. Clause Viewing
- Organized by clause type
- Highlight important clauses
- Navigate between clauses
- View clause context

### 4. Contract Comparison
- Side-by-side comparison
- Highlight differences
- Compare specific clauses
- Export comparison report

### 5. Dashboard
- Total contracts count
- Processing status overview
- Clause type distribution
- Recent uploads

## Success Criteria

✅ Users can upload contracts (PDF/DOCX)
✅ Docling successfully extracts text and structure
✅ Clauses are identified and categorized
✅ Users can view contract details and clauses
✅ Search works across all contracts
✅ Contract comparison shows side-by-side view
✅ Application runs completely offline
✅ Docker Compose setup works out of the box
✅ No breaking errors in core functionality

## Notes

- **No Testing Phase**: Focus on writing working code, manual testing as you go
- **Simple Error Handling**: Basic try-catch, log errors, show user-friendly messages
- **Minimal Validation**: Essential validation only (file types, sizes)
- **Basic UI**: Clean and functional, not pixel-perfect
- **Local Only**: No authentication, no multi-user support initially
- **Docling Focus**: Leverage Docling's structured output, avoid complex NLP

## Next Steps

Once this simplified version is working:
1. Add user authentication
2. Integrate LLM for advanced analysis
3. Add cloud storage (COS) support
4. Implement comprehensive testing
5. Add advanced search (semantic search)
6. Build workflow features (approvals, notifications)