#!/usr/bin/env python3
"""
Simple setup test - checks components one by one
"""

import sys

def test_ollama():
    """Test Ollama connection"""
    print("\n=== Testing Ollama ===")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running")
            print(f"   Available models: {[m['name'] for m in models]}")
            
            # Check for required models
            model_names = [m['name'] for m in models]
            if 'qwen3.5:latest' in model_names:
                print("✅ qwen3.5:latest model found")
            else:
                print("❌ qwen3.5:latest model not found")
                return False
                
            if 'nomic-embed-text:latest' in model_names:
                print("✅ nomic-embed-text:latest model found")
            else:
                print("❌ nomic-embed-text:latest model not found")
                return False
            return True
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

def test_neo4j():
    """Test Neo4j connection"""
    print("\n=== Testing Neo4j ===")
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password123")
        )
        driver.verify_connectivity()
        print("✅ Neo4j is running and accessible")
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("   Make sure Neo4j is running: cd new-process && docker-compose up -d")
        return False

def test_basic_imports():
    """Test basic Python imports"""
    print("\n=== Testing Python Dependencies ===")
    try:
        import langchain
        print("✅ langchain imported")
        
        import langchain_community
        print("✅ langchain_community imported")
        
        import langchain_ollama
        print("✅ langchain_ollama imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_docling():
    """Test docling for document parsing"""
    print("\n=== Testing Docling (Document Parser) ===")
    try:
        from docling.document_converter import DocumentConverter
        print("✅ Docling imported successfully")
        
        # Test with sample file
        import os
        sample_file = "sample_contract.txt"
        if os.path.exists(sample_file):
            print(f"✅ Sample contract file found: {sample_file}")
            
            # Try to parse it
            converter = DocumentConverter()
            result = converter.convert(sample_file)
            print(f"✅ Document parsed successfully")
            print(f"   Content preview: {result.document.export_to_markdown()[:100]}...")
            return True
        else:
            print(f"⚠️  Sample file not found: {sample_file}")
            print("   Docling import successful but no test file available")
            return True
    except Exception as e:
        print(f"❌ Docling test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Contract Analysis Pipeline - Setup Test")
    print("=" * 60)
    
    results = {
        "Ollama": test_ollama(),
        "Neo4j": test_neo4j(),
        "Python Dependencies": test_basic_imports(),
        "Docling (OCR/Parser)": test_docling()
    }
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready.")
        print("\nNext steps:")
        print("1. Run the pipeline: python3 contract_analysis_pipeline.py")
        print("2. Check the results in Neo4j browser: http://localhost:7474")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
