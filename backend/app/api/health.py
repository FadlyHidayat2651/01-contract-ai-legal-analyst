from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    
    Returns API status and database connectivity
    """
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": "1.0.0",
    }

# Made with Bob
