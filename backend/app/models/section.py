from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class DocumentSection(Base):
    """DocumentSection model for storing document structure and sections"""
    
    __tablename__ = "document_sections"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to contract
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Section identification
    section_number = Column(String(50), index=True)  # e.g., "1", "2.1", "Appendix A"
    section_title = Column(String(500))
    section_type = Column(String(100))  # e.g., "heading", "paragraph", "list", "table"
    
    # Hierarchy
    parent_section_id = Column(Integer, ForeignKey("document_sections.id", ondelete="CASCADE"), nullable=True)
    level = Column(Integer, default=0)  # Depth in document hierarchy (0 = top level)
    order_index = Column(Integer, default=0)  # Order within parent section
    
    # Content
    content = Column(Text)
    
    # Position in document
    page_number = Column(Integer)
    position_start = Column(Integer)  # Character position in full text
    position_end = Column(Integer)
    
    # Docling metadata
    docling_element_type = Column(String(100))  # Original Docling element type
    docling_metadata = Column(JSON)  # Additional Docling metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    contract = relationship("Contract", back_populates="sections")
    parent = relationship("DocumentSection", remote_side=[id], backref="children")
    
    def __repr__(self):
        return f"<DocumentSection(id={self.id}, contract_id={self.contract_id}, title='{self.section_title}')>"
    
    def to_dict(self, include_children=False):
        """Convert model to dictionary"""
        result = {
            "id": self.id,
            "contract_id": self.contract_id,
            "section_number": self.section_number,
            "section_title": self.section_title,
            "section_type": self.section_type,
            "parent_section_id": self.parent_section_id,
            "level": self.level,
            "order_index": self.order_index,
            "content": self.content,
            "page_number": self.page_number,
            "position_start": self.position_start,
            "position_end": self.position_end,
            "docling_element_type": self.docling_element_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_children and hasattr(self, 'children'):
            result["children"] = [child.to_dict(include_children=True) for child in self.children]
        
        return result

# Made with Bob
