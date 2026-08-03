# Contract AI Application - Quick Start Guide

Get the Contract AI Application running in 5 minutes!

## 🚀 Fastest Way: Docker

### Prerequisites
- Docker and Docker Compose installed

### Steps

1. **Clone and Navigate**
   ```bash
   git clone <repository-url>
   cd contract-ai-app
   ```

2. **Start Everything**
   ```bash
   docker-compose up -d
   ```

3. **Access the Application**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **Test It**
   ```bash
   curl http://localhost:8000/health
   ```

That's it! 🎉

---

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+

### Steps

1. **Setup Database**
   ```bash
   psql -U postgres -c "CREATE DATABASE contract_db;"
   ```

2. **Setup Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run Migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start Server**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the Application**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## 📝 Try It Out

### Upload a Contract

Using the API docs at http://localhost:8000/docs:
1. Navigate to `POST /api/contracts/upload`
2. Click "Try it out"
3. Upload a PDF or DOCX contract file
4. Click "Execute"

Or use curl:
```bash
curl -X POST "http://localhost:8000/api/contracts/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/contract.pdf"
```

### View Contracts

```bash
curl http://localhost:8000/api/contracts/
```

### View Extracted Clauses

```bash
curl http://localhost:8000/api/contracts/{contract_id}/clauses
```

---

## 🔍 What's Included

✅ **Document Processing** - Upload PDF/DOCX contracts  
✅ **IBM Docling Integration** - Advanced document parsing  
✅ **Clause Extraction** - Automatic identification of 10 clause types  
✅ **Risk Assessment** - Automatic risk level assignment  
✅ **REST API** - Full CRUD operations  
✅ **PostgreSQL Database** - Persistent storage  
✅ **Docker Support** - Easy deployment  

---

## 📚 Next Steps

- Read [SETUP.md](SETUP.md) for detailed setup instructions
- Check [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design
- Review [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for development details
- Explore the API at http://localhost:8000/docs

---

## ❓ Need Help?

**Database connection issues?**
- Ensure PostgreSQL is running
- Check credentials in `backend/.env`

**Import errors?**
- Activate virtual environment
- Run `pip install -r requirements.txt`

**Port already in use?**
- Change port in docker-compose.yml or uvicorn command

For more troubleshooting, see [SETUP.md](SETUP.md#troubleshooting)

---

## 🎯 Key Features

### Supported Clause Types
1. Payment Terms
2. Termination Clauses
3. Confidentiality
4. Liability Limitations
5. Indemnification
6. Warranties
7. Dispute Resolution
8. Force Majeure
9. Intellectual Property
10. Data Protection

### Risk Levels
- **Critical** - Requires immediate attention
- **High** - Significant risk
- **Medium** - Moderate risk
- **Low** - Minimal risk

---

## 🔄 Stop the Application

**Docker:**
```bash
docker-compose down
```

**Local:**
```bash
# Press Ctrl+C in the terminal running uvicorn
```

---

Happy contract analyzing! 🎉