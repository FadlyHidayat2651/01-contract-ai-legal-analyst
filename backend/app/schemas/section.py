from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentSectionBase(BaseModel):
    """Base schema for DocumentSection"""
    section_number: Optional[str] = Field(None, max_length=50)
    section_title: Optional[str] = Field(None, max_length=500)
    section_type: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = None
    page_number: Optional[int] = None
    level: int = 0
    order_index: int = 0


class DocumentSectionCreate(DocumentSectionBase):
    """Schema for creating a new document section"""
    contract_id: int
    parent_section_id: Optional[int] = None
    position_start: Optional[int] = None
    position_end: Optional[int] = None
    docling_element_type: Optional[str] = None
    docling_metadata: Optional[Dict[str, Any]] = None


class DocumentSectionResponse(DocumentSectionBase):
    """Schema for document section response"""
    id: int
    contract_id: int
    parent_section_id: Optional[int] = None
    position_start: Optional[int] = None
    position_end: Optional[int] = None
    docling_element_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    children: Optional[List["DocumentSectionResponse"]] = None
    
    class Config:
        from_attributes = True


class DocumentSectionListResponse(BaseModel):
    """Schema for list of document sections"""
    sections: List[DocumentSectionResponse]
    total: int


# Update forward references
DocumentSectionResponse.model_rebuild()

# Made with Bob
