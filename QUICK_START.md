# Quick Start Guide - Contract AI Application

## 🚨 Current Status

**Frontend**: ✅ Running on port 3000  
**Backend**: ❌ Not running (causing connection errors)  
**Database**: ✅ PostgreSQL configured and ready

## 🔴 The Errors You're Seeing

The frontend errors are **NORMAL** and **EXPECTED** because the backend isn't running yet:

```
Error: connect ECONNREFUSED ::1:8000
```

This means: "Frontend is trying to connect to backend on port 8000, but nothing is listening there."

**Solution**: Start the backend server (instructions below)

---

## 🚀 Start Backend Server (3 Simple Steps)

### Step 1: Open New Terminal

Open a new terminal window (keep the frontend terminal running).

### Step 2: Navigate and Activate Environment

```bash
cd /Users/muhammadfadlyhidayat/Documents/ibm/IBM\ 2026/BOB\ in\ Action/Bob\ -\ Legal\ Analyst\ -\ MajorTelecom/backend
conda activate contract_ai
```

### Step 3: Start Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### ✅ Success Indicators

You should see:
```
Starting up application...
Database URL: postgresql://contract_user:contract_pass@localhost:5432/contract_db
Upload directory: ./uploads
Database tables created
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### ✅ Verify Backend is Running

Open browser: http://localhost:8000/docs

You should see the FastAPI interactive documentation.

---

## 🎯 After Backend Starts

### The Frontend Errors Will Disappear

Once the backend is running, refresh your browser at http://localhost:3000

The dashboard should load without errors and show:
- Processing Status: 0%
- Clause Analysis: 85%
- Risk Assessment: 0%
- Total Contracts: 0
- High Risk Clauses: 0
- Critical Issues: 0
- Processing Rate: 0%

---

## 🧪 Test the Application

### 1. Upload a Contract

1. Click "Upload" in the navigation
2. Select a PDF or DOCX file
3. Enter a title
4. Click "Upload Contract"
5. Wait for processing to complete

### 2. View Contracts

1. Click "Contracts" in the navigation
2. You should see your uploaded contract
3. Click on it to view details and extracted clauses

### 3. Check Dashboard

1. Click "Dashboard" in the navigation
2. Statistics should now show real data

---

## 🛠️ Kill Process on Port (If Needed)

### If Port 8000 is Already in Use

```bash
# Find and kill process on port 8000
kill -9 $(lsof -ti:8000)
```

### If Port 3000 is Already in Use

```bash
# Find and kill process on port 3000
kill -9 $(lsof -ti:3000)

# Then restart frontend
cd frontend
npm run dev
```

---

## 📋 API Endpoints Available

Once backend is running, these endpoints work:

### Contracts
- `POST /api/contracts/upload` - Upload contract
- `GET /api/contracts/` - List contracts
- `GET /api/contracts/{id}` - Get contract details
- `DELETE /api/contracts/{id}` - Delete contract
- `GET /api/contracts/{id}/clauses` - Get contract clauses

### Clauses
- `GET /api/clauses/` - List clauses (with filters)
- `GET /api/clauses/{id}` - Get clause details
- `PUT /api/clauses/{id}` - Update clause
- `DELETE /api/clauses/{id}` - Delete clause

### Statistics
- `GET /api/stats/contracts` - Contract statistics
- `GET /api/stats/risk-distribution` - Risk distribution
- `GET /api/stats/clause-types` - Clause type distribution
- `GET /api/stats/recent-activity` - Recent activity

### Health
- `GET /api/health` - Health check

---

## 🔍 Troubleshooting

### Backend Won't Start

**Error**: `ModuleNotFoundError`
```bash
# Make sure you're in backend directory and conda env is activated
cd backend
conda activate contract_ai
pip install -r requirements.txt
```

**Error**: `Database connection failed`
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Restart if needed
brew services restart postgresql@14
```

**Error**: `Port 8000 already in use`
```bash
# Kill the process
kill -9 $(lsof -ti:8000)
```

### Frontend Shows Errors

**Error**: `ECONNREFUSED ::1:8000`
- **Cause**: Backend not running
- **Solution**: Start backend (see steps above)

**Error**: `404 Not Found`
- **Cause**: API endpoint doesn't exist
- **Solution**: Check backend logs for errors

### Database Issues

**Error**: `relation "contracts" does not exist`
```bash
# Tables are auto-created on backend startup
# Just restart the backend server
```

---

## 📊 Application Architecture

```
┌─────────────────┐
│   Frontend      │  Port 3000 (Vite + React)
│   (Browser)     │
└────────┬────────┘
         │ HTTP Requests to /api
         │ (Proxied by Vite)
         ↓
┌─────────────────┐
│   Backend       │  Port 8000 (FastAPI)
│   (Python)      │
└────────┬────────┘
         │ SQL Queries
         ↓
┌─────────────────┐
│   PostgreSQL    │  Port 5432
│   (Database)    │
└─────────────────┘
```

---

## ✅ Verification Checklist

Before testing:
- [ ] PostgreSQL is running (`brew services list`)
- [ ] Frontend is running on port 3000 (already running)
- [ ] Backend is running on port 8000 (start it now)
- [ ] No port conflicts
- [ ] Conda environment activated
- [ ] Can access http://localhost:8000/docs

---

## 🎉 You're Ready!

Once the backend is running:
1. Frontend errors will disappear
2. Dashboard will load properly
3. You can upload and analyze contracts
4. All features will work

**Next Step**: Start the backend server using the 3 steps above! 🚀

---

**Made with Bob** 🤖