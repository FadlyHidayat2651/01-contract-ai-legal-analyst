# Port Management Guide

## Kill Process on Specific Port

### Method 1: Using lsof and kill (Recommended)

```bash
# Find process ID on port 8000
lsof -ti:8000

# Kill the process
kill -9 $(lsof -ti:8000)
```

### Method 2: Using lsof with details

```bash
# See detailed info about what's using port 8000
lsof -i:8000

# Then kill by PID
kill -9 <PID>
```

### Method 3: For frontend port 3000

```bash
# Kill process on port 3000
kill -9 $(lsof -ti:3000)
```

## Common Ports in This Project

- **Port 3000**: Frontend (Vite dev server)
- **Port 8000**: Backend (FastAPI/Uvicorn)
- **Port 5432**: PostgreSQL database

## Kill All Project Processes

```bash
# Kill frontend
kill -9 $(lsof -ti:3000)

# Kill backend
kill -9 $(lsof -ti:8000)
```

## Check What's Running on Ports

```bash
# Check port 8000
lsof -i:8000

# Check port 3000
lsof -i:3000

# Check all ports
lsof -i -P | grep LISTEN
```

## Restart Services

### Restart Frontend
```bash
cd frontend
npm run dev
```

### Restart Backend
```bash
cd backend
conda activate contract_ai
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

**Made with Bob** 🤖