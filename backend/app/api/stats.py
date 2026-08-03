from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.contract import Contract
from app.models.clause import Clause

router = APIRouter()


@router.get("/contracts")
async def get_contract_stats(db: Session = Depends(get_db)):
    """
    Get contract statistics
    
    Returns:
    - total_contracts: Total number of contracts
    - processed_contracts: Number of processed contracts
    - pending_contracts: Number of pending contracts
    - failed_contracts: Number of failed contracts
    """
    total = db.query(Contract).count()
    processed = db.query(Contract).filter(Contract.processed == True).count()
    pending = db.query(Contract).filter(Contract.processing_status == "pending").count()
    failed = db.query(Contract).filter(Contract.processing_status == "failed").count()
    
    return {
        "total_contracts": total,
        "processed_contracts": processed,
        "pending_contracts": pending,
        "failed_contracts": failed,
    }


@router.get("/risk-distribution")
async def get_risk_distribution(db: Session = Depends(get_db)):
    """
    Get risk level distribution across all clauses
    
    Returns distribution of clauses by risk level:
    - low: Number of low risk clauses
    - medium: Number of medium risk clauses
    - high: Number of high risk clauses
    - critical: Number of critical risk clauses
    """
    # Query risk level distribution
    risk_counts = db.query(
        Clause.risk_level,
        func.count(Clause.id).label('count')
    ).group_by(Clause.risk_level).all()
    
    # Initialize all risk levels with 0
    distribution = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
    }
    
    # Update with actual counts
    for risk_level, count in risk_counts:
        if risk_level and risk_level.lower() in distribution:
            distribution[risk_level.lower()] = count
    
    return distribution


@router.get("/clause-types")
async def get_clause_type_distribution(db: Session = Depends(get_db)):
    """
    Get distribution of clauses by type
    
    Returns the count of clauses for each clause type
    """
    clause_types = db.query(
        Clause.clause_type,
        func.count(Clause.id).label('count')
    ).group_by(Clause.clause_type).all()
    
    return {
        "clause_types": [
            {"type": ct, "count": count}
            for ct, count in clause_types
            if ct
        ]
    }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get recent contract activity
    
    Returns the most recently uploaded/updated contracts
    """
    recent_contracts = db.query(Contract).order_by(
        Contract.updated_at.desc()
    ).limit(limit).all()
    
    return {
        "recent_contracts": [
            {
                "id": c.id,
                "title": c.title,
                "filename": c.filename,
                "upload_date": c.upload_date.isoformat() if c.upload_date else None,
                "processing_status": c.processing_status,
                "risk_level": c.risk_level,
            }
            for c in recent_contracts
        ]
    }

# Made with Bob