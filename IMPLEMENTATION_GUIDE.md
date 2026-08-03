# Contract Analysis App - Implementation Guide

## Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Git installed
- 8GB RAM minimum
- 10GB free disk space

### Initial Setup (5 minutes)

```bash
# 1. Create project structure
mkdir contract-analysis-app
cd contract-analysis-app
mkdir -p backend/app frontend

# 2. Initialize backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary pydantic python-multipart docling

# 3. Initialize frontend
cd ../frontend
npm create vite@latest . -- --template react-ts
npm install
npm install react-router-dom @tanstack/react-query axios tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 4. Create docker-compose.yml in root
cd ..
# (Copy docker-compose.yml from SIMPLIFIED_DEV_PLAN.md)

# 5. Start services
docker-compose up -d
```

## Development Phases

### Phase 1: Foundation (Days 1-3)

#### Day 1: Project Setup
```bash
# Backend structure
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   └── database.py
├── requirements.txt
├── Dockerfile
└── .env

# Frontend structure
frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── package.json
├── vite.config.ts
└── Dockerfile
```

**Backend main.py (Starter)**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Contract Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Contract Analysis API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Frontend App.tsx (Starter)**
```typescript
import { useState } from 'react'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <h1 className="text-3xl font-bold text-gray-900">
            Contract Analysis
          </h1>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 px-4">
        <p>Welcome to Contract Analysis App</p>
      </main>
    </div>
  )
}

export default App
```

#### Day 2: Database Setup
```bash
# Create alembic migration
cd backend
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

**Database Models (app/models/contract.py)**
```python
from sqlalchemy import Column, String, BigInteger, DateTime, Date, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    upload_date = Column(DateTime, default=func.now())
    contract_type = Column(String(100))
    parties = Column(ARRAY(Text))
    effective_date = Column(Date)
    expiration_date = Column(Date)
    status = Column(String(50), default='uploaded')
    processing_status = Column(String(50), default='pending')
    full_text = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### Day 3: Basic API Routes
```python
# app/api/contracts.py
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.contract import Contract
from app.schemas.contract import ContractResponse

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

@router.post("/", response_model=ContractResponse)
async def upload_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Save file and create contract record
    pass

@router.get("/", response_model=list[ContractResponse])
async def list_contracts(db: Session = Depends(get_db)):
    contracts = db.query(Contract).all()
    return contracts

@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    return contract
```

### Phase 2: Document Processing (Days 4-6)

#### Day 4: Docling Integration
```python
# app/services/docling_processor.py
from docling.document_converter import DocumentConverter
from pathlib import Path

class DoclingProcessor:
    def __init__(self):
        self.converter = DocumentConverter()
    
    def process_document(self, file_path: str) -> dict:
        """Process document and extract structured data"""
        result = self.converter.convert(file_path)
        
        return {
            'text': result.document.export_to_text(),
            'markdown': result.document.export_to_markdown(),
            'sections': self._extract_sections(result),
            'tables': self._extract_tables(result),
            'metadata': {
                'title': result.document.title,
                'pages': result.document.page_count,
            }
        }
    
    def _extract_sections(self, result):
        sections = []
        for section in result.document.sections:
            sections.append({
                'title': section.title,
                'content': section.text,
                'level': section.level,
                'page': section.page_number
            })
        return sections
    
    def _extract_tables(self, result):
        tables = []
        for table in result.document.tables:
            tables.append({
                'data': table.export_to_dataframe().to_dict(),
                'page': table.page_number
            })
        return tables
```

#### Day 5: File Upload & Storage
```python
# app/services/storage_service.py
import os
import uuid
from pathlib import Path
from fastapi import UploadFile

class StorageService:
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def save_file(self, file: UploadFile) -> dict:
        """Save uploaded file and return file info"""
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        file_name = f"{file_id}{file_ext}"
        file_path = self.upload_dir / file_name
        
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            'file_name': file.filename,
            'file_path': str(file_path),
            'file_size': len(content),
            'mime_type': file.content_type
        }
    
    def delete_file(self, file_path: str):
        """Delete file from storage"""
        Path(file_path).unlink(missing_ok=True)
```

#### Day 6: Complete Upload Pipeline
```python
# app/services/contract_service.py
from app.services.docling_processor import DoclingProcessor
from app.services.storage_service import StorageService
from app.models.contract import Contract
from sqlalchemy.orm import Session

class ContractService:
    def __init__(self):
        self.docling = DoclingProcessor()
        self.storage = StorageService()
    
    async def create_contract(self, file: UploadFile, db: Session) -> Contract:
        # 1. Save file
        file_info = await self.storage.save_file(file)
        
        # 2. Create contract record
        contract = Contract(
            title=file.filename,
            file_name=file_info['file_name'],
            file_path=file_info['file_path'],
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            processing_status='processing'
        )
        db.add(contract)
        db.commit()
        
        # 3. Process document
        try:
            doc_data = self.docling.process_document(file_info['file_path'])
            
            # 4. Update contract with extracted data
            contract.full_text = doc_data['text']
            contract.metadata = doc_data['metadata']
            contract.processing_status = 'completed'
            db.commit()
        except Exception as e:
            contract.processing_status = 'failed'
            db.commit()
            raise
        
        return contract
```

### Phase 3: Clause Extraction (Days 7-9)

#### Day 7: Clause Patterns
```python
# app/services/clause_extractor.py
import re
from typing import List, Dict

class ClauseExtractor:
    CLAUSE_PATTERNS = {
        'payment': [
            r'payment\s+terms?',
            r'compensation',
            r'fees?\s+and\s+charges',
        ],
        'termination': [
            r'termination',
            r'cancellation',
        ],
        'liability': [
            r'liability',
            r'indemnification',
        ],
        'confidentiality': [
            r'confidential',
            r'non-disclosure',
        ],
        'warranty': [
            r'warrant(y|ies)',
            r'guarantee',
        ],
    }
    
    def extract_clauses(self, sections: List[Dict]) -> List[Dict]:
        clauses = []
        
        for section in sections:
            clause_type = self._classify_section(
                section.get('title', ''),
                section.get('content', '')
            )
            
            if clause_type:
                clauses.append({
                    'type': clause_type,
                    'title': section['title'],
                    'content': section['content'],
                    'page': section.get('page'),
                    'confidence': 0.8
                })
        
        return clauses
    
    def _classify_section(self, title: str, content: str) -> str:
        text = f"{title} {content}".lower()
        
        for clause_type, patterns in self.CLAUSE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return clause_type
        
        return 'general'
```

#### Day 8-9: Clause Storage & Retrieval
```python
# app/models/clause.py
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class Clause(Base):
    __tablename__ = "clauses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey('contracts.id', ondelete='CASCADE'))
    clause_type = Column(String(100))
    title = Column(String(500))
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    position_start = Column(Integer)
    position_end = Column(Integer)
    confidence_score = Column(Float)
    metadata = Column(JSONB)
    
    contract = relationship("Contract", back_populates="clauses")
```

### Phase 4: Frontend UI (Days 10-14)

#### Day 10: Upload Component
```typescript
// src/components/ContractUpload.tsx
import { useState } from 'react'
import axios from 'axios'

export function ContractUpload({ onUploadSuccess }: { onUploadSuccess: () => void }) {
  const [uploading, setUploading] = useState(false)
  
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      await axios.post('http://localhost:8000/api/contracts', formData)
      onUploadSuccess()
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setUploading(false)
    }
  }
  
  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
      <input
        type="file"
        accept=".pdf,.docx,.txt"
        onChange={handleFileUpload}
        disabled={uploading}
        className="block w-full"
      />
      {uploading && <p className="mt-2 text-sm text-gray-500">Uploading...</p>}
    </div>
  )
}
```

#### Day 11-12: Contract List & Detail Views
```typescript
// src/components/ContractList.tsx
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

export function ContractList() {
  const { data: contracts, isLoading } = useQuery({
    queryKey: ['contracts'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/api/contracts')
      return response.data
    }
  })
  
  if (isLoading) return <div>Loading...</div>
  
  return (
    <div className="space-y-4">
      {contracts?.map((contract: any) => (
        <div key={contract.id} className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold">{contract.title}</h3>
          <p className="text-sm text-gray-500">
            Uploaded: {new Date(contract.upload_date).toLocaleDateString()}
          </p>
        </div>
      ))}
    </div>
  )
}
```

#### Day 13: Search & Comparison
```typescript
// src/components/ContractSearch.tsx
import { useState } from 'react'
import axios from 'axios'

export function ContractSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  
  const handleSearch = async () => {
    const response = await axios.get(
      `http://localhost:8000/api/contracts/search?q=${query}`
    )
    setResults(response.data)
  }
  
  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search contracts..."
        className="border rounded px-4 py-2 w-full"
      />
      <button onClick={handleSearch} className="mt-2 bg-blue-500 text-white px-4 py-2 rounded">
        Search
      </button>
      {/* Display results */}
    </div>
  )
}
```

#### Day 14: Dashboard
```typescript
// src/components/Dashboard.tsx
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

export function Dashboard() {
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/api/stats')
      return response.data
    }
  })
  
  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-gray-500 text-sm">Total Contracts</h3>
        <p className="text-3xl font-bold">{stats?.total_contracts || 0}</p>
      </div>
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-gray-500 text-sm">Processing</h3>
        <p className="text-3xl font-bold">{stats?.processing || 0}</p>
      </div>
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-gray-500 text-sm">Completed</h3>
        <p className="text-3xl font-bold">{stats?.completed || 0}</p>
      </div>
    </div>
  )
}
```

### Phase 5: Docker & Polish (Days 15-16)

#### Day 15: Docker Configuration
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json .
RUN npm install

COPY . .

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

#### Day 16: Final Polish
- Add error boundaries
- Improve loading states
- Add toast notifications
- Write README.md
- Test end-to-end flow

## Testing Checklist

### Manual Testing
- [ ] Upload PDF contract
- [ ] Upload DOCX contract
- [ ] View contract list
- [ ] View contract details
- [ ] View extracted clauses
- [ ] Search contracts
- [ ] Compare two contracts
- [ ] View dashboard statistics
- [ ] Delete contract

### Error Scenarios
- [ ] Upload invalid file type
- [ ] Upload file too large
- [ ] Process corrupted document
- [ ] Handle network errors
- [ ] Handle database errors

## Common Issues & Solutions

### Issue: Docling installation fails
```bash
# Solution: Install system dependencies first
apt-get update
apt-get install -y poppler-utils tesseract-ocr
pip install docling
```

### Issue: PostgreSQL connection refused
```bash
# Solution: Check if PostgreSQL is running
docker-compose ps
docker-compose logs postgres
```

### Issue: CORS errors in frontend
```python
# Solution: Update CORS middleware in main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: File upload fails
```python
# Solution: Check upload directory permissions
import os
os.makedirs("./uploads", exist_ok=True)
os.chmod("./uploads", 0o755)
```

## Performance Tips

1. **Database Queries**
   - Use indexes on frequently queried fields
   - Limit result sets with pagination
   - Use select_related for foreign keys

2. **File Processing**
   - Process documents asynchronously
   - Add progress tracking
   - Implement retry logic

3. **Frontend**
   - Use React Query caching
   - Implement virtual scrolling for large lists
   - Lazy load components

## Next Steps After MVP

1. Add user authentication
2. Implement LLM integration for advanced analysis
3. Add cloud storage support
4. Build comprehensive test suite
5. Deploy to production environment
6. Add monitoring and logging
7. Implement backup strategy

## Resources

- [IBM Docling Documentation](https://docling-project.github.io/docling/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Query Documentation](https://tanstack.com/query/latest)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)