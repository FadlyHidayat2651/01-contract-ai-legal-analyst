# Contract Analysis AI Pipeline - Complete Setup Guide

## 🎯 Overview

This is a **5-stage AI-powered contract analysis pipeline** that uses:
- **Local LLM** (Ollama with qwen2.5:latest)
- **Knowledge Graph** (Neo4j)
- **Multi-Agent System** (7 domain expert agents)
- **Simplified Document Processing** (PyPDF2 - no heavy OCR dependencies)

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTRACT ANALYSIS AI                      │
│                     5-Stage Pipeline                         │
└─────────────────────────────────────────────────────────────┘

Stage 1: Document Ingestion
├── PDF/TXT → PyPDF2 text extraction
└── Text chunking (1000 chars, 200 overlap)

Stage 2: Knowledge Graph Build
├── Entity extraction (NER with LLM)
├── Relationship extraction
└── Neo4j graph storage

Stage 3: Analyst Agent Generation
└── 7 domain experts:
    ├── Legal Counsel
    ├── Financial Analyst
    ├── Compliance Officer
    ├── IT Security
    ├── Commercial Strategy
    ├── Operations Manager
    └── IP Specialist

Stage 4: Multi-Agent Contract Review
├── Each agent analyzes contract
├── Risk identification
└── Cross-validation

Stage 5: Report Generation
├── Risk dashboard
├── Findings compilation
└── JSON export
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+**
2. **Ollama** installed and running
3. **Neo4j** (via Docker)
4. **Docker** and **Docker Compose**

### Step 1: Install Ollama

```bash
# macOS
brew install ollama

# Start Ollama service
ollama serve

# Pull the model (in another terminal)
ollama pull qwen2.5:latest

# Verify
curl http://localhost:11434/api/tags
```

### Step 2: Start Neo4j

```bash
cd new-process
docker-compose up -d

# Verify Neo4j is running
docker ps | grep neo4j

# Access Neo4j Browser: http://localhost:7474
# Username: neo4j
# Password: password
```

### Step 3: Install Python Dependencies

```bash
cd new-process
pip3 install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Create .env file (already exists)
cat .env

# Should contain:
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=qwen2.5:latest
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=password
```

### Step 5: Run the Pipeline

```bash
# Full pipeline (takes 5-10 minutes)
python3 contract_analysis_pipeline_simplified.py

# Or test stages individually
python3 test_pipeline_stages.py
```

## 📁 Project Structure

```
new-process/
├── contract_analysis_pipeline_simplified.py  # Main pipeline (simplified, no OCR)
├── contract_analysis_pipeline.py            # Original (with docling OCR)
├── test_pipeline_stages.py                  # Stage-by-stage testing
├── requirements.txt                         # Python dependencies
├── docker-compose.yml                       # Neo4j setup
├── .env                                     # Configuration
├── sample_contract.txt                      # Test contract
├── output/                                  # Generated reports
└── README.md                                # This file
```

## 🔧 Configuration

### Ollama Settings

```python
# In contract_analysis_pipeline_simplified.py
ollama_base_url: str = "http://localhost:11434"
model_name: str = "qwen2.5:latest"
temperature: float = 0.1
```

### Neo4j Settings

```python
neo4j_uri: str = "bolt://localhost:7687"
neo4j_user: str = "neo4j"
neo4j_password: str = "password"
```

### Document Processing

```python
chunk_size: int = 1000        # Characters per chunk
chunk_overlap: int = 200      # Overlap between chunks
```

## 📊 Pipeline Stages Explained

### Stage 1: Document Ingestion

**Purpose:** Load and prepare contract documents

**Process:**
1. Load PDF/TXT file
2. Extract text using PyPDF2 (for PDFs)
3. Split into chunks with overlap
4. Create LangChain documents

**Output:** List of Document objects with metadata

**Code:**
```python
ingestor = ContractIngestor(config)
documents = ingestor.ingest("sample_contract.txt")
# Returns: List[Document] with ~10-20 chunks
```

### Stage 2: Knowledge Graph Build

**Purpose:** Extract entities and relationships, build knowledge graph

**Process:**
1. For each chunk, extract:
   - Entities (parties, obligations, rights, conditions)
   - Relationships (dependencies, conditions)
2. Store in Neo4j graph database
3. Create vector index for semantic search

**Output:** Graph data structure in Neo4j

**Code:**
```python
builder = ContractGraphBuilder(config)
graph_data = builder.build_graph(documents)
# Returns: {"entities": [...], "relationships": [...]}
```

**Neo4j Queries:**
```cypher
// View all entities
MATCH (n:Entity) RETURN n LIMIT 25

// View relationships
MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 25
```

### Stage 3: Analyst Agent Generation

**Purpose:** Create 7 specialized domain expert agents

**Agents:**
1. **Legal Counsel** - Legal compliance, liability, indemnity
2. **Financial Analyst** - Payment terms, financial obligations
3. **Compliance Officer** - Regulatory compliance, data privacy
4. **IT Security** - Data security, confidentiality
5. **Commercial Strategy** - Business terms, termination, SLAs
6. **Operations Manager** - Operational requirements, force majeure
7. **IP Specialist** - Intellectual property, confidentiality

**Code:**
```python
factory = AnalystAgentFactory(config)
agents = factory.create_agents()
# Returns: List[AnalystAgent] with 7 agents
```

### Stage 4: Multi-Agent Contract Review

**Purpose:** Each agent analyzes contract from their domain perspective

**Process:**
1. Each agent reviews relevant contract sections
2. Identifies risks in their domain
3. Generates findings with:
   - Risk level (critical/high/medium/low)
   - Description
   - Affected sections
   - Recommendations
4. Cross-validation between agents

**Output:** List of RiskFinding objects

**Code:**
```python
engine = ContractReviewEngine(config, agents)
findings = engine.review(documents, graph_data)
# Returns: List[RiskFinding] with ~10-30 findings
```

### Stage 5: Report Generation

**Purpose:** Compile findings into comprehensive risk report

**Process:**
1. Aggregate findings by risk level
2. Generate summary statistics
3. Create JSON report
4. Save to output directory

**Output:** JSON report file

**Code:**
```python
generator = ContractReportGenerator(config)
report = generator.generate(findings, graph_data)
# Saves: output/report_YYYYMMDD_HHMMSS.json
```

**Report Structure:**
```json
{
  "generated_at": "2024-01-15T10:30:00",
  "summary": {
    "total_findings": 15,
    "critical": 2,
    "high": 5,
    "medium": 6,
    "low": 2
  },
  "findings": [
    {
      "id": "Legal_Counsel_1",
      "title": "Unlimited Liability Clause",
      "description": "...",
      "risk_level": "critical",
      "agent": "Legal Counsel",
      "recommendation": "..."
    }
  ],
  "graph_summary": {
    "entities": 45,
    "relationships": 32
  }
}
```

## 🧪 Testing

### Test Individual Stages

```bash
python3 test_pipeline_stages.py
```

This will test each stage independently and show:
- ✅ PASS or ❌ FAIL for each stage
- Number of chunks, entities, agents, findings
- Any errors encountered

### Test Document Parsing

```bash
# Test PyPDF2 extraction
python3 test_document_parsing.py
```

### Verify Ollama

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test model
ollama run qwen2.5:latest "Hello, how are you?"
```

### Verify Neo4j

```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Access browser
open http://localhost:7474

# Run test query
MATCH (n) RETURN count(n)
```

## 📈 Performance

### Typical Processing Times

- **Stage 1 (Ingestion):** 1-2 seconds
- **Stage 2 (Graph Build):** 30-60 seconds (depends on chunks)
- **Stage 3 (Agents):** < 1 second
- **Stage 4 (Review):** 2-5 minutes (7 agents × LLM calls)
- **Stage 5 (Report):** < 1 second

**Total:** ~3-7 minutes for a typical contract

### Resource Usage

- **Memory:** ~500MB-1GB
- **CPU:** Moderate (LLM inference)
- **Disk:** Minimal (reports are small JSON files)

## 🔍 Troubleshooting

### Ollama Not Running

```bash
# Start Ollama
ollama serve

# In another terminal, verify
curl http://localhost:11434/api/tags
```

### Neo4j Connection Error

```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Restart Neo4j
cd new-process
docker-compose restart neo4j

# Check logs
docker-compose logs neo4j
```

### Python Dependencies

```bash
# Reinstall dependencies
pip3 install -r requirements.txt --force-reinstall

# Check installed packages
pip3 list | grep -E "langchain|neo4j|PyPDF2"
```

### Model Not Found

```bash
# Pull the model
ollama pull qwen2.5:latest

# List available models
ollama list
```

## 🎨 Customization

### Change LLM Model

```python
# In .env or config
OLLAMA_MODEL=llama2:latest  # or any other model
```

### Adjust Chunk Size

```python
# In ContractAnalysisConfig
chunk_size: int = 1500        # Larger chunks
chunk_overlap: int = 300      # More overlap
```

### Modify Agents

```python
# In AnalystAgentFactory.create_agents()
# Add/remove/modify agents as needed
agents = [
    AnalystAgent(
        name="Custom Agent",
        role="Custom role",
        focus_areas=[ClauseType.CUSTOM],
        prompt_template="Custom prompt..."
    )
]
```

### Change Risk Levels

```python
# In RiskLevel enum
class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    # Add custom levels
```

## 📚 API Reference

### ContractAnalysisPipeline

```python
pipeline = ContractAnalysisPipeline(config)
report = pipeline.analyze("contract.pdf")
```

### ContractIngestor

```python
ingestor = ContractIngestor(config)
documents = ingestor.ingest("contract.txt")
```

### ContractGraphBuilder

```python
builder = ContractGraphBuilder(config)
graph_data = builder.build_graph(documents)
```

### ContractReviewEngine

```python
engine = ContractReviewEngine(config, agents)
findings = engine.review(documents, graph_data)
```

### ContractReportGenerator

```python
generator = ContractReportGenerator(config)
report = generator.generate(findings, graph_data)
```

## 🔐 Security Notes

- Neo4j default password should be changed in production
- Ollama runs locally - no data sent to external APIs
- All processing is done on-premise
- Reports contain sensitive contract data - secure appropriately

## 📝 License

This is a demonstration project for contract analysis using AI.

## 🤝 Contributing

This is a reference implementation. Customize as needed for your use case.

## 📞 Support

For issues or questions:
1. Check troubleshooting section
2. Verify all services are running
3. Check logs in `output/` directory

## 🎯 Next Steps

1. **Test with your contracts** - Replace `sample_contract.txt`
2. **Customize agents** - Modify agent roles and focus areas
3. **Tune parameters** - Adjust chunk size, temperature, etc.
4. **Add more features** - Integrate with your systems
5. **Scale up** - Use more powerful models or distributed processing

---

**Built with:** Python, LangChain, Ollama, Neo4j, PyPDF2

**Last Updated:** 2024-01-15