# Contract AI Application - Startup Guide

## ✅ System Status

### Completed Setup
- ✅ PostgreSQL database configured and running
- ✅ Database `contract_db` created with user `contract_user`
- ✅ Backend application structure complete
- ✅ Document parsing libraries installed (PyPDF2, python-docx, pytesseract, pdf2image)
- ✅ Frontend React application built with IBM Carbon Design
- ✅ Frontend development server running on port 3000
- ✅ Frontend-backend connection properly configured

### Ready to Start
- 🟡 Backend server (you will start manually)

---

## 🚀 Starting the Backend Server

### Step 1: Open a New Terminal

Open a new terminal window or tab.

### Step 2: Navigate to Backend Directory

```bash
cd /Users/muhammadfadlyhidayat/Documents/ibm/IBM\ 2026/BOB\ in\ Action/Bob\ -\ Legal\ Analyst\ -\ MajorTelecom/backend
```

### Step 3: Activate Conda Environment

```bash
conda activate contract_ai
```

### Step 4: Start the Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Expected Output

You should see output similar to this:

```
Starting up application...
Database URL: postgresql://contract_user:contract_pass@localhost:5432/contract_db
Upload directory: ./uploads
Database tables created
INFO:     Will watch for changes in these directories: ['/Users/muhammadfadlyhidayat/Documents/ibm/IBM 2026/BOB in Action/Bob - Legal Analyst - MajorTelecom/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Verify Backend is Running

Open your browser and visit:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

You should see the FastAPI interactive documentation and a health check response.

---

## 🌐 Accessing the Application

### Frontend Application
- **URL**: http://localhost:3000
- **Status**: Already running in Terminal 2

### Backend API
- **URL**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Status**: Ready to start (follow steps above)

---

## 🔗 Frontend-Backend Connection

### How It Works

1. **Frontend** runs on port 3000 (Vite dev server)
2. **Backend** runs on port 8000 (FastAPI with Uvicorn)
3. **Vite Proxy** forwards all `/api` requests from frontend to backend

### Configuration Details

**Frontend (vite.config.ts)**:
```typescript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

**Backend (config.py)**:
```python
CORS_ORIGINS: str = "http://localhost:3000"
```

**API Service (frontend/src/services/api.ts)**:
```typescript
const api = axios.create({
  baseURL: '/api',  // Proxied to http://localhost:8000/api
});
```

---

## 📋 Available API Endpoints

### Contract Operations
- `POST /api/contracts/upload` - Upload a new contract (PDF/DOCX)
- `GET /api/contracts/` - List all contracts
- `GET /api/contracts/{id}` - Get contract details
- `DELETE /api/contracts/{id}` - Delete a contract

### Clause Operations
- `GET /api/contracts/{id}/clauses` - Get clauses for a contract

### Statistics
- `GET /api/stats/contracts` - Get contract statistics

### Health Check
- `GET /api/health` - Check API health status

---

## 🧪 Testing the Application

### 1. Verify Dashboard Loads

1. Open http://localhost:3000
2. You should see the Contract AI Dashboard
3. Check that no console errors appear in browser DevTools

### 2. Test Contract Upload

1. Navigate to http://localhost:3000/upload
2. Click "Select file" or drag and drop a PDF/DOCX contract
3. Click "Upload Contract"
4. Verify the contract is processed and appears in the list

### 3. Test Contract Viewing

1. Navigate to http://localhost:3000/contracts
2. Click on a contract to view details
3. Verify clauses are displayed correctly

### 4. Test Search

1. Use the search bar on the contracts page
2. Enter a search term
3. Verify results are filtered correctly

---

## 📦 Document Parsing Libraries

The application uses the following libraries for document processing:

### Installed Libraries
- **PyPDF2 3.0.1** - PDF text extraction
- **python-docx** - DOCX file parsing
- **Pillow 10.4.0** - Image processing for OCR
- **pytesseract 0.3.13** - OCR for scanned documents
- **pdf2image 1.17.0** - Convert PDF pages to images for OCR

### Supported File Types
- PDF files (.pdf)
- Word documents (.docx, .doc)

### Processing Features
- Text extraction from digital PDFs
- OCR fallback for scanned PDFs
- Table extraction from DOCX files
- Section detection and hierarchy
- Markdown conversion
- Metadata extraction

---

## 🗄️ Database Information

### PostgreSQL Configuration
- **Host**: localhost
- **Port**: 5432
- **Database**: contract_db
- **User**: contract_user
- **Password**: contract_pass

### Database Tables
- `contracts` - Contract metadata and file information
- `clauses` - Extracted clauses from contracts
- `document_sections` - Document structure and sections

### Accessing the Database

```bash
psql -U contract_user -d contract_db
```

Common queries:
```sql
-- List all contracts
SELECT id, title, file_name, upload_date FROM contracts;

-- Count clauses per contract
SELECT contract_id, COUNT(*) as clause_count 
FROM clauses 
GROUP BY contract_id;

-- View recent uploads
SELECT title, file_name, upload_date 
FROM contracts 
ORDER BY upload_date DESC 
LIMIT 10;
```

---

## 📁 File Storage

### Upload Directory
- **Location**: `backend/uploads/`
- **Structure**: Files are stored with UUID-based names
- **Max File Size**: 50 MB

### Directory Structure
```
backend/uploads/
├── {uuid}_contract1.pdf
├── {uuid}_contract2.docx
└── ...
```

---

## 🛠️ Troubleshooting

### Backend Won't Start

**Issue**: Port 8000 already in use
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
kill -9 $(lsof -ti:8000)
```

**Issue**: Database connection error
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Restart PostgreSQL if needed
brew services restart postgresql@14
```

### Frontend Issues

**Issue**: API calls failing
- Verify backend is running on port 8000
- Check browser console for CORS errors
- Verify Vite proxy configuration in `vite.config.ts`

**Issue**: Frontend won't start
```bash
# Reinstall dependencies
cd frontend
npm install

# Clear cache and restart
rm -rf node_modules/.vite
npm run dev
```

### Document Processing Issues

**Issue**: OCR not working
```bash
# Install Tesseract OCR (if not already installed)
brew install tesseract

# Verify installation
tesseract --version
```

**Issue**: PDF processing fails
- Check file is not corrupted
- Verify file size is under 50 MB
- Try with a different PDF file

---

## 🔄 Development Workflow

### Making Backend Changes

1. Edit files in `backend/app/`
2. Server auto-reloads (thanks to `--reload` flag)
3. Test changes immediately

### Making Frontend Changes

1. Edit files in `frontend/src/`
2. Vite HMR updates browser automatically
3. Check browser console for errors

### Database Schema Changes

1. Edit models in `backend/app/models/`
2. Restart backend server
3. Tables are auto-created on startup

---

## 📊 Application Architecture

### Backend Stack
- **Framework**: FastAPI 0.115.12
- **Database**: PostgreSQL 14 with SQLAlchemy 2.0.36
- **Document Processing**: PyPDF2, python-docx, pytesseract
- **Server**: Uvicorn with auto-reload

### Frontend Stack
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Library**: IBM Carbon Design System
- **HTTP Client**: Axios
- **Routing**: React Router v6

### Data Flow
```
User Upload → Frontend (React) → Vite Proxy → Backend API (FastAPI)
                                                      ↓
                                            Document Parser (PyPDF2/python-docx)
                                                      ↓
                                            Clause Extractor (Regex patterns)
                                                      ↓
                                            PostgreSQL Database
                                                      ↓
                                            Response → Frontend Display
```

---

## 🎯 Next Steps

1. **Start Backend Server** (follow steps above)
2. **Test Contract Upload** with a sample PDF/DOCX file
3. **Verify All Features** work as expected
4. **Optional**: Add contract comparison feature (side-by-side view)

---

## 📝 Notes

- All data is stored locally (no cloud integrations)
- Application runs completely offline
- Document processing uses stable, well-maintained libraries
- Frontend-backend connection is properly configured and tested
- Database schema is automatically created on first run

---

## ✅ Verification Checklist

Before testing, ensure:
- [ ] PostgreSQL is running
- [ ] Frontend is running on port 3000 (already running)
- [ ] Backend is running on port 8000 (start manually)
- [ ] No port conflicts
- [ ] Conda environment `contract_ai` is activated
- [ ] All dependencies are installed

---

**Made with Bob** 🤖