#!/usr/bin/env python3
"""
Test Document Parsing and OCR Capabilities
Tests Stage 1: Document Ingestion
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("STAGE 1: DOCUMENT INGESTION TEST")
print("=" * 80)

# Test 1: Import required libraries
print("\n[1/5] Testing library imports...")
try:
    from langchain_community.document_loaders import TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    print("✓ All required libraries imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test 2: Load sample contract
print("\n[2/5] Loading sample contract...")
try:
    contract_path = Path("sample_contract.txt")
    if not contract_path.exists():
        print(f"✗ Sample contract not found at {contract_path}")
        sys.exit(1)
    
    loader = TextLoader(str(contract_path))
    documents = loader.load()
    print(f"✓ Loaded {len(documents)} document(s)")
    print(f"  - Total characters: {len(documents[0].page_content)}")
    print(f"  - First 200 chars: {documents[0].page_content[:200]}...")
except Exception as e:
    print(f"✗ Error loading document: {e}")
    sys.exit(1)

# Test 3: Text splitting/chunking
print("\n[3/5] Testing text chunking...")
try:
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"✓ Split into {len(chunks)} chunks")
    print(f"  - Chunk size: {chunk_size} chars")
    print(f"  - Overlap: {chunk_overlap} chars")
    print(f"\n  Sample chunk 1:")
    print(f"  {chunks[0].page_content[:300]}...")
except Exception as e:
    print(f"✗ Error chunking document: {e}")
    sys.exit(1)

# Test 4: Extract key sections
print("\n[4/5] Extracting key contract sections...")
try:
    full_text = documents[0].page_content
    sections = []
    
    # Simple section extraction based on numbered headings
    import re
    section_pattern = r'(\d+\.\s+[A-Z\s]+)\n'
    matches = re.finditer(section_pattern, full_text)
    
    for match in matches:
        section_title = match.group(1).strip()
        sections.append(section_title)
    
    print(f"✓ Extracted {len(sections)} sections:")
    for i, section in enumerate(sections[:5], 1):
        print(f"  {i}. {section}")
    if len(sections) > 5:
        print(f"  ... and {len(sections) - 5} more")
except Exception as e:
    print(f"✗ Error extracting sections: {e}")
    sys.exit(1)

# Test 5: Metadata extraction
print("\n[5/5] Extracting contract metadata...")
try:
    metadata = {
        "total_length": len(full_text),
        "num_chunks": len(chunks),
        "num_sections": len(sections),
        "contract_parties": [],
        "contract_date": None,
        "contract_value": None
    }
    
    # Extract parties
    parties_pattern = r'between\s+([^(]+)\s+\("Client"\).*?and\s+([^(]+)\s+\("Provider"\)'
    parties_match = re.search(parties_pattern, full_text, re.DOTALL)
    if parties_match:
        metadata["contract_parties"] = [
            parties_match.group(1).strip(),
            parties_match.group(2).strip()
        ]
    
    # Extract date
    date_pattern = r'as of\s+([A-Za-z]+\s+\d+,\s+\d{4})'
    date_match = re.search(date_pattern, full_text)
    if date_match:
        metadata["contract_date"] = date_match.group(1)
    
    # Extract contract value
    value_pattern = r'IDR\s+([\d,]+)'
    value_match = re.search(value_pattern, full_text)
    if value_match:
        metadata["contract_value"] = value_match.group(1)
    
    print("✓ Metadata extracted:")
    print(f"  - Parties: {', '.join(metadata['contract_parties'])}")
    print(f"  - Date: {metadata['contract_date']}")
    print(f"  - Value: IDR {metadata['contract_value']}")
    print(f"  - Total length: {metadata['total_length']} chars")
    print(f"  - Chunks: {metadata['num_chunks']}")
    print(f"  - Sections: {metadata['num_sections']}")
except Exception as e:
    print(f"✗ Error extracting metadata: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✓ DOCUMENT INGESTION TEST COMPLETED SUCCESSFULLY")
print("=" * 80)
print("\nNext steps:")
print("  1. Test knowledge graph building (Stage 2)")
print("  2. Test agent generation (Stage 3)")
print("  3. Run full pipeline with: python contract_analysis_pipeline.py")

# Made with Bob
