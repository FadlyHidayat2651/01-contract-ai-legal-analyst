from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.clause import Clause
from app.schemas.clause import ClauseResponse, ClauseUpdate, ClauseListResponse

router = APIRouter()


@router.get("/", response_model=ClauseListResponse)
async def list_clauses(
    contract_id: Optional[int] = Query(None, description="Filter by contract ID"),
    clause_type: Optional[str] = Query(None, description="Filter by clause type"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List clauses with optional filtering
    
    - **contract_id**: Filter by contract ID
    - **clause_type**: Filter by clause type
    - **risk_level**: Filter by risk level (low, medium, high, critical)
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    query = db.query(Clause)
    
    if contract_id:
        query = query.filter(Clause.contract_id == contract_id)
    
    if clause_type:
        query = query.filter(Clause.clause_type == clause_type)
    
    if risk_level:
        query = query.filter(Clause.risk_level == risk_level)
    
    clauses = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return ClauseListResponse(
        clauses=[ClauseResponse.from_orm(c) for c in clauses],
        total=total,
    )


@router.get("/{clause_id}", response_model=ClauseResponse)
async def get_clause(
    clause_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific clause by ID
    
    - **clause_id**: Clause ID
    """
    clause = db.query(Clause).filter(Clause.id == clause_id).first()
    
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
    
    return ClauseResponse.from_orm(clause)


@router.put("/{clause_id}", response_model=ClauseResponse)
async def update_clause(
    clause_id: int,
    clause_update: ClauseUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a clause
    
    - **clause_id**: Clause ID
    - **clause_update**: Updated clause data
    """
    clause = db.query(Clause).filter(Clause.id == clause_id).first()
    
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
    
    # Update fields
    update_data = clause_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(clause, field, value)
    
    db.commit()
    db.refresh(clause)
    
    return ClauseResponse.from_orm(clause)


@router.delete("/{clause_id}")
async def delete_clause(
    clause_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a clause
    
    - **clause_id**: Clause ID
    """
    clause = db.query(Clause).filter(Clause.id == clause_id).first()
    
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
    
    db.delete(clause)
    db.commit()
    
    return {"message": "Clause deleted successfully"}


@router.get("/types/")
async def get_clause_types(
    db: Session = Depends(get_db),
):
    """
    Get all unique clause types
    """
    clause_types = db.query(Clause.clause_type).distinct().all()
    
    return {
        "clause_types": [ct[0] for ct in clause_types if ct[0]],
    }


@router.get("/risk-levels/")
async def get_risk_levels():
    """
    Get available risk levels
    """
    return {
        "risk_levels": ["low", "medium", "high", "critical"],
    }

# Made with Bob
