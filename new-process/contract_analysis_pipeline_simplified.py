#!/usr/bin/env python3
"""
Contract Analysis AI Pipeline - Simplified Version
No OCR/Docling - Uses PyPDF2 for PDF text extraction
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Core dependencies
from langchain_ollama import ChatOllama
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.graphs import Neo4jGraph
from langchain_neo4j import Neo4jVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from neo4j import GraphDatabase
import PyPDF2
from dotenv import load_dotenv

# Load environment
load_dotenv()

# ============================================================================
# ENUMS & DATA MODELS
# ============================================================================

class RiskLevel(str, Enum):
    """Risk severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ClauseType(str, Enum):
    """Contract clause categories"""
    PAYMENT = "payment"
    TERMINATION = "termination"
    LIABILITY = "liability"
    CONFIDENTIALITY = "confidentiality"
    IP_RIGHTS = "intellectual_property"
    WARRANTY = "warranty"
    INDEMNITY = "indemnity"
    DISPUTE = "dispute_resolution"
    FORCE_MAJEURE = "force_majeure"
    COMPLIANCE = "compliance"
    DATA_PRIVACY = "data_privacy"
    SLA = "service_level_agreement"
    GENERAL = "general"

@dataclass
class ContractEntity:
    """Extracted contract entity"""
    name: str
    type: str  # party, obligation, right, condition, etc.
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ContractRelationship:
    """Relationship between entities"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RiskFinding:
    """Risk assessment finding"""
    risk_id: str
    title: str
    description: str
    risk_level: RiskLevel
    clause_type: ClauseType
    affected_sections: List[str]
    recommendation: str
    agent_name: str

@dataclass
class AnalystAgent:
    """Domain expert agent configuration"""
    name: str
    role: str
    focus_areas: List[ClauseType]
    prompt_template: str

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ContractAnalysisConfig:
    """Pipeline configuration"""
    # LLM Settings
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "qwen2.5:latest"
    temperature: float = 0.1
    
    # Neo4j Settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Output
    output_dir: Path = Path("output")
    
    def __post_init__(self):
        self.output_dir.mkdir(exist_ok=True)

# ============================================================================
# STAGE 1: DOCUMENT INGESTION (Simplified - No OCR)
# ============================================================================

class ContractIngestor:
    """
    Stage 1: Document Ingestion
    Loads PDF/TXT and splits into chunks
    """
    
    def __init__(self, config: ContractAnalysisConfig):
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def ingest(self, file_path: str) -> List[Document]:
        """Load and chunk document"""
        print(f"\n{'='*60}")
        print(f"📄 STAGE 1: Document Ingestion")
        print(f"{'='*60}")
        print(f"Loading: {file_path}")
        
        # Extract text based on file type
        file_path_obj = Path(file_path)
        
        if file_path_obj.suffix.lower() == '.pdf':
            text = self._extract_pdf_text(file_path)
        elif file_path_obj.suffix.lower() in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file type: {file_path_obj.suffix}")
        
        print(f"✅ Extracted {len(text)} characters")
        
        # Split into chunks
        documents = self.text_splitter.create_documents(
            texts=[text],
            metadatas=[{"source": file_path, "type": "contract"}]
        )
        
        print(f"✅ Created {len(documents)} chunks")
        print(f"   Chunk size: {self.config.chunk_size}")
        print(f"   Overlap: {self.config.chunk_overlap}")
        
        return documents
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF using PyPDF2"""
        text_parts = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            print(f"   PDF pages: {num_pages}")
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_parts.append(f"[Page {page_num}]\n{text}")
        
        return "\n\n".join(text_parts)

# ============================================================================
# STAGE 2: KNOWLEDGE GRAPH BUILD
# ============================================================================

class ContractGraphBuilder:
    """
    Stage 2: Knowledge Graph Construction
    Extracts entities and relationships, stores in Neo4j
    """
    
    def __init__(self, config: ContractAnalysisConfig):
        self.config = config
        self.llm = ChatOllama(
            base_url=config.ollama_base_url,
            model=config.model_name,
            temperature=config.temperature
        )
        self.graph = Neo4jGraph(
            url=config.neo4j_uri,
            username=config.neo4j_user,
            password=config.neo4j_password
        )
    
    def build_graph(self, documents: List[Document]) -> Dict[str, Any]:
        """Extract entities and build knowledge graph"""
        print(f"\n{'='*60}")
        print(f"🕸️  STAGE 2: Knowledge Graph Build")
        print(f"{'='*60}")
        
        all_entities = []
        all_relationships = []
        
        # Extract from each chunk
        for i, doc in enumerate(documents[:5], 1):  # Limit for demo
            print(f"\nProcessing chunk {i}/{min(5, len(documents))}...")
            
            entities, relationships = self._extract_from_chunk(doc.page_content)
            all_entities.extend(entities)
            all_relationships.extend(relationships)
        
        # Persist to Neo4j
        self._persist_to_neo4j(all_entities, all_relationships)
        
        print(f"\n✅ Graph built:")
        print(f"   Entities: {len(all_entities)}")
        print(f"   Relationships: {len(all_relationships)}")
        
        return {
            "entities": all_entities,
            "relationships": all_relationships
        }
    
    def _extract_from_chunk(self, text: str) -> tuple:
        """Extract entities and relationships from text chunk"""
        
        prompt = ChatPromptTemplate.from_template("""
You are a legal contract analyzer. Extract key entities and relationships from this contract text.

Contract Text:
{text}

Extract:
1. Entities: parties, obligations, rights, conditions, dates, amounts
2. Relationships: who owes what to whom, dependencies, conditions

Return JSON:
{{
  "entities": [
    {{"name": "...", "type": "...", "description": "..."}}
  ],
  "relationships": [
    {{"source": "...", "target": "...", "type": "...", "description": "..."}}
  ]
}}
""")
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            result = chain.invoke({"text": text[:2000]})  # Limit text length
            
            entities = [
                ContractEntity(
                    name=e.get("name", ""),
                    type=e.get("type", ""),
                    description=e.get("description", "")
                )
                for e in result.get("entities", [])
            ]
            
            relationships = [
                ContractRelationship(
                    source=r.get("source", ""),
                    target=r.get("target", ""),
                    type=r.get("type", ""),
                    properties={"description": r.get("description", "")}
                )
                for r in result.get("relationships", [])
            ]
            
            return entities, relationships
            
        except Exception as e:
            print(f"   ⚠️  Extraction error: {e}")
            return [], []
    
    def _persist_to_neo4j(self, entities: List[ContractEntity], 
                          relationships: List[ContractRelationship]):
        """Store entities and relationships in Neo4j"""
        
        # Clear existing data
        self.graph.query("MATCH (n) DETACH DELETE n")
        
        # Create entities
        for entity in entities:
            if entity.name:
                self.graph.query("""
                    MERGE (e:Entity {name: $name})
                    SET e.type = $type, e.description = $description
                """, {
                    "name": entity.name,
                    "type": entity.type,
                    "description": entity.description
                })
        
        # Create relationships
        for rel in relationships:
            if rel.source and rel.target:
                self.graph.query("""
                    MATCH (a:Entity {name: $source})
                    MATCH (b:Entity {name: $target})
                    MERGE (a)-[r:RELATES_TO {type: $type}]->(b)
                    SET r.description = $description
                """, {
                    "source": rel.source,
                    "target": rel.target,
                    "type": rel.type,
                    "description": rel.properties.get("description", "")
                })

# ============================================================================
# STAGE 3: ANALYST AGENT GENERATION
# ============================================================================

class AnalystAgentFactory:
    """
    Stage 3: Generate domain expert agents
    Creates 7 specialized analyst agents
    """
    
    def __init__(self, config: ContractAnalysisConfig):
        self.config = config
    
    def create_agents(self) -> List[AnalystAgent]:
        """Create 7 domain expert agents"""
        print(f"\n{'='*60}")
        print(f"👥 STAGE 3: Analyst Agent Generation")
        print(f"{'='*60}")
        
        agents = [
            AnalystAgent(
                name="Legal Counsel",
                role="Legal compliance and regulatory expert",
                focus_areas=[ClauseType.LIABILITY, ClauseType.INDEMNITY, ClauseType.COMPLIANCE],
                prompt_template="Analyze legal compliance and liability risks..."
            ),
            AnalystAgent(
                name="Financial Analyst",
                role="Payment terms and financial risk expert",
                focus_areas=[ClauseType.PAYMENT, ClauseType.WARRANTY],
                prompt_template="Analyze payment terms and financial obligations..."
            ),
            AnalystAgent(
                name="Compliance Officer",
                role="Regulatory compliance specialist",
                focus_areas=[ClauseType.COMPLIANCE, ClauseType.DATA_PRIVACY],
                prompt_template="Review regulatory compliance requirements..."
            ),
            AnalystAgent(
                name="IT Security",
                role="Data security and privacy expert",
                focus_areas=[ClauseType.DATA_PRIVACY, ClauseType.CONFIDENTIALITY],
                prompt_template="Assess data security and privacy risks..."
            ),
            AnalystAgent(
                name="Commercial Strategy",
                role="Business terms and strategy expert",
                focus_areas=[ClauseType.TERMINATION, ClauseType.SLA],
                prompt_template="Evaluate commercial terms and business impact..."
            ),
            AnalystAgent(
                name="Operations Manager",
                role="Operational execution expert",
                focus_areas=[ClauseType.SLA, ClauseType.FORCE_MAJEURE],
                prompt_template="Review operational requirements and SLAs..."
            ),
            AnalystAgent(
                name="IP Specialist",
                role="Intellectual property expert",
                focus_areas=[ClauseType.IP_RIGHTS, ClauseType.CONFIDENTIALITY],
                prompt_template="Analyze IP rights and confidentiality terms..."
            )
        ]
        
        print(f"✅ Created {len(agents)} analyst agents:")
        for agent in agents:
            print(f"   • {agent.name}: {agent.role}")
        
        return agents

# ============================================================================
# STAGE 4: MULTI-AGENT CONTRACT REVIEW
# ============================================================================

class ContractReviewEngine:
    """
    Stage 4: Multi-agent review with cross-validation
    Each agent analyzes contract and findings are cross-validated
    """
    
    def __init__(self, config: ContractAnalysisConfig, agents: List[AnalystAgent]):
        self.config = config
        self.agents = agents
        self.llm = ChatOllama(
            base_url=config.ollama_base_url,
            model=config.model_name,
            temperature=config.temperature
        )
    
    def review(self, documents: List[Document], graph_data: Dict[str, Any]) -> List[RiskFinding]:
        """Conduct multi-agent review"""
        print(f"\n{'='*60}")
        print(f"🔍 STAGE 4: Multi-Agent Contract Review")
        print(f"{'='*60}")
        
        all_findings = []
        
        # Each agent reviews
        for agent in self.agents:
            print(f"\n{agent.name} reviewing...")
            findings = self._agent_review(agent, documents, graph_data)
            all_findings.extend(findings)
            print(f"   Found {len(findings)} issues")
        
        # Cross-validate
        validated_findings = self._cross_validate(all_findings)
        
        print(f"\n✅ Review complete:")
        print(f"   Total findings: {len(all_findings)}")
        print(f"   After validation: {len(validated_findings)}")
        
        return validated_findings
    
    def _agent_review(self, agent: AnalystAgent, documents: List[Document], 
                      graph_data: Dict[str, Any]) -> List[RiskFinding]:
        """Single agent review"""
        
        # Combine relevant chunks
        text = "\n\n".join([doc.page_content for doc in documents[:3]])
        
        prompt = ChatPromptTemplate.from_template("""
You are {agent_name}, a {agent_role}.

Review this contract and identify risks in your domain:

Contract Text:
{text}

Focus on: {focus_areas}

Return JSON array of findings:
[
  {{
    "title": "...",
    "description": "...",
    "risk_level": "critical|high|medium|low",
    "clause_type": "...",
    "recommendation": "..."
  }}
]
""")
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            result = chain.invoke({
                "agent_name": agent.name,
                "agent_role": agent.role,
                "text": text[:3000],
                "focus_areas": ", ".join([ct.value for ct in agent.focus_areas])
            })
            
            findings = []
            for i, item in enumerate(result[:3], 1):  # Limit findings
                finding = RiskFinding(
                    risk_id=f"{agent.name.replace(' ', '_')}_{i}",
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    risk_level=RiskLevel(item.get("risk_level", "medium")),
                    clause_type=ClauseType.GENERAL,
                    affected_sections=[],
                    recommendation=item.get("recommendation", ""),
                    agent_name=agent.name
                )
                findings.append(finding)
            
            return findings
            
        except Exception as e:
            print(f"   ⚠️  Review error: {e}")
            return []
    
    def _cross_validate(self, findings: List[RiskFinding]) -> List[RiskFinding]:
        """Cross-validate findings between agents"""
        # Simple deduplication for now
        seen = set()
        validated = []
        
        for finding in findings:
            key = f"{finding.title}_{finding.risk_level}"
            if key not in seen:
                seen.add(key)
                validated.append(finding)
        
        return validated

# ============================================================================
# STAGE 5: REPORT GENERATION
# ============================================================================

class ContractReportGenerator:
    """
    Stage 5: Generate comprehensive risk report
    """
    
    def __init__(self, config: ContractAnalysisConfig):
        self.config = config
    
    def generate(self, findings: List[RiskFinding], graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final report"""
        print(f"\n{'='*60}")
        print(f"📊 STAGE 5: Report Generation")
        print(f"{'='*60}")
        
        # Compile findings by risk level
        by_risk = {level: [] for level in RiskLevel}
        for finding in findings:
            by_risk[finding.risk_level].append(finding)
        
        # Generate report
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_findings": len(findings),
                "critical": len(by_risk[RiskLevel.CRITICAL]),
                "high": len(by_risk[RiskLevel.HIGH]),
                "medium": len(by_risk[RiskLevel.MEDIUM]),
                "low": len(by_risk[RiskLevel.LOW])
            },
            "findings": [
                {
                    "id": f.risk_id,
                    "title": f.title,
                    "description": f.description,
                    "risk_level": f.risk_level.value,
                    "agent": f.agent_name,
                    "recommendation": f.recommendation
                }
                for f in findings
            ],
            "graph_summary": {
                "entities": len(graph_data.get("entities", [])),
                "relationships": len(graph_data.get("relationships", []))
            }
        }
        
        # Save report
        report_path = self.config.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Report generated:")
        print(f"   Total findings: {report['summary']['total_findings']}")
        print(f"   Critical: {report['summary']['critical']}")
        print(f"   High: {report['summary']['high']}")
        print(f"   Medium: {report['summary']['medium']}")
        print(f"   Low: {report['summary']['low']}")
        print(f"   Saved to: {report_path}")
        
        return report

# ============================================================================
# MAIN PIPELINE
# ============================================================================

class ContractAnalysisPipeline:
    """
    Main orchestrator for the 5-stage pipeline
    """
    
    def __init__(self, config: ContractAnalysisConfig):
        self.config = config
        self.ingestor = ContractIngestor(config)
        self.graph_builder = ContractGraphBuilder(config)
        self.agent_factory = AnalystAgentFactory(config)
        self.report_generator = ContractReportGenerator(config)
    
    def analyze(self, contract_path: str) -> Dict[str, Any]:
        """Run complete analysis pipeline"""
        print(f"\n{'#'*60}")
        print(f"# CONTRACT ANALYSIS AI - SIMPLIFIED PIPELINE")
        print(f"{'#'*60}")
        print(f"Contract: {contract_path}")
        print(f"Model: {self.config.model_name}")
        print(f"{'#'*60}\n")
        
        # Stage 1: Ingest
        documents = self.ingestor.ingest(contract_path)
        
        # Stage 2: Build graph
        graph_data = self.graph_builder.build_graph(documents)
        
        # Stage 3: Create agents
        agents = self.agent_factory.create_agents()
        
        # Stage 4: Review
        review_engine = ContractReviewEngine(self.config, agents)
        findings = review_engine.review(documents, graph_data)
        
        # Stage 5: Generate report
        report = self.report_generator.generate(findings, graph_data)
        
        print(f"\n{'#'*60}")
        print(f"# ANALYSIS COMPLETE")
        print(f"{'#'*60}\n")
        
        return report

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point"""
    
    # Configuration
    config = ContractAnalysisConfig(
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model_name=os.getenv("OLLAMA_MODEL", "qwen2.5:latest"),
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "password")
    )
    
    # Run pipeline
    pipeline = ContractAnalysisPipeline(config)
    
    # Analyze sample contract
    contract_path = "sample_contract.txt"
    if not Path(contract_path).exists():
        print(f"❌ Contract file not found: {contract_path}")
        return
    
    report = pipeline.analyze(contract_path)
    
    print(f"\n✅ Analysis complete! Report saved to: {config.output_dir}")

if __name__ == "__main__":
    main()

# Made with Bob
