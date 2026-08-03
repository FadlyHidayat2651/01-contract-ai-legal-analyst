from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Contract(Base):
    """Contract model for storing contract documents and metadata"""
    
    __tablename__ = "contracts"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic information
    title = Column(String(500), nullable=False, index=True)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)  # in bytes
    file_type = Column(String(50))  # pdf, docx, etc.
    
    # Contract metadata
    contract_type = Column(String(200), index=True)  # e.g., "Service Agreement", "NDA"
    parties = Column(JSON)  # List of parties involved
    effective_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    
    # Extracted content
    full_text = Column(Text)  # Full extracted text from document
    summary = Column(Text)  # Brief summary of contract
    
    # Processing metadata
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    
    # Document statistics
    page_count = Column(Integer)
    word_count = Column(Integer)
    clause_count = Column(Integer, default=0)
    
    # Docling processing metadata
    docling_metadata = Column(JSON)  # Store Docling extraction metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    clauses = relationship("Clause", back_populates="contract", cascade="all, delete-orphan")
    sections = relationship("DocumentSection", back_populates="contract", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Contract(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "contract_type": self.contract_type,
            "parties": self.parties,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "summary": self.summary,
            "status": self.status,
            "page_count": self.page_count,
            "word_count": self.word_count,
            "clause_count": self.clause_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }

# Made with Bob
