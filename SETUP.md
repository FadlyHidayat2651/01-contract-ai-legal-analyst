# Contract AI Application - Setup Guide

This guide provides step-by-step instructions for setting up and running the Contract AI Application locally.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 15+** - [Download PostgreSQL](https://www.postgresql.org/download/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/) (for frontend)
- **Docker & Docker Compose** (Optional) - [Download Docker](https://www.docker.com/products/docker-desktop/)

## Setup Options

You can run the application in two ways:
1. **Docker Setup** (Recommended) - Easiest way to get started
2. **Local Setup** - For development and debugging

---

## Option 1: Docker Setup (Recommended)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd contract-ai-app
```

### 2. Start the Application

```bash
docker-compose up -d
```

This will:
- Start PostgreSQL database on port 5432
- Run database migrations automatically
- Start the FastAPI backend on port 8000

### 3. Verify the Application

- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 4. Stop the Application

```bash
docker-compose down
```

To remove volumes (database data):
```bash
docker-compose down -v
```

---

## Option 2: Local Setup

### Backend Setup

#### 1. Create PostgreSQL Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE contract_db;

# Exit
\q
```

#### 2. Set Up Python Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Create a `.env` file in the `backend` directory (or use the existing one):

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/contract_db
UPLOAD_DIR=./uploads
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

#### 5. Run Database Migrations

```bash
# Initialize Alembic (only needed once)
alembic upgrade head
```

#### 6. Create Uploads Directory

```bash
mkdir -p uploads
```

#### 7. Start the Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at:
- API: http://localhost:8000
- Interactive API Docs: http://localhost:8000/docs
- Alternative API Docs: http://localhost:8000/redoc

---

## Frontend Setup (Coming Soon)

The React frontend will be added in the next phase. Instructions will include:

1. Navigate to frontend directory
2. Install dependencies with `npm install`
3. Configure environment variables
4. Start development server with `npm run dev`

---

## Testing the Application

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. Upload a Contract

```bash
curl -X POST "http://localhost:8000/api/contracts/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/contract.pdf"
```

### 3. List Contracts

```bash
curl http://localhost:8000/api/contracts/
```

### 4. Get Contract Details

```bash
curl http://localhost:8000/api/contracts/{contract_id}
```

### 5. Get Contract Clauses

```bash
curl http://localhost:8000/api/contracts/{contract_id}/clauses
```

---

## API Documentation

Once the backend is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- View all available endpoints
- Test API calls directly from the browser
- See request/response schemas
- Understand parameter requirements

---

## Database Management

### View Database Tables

```bash
psql -U postgres -d contract_db

# List tables
\dt

# View contracts
SELECT * FROM contracts;

# View clauses
SELECT * FROM clauses;

# View sections
SELECT * FROM document_sections;

# Exit
\q
```

### Reset Database

```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE contract_db;"
psql -U postgres -c "CREATE DATABASE contract_db;"

# Run migrations again
cd backend
alembic upgrade head
```

---

## Troubleshooting

### Database Connection Issues

**Problem**: Cannot connect to PostgreSQL

**Solutions**:
1. Ensure PostgreSQL is running:
   ```bash
   # macOS
   brew services start postgresql
   
   # Linux
   sudo systemctl start postgresql
   
   # Windows
   # Start PostgreSQL service from Services app
   ```

2. Verify database credentials in `.env` file
3. Check if port 5432 is available

### Import Errors

**Problem**: Module not found errors

**Solutions**:
1. Ensure virtual environment is activated
2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Alembic Migration Issues

**Problem**: Migration fails or tables not created

**Solutions**:
1. Check database connection
2. Reset migrations:
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

### Docker Issues

**Problem**: Container fails to start

**Solutions**:
1. Check Docker logs:
   ```bash
   docker-compose logs backend
   docker-compose logs postgres
   ```

2. Rebuild containers:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Port Already in Use

**Problem**: Port 8000 or 5432 already in use

**Solutions**:
1. Find and kill the process:
   ```bash
   # macOS/Linux
   lsof -ti:8000 | xargs kill -9
   lsof -ti:5432 | xargs kill -9
   
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

2. Or change the port in docker-compose.yml or when starting uvicorn

---

## Development Workflow

### Making Code Changes

1. Backend code changes are automatically reloaded (with `--reload` flag)
2. Database schema changes require new migrations:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   alembic upgrade head
   ```

### Adding New Dependencies

1. Add to `requirements.txt`
2. Install:
   ```bash
   pip install -r requirements.txt
   ```
3. If using Docker, rebuild:
   ```bash
   docker-compose build backend
   ```

---

## Project Structure

```
contract-ai-app/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database setup
│   │   └── main.py           # FastAPI application
│   ├── uploads/              # Uploaded files
│   ├── .env                  # Environment variables
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Docker configuration
├── docker-compose.yml        # Docker Compose configuration
└── SETUP.md                  # This file
```

---

## Next Steps

1. **Test the API** using the Swagger UI at http://localhost:8000/docs
2. **Upload sample contracts** to test document processing
3. **Review extracted clauses** to verify clause extraction logic
4. **Build the frontend** (coming in next phase)

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API documentation at http://localhost:8000/docs
3. Check application logs for error messages

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [IBM Docling Documentation](https://docling-project.github.io/docling/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)