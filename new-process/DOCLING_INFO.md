# Docling - Document Intelligence Library

## Overview
Docling is a powerful document parsing library that simplifies document processing, parsing diverse formats including advanced PDF understanding, and providing seamless integrations with the gen AI ecosystem.

## Key Features for Our Pipeline

### 1. **Document Format Support**
- PDF (with advanced understanding)
- DOCX, PPTX, XLSX
- HTML, Images (PNG, TIFF, JPEG)
- Plain text, Markdown
- LaTeX

### 2. **Advanced PDF Understanding**
- Page layout analysis
- Reading order detection
- Table structure extraction
- Code and formula recognition
- Image classification

### 3. **Export Formats**
- Markdown
- HTML
- JSON (lossless)
- DocTags

## Installation

```bash
pip install docling
```

**Requirements:**
- Python 3.10 or higher (Python 3.9 support dropped in v2.70.0)
- Works on macOS, Linux, Windows
- Both x86_64 and arm64 architectures

## Basic Usage

### Python API (Recommended)

```python
from docling.document_converter import DocumentConverter

# Initialize converter
converter = DocumentConverter()

# Convert document (local path or URL)
source = "path/to/document.pdf"
result = converter.convert(source)

# Export to markdown
markdown_content = result.document.export_to_markdown()

# Export to JSON
json_content = result.document.export_to_json()
```

### CLI Usage

```bash
# Basic conversion
docling path/to/document.pdf

# With VLM (Visual Language Model)
docling --pipeline vlm --vlm-model granite_docling path/to/document.pdf
```

## Integration with Our Pipeline

### Stage 1: Document Ingestion

Docling will be used in our pipeline for:

1. **PDF/DOCX/TXT Parsing**
   - Extract text content
   - Preserve document structure
   - Identify sections and clauses

2. **Structured Output**
   - Convert to markdown for easier processing
   - Maintain hierarchical structure
   - Extract tables and lists

### Example Integration

```python
from docling.document_converter import DocumentConverter

def parse_contract_document(file_path: str) -> dict:
    """
    Parse contract document using Docling
    
    Args:
        file_path: Path to contract file (PDF, DOCX, TXT)
        
    Returns:
        dict: Parsed document with text and structure
    """
    converter = DocumentConverter()
    result = converter.convert(file_path)
    
    return {
        "text": result.document.export_to_markdown(),
        "json": result.document.export_to_json(),
        "metadata": {
            "pages": len(result.document.pages) if hasattr(result.document, 'pages') else None,
            "format": file_path.split('.')[-1]
        }
    }
```

## Advanced Features

### 1. Custom Pipeline Options

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat

# Configure PDF options
pdf_options = PdfFormatOption(
    pipeline_options={
        "do_ocr": True,  # Enable OCR for scanned PDFs
        "do_table_structure": True,  # Extract table structure
    }
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: pdf_options
    }
)
```

### 2. Batch Processing

```python
# Process multiple documents
sources = ["doc1.pdf", "doc2.docx", "doc3.txt"]
results = converter.convert_all(sources)

for result in results:
    print(result.document.export_to_markdown())
```

## Benefits for Contract Analysis

1. **Accurate Text Extraction**: Handles complex PDF layouts
2. **Structure Preservation**: Maintains document hierarchy
3. **Table Extraction**: Crucial for contract terms and conditions
4. **Multi-format Support**: Works with various contract formats
5. **Local Processing**: No data leaves the system (important for legal documents)

## Performance Considerations

- **Speed**: Fast processing with the new Heron layout model
- **Memory**: Efficient handling of large documents
- **Accuracy**: High-quality text extraction even from scanned documents

## Resources

- Documentation: https://docling-project.github.io/docling/
- GitHub: https://github.com/docling-project/docling
- PyPI: https://pypi.org/project/docling/
- Technical Report: https://arxiv.org/abs/2408.09869

## Version Information

- Current Version: 2.93.0 (as of May 2026)
- License: MIT
- Maintained by: IBM Research Zurich (LF AI & Data Foundation)