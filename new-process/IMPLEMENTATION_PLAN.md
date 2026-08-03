# Contract Analysis AI Pipeline - Implementation Plan

## 📋 Overview

This document outlines the complete implementation plan for the **Contract Analysis AI Pipeline** - a multi-agent system that analyzes legal contracts using:
- **Local LLM**: Ollama with qwen3.5:latest
- **Knowledge Graph**: Neo4j for entity/relationship storage
- **Multi-Agent Review**: 7 specialized domain experts
- **Document Processing**: OCR and intelligent chunking

## 🏗️ Architecture (5 Stages)

Based on the architecture diagram, the pipeline consists of:

### Stage 1: Document Ingestion
- **Input**: PDF/DOCX/TXT contracts
- **Process**: Document parsing → Intelligent chunking → Clause classification
- **Output**: Classified chunks with metadata

### Stage 2: Knowledge Graph Build
- **Process**: NER + relationship extraction → Neo4j storage
- **Components**: 
  - Entity extraction (parties, obligations, dates, amounts)
  - Relationship mapping (dependencies, conditions)
  - Vector embeddings for semantic search

### Stage 3: Analyst Agent Generation
- **Process**: Generate 7 domain expert agents from graph entities
- **Agents**:
  1. Legal Counsel
  2. Financial Analyst
  3. Compliance Officer
  4. IT Security Specialist
  5. Commercial Strategy Expert
  6. Operations Manager
  7. IP Specialist

### Stage 4: Multi-Agent Contract Review
- **Process**: Each agent reviews relevant clauses → Cross-validation
- **Output**: Risk findings with severity levels (CRITICAL, HIGH, MEDIUM, LOW)

### Stage 5: Report Generation
- **Output**: 
  - Risk dashboard with metrics
  - Detailed findings report
  - JSON export for integration
  - Graph queries for exploration

## 🎯 Implementation Steps

### Step 1: Environment Setup ✅

**Verify Ollama is Running**
```bash
# Check if Ollama is accessible
curl http://localhost:11434/api/tags

# Verify qwen3.5:latest model is available
ollama list | grep qwen3.5
```

**Expected Output**: Model should be listed and accessible

---

### Step 2: Install Dependencies

**Create Python Virtual Environment**
```bash
cd new-process
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

**Install Required Packages**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Key Dependencies**:
- `langchain>=0.3.0` - LLM orchestration framework
- `langchain-ollama>=0.2.0` - Ollama integration
- `neo4j>=5.15` - Graph database driver
- `pypdf>=4.0` - PDF parsing
- `unstructured>=0.15.0` - Advanced document processing
- `python-docx>=1.1` - DOCX support

---

### Step 3: Start Neo4j Database

**Using Docker Compose**
```bash
cd new-process
docker-compose up -d neo4j
```

**Verify Neo4j is Running**
```bash
# Check container status
docker ps | grep neo4j

# Access Neo4j Browser
open http://localhost:7474
```

**Login Credentials**:
- Username: `neo4j`
- Password: `contract123`

**Verify Connection**:
```bash
# Test connection
docker exec -it contract-neo4j cypher-shell -u neo4j -p contract123
```

---

### Step 4: Configure Environment

**Create `.env` File**
```bash
cat > new-process/.env << 'EOF'
# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3.5:latest
OLLAMA_SMALL_MODEL=qwen3.5:latest
OLLAMA_BASE_URL=http://localhost:11434

# Neo4j Configuration
NEO4J_URL=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=contract123

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Analysis Configuration
ANALYSIS_DEPTH=comprehensive
JURISDICTION=Indonesia
INDUSTRY=Banking
REGULATORY_FRAMEWORKS=OJK,BI,GDPR

# Optional: Watsonx (if needed later)
# WATSONX_URL=https://us-south.ml.cloud.ibm.com
# WATSONX_PROJECT_ID=your-project-id
# WATSONX_API_KEY=your-api-key
EOF
```

---

### Step 5: Test Document OCR/Parsing

**Test with Sample Contract**
```bash
cd new-process
source venv/bin/activate

# Run a quick test
python3 << 'PYEOF'
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Test text loading
print("Testing document loading...")
loader = TextLoader("sample_contract.txt")
docs = loader.load()
print(f"✓ Loaded {len(docs)} document(s)")
print(f"✓ Total characters: {len(docs[0].page_content)}")

# Test chunking
print("\nTesting text splitting...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]
)
chunks = splitter.split_documents(docs)
print(f"✓ Created {len(chunks)} chunks")
print(f"✓ First chunk preview: {chunks[0].page_content[:100]}...")

print("\n✅ Document processing test PASSED")
PYEOF
```

**Expected Output**:
```
Testing document loading...
✓ Loaded 1 document(s)
✓ Total characters: 6500+

Testing text splitting...
✓ Created 8-10 chunks
✓ First chunk preview: SERVICE AGREEMENT...

✅ Document processing test PASSED
```

---

### Step 6: Test Ollama Connection

**Verify LLM Integration**
```bash
python3 << 'PYEOF'
from langchain_ollama import ChatOllama
import json

print("Testing Ollama connection...")
llm = ChatOllama(
    model="qwen3.5:latest",
    base_url="http://localhost:11434",
    temperature=0.1
)

# Simple test
response = llm.invoke("What is a service level agreement? Answer in one sentence.")
print(f"✓ Response: {response.content}")

# JSON extraction test
prompt = """Extract the key information from this text in JSON format:
"The contract value is IDR 15,000,000,000 with 30% due upon signing."

Return only valid JSON with fields: amount, currency, payment_terms"""

response = llm.invoke(prompt)
print(f"\n✓ JSON extraction test:")
print(response.content)

print("\n✅ Ollama integration test PASSED")
PYEOF
```

---

### Step 7: Run Full Pipeline Test

**Execute Complete Analysis**
```bash
cd new-process
source venv/bin/activate

# Run the pipeline
python contract_analysis_pipeline.py
```

**Expected Execution Flow**:
```
🚀 Contract Analysis AI — Multi-Agent Pipeline
================================================

Stage 1: Document Ingestion
----------------------------
✓ Loading contract: sample_contract.txt
✓ Created 8 chunks
✓ Classifying chunks...
  - PAYMENT: 2 chunks
  - SLA: 2 chunks
  - DATA_PROTECTION: 2 chunks
  - LIABILITY: 1 chunk
  - TERMINATION: 1 chunk

Stage 2: Knowledge Graph Build
-------------------------------
✓ Extracting entities and relationships...
✓ Found 45 entities
✓ Found 38 relationships
✓ Persisting to Neo4j...
✓ Creating vector index...

Stage 3: Agent Generation
--------------------------
✓ Creating 7 analyst agents:
  1. Legal Counsel
  2. Financial Analyst
  3. Compliance Officer
  4. IT Security
  5. Commercial Strategy
  6. Operations Manager
  7. IP Specialist

Stage 4: Multi-Agent Review
----------------------------
✓ Legal Counsel: Reviewing 5 relevant chunks...
  - Found 3 findings (1 CRITICAL, 2 HIGH)
✓ Financial Analyst: Reviewing 3 relevant chunks...
  - Found 2 findings (1 HIGH, 1 MEDIUM)
✓ Compliance Officer: Reviewing 4 relevant chunks...
  - Found 4 findings (2 HIGH, 2 MEDIUM)
... (continues for all agents)

✓ Cross-validation complete
✓ Total findings: 18

Stage 5: Report Generation
---------------------------
✓ Generating comprehensive report...
✓ Report saved to: contract_analysis_report.md
✓ Findings exported to: findings.json

================================================
✅ Analysis Complete!
```

---

### Step 8: Verify Outputs

**Check Generated Files**
```bash
# View the report
cat contract_analysis_report.md

# Check JSON findings
cat findings.json | python -m json.tool | head -50

# View risk summary
python3 << 'PYEOF'
import json

with open('findings.json', 'r') as f:
    data = json.load(f)

print("Risk Summary:")
print(f"Total Findings: {len(data['findings'])}")

by_level = {}
for f in data['findings']:
    level = f['risk_level']
    by_level[level] = by_level.get(level, 0) + 1

for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
    count = by_level.get(level, 0)
    print(f"  {level}: {count}")
PYEOF
```

---

### Step 9: Explore Neo4j Graph

**Access Neo4j Browser**
```bash
open http://localhost:7474
```

**Run Sample Queries**:

1. **View All Entities**:
```cypher
MATCH (n:ContractEntity)
RETURN n.name, n.entity_type, n.description
LIMIT 25
```

2. **View Relationships**:
```cypher
MATCH (a:ContractEntity)-[r:RELATES_TO]->(b:ContractEntity)
RETURN a.name, type(r), b.name, r.description
LIMIT 25
```

3. **Find Payment-Related Entities**:
```cypher
MATCH (n:ContractEntity)
WHERE n.entity_type CONTAINS 'payment' OR n.name CONTAINS 'payment'
RETURN n
```

4. **Find High-Risk Paths**:
```cypher
MATCH path = (a:ContractEntity)-[*1..3]-(b:ContractEntity)
WHERE a.entity_type = 'penalty' OR b.entity_type = 'liability'
RETURN path
LIMIT 10
```

---

## 🔍 Testing Document OCR

### Test with Different Document Types

**1. Test with PDF**
```bash
# Create a test PDF (if you have one)
python3 << 'PYEOF'
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("path/to/your/contract.pdf")
docs = loader.load()
print(f"✓ Loaded {len(docs)} pages from PDF")
print(f"✓ First page preview: {docs[0].page_content[:200]}...")
PYEOF
```

**2. Test with DOCX**
```bash
python3 << 'PYEOF'
from langchain_community.document_loaders import Docx2txtLoader

loader = Docx2txtLoader("path/to/your/contract.docx")
docs = loader.load()
print(f"✓ Loaded DOCX document")
print(f"✓ Content preview: {docs[0].page_content[:200]}...")
PYEOF
```

**3. Test with Unstructured (Advanced OCR)**
```bash
python3 << 'PYEOF'
from langchain_community.document_loaders import UnstructuredFileLoader

# This handles PDFs, images, and more with OCR
loader = UnstructuredFileLoader(
    "path/to/your/document.pdf",
    mode="elements"  # Preserves document structure
)
docs = loader.load()
print(f"✓ Loaded {len(docs)} elements")
for i, doc in enumerate(docs[:3]):
    print(f"Element {i}: {doc.page_content[:100]}...")
PYEOF
```

---

## 🎨 Customization Options

### Adjust Agent Expertise

Edit `contract_analysis_pipeline.py` lines 540-590 to customize agent roles:

```python
DEFAULT_AGENTS = [
    {
        "name": "Legal Counsel",
        "role": "Senior Legal Advisor",
        "expertise": ["contract law", "liability", "indemnification"],
        "review_focus": [ClauseType.LIABILITY, ClauseType.INDEMNITY],
        "perspective": "Risk mitigation and legal compliance"
    },
    # Add your custom agents here
]
```

### Adjust Risk Thresholds

Modify the review prompts to change risk assessment criteria:

```python
# In ContractReviewEngine.REVIEW_PROMPT (line 638)
# Adjust the risk level definitions
```

### Change Chunk Size

For different document types, adjust chunking:

```python
# In .env file
CHUNK_SIZE=1500  # Larger chunks for detailed analysis
CHUNK_OVERLAP=300  # More overlap for context preservation
```

---

## 🐛 Troubleshooting

### Issue: Ollama Connection Failed
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama if needed
# On macOS: restart the Ollama app
# On Linux: sudo systemctl restart ollama
```

### Issue: Neo4j Connection Failed
```bash
# Check Neo4j container
docker ps | grep neo4j

# View logs
docker logs contract-neo4j

# Restart Neo4j
docker-compose restart neo4j
```

### Issue: Out of Memory
```bash
# Reduce chunk size in .env
CHUNK_SIZE=500
CHUNK_OVERLAP=100

# Or use smaller model
OLLAMA_MODEL=qwen3.5:latest  # Already the smallest
```

### Issue: Slow Processing
```bash
# Use smaller model for classification
OLLAMA_SMALL_MODEL=qwen3.5:latest

# Reduce analysis depth
ANALYSIS_DEPTH=standard  # Instead of comprehensive
```

---

## 📊 Expected Results

### Sample Output Structure

**contract_analysis_report.md**:
```markdown
# Contract Analysis Report

## Executive Summary
- Total Findings: 18
- Critical Risks: 2
- High Risks: 6
- Medium Risks: 8
- Low Risks: 2

## Key Risk Areas
1. **Data Protection** (CRITICAL)
   - 24-hour breach notification may be insufficient
   - Recommendation: Implement immediate notification protocol

2. **Payment Terms** (HIGH)
   - Late payment penalty of 2% compounded monthly is aggressive
   - Recommendation: Negotiate cap on penalties

...
```

**findings.json**:
```json
{
  "contract_file": "sample_contract.txt",
  "analysis_date": "2026-05-19T10:30:00Z",
  "findings": [
    {
      "id": "finding_001",
      "agent": "Legal Counsel",
      "risk_level": "CRITICAL",
      "category": "DATA_PROTECTION",
      "title": "Insufficient Breach Notification Timeline",
      "description": "24-hour notification period may violate GDPR requirements",
      "recommendation": "Reduce to 72 hours maximum as per GDPR Article 33",
      "confidence": 0.95
    }
  ]
}
```

---

## 🚀 Next Steps

1. **Test with Real Contracts**: Run the pipeline on actual contract documents
2. **Customize Agents**: Adjust agent expertise for your specific domain
3. **Integrate with Existing System**: Connect to your contract management system
4. **Add Watsonx Support**: Configure watsonx.ai for production deployment
5. **Build UI**: Create a web interface for easier interaction

---

## 📚 Additional Resources

- **LangChain Documentation**: https://python.langchain.com/
- **Neo4j Cypher Guide**: https://neo4j.com/docs/cypher-manual/
- **Ollama Models**: https://ollama.ai/library
- **Contract Analysis Best Practices**: See `ARCHITECTURE.md`

---

## ✅ Success Criteria

The implementation is successful when:
- ✅ All 5 stages execute without errors
- ✅ Document OCR correctly extracts text from PDF/DOCX
- ✅ Neo4j graph contains entities and relationships
- ✅ All 7 agents generate findings
- ✅ Report is generated with risk metrics
- ✅ JSON export is valid and complete

---

**Last Updated**: 2026-05-19
**Version**: 1.0
**Status**: Ready for Implementation