from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ClauseBase(BaseModel):
    """Base schema for Clause"""
    clause_number: Optional[str] = Field(None, max_length=50)
    clause_title: Optional[str] = Field(None, max_length=500)
    clause_type: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1)
    page_number: Optional[int] = None
    risk_level: Optional[str] = None
    importance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    keywords: Optional[List[str]] = None
    notes: Optional[str] = None


class ClauseCreate(ClauseBase):
    """Schema for creating a new clause"""
    contract_id: int
    position_start: Optional[int] = None
    position_end: Optional[int] = None
    extraction_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    extraction_method: Optional[str] = None


class ClauseUpdate(BaseModel):
    """Schema for updating a clause"""
    clause_number: Optional[str] = Field(None, max_length=50)
    clause_title: Optional[str] = Field(None, max_length=500)
    clause_type: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    page_number: Optional[int] = None
    risk_level: Optional[str] = None
    importance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    keywords: Optional[List[str]] = None
    notes: Optional[str] = None


class ClauseResponse(ClauseBase):
    """Schema for clause response"""
    id: int
    contract_id: int
    position_start: Optional[int] = None
    position_end: Optional[int] = None
    extraction_confidence: Optional[float] = None
    extraction_method: Optional[str] = None
    related_clauses: Optional[List[int]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClauseListResponse(BaseModel):
    """Schema for list of clauses"""
    clauses: List[ClauseResponse]
    total: int

# Made with Bob
