from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.api import health, contracts, clauses, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print("Starting up application...")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Upload directory: {settings.UPLOAD_DIR}")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    
    yield
    
    # Shutdown
    print("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="Contract Analysis API",
    description="API for contract document analysis using IBM Docling",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["Contracts"])
app.include_router(clauses.router, prefix="/api/clauses", tags=["Clauses"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Contract Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
    }

# Made with Bob
