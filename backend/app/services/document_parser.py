import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import PyPDF2
from docx import Document
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


class DocumentParser:
    """Service for processing documents using PyPDF2, python-docx, and OCR"""
    
    def __init__(self):
        """Initialize document parser"""
        logger.info("DocumentParser initialized successfully")
    
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
            
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.pdf':
                result = self._process_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                result = self._process_docx(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Add success flag
            result["success"] = True
            result["file_path"] = file_path
            result["processed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Successfully processed document: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "full_text": None,
                "markdown_text": None,
                "metadata": {},
                "sections": [],
                "tables": [],
            }
    
    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Process PDF using PyPDF2 with OCR fallback
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with extracted content
        """
        full_text = ""
        page_count = 0
        
        try:
            # Try text extraction first
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
            
            # If no text extracted or very little text, use OCR
            if not full_text.strip() or len(full_text.strip()) < 100:
                logger.info(f"PDF appears to be scanned, using OCR for {file_path}")
                full_text = self._ocr_pdf(file_path)
                
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
        
        # Extract sections from text
        sections = self._extract_sections(full_text)
        
        # Generate markdown representation
        markdown_text = self._text_to_markdown(full_text, sections)
        
        # Calculate metadata
        metadata = {
            "page_count": page_count,
            "word_count": len(full_text.split()) if full_text else 0,
            "file_type": "pdf",
        }
        
        return {
            "full_text": full_text,
            "markdown_text": markdown_text,
            "metadata": metadata,
            "sections": sections,
            "tables": [],  # Basic implementation - tables not extracted from PDF
        }
    
    def _ocr_pdf(self, file_path: str) -> str:
        """
        Perform OCR on PDF using pytesseract
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text from OCR
        """
        text = ""
        try:
            # Convert PDF pages to images
            images = convert_from_path(file_path)
            
            # Perform OCR on each page
            for page_num, image in enumerate(images):
                logger.info(f"Performing OCR on page {page_num + 1}")
                page_text = pytesseract.image_to_string(image)
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                
        except Exception as e:
            logger.error(f"Error performing OCR: {str(e)}")
            raise
        
        return text
    
    def _process_docx(self, file_path: str) -> Dict[str, Any]:
        """
        Process DOCX using python-docx
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Dictionary with extracted content
        """
        try:
            doc = Document(file_path)
            
            # Extract text from paragraphs
            full_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            # Extract sections
            sections = self._extract_sections(full_text)
            
            # Extract tables
            tables = self._extract_docx_tables(doc)
            
            # Generate markdown
            markdown_text = self._text_to_markdown(full_text, sections)
            
            # Calculate metadata
            metadata = {
                "page_count": 0,  # DOCX doesn't have explicit page count
                "word_count": len(full_text.split()) if full_text else 0,
                "file_type": "docx",
                "paragraph_count": len(doc.paragraphs),
                "table_count": len(tables),
            }
            
            return {
                "full_text": full_text,
                "markdown_text": markdown_text,
                "metadata": metadata,
                "sections": sections,
                "tables": tables,
            }
            
        except Exception as e:
            logger.error(f"Error processing DOCX: {str(e)}")
            raise
    
    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract sections using heading detection
        
        Args:
            text: Full document text
            
        Returns:
            List of section dictionaries
        """
        sections = []
        
        # Patterns for common section headers
        section_patterns = [
            r'^([A-Z][A-Z\s]{3,}:)',  # ALL CAPS HEADERS:
            r'^(\d+\.\s+[A-Z][^.]+)',  # 1. Numbered Headers
            r'^(ARTICLE\s+\d+[:\s])',  # ARTICLE 1:
            r'^(Section\s+\d+[:\s])',  # Section 1:
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:)',  # Title Case Headers:
        ]
        
        lines = text.split('\n')
        current_section = None
        current_content = []
        section_index = 0
        
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if line matches any section pattern
            is_section_header = False
            for pattern in section_patterns:
                if re.match(pattern, line_stripped):
                    is_section_header = True
                    break
            
            if is_section_header and len(line_stripped) < 200:  # Reasonable header length
                # Save previous section
                if current_section:
                    sections.append({
                        "index": section_index,
                        "type": "section",
                        "content": "\n".join(current_content).strip(),
                        "page_number": None,
                        "level": self._determine_heading_level(current_section),
                        "title": current_section,
                    })
                    section_index += 1
                
                # Start new section
                current_section = line_stripped
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Add final section
        if current_section:
            sections.append({
                "index": section_index,
                "type": "section",
                "content": "\n".join(current_content).strip(),
                "page_number": None,
                "level": self._determine_heading_level(current_section),
                "title": current_section,
            })
        
        return sections
    
    def _determine_heading_level(self, title: str) -> int:
        """
        Determine heading level from title text
        
        Args:
            title: Section title
            
        Returns:
            Heading level (1-6, or 0 for non-headings)
        """
        # ARTICLE or main numbered sections = level 1
        if re.match(r'^(ARTICLE\s+\d+|Section\s+\d+)', title, re.IGNORECASE):
            return 1
        
        # Numbered subsections (1.1, 2.3, etc.) = level 2
        if re.match(r'^\d+\.\d+', title):
            return 2
        
        # Simple numbers (1., 2., etc.) = level 1
        if re.match(r'^\d+\.', title):
            return 1
        
        # ALL CAPS = level 1
        if title.isupper() and len(title) > 3:
            return 1
        
        # Title Case = level 2
        if title[0].isupper() and any(c.islower() for c in title):
            return 2
        
        return 0
    
    def _extract_docx_tables(self, doc) -> List[Dict[str, Any]]:
        """
        Extract tables from DOCX document
        
        Args:
            doc: python-docx Document object
            
        Returns:
            List of table dictionaries
        """
        tables = []
        
        try:
            for table_idx, table in enumerate(doc.tables):
                table_data = []
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    table_data.append(row_data)
                
                tables.append({
                    "index": table_idx,
                    "content": str(table_data),
                    "rows": len(table.rows),
                    "columns": len(table.columns) if table.rows else 0,
                    "data": table_data,
                    "page_number": None,
                })
                
        except Exception as e:
            logger.warning(f"Error extracting tables: {str(e)}")
        
        return tables
    
    def _text_to_markdown(self, text: str, sections: List[Dict[str, Any]]) -> str:
        """
        Convert text to markdown format
        
        Args:
            text: Full document text
            sections: Extracted sections
            
        Returns:
            Markdown formatted text
        """
        if not sections:
            return text
        
        markdown = ""
        for section in sections:
            level = section.get("level", 1)
            title = section.get("title", "")
            content = section.get("content", "")
            
            # Add markdown heading
            markdown += f"\n{'#' * level} {title}\n\n"
            markdown += f"{content}\n"
        
        return markdown
    
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
            "amounts": [],
        }
        
        if not doc_result.get("success"):
            return metadata
        
        full_text = doc_result.get("full_text", "")
        
        # Extract contract parties
        parties_patterns = [
            r'between\s+([^,\n]+)\s+and\s+([^,\n]+)',
            r'Party\s+A[:\s]+([^\n]+)',
            r'Party\s+B[:\s]+([^\n]+)',
        ]
        
        for pattern in parties_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    metadata["parties"].extend([m.strip() for m in match])
                else:
                    metadata["parties"].append(match.strip())
        
        # Remove duplicates
        metadata["parties"] = list(set(metadata["parties"]))[:10]  # Limit to 10
        
        # Extract dates
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
        ]
        
        for pattern in date_patterns:
            dates = re.findall(pattern, full_text, re.IGNORECASE)
            metadata["dates"].extend(dates)
        
        # Remove duplicates and limit
        metadata["dates"] = list(set(metadata["dates"]))[:10]
        
        # Extract contract value/amounts
        amount_patterns = [
            r'\$\s*[\d,]+(?:\.\d{2})?',
            r'\d+\s*(?:million|thousand|billion)',
        ]
        
        for pattern in amount_patterns:
            amounts = re.findall(pattern, full_text, re.IGNORECASE)
            metadata["amounts"].extend(amounts)
        
        metadata["amounts"] = list(set(metadata["amounts"]))[:10]
        
        # Extract contract type from first few lines
        lines = full_text.split('\n')
        first_lines = ' '.join(lines[:10]).lower()
        
        contract_types = {
            'service agreement': 'Service Agreement',
            'non-disclosure': 'Non-Disclosure Agreement',
            'nda': 'Non-Disclosure Agreement',
            'employment': 'Employment Agreement',
            'lease': 'Lease Agreement',
            'purchase': 'Purchase Agreement',
            'sales': 'Sales Agreement',
            'license': 'License Agreement',
            'consulting': 'Consulting Agreement',
        }
        
        for keyword, contract_type in contract_types.items():
            if keyword in first_lines:
                metadata["contract_type"] = contract_type
                break
        
        return metadata


# Made with Bob