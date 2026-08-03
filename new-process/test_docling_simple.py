#!/usr/bin/env python3
"""
Simple test of docling document parsing
"""

from docling.document_converter import DocumentConverter

def test_docling():
    print("=" * 60)
    print("Testing Docling Document Parsing")
    print("=" * 60)
    
    # Test with sample contract
    file_path = "sample_contract.txt"
    
    print(f"\n📄 Loading document: {file_path}")
    
    try:
        converter = DocumentConverter()
        result = converter.convert(file_path)
        
        # Export to markdown
        markdown_text = result.document.export_to_markdown()
        
        print(f"\n✅ Document loaded successfully!")
        print(f"📊 Document length: {len(markdown_text)} characters")
        print(f"\n📝 First 500 characters:")
        print("-" * 60)
        print(markdown_text[:500])
        print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_docling()
    exit(0 if success else 1)

# Made with Bob
