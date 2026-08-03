import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ClauseExtractor:
    """Service for extracting and classifying contract clauses"""
    
    # Clause type patterns (keyword-based identification)
    CLAUSE_PATTERNS = {
        "Payment Terms": [
            r"payment\s+terms?",
            r"compensation",
            r"fees?\s+and\s+charges",
            r"invoice",
            r"billing",
            r"price|pricing",
        ],
        "Termination": [
            r"termination",
            r"cancellation",
            r"end\s+of\s+agreement",
            r"notice\s+period",
        ],
        "Confidentiality": [
            r"confidential",
            r"non-disclosure",
            r"proprietary\s+information",
            r"trade\s+secrets?",
        ],
        "Liability": [
            r"liability",
            r"indemnif",
            r"damages",
            r"limitation\s+of\s+liability",
        ],
        "Intellectual Property": [
            r"intellectual\s+property",
            r"copyright",
            r"patent",
            r"trademark",
            r"ownership\s+of",
        ],
        "Warranty": [
            r"warrant",
            r"guarantee",
            r"representation",
        ],
        "Dispute Resolution": [
            r"dispute\s+resolution",
            r"arbitration",
            r"mediation",
            r"governing\s+law",
            r"jurisdiction",
        ],
        "Force Majeure": [
            r"force\s+majeure",
            r"act\s+of\s+god",
            r"unforeseeable\s+circumstances",
        ],
        "Assignment": [
            r"assignment",
            r"transfer\s+of\s+rights",
            r"delegation",
        ],
        "Amendment": [
            r"amendment",
            r"modification",
            r"change\s+to\s+agreement",
        ],
        "Entire Agreement": [
            r"entire\s+agreement",
            r"complete\s+agreement",
            r"supersedes",
        ],
        "Severability": [
            r"severability",
            r"invalid\s+provision",
        ],
    }
    
    # Risk level keywords
    HIGH_RISK_KEYWORDS = [
        "unlimited liability",
        "no warranty",
        "as is",
        "automatic renewal",
        "non-compete",
        "exclusive",
        "perpetual",
    ]
    
    MEDIUM_RISK_KEYWORDS = [
        "penalty",
        "late fee",
        "interest",
        "breach",
        "default",
    ]
    
    def __init__(self):
        """Initialize clause extractor"""
        logger.info("ClauseExtractor initialized")
    
    def extract_clauses(self, full_text: str, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract clauses from document text and sections
        
        Args:
            full_text: Full text of the document
            sections: List of document sections from Docling
            
        Returns:
            List of extracted clause dictionaries
        """
        clauses = []
        
        # Method 1: Extract from numbered sections
        numbered_clauses = self._extract_numbered_clauses(sections)
        clauses.extend(numbered_clauses)
        
        # Method 2: Extract from paragraph patterns
        paragraph_clauses = self._extract_paragraph_clauses(full_text)
        clauses.extend(paragraph_clauses)
        
        # Classify and enrich clauses
        for clause in clauses:
            clause["clause_type"] = self._classify_clause(clause["content"])
            clause["risk_level"] = self._assess_risk_level(clause["content"])
            clause["importance_score"] = self._calculate_importance(clause)
            clause["keywords"] = self._extract_keywords(clause["content"])
        
        # Remove duplicates based on content similarity
        clauses = self._deduplicate_clauses(clauses)
        
        logger.info(f"Extracted {len(clauses)} clauses")
        return clauses
    
    def _extract_numbered_clauses(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract clauses from numbered sections
        
        Args:
            sections: List of document sections
            
        Returns:
            List of clause dictionaries
        """
        clauses = []
        
        # Pattern for numbered sections (e.g., "1.", "1.1", "Article 1")
        number_pattern = re.compile(r'^(\d+\.?\d*\.?\d*|\w+\s+\d+)', re.IGNORECASE)
        
        for idx, section in enumerate(sections):
            content = section.get("content", "").strip()
            
            if not content or len(content) < 20:  # Skip very short sections
                continue
            
            # Check if section starts with a number
            match = number_pattern.match(content)
            
            if match:
                clause_number = match.group(1)
                
                # Extract title if present (usually first line or sentence)
                lines = content.split('\n')
                first_line = lines[0] if lines else content[:100]
                
                clause = {
                    "clause_number": clause_number,
                    "clause_title": self._extract_title(first_line),
                    "content": content,
                    "page_number": section.get("page_number"),
                    "position_start": idx * 1000,  # Approximate position
                    "position_end": (idx + 1) * 1000,
                    "extraction_method": "numbered_section",
                    "extraction_confidence": 0.9,
                }
                
                clauses.append(clause)
        
        return clauses
    
    def _extract_paragraph_clauses(self, full_text: str) -> List[Dict[str, Any]]:
        """
        Extract clauses from paragraphs using pattern matching
        
        Args:
            full_text: Full document text
            
        Returns:
            List of clause dictionaries
        """
        clauses = []
        
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', full_text)
        
        for idx, para in enumerate(paragraphs):
            para = para.strip()
            
            # Skip short paragraphs
            if len(para) < 50:
                continue
            
            # Check if paragraph contains clause indicators
            if self._is_likely_clause(para):
                clause = {
                    "clause_number": None,
                    "clause_title": self._extract_title(para[:100]),
                    "content": para,
                    "page_number": None,
                    "position_start": idx * 500,
                    "position_end": (idx + 1) * 500,
                    "extraction_method": "paragraph_pattern",
                    "extraction_confidence": 0.7,
                }
                
                clauses.append(clause)
        
        return clauses
    
    def _is_likely_clause(self, text: str) -> bool:
        """
        Determine if text is likely a contract clause
        
        Args:
            text: Text to check
            
        Returns:
            True if likely a clause
        """
        text_lower = text.lower()
        
        # Check for clause indicators
        indicators = [
            "shall",
            "must",
            "agrees to",
            "obligated to",
            "responsible for",
            "entitled to",
            "subject to",
        ]
        
        return any(indicator in text_lower for indicator in indicators)
    
    def _classify_clause(self, content: str) -> Optional[str]:
        """
        Classify clause type based on content
        
        Args:
            content: Clause content
            
        Returns:
            Clause type or None
        """
        content_lower = content.lower()
        
        # Check each clause type pattern
        for clause_type, patterns in self.CLAUSE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return clause_type
        
        return "General"
    
    def _assess_risk_level(self, content: str) -> str:
        """
        Assess risk level of clause
        
        Args:
            content: Clause content
            
        Returns:
            Risk level: "low", "medium", "high", or "critical"
        """
        content_lower = content.lower()
        
        # Check for high risk keywords
        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in content_lower:
                return "high"
        
        # Check for medium risk keywords
        for keyword in self.MEDIUM_RISK_KEYWORDS:
            if keyword in content_lower:
                return "medium"
        
        return "low"
    
    def _calculate_importance(self, clause: Dict[str, Any]) -> float:
        """
        Calculate importance score for clause
        
        Args:
            clause: Clause dictionary
            
        Returns:
            Importance score (0.0 to 1.0)
        """
        score = 0.5  # Base score
        
        # Increase score for certain clause types
        important_types = ["Payment Terms", "Termination", "Liability", "Confidentiality"]
        if clause.get("clause_type") in important_types:
            score += 0.2
        
        # Increase score for high risk
        if clause.get("risk_level") == "high":
            score += 0.2
        elif clause.get("risk_level") == "medium":
            score += 0.1
        
        # Increase score for longer clauses (more detailed)
        content_length = len(clause.get("content", ""))
        if content_length > 500:
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_keywords(self, content: str) -> List[str]:
        """
        Extract important keywords from clause content
        
        Args:
            content: Clause content
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction (can be enhanced with NLP)
        keywords = []
        
        # Extract capitalized words (potential proper nouns)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', content)
        keywords.extend(capitalized[:5])  # Limit to 5
        
        # Extract important legal terms
        legal_terms = [
            "agreement", "contract", "party", "obligation", "right",
            "liability", "warranty", "indemnity", "breach", "termination"
        ]
        
        content_lower = content.lower()
        for term in legal_terms:
            if term in content_lower:
                keywords.append(term)
        
        return list(set(keywords))[:10]  # Return unique keywords, max 10
    
    def _extract_title(self, text: str) -> str:
        """
        Extract title from text (first sentence or line)
        
        Args:
            text: Text to extract title from
            
        Returns:
            Extracted title
        """
        # Get first sentence or first 100 characters
        sentences = re.split(r'[.!?]', text)
        title = sentences[0].strip() if sentences else text[:100]
        
        # Clean up
        title = re.sub(r'^\d+\.?\s*', '', title)  # Remove leading numbers
        title = title.strip()
        
        return title[:200]  # Limit length
    
    def _deduplicate_clauses(self, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate clauses based on content similarity
        
        Args:
            clauses: List of clause dictionaries
            
        Returns:
            Deduplicated list of clauses
        """
        if not clauses:
            return []
        
        unique_clauses = []
        seen_content = set()
        
        for clause in clauses:
            # Use first 100 characters as fingerprint
            content_fingerprint = clause.get("content", "")[:100].lower().strip()
            
            if content_fingerprint not in seen_content:
                seen_content.add(content_fingerprint)
                unique_clauses.append(clause)
        
        return unique_clauses

# Made with Bob
