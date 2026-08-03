import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.clause import Clause
from app.models.section import DocumentSection
from app.services.document_parser import DocumentParser
from app.services.storage_service import StorageService
from app.services.clause_extractor import ClauseExtractor

logger = logging.getLogger(__name__)


class ContractService:
    """Service for managing contract operations"""
    
    def __init__(self):
        """Initialize contract service with dependencies"""
        self.document_parser = DocumentParser()
        self.storage_service = StorageService()
        self.clause_extractor = ClauseExtractor()
        logger.info("ContractService initialized")
    
    def create_contract(
        self,
        db: Session,
        file_obj,
        title: str,
        contract_type: Optional[str] = None,
    ) -> Contract:
        """
        Create a new contract from uploaded file
        
        Args:
            db: Database session
            file_obj: Uploaded file object
            title: Contract title
            contract_type: Optional contract type
            
        Returns:
            Created Contract object
        """
        try:
            # Save file to storage
            file_path, file_name, file_size = self.storage_service.save_uploaded_file(
                file_obj, file_obj.filename
            )
            
            # Determine file type
            file_type = file_name.split('.')[-1].lower() if '.' in file_name else 'unknown'
            
            # Create contract record
            contract = Contract(
                title=title,
                file_name=file_name,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                contract_type=contract_type,
                status="pending",
            )
            
            db.add(contract)
            db.commit()
            db.refresh(contract)
            
            logger.info(f"Contract created: {contract.id} - {title}")
            
            # Process document asynchronously (in real app, use background task)
            self.process_contract(db, contract.id)
            
            return contract
            
        except Exception as e:
            logger.error(f"Error creating contract: {str(e)}")
            db.rollback()
            raise
    
    def process_contract(self, db: Session, contract_id: int) -> Contract:
        """
        Process contract document and extract content
        
        Args:
            db: Database session
            contract_id: Contract ID to process
            
        Returns:
            Updated Contract object
        """
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        
        if not contract:
            raise ValueError(f"Contract not found: {contract_id}")
        
        try:
            # Update status
            contract.status = "processing"
            db.commit()
            
            logger.info(f"Processing contract: {contract_id}")
            
            # Process document with DocumentParser
            doc_result = self.document_parser.process_document(contract.file_path)
            
            if not doc_result.get("success"):
                raise Exception(doc_result.get("error", "Unknown error"))
            
            # Update contract with extracted content
            contract.full_text = doc_result.get("full_text")
            contract.page_count = doc_result.get("metadata", {}).get("page_count")
            contract.word_count = doc_result.get("metadata", {}).get("word_count")
            contract.docling_metadata = doc_result.get("metadata")
            
            # Extract metadata
            metadata = self.document_parser.extract_metadata(doc_result)
            if metadata.get("contract_type") and not contract.contract_type:
                contract.contract_type = metadata["contract_type"]
            if metadata.get("parties"):
                contract.parties = metadata["parties"][:5]  # Limit to 5 parties
            
            # Extract and save sections
            sections = doc_result.get("sections", [])
            self._save_sections(db, contract.id, sections)
            
            # Extract and save clauses
            clauses = self.clause_extractor.extract_clauses(
                contract.full_text or "",
                sections
            )
            self._save_clauses(db, contract.id, clauses)
            
            # Update contract status
            contract.status = "completed"
            contract.processed_at = datetime.utcnow()
            contract.clause_count = len(clauses)
            
            db.commit()
            db.refresh(contract)
            
            logger.info(f"Contract processed successfully: {contract_id}")
            
            return contract
            
        except Exception as e:
            logger.error(f"Error processing contract {contract_id}: {str(e)}")
            contract.status = "failed"
            contract.processing_error = str(e)
            db.commit()
            raise
    
    def _save_sections(self, db: Session, contract_id: int, sections: List[Dict[str, Any]]):
        """
        Save document sections to database
        
        Args:
            db: Database session
            contract_id: Contract ID
            sections: List of section dictionaries
        """
        for section_data in sections:
            section = DocumentSection(
                contract_id=contract_id,
                section_number=section_data.get("index"),
                section_title=section_data.get("content", "")[:500],
                section_type=section_data.get("type"),
                content=section_data.get("content"),
                page_number=section_data.get("page_number"),
                level=section_data.get("level", 0),
                order_index=section_data.get("index", 0),
                docling_element_type=section_data.get("type"),
            )
            db.add(section)
        
        db.commit()
        logger.info(f"Saved {len(sections)} sections for contract {contract_id}")
    
    def _save_clauses(self, db: Session, contract_id: int, clauses: List[Dict[str, Any]]):
        """
        Save extracted clauses to database
        
        Args:
            db: Database session
            contract_id: Contract ID
            clauses: List of clause dictionaries
        """
        for clause_data in clauses:
            clause = Clause(
                contract_id=contract_id,
                clause_number=clause_data.get("clause_number"),
                clause_title=clause_data.get("clause_title"),
                clause_type=clause_data.get("clause_type"),
                content=clause_data.get("content"),
                page_number=clause_data.get("page_number"),
                position_start=clause_data.get("position_start"),
                position_end=clause_data.get("position_end"),
                risk_level=clause_data.get("risk_level"),
                importance_score=clause_data.get("importance_score"),
                extraction_confidence=clause_data.get("extraction_confidence"),
                extraction_method=clause_data.get("extraction_method"),
                keywords=clause_data.get("keywords"),
            )
            db.add(clause)
        
        db.commit()
        logger.info(f"Saved {len(clauses)} clauses for contract {contract_id}")
    
    def get_contract(self, db: Session, contract_id: int) -> Optional[Contract]:
        """
        Get contract by ID
        
        Args:
            db: Database session
            contract_id: Contract ID
            
        Returns:
            Contract object or None
        """
        return db.query(Contract).filter(Contract.id == contract_id).first()
    
    def list_contracts(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        contract_type: Optional[str] = None,
    ) -> List[Contract]:
        """
        List contracts with optional filtering
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
            contract_type: Optional contract type filter
            
        Returns:
            List of Contract objects
        """
        query = db.query(Contract)
        
        if status:
            query = query.filter(Contract.status == status)
        
        if contract_type:
            query = query.filter(Contract.contract_type == contract_type)
        
        return query.order_by(Contract.created_at.desc()).offset(skip).limit(limit).all()
    
    def search_contracts(self, db: Session, search_term: str) -> List[Contract]:
        """
        Search contracts by title or content
        
        Args:
            db: Database session
            search_term: Search term
            
        Returns:
            List of matching Contract objects
        """
        search_pattern = f"%{search_term}%"
        
        return db.query(Contract).filter(
            (Contract.title.ilike(search_pattern)) |
            (Contract.full_text.ilike(search_pattern))
        ).order_by(Contract.created_at.desc()).all()
    
    def delete_contract(self, db: Session, contract_id: int) -> bool:
        """
        Delete contract and associated file
        
        Args:
            db: Database session
            contract_id: Contract ID
            
        Returns:
            True if deleted successfully
        """
        contract = self.get_contract(db, contract_id)
        
        if not contract:
            return False
        
        try:
            # Delete file from storage
            self.storage_service.delete_file(contract.file_name)
            
            # Delete from database (cascades to clauses and sections)
            db.delete(contract)
            db.commit()
            
            logger.info(f"Contract deleted: {contract_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting contract {contract_id}: {str(e)}")
            db.rollback()
            return False
    
    def get_contract_clauses(self, db: Session, contract_id: int) -> List[Clause]:
        """
        Get all clauses for a contract
        
        Args:
            db: Database session
            contract_id: Contract ID
            
        Returns:
            List of Clause objects
        """
        return db.query(Clause).filter(Clause.contract_id == contract_id).all()
    
    def get_contract_sections(self, db: Session, contract_id: int) -> List[DocumentSection]:
        """
        Get all sections for a contract
        
        Args:
            db: Database session
            contract_id: Contract ID
            
        Returns:
            List of DocumentSection objects
        """
        return db.query(DocumentSection).filter(
            DocumentSection.contract_id == contract_id
        ).order_by(DocumentSection.order_index).all()

# Made with Bob
