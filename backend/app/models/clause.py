from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Clause(Base):
    """Clause model for storing extracted contract clauses"""
    
    __tablename__ = "clauses"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to contract
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Clause identification
    clause_number = Column(String(50), index=True)  # e.g., "1.1", "2.3.4"
    clause_title = Column(String(500))
    clause_type = Column(String(200), index=True)  # e.g., "Payment Terms", "Termination", "Confidentiality"
    
    # Clause content
    content = Column(Text, nullable=False)
    
    # Position in document
    page_number = Column(Integer)
    position_start = Column(Integer)  # Character position in full text
    position_end = Column(Integer)
    
    # Risk and importance
    risk_level = Column(String(50))  # low, medium, high, critical
    importance_score = Column(Float)  # 0.0 to 1.0
    
    # Extraction metadata
    extraction_confidence = Column(Float)  # Confidence score of extraction
    extraction_method = Column(String(100))  # e.g., "pattern_matching", "docling_structure"
    
    # Additional metadata
    keywords = Column(JSON)  # List of important keywords
    related_clauses = Column(JSON)  # List of related clause IDs
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    contract = relationship("Contract", back_populates="clauses")
    
    def __repr__(self):
        return f"<Clause(id={self.id}, contract_id={self.contract_id}, type='{self.clause_type}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "clause_number": self.clause_number,
            "clause_title": self.clause_title,
            "clause_type": self.clause_type,
            "content": self.content,
            "page_number": self.page_number,
            "position_start": self.position_start,
            "position_end": self.position_end,
            "risk_level": self.risk_level,
            "importance_score": self.importance_score,
            "extraction_confidence": self.extraction_confidence,
            "extraction_method": self.extraction_method,
            "keywords": self.keywords,
            "related_clauses": self.related_clauses,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# Made with Bob
