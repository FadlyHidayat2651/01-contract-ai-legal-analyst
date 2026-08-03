import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

logger = logging.getLogger(__name__)


class DoclingService:
    """Service for processing documents using IBM Docling"""
    
    def __init__(self):
        """Initialize Docling service with default configuration"""
        # Configure PDF pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True  # Enable OCR for scanned documents
        pipeline_options.do_table_structure = True  # Extract table structures
        
        # Initialize document converter
        self.converter = DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.PPTX,
                InputFormat.HTML,
                InputFormat.IMAGE,
            ],
            format_options={
                InputFormat.PDF: pipeline_options,
            }
        )
        
        logger.info("DoclingService initialized successfully")
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document and extract structured content
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        try:
            logger.info(f"Processing document: {file_path}")
            
            # Convert document
            result = self.converter.convert(file_path)
            
            # Extract document content
            doc = result.document
            
            # Get full text
            full_text = doc.export_to_text()
            
            # Get markdown representation
            markdown_text = doc.export_to_markdown()
            
            # Extract metadata
            metadata = {
                "file_path": file_path,
                "processed_at": datetime.utcnow().isoformat(),
                "page_count": len(doc.pages) if hasattr(doc, 'pages') else 0,
                "word_count": len(full_text.split()) if full_text else 0,
            }
            
            # Extract document structure
            sections = self._extract_sections(doc)
            
            # Extract tables if present
            tables = self._extract_tables(doc)
            
            return {
                "success": True,
                "full_text": full_text,
                "markdown_text": markdown_text,
                "metadata": metadata,
                "sections": sections,
                "tables": tables,
                "raw_document": doc,  # Keep for further processing
            }
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "full_text": None,
                "metadata": {},
                "sections": [],
                "tables": [],
            }
    
    def _extract_sections(self, doc) -> List[Dict[str, Any]]:
        """
        Extract document sections from Docling document
        
        Args:
            doc: Docling document object
            
        Returns:
            List of section dictionaries
        """
        sections = []
        
        try:
            # Iterate through document elements
            for idx, item in enumerate(doc.iterate_items()):
                section = {
                    "index": idx,
                    "type": item.label if hasattr(item, 'label') else "unknown",
                    "content": item.text if hasattr(item, 'text') else "",
                    "page_number": item.prov[0].page_no if hasattr(item, 'prov') and item.prov else None,
                    "level": self._determine_heading_level(item),
                }
                sections.append(section)
                
        except Exception as e:
            logger.warning(f"Error extracting sections: {str(e)}")
        
        return sections
    
    def _determine_heading_level(self, item) -> int:
        """
        Determine heading level from document item
        
        Args:
            item: Document item
            
        Returns:
            Heading level (0 for non-headings)
        """
        if not hasattr(item, 'label'):
            return 0
        
        label = item.label.lower()
        
        # Map Docling labels to heading levels
        if 'title' in label or 'heading-1' in label:
            return 1
        elif 'heading-2' in label or 'subtitle' in label:
            return 2
        elif 'heading-3' in label:
            return 3
        elif 'heading-4' in label:
            return 4
        elif 'heading-5' in label:
            return 5
        elif 'heading-6' in label:
            return 6
        
        return 0
    
    def _extract_tables(self, doc) -> List[Dict[str, Any]]:
        """
        Extract tables from Docling document
        
        Args:
            doc: Docling document object
            
        Returns:
            List of table dictionaries
        """
        tables = []
        
        try:
            for idx, item in enumerate(doc.iterate_items()):
                if hasattr(item, 'label') and 'table' in item.label.lower():
                    table = {
                        "index": idx,
                        "content": item.text if hasattr(item, 'text') else "",
                        "page_number": item.prov[0].page_no if hasattr(item, 'prov') and item.prov else None,
                    }
                    tables.append(table)
                    
        except Exception as e:
            logger.warning(f"Error extracting tables: {str(e)}")
        
        return tables
    
    def extract_metadata(self, doc_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract contract-specific metadata from processed document
        
        Args:
            doc_result: Result from process_document
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            "parties": [],
            "dates": [],
            "contract_type": None,
        }
        
        if not doc_result.get("success"):
            return metadata
        
        full_text = doc_result.get("full_text", "")
        
        # Simple pattern-based extraction (can be enhanced)
        # Extract potential parties (lines with "Party", "between", etc.)
        lines = full_text.split('\n')
        for line in lines[:50]:  # Check first 50 lines
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['party', 'between', 'agreement between']):
                metadata["parties"].append(line.strip())
        
        # Extract contract type from title or first few lines
        if lines:
            first_lines = ' '.join(lines[:5])
            if 'service agreement' in first_lines.lower():
                metadata["contract_type"] = "Service Agreement"
            elif 'non-disclosure' in first_lines.lower() or 'nda' in first_lines.lower():
                metadata["contract_type"] = "Non-Disclosure Agreement"
            elif 'employment' in first_lines.lower():
                metadata["contract_type"] = "Employment Agreement"
            elif 'lease' in first_lines.lower():
                metadata["contract_type"] = "Lease Agreement"
        
        return metadata

# Made with Bob
