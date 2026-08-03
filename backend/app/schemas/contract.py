from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ContractBase(BaseModel):
    """Base schema for Contract"""
    title: str = Field(..., min_length=1, max_length=500)
    contract_type: Optional[str] = Field(None, max_length=200)
    parties: Optional[List[str]] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    summary: Optional[str] = None


class ContractCreate(ContractBase):
    """Schema for creating a new contract"""
    pass


class ContractUpdate(BaseModel):
    """Schema for updating a contract"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    contract_type: Optional[str] = Field(None, max_length=200)
    parties: Optional[List[str]] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    summary: Optional[str] = None
    status: Optional[str] = None


class ContractResponse(ContractBase):
    """Schema for contract response"""
    id: int
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    status: str
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    clause_count: int = 0
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    """Schema for list of contracts"""
    contracts: List[ContractResponse]
    total: int
    page: int
    page_size: int


class ContractDetailResponse(ContractResponse):
    """Schema for detailed contract response with clauses"""
    full_text: Optional[str] = None
    docling_metadata: Optional[Dict[str, Any]] = None
    processing_error: Optional[str] = None
    
    class Config:
        from_attributes = True


class ContractUploadResponse(BaseModel):
    """Schema for contract upload response"""
    message: str
    contract_id: int
    file_name: str
    status: str

# Made with Bob
