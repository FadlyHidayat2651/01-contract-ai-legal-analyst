"""
Contract Analysis AI — MiroFish KG Architecture × LangChain
=============================================================
Multi-agent contract intelligence platform that:
  1. Ingests contracts (PDF/DOCX/TXT)
  2. Builds a knowledge graph of parties, obligations, clauses, risks
  3. Spawns domain-expert AI agents to review from different angles
  4. Cross-references with regulatory frameworks
  5. Generates risk report with actionable recommendations

Supports: Ollama (fully local) | IBM watsonx.ai (enterprise) | Hybrid

Stack: LangChain | Neo4j | Ollama/watsonx | ChromaDB (vector backup)
"""

import json
import uuid
import os
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

# ─── LangChain Core ───────────────────────────────────────────────
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# Simple text splitter to avoid torch dependencies
class SimpleTextSplitter:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text):
        """Split text into chunks"""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.chunk_overlap
            
        return chunks
    
    def create_documents(self, texts):
        """Create document objects from texts"""
        from langchain_core.documents import Document
        documents = []
        for text in texts:
            chunks = self.split_text(text)
            for chunk in chunks:
                documents.append(Document(page_content=chunk))
        return documents
    
    def split_documents(self, documents):
        """Split documents into chunks"""
        from langchain_core.documents import Document
        result = []
        for doc in documents:
            chunks = self.split_text(doc.page_content)
            for chunk in chunks:
                result.append(Document(
                    page_content=chunk,
                    metadata=doc.metadata
                ))
        return result

# ─── Document Loaders ─────────────────────────────────────────────
# Avoid torch dependencies - use docling directly
from docling.document_converter import DocumentConverter

# ─── Neo4j ────────────────────────────────────────────────────────
from langchain_neo4j import Neo4jGraph, Neo4jVector, GraphCypherQAChain

# ─── Ollama ───────────────────────────────────────────────────────
from langchain_ollama import ChatOllama, OllamaEmbeddings


# =====================================================================
# ENUMS & DATA MODELS
# =====================================================================

class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class ClauseType(str, Enum):
    OBLIGATION = "OBLIGATION"
    RIGHT = "RIGHT"
    CONDITION = "CONDITION"
    TERMINATION = "TERMINATION"
    INDEMNITY = "INDEMNITY"
    CONFIDENTIALITY = "CONFIDENTIALITY"
    LIABILITY = "LIABILITY"
    PAYMENT = "PAYMENT"
    SLA = "SLA"
    FORCE_MAJEURE = "FORCE_MAJEURE"
    GOVERNING_LAW = "GOVERNING_LAW"
    DISPUTE = "DISPUTE"
    IP = "INTELLECTUAL_PROPERTY"
    DATA_PROTECTION = "DATA_PROTECTION"
    PENALTY = "PENALTY"
    RENEWAL = "RENEWAL"
    WARRANTY = "WARRANTY"
    GENERAL = "GENERAL"


@dataclass
class ContractEntity:
    """An entity extracted from a contract."""
    id: str
    name: str
    entity_type: str   # PARTY, CLAUSE, OBLIGATION, DATE, AMOUNT, JURISDICTION, ASSET
    description: str = ""
    properties: Dict = field(default_factory=dict)
    source_chunk: str = ""


@dataclass
class ContractRelationship:
    """A relationship between contract entities."""
    source: str
    target: str
    relation_type: str  # OBLIGATED_TO, PAYS, GOVERNED_BY, TERMINATES_IF, etc.
    description: str = ""
    conditions: str = ""


@dataclass
class RiskFinding:
    """A risk identified by an analyst agent."""
    id: str
    clause_ref: str
    risk_level: RiskLevel
    category: str
    title: str
    description: str
    recommendation: str
    agent_name: str
    confidence: float = 0.0


@dataclass
class AnalystAgent:
    """A domain-expert agent that reviews contracts from a specific angle."""
    id: str
    name: str
    role: str
    expertise: str
    review_focus: str
    perspective: str  # whose interests they protect
    findings: List[RiskFinding] = field(default_factory=list)


# =====================================================================
# CONFIG
# =====================================================================

@dataclass
class ContractAnalysisConfig:
    """Pipeline configuration."""

    # LLM Provider
    llm_provider: str = "ollama"           # "ollama" | "watsonx" | "hybrid"

    # Ollama settings
    ollama_model: str = "qwen3.5:latest"      # Main reasoning model
    ollama_small_model: str = "qwen3.5:latest" # For lighter tasks (NER, classification)
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"

    # watsonx settings (for "watsonx" or "hybrid" provider)
    watsonx_model_id: str = "ibm/granite-3-8b-instruct"
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"
    watsonx_project_id: str = ""
    watsonx_api_key: str = ""

    # Neo4j
    neo4j_url: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = os.environ.get("NEO4J_PASSWORD", "your_value_here")

    # Processing
    chunk_size: int = 1500
    chunk_overlap: int = 200

    # Analysis depth
    analysis_depth: str = "thorough"  # "quick" | "standard" | "thorough"

    # Regulatory context
    jurisdiction: str = "Indonesia"
    industry: str = "Banking"
    regulatory_frameworks: List[str] = field(default_factory=lambda: [
        "OJK Regulations",
        "Indonesian Civil Code (KUHPerdata)",
        "UU ITE (Electronic Information)",
        "POJK Data Protection",
        "Bank Indonesia Regulations",
    ])


# =====================================================================
# LLM FACTORY
# =====================================================================

class LLMFactory:
    """Creates LLM instances based on config."""

    @staticmethod
    def create_main_llm(config: ContractAnalysisConfig):
        """Main reasoning LLM (for analysis, report generation)."""
        if config.llm_provider in ("ollama", "hybrid"):
            return ChatOllama(
                model=config.ollama_model,
                base_url=config.ollama_base_url,
                temperature=0.3,  # Lower temp for analytical tasks
                num_ctx=8192,
            )
        elif config.llm_provider == "watsonx":
            from langchain_ibm import WatsonxLLM
            return WatsonxLLM(
                model_id=config.watsonx_model_id,
                url=config.watsonx_url,
                project_id=config.watsonx_project_id,
                apikey=config.watsonx_api_key,
                params={
                    "max_new_tokens": 4096,
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "repetition_penalty": 1.1,
                },
            )

    @staticmethod
    def create_extraction_llm(config: ContractAnalysisConfig):
        """Lighter LLM for entity extraction (can be smaller model)."""
        if config.llm_provider == "hybrid":
            # Hybrid: use watsonx for extraction (better quality)
            from langchain_ibm import WatsonxLLM
            return WatsonxLLM(
                model_id=config.watsonx_model_id,
                url=config.watsonx_url,
                project_id=config.watsonx_project_id,
                apikey=config.watsonx_api_key,
                params={"max_new_tokens": 2048, "temperature": 0.1},
            )
        else:
            return ChatOllama(
                model=config.ollama_small_model,
                base_url=config.ollama_base_url,
                temperature=0.1,  # Very low for extraction accuracy
            )

    @staticmethod
    def create_embeddings(config: ContractAnalysisConfig):
        """Embeddings — always Ollama (local, free, fast)."""
        return OllamaEmbeddings(
            model=config.embedding_model,
            base_url=config.ollama_base_url,
        )


# =====================================================================
# STAGE 1: CONTRACT INGESTION & PREPROCESSING
# =====================================================================

class ContractIngestor:
    """
    Stage 1: Load contract documents, split into semantic chunks,
    and classify each chunk by clause type.
    """

    CLASSIFY_PROMPT = ChatPromptTemplate.from_messages([
        ("system", """You are a legal document classifier. Given a contract text chunk,
classify it into ONE primary clause type and extract key metadata.

Clause types: OBLIGATION, RIGHT, CONDITION, TERMINATION, INDEMNITY,
CONFIDENTIALITY, LIABILITY, PAYMENT, SLA, FORCE_MAJEURE, GOVERNING_LAW,
DISPUTE, INTELLECTUAL_PROPERTY, DATA_PROTECTION, PENALTY, RENEWAL, WARRANTY, GENERAL

Return ONLY valid JSON:
{{
  "clause_type": "one of the types above",
  "summary": "1-sentence summary of this section",
  "key_terms": ["list", "of", "key", "legal", "terms"],
  "has_deadline": true/false,
  "has_monetary_value": true/false,
  "parties_mentioned": ["Party A", "Party B"]
}}"""),
        ("human", "Classify this contract section:\n\n{text}"),
    ])

    def __init__(self, config: ContractAnalysisConfig):
        self.config = config
        self.splitter = SimpleTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        self.llm = LLMFactory.create_extraction_llm(config)
        self.parser = JsonOutputParser()

    def ingest(self, file_path: str) -> List[Dict]:
        """Load, chunk, and classify contract document."""
        from langchain_core.documents import Document
        
        # Load document using docling (no torch dependency)
        if file_path.endswith((".pdf", ".docx", ".doc")):
            converter = DocumentConverter()
            result = converter.convert(file_path)
            text = result.document.export_to_markdown()
        else:
            # Plain text file
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        
        # Create document and split
        docs = [Document(page_content=text, metadata={"source": file_path})]
        chunks = self.splitter.split_documents(docs)
        print(f"[Stage 1] Loaded {len(chunks)} chunks from {file_path}")

        # Classify each chunk
        classified_chunks = []
        chain = self.CLASSIFY_PROMPT | self.llm | self.parser

        for i, chunk in enumerate(chunks):
            try:
                metadata = chain.invoke({"text": chunk.page_content})
                classified_chunks.append({
                    "id": f"chunk_{i:03d}",
                    "text": chunk.page_content,
                    "clause_type": metadata.get("clause_type", "GENERAL"),
                    "summary": metadata.get("summary", ""),
                    "key_terms": metadata.get("key_terms", []),
                    "has_deadline": metadata.get("has_deadline", False),
                    "has_monetary_value": metadata.get("has_monetary_value", False),
                    "parties_mentioned": metadata.get("parties_mentioned", []),
                    "page": chunk.metadata.get("page", 0),
                })
            except Exception as e:
                classified_chunks.append({
                    "id": f"chunk_{i:03d}",
                    "text": chunk.page_content,
                    "clause_type": "GENERAL",
                    "summary": "",
                    "key_terms": [],
                    "has_deadline": False,
                    "has_monetary_value": False,
                    "parties_mentioned": [],
                    "page": chunk.metadata.get("page", 0),
                })

        # Print classification summary
        type_counts = {}
        for c in classified_chunks:
            t = c["clause_type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        print(f"[Stage 1] Clause types: {json.dumps(type_counts, indent=2)}")

        return classified_chunks


# =====================================================================
# STAGE 2: CONTRACT KNOWLEDGE GRAPH
# =====================================================================

class ContractGraphBuilder:
    """
    Stage 2: Extract entities & relationships from contract,
    build a structured knowledge graph in Neo4j.
    """

    EXTRACT_PROMPT = ChatPromptTemplate.from_messages([
        ("system", """You are an expert contract analyst extracting structured data.
Given a contract section, extract ALL entities and their relationships.

Entity types:
- PARTY: companies, individuals, departments involved
- CLAUSE: specific contract clauses with reference numbers
- OBLIGATION: things a party must do
- RIGHT: things a party may do
- AMOUNT: monetary values, fees, penalties
- DATE: deadlines, effective dates, renewal dates
- JURISDICTION: governing law, courts, regulators
- ASSET: intellectual property, data, deliverables, systems
- CONDITION: preconditions, triggers, thresholds
- SLA_METRIC: uptime %, response time, performance KPIs

Relationship types:
- OBLIGATED_TO: party has obligation
- ENTITLED_TO: party has right
- PAYS: payment relationship
- GOVERNED_BY: jurisdiction/law
- TERMINATES_IF: termination trigger
- INDEMNIFIES: indemnification relationship
- DELIVERS: deliverable relationship
- OWNS_IP: intellectual property ownership
- MUST_COMPLY: regulatory compliance
- PENALIZED_IF: penalty trigger
- RENEWS_ON: renewal condition
- DEPENDS_ON: dependency between clauses
- LIMITS_LIABILITY: liability cap relationship

Return ONLY valid JSON:
{{
  "entities": [
    {{"name": "...", "type": "PARTY|CLAUSE|OBLIGATION|...", "description": "..."}}
  ],
  "relationships": [
    {{"source": "entity_name", "target": "entity_name", "type": "relation_type", "description": "...", "conditions": "any conditions"}}
  ]
}}"""),
        ("human", """Extract entities and relationships from this contract section:

Clause Type: {clause_type}
Section Summary: {summary}

Text:
{text}"""),
    ])

    def __init__(self, config: ContractAnalysisConfig):
        self.config = config
        self.llm = LLMFactory.create_extraction_llm(config)
        self.embeddings = LLMFactory.create_embeddings(config)
        self.graph = Neo4jGraph(
            url=config.neo4j_url,
            username=config.neo4j_username,
            password=config.neo4j_password,
        )
        self.parser = JsonOutputParser()

    def build_graph(self, classified_chunks: List[Dict]) -> Dict:
        """Build full contract knowledge graph."""
        all_entities = {}
        all_relationships = []

        print(f"[Stage 2] Extracting contract entities from {len(classified_chunks)} chunks...")

        chain = self.EXTRACT_PROMPT | self.llm | self.parser

        for i, chunk in enumerate(classified_chunks):
            print(f"  Chunk {i+1}/{len(classified_chunks)} ({chunk['clause_type']})...")
            try:
                result = chain.invoke({
                    "text": chunk["text"],
                    "clause_type": chunk["clause_type"],
                    "summary": chunk.get("summary", ""),
                })

                for ent in result.get("entities", []):
                    key = ent["name"].lower().strip()
                    if key not in all_entities:
                        all_entities[key] = ContractEntity(
                            id=str(uuid.uuid4())[:8],
                            name=ent["name"],
                            entity_type=ent.get("type", "GENERAL"),
                            description=ent.get("description", ""),
                            source_chunk=chunk["id"],
                        )

                for rel in result.get("relationships", []):
                    all_relationships.append(ContractRelationship(
                        source=rel["source"],
                        target=rel["target"],
                        relation_type=rel.get("type", "RELATED_TO"),
                        description=rel.get("description", ""),
                        conditions=rel.get("conditions", ""),
                    ))

            except Exception as e:
                print(f"    [WARN] Extraction failed: {e}")

        # Deduplicate
        seen = set()
        unique_rels = []
        for r in all_relationships:
            key = (r.source.lower(), r.target.lower(), r.relation_type)
            if key not in seen:
                seen.add(key)
                unique_rels.append(r)

        # Persist to Neo4j
        self._persist_to_neo4j(list(all_entities.values()), unique_rels)

        # Create vector index
        self._create_vector_index(classified_chunks)

        print(f"[Stage 2] Contract graph: {len(all_entities)} entities, {len(unique_rels)} relationships")

        return {
            "entities": list(all_entities.values()),
            "relationships": unique_rels,
        }

    def _persist_to_neo4j(self, entities: List[ContractEntity], relationships: List[ContractRelationship]):
        """Write contract graph to Neo4j."""
        self.graph.query("MATCH (n) DETACH DELETE n")

        for ent in entities:
            self.graph.query(
                f"""
                CREATE (e:{ent.entity_type} {{
                    name: $name,
                    description: $description,
                    entity_id: $entity_id,
                    source_chunk: $source_chunk
                }})
                """,
                params={
                    "name": ent.name,
                    "description": ent.description,
                    "entity_id": ent.id,
                    "source_chunk": ent.source_chunk,
                },
            )

        for rel in relationships:
            self.graph.query(
                f"""
                MATCH (a {{name: $source}})
                MATCH (b {{name: $target}})
                CREATE (a)-[r:{rel.relation_type} {{
                    description: $description,
                    conditions: $conditions
                }}]->(b)
                """,
                params={
                    "source": rel.source,
                    "target": rel.target,
                    "description": rel.description,
                    "conditions": rel.conditions,
                },
            )

    def _create_vector_index(self, chunks: List[Dict]):
        """Create vector index for semantic contract search."""
        texts = [c["text"] for c in chunks]
        metadatas = [{"clause_type": c["clause_type"], "chunk_id": c["id"]} for c in chunks]

        Neo4jVector.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
            url=self.config.neo4j_url,
            username=self.config.neo4j_username,
            password=self.config.neo4j_password,
            index_name="contract_vectors",
            node_label="ContractChunk",
            text_node_property="text",
            embedding_node_property="embedding",
        )
        print("[Stage 2] Vector index created")

    def query_graph(self, question: str) -> str:
        """Natural language query over the contract graph."""
        chain = GraphCypherQAChain.from_llm(
            llm=LLMFactory.create_main_llm(self.config),
            graph=self.graph,
            verbose=False,
        )
        return chain.invoke({"query": question})


# =====================================================================
# STAGE 3: ANALYST AGENT GENERATION
# =====================================================================

class AnalystAgentFactory:
    """
    Stage 3: Generate specialized analyst agents.
    Instead of MiroFish's random personas, these are domain experts
    who each review the contract from a different angle.
    """

    # Pre-defined expert roles (can also be LLM-generated)
    DEFAULT_AGENTS = [
        {
            "name": "Legal Counsel",
            "role": "Senior Legal Advisor",
            "expertise": "Contract law, liability, indemnification, dispute resolution",
            "review_focus": "Legal enforceability, ambiguous clauses, missing protections, jurisdictional risks",
            "perspective": "Protecting the client from legal exposure",
        },
        {
            "name": "Financial Analyst",
            "role": "Financial Risk Analyst",
            "expertise": "Payment terms, penalties, cost structures, financial exposure",
            "review_focus": "Hidden costs, unfavorable payment terms, penalty clauses, financial risk exposure",
            "perspective": "Minimizing financial risk and optimizing cost terms",
        },
        {
            "name": "Compliance Officer",
            "role": "Regulatory Compliance Specialist",
            "expertise": "OJK regulations, data protection, banking compliance, UU ITE",
            "review_focus": "Regulatory compliance gaps, data protection violations, reporting obligations",
            "perspective": "Ensuring full regulatory compliance",
        },
        {
            "name": "IT Security Reviewer",
            "role": "Information Security & Data Protection Analyst",
            "expertise": "Data handling, cybersecurity clauses, SLA, system access, API security",
            "review_focus": "Data protection gaps, insufficient SLAs, security requirements, breach notification",
            "perspective": "Protecting data assets and system integrity",
        },
        {
            "name": "Commercial Strategist",
            "role": "Business Strategy Advisor",
            "expertise": "Negotiation leverage, market terms, vendor lock-in, exit strategies",
            "review_focus": "Unfavorable commercial terms, lock-in risks, renewal traps, competitive benchmarking",
            "perspective": "Maximizing business value and negotiation position",
        },
        {
            "name": "Operations Manager",
            "role": "Operational Delivery Specialist",
            "expertise": "SLAs, deliverables, timelines, resource commitments, escalation procedures",
            "review_focus": "Unrealistic timelines, vague deliverables, missing escalation paths, resource gaps",
            "perspective": "Ensuring operational feasibility and delivery success",
        },
        {
            "name": "IP Specialist",
            "role": "Intellectual Property Advisor",
            "expertise": "IP ownership, licensing, work-for-hire, technology transfer, open source",
            "review_focus": "IP ownership ambiguity, unfavorable licensing terms, technology transfer risks",
            "perspective": "Protecting intellectual property rights",
        },
    ]

    def __init__(self, config: ContractAnalysisConfig):
        self.config = config
        self.llm = LLMFactory.create_main_llm(config)

    def create_agents(self, graph_data: Dict) -> List[AnalystAgent]:
        """Create analyst agents based on contract content."""
        agents = []

        # Use pre-defined experts
        for agent_def in self.DEFAULT_AGENTS:
            agents.append(AnalystAgent(
                id=str(uuid.uuid4())[:8],
                name=agent_def["name"],
                role=agent_def["role"],
                expertise=agent_def["expertise"],
                review_focus=agent_def["review_focus"],
                perspective=agent_def["perspective"],
            ))

        # Optionally generate additional domain-specific agents based on KG
        entity_types = set(e.entity_type for e in graph_data["entities"])
        if "SLA_METRIC" in entity_types and not any(a.name == "SLA Auditor" for a in agents):
            agents.append(AnalystAgent(
                id=str(uuid.uuid4())[:8],
                name="SLA Auditor",
                role="SLA Performance Analyst",
                expertise="Service level agreements, uptime metrics, penalty calculation",
                review_focus="SLA achievability, measurement methodology, penalty fairness",
                perspective="Ensuring SLAs are measurable and achievable",
            ))

        print(f"[Stage 3] Created {len(agents)} analyst agents: {[a.name for a in agents]}")
        return agents


# =====================================================================
# STAGE 4: MULTI-AGENT CONTRACT REVIEW
# =====================================================================

class ContractReviewEngine:
    """
    Stage 4: Each analyst agent reviews relevant contract sections
    and produces risk findings. Agents can also debate each other's
    findings for cross-validation.
    """

    REVIEW_PROMPT = ChatPromptTemplate.from_messages([
        ("system", """You are {agent_name}, a {agent_role}.

Your expertise: {expertise}
Your focus: {review_focus}
Your perspective: {perspective}

Jurisdiction: {jurisdiction}
Industry: {industry}
Applicable regulations: {regulations}

You are reviewing a contract section. Analyze it thoroughly from your
domain perspective and identify ALL risks, issues, and concerns.

For each finding, assess:
- Risk level: CRITICAL (deal-breaker), HIGH (needs change before signing),
  MEDIUM (negotiate if possible), LOW (acceptable but note), INFO (observation)
- Confidence: 0.0-1.0 in your assessment

Return ONLY valid JSON:
{{
  "findings": [
    {{
      "clause_ref": "reference to the clause/section",
      "risk_level": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
      "category": "e.g. Liability, Payment, Compliance, SLA, IP, Data, Termination",
      "title": "short title",
      "description": "detailed explanation of the risk/issue",
      "recommendation": "specific actionable recommendation",
      "confidence": 0.0-1.0
    }}
  ],
  "overall_assessment": "1-2 sentence summary from your perspective"
}}

Be thorough but precise. Flag REAL issues, not theoretical ones.
Consider {jurisdiction} law and {industry} industry standards."""),
        ("human", """Review this contract section:

Clause Type: {clause_type}
Section: {text}

Knowledge Graph Context (related entities):
{graph_context}"""),
    ])

    DEBATE_PROMPT = ChatPromptTemplate.from_messages([
        ("system", """You are {agent_name}, a {agent_role}.
Another analyst ({other_agent}) made this finding about the contract:

Finding: {finding_title}
Risk Level: {finding_risk}
Description: {finding_description}
Recommendation: {finding_recommendation}

Do you agree, disagree, or want to add nuance? Consider your own expertise.

Return ONLY valid JSON:
{{
  "agreement": "agree|disagree|partial",
  "reasoning": "your perspective on this finding",
  "adjusted_risk": "same or different risk level",
  "additional_insight": "any additional context from your expertise"
}}"""),
        ("human", "Evaluate this finding from your perspective."),
    ])

    def __init__(self, config: ContractAnalysisConfig):
        self.config = config
        self.llm = LLMFactory.create_main_llm(config)
        self.parser = JsonOutputParser()

    def review(
        self,
        agents: List[AnalystAgent],
        classified_chunks: List[Dict],
        graph_data: Dict,
    ) -> List[AnalystAgent]:
        """Run all agents through relevant contract sections."""
        print(f"[Stage 4] Starting multi-agent review...")

        # Build graph context string
        graph_context = self._build_graph_context(graph_data)

        for agent in agents:
            print(f"  Agent: {agent.name} ({agent.role})...")

            # Filter chunks relevant to this agent's focus
            relevant_chunks = self._filter_relevant_chunks(agent, classified_chunks)

            chain = self.REVIEW_PROMPT | self.llm | self.parser

            for chunk in relevant_chunks:
                try:
                    result = chain.invoke({
                        "agent_name": agent.name,
                        "agent_role": agent.role,
                        "expertise": agent.expertise,
                        "review_focus": agent.review_focus,
                        "perspective": agent.perspective,
                        "jurisdiction": self.config.jurisdiction,
                        "industry": self.config.industry,
                        "regulations": ", ".join(self.config.regulatory_frameworks),
                        "clause_type": chunk["clause_type"],
                        "text": chunk["text"],
                        "graph_context": graph_context,
                    })

                    for finding in result.get("findings", []):
                        agent.findings.append(RiskFinding(
                            id=str(uuid.uuid4())[:8],
                            clause_ref=finding.get("clause_ref", chunk["id"]),
                            risk_level=RiskLevel(finding.get("risk_level", "MEDIUM")),
                            category=finding.get("category", "General"),
                            title=finding.get("title", ""),
                            description=finding.get("description", ""),
                            recommendation=finding.get("recommendation", ""),
                            agent_name=agent.name,
                            confidence=finding.get("confidence", 0.5),
                        ))

                except Exception as e:
                    print(f"    [WARN] Review failed for {agent.name}: {e}")

            print(f"    → {len(agent.findings)} findings")

        # Cross-validation debate (optional, for thorough mode)
        if self.config.analysis_depth == "thorough":
            self._cross_validate(agents)

        total = sum(len(a.findings) for a in agents)
        print(f"[Stage 4] Review complete: {total} total findings")
        return agents

    def _filter_relevant_chunks(self, agent: AnalystAgent, chunks: List[Dict]) -> List[Dict]:
        """Filter chunks relevant to an agent's expertise."""
        relevance_map = {
            "Legal Counsel": ["OBLIGATION", "RIGHT", "TERMINATION", "INDEMNITY",
                              "LIABILITY", "DISPUTE", "GOVERNING_LAW", "WARRANTY"],
            "Financial Analyst": ["PAYMENT", "PENALTY", "SLA", "LIABILITY", "INDEMNITY"],
            "Compliance Officer": ["DATA_PROTECTION", "GOVERNING_LAW", "OBLIGATION",
                                   "CONFIDENTIALITY"],
            "IT Security Reviewer": ["DATA_PROTECTION", "SLA", "CONFIDENTIALITY",
                                     "INTELLECTUAL_PROPERTY"],
            "Commercial Strategist": ["TERMINATION", "RENEWAL", "PAYMENT", "PENALTY",
                                      "FORCE_MAJEURE"],
            "Operations Manager": ["SLA", "OBLIGATION", "PAYMENT", "FORCE_MAJEURE",
                                   "CONDITION"],
            "IP Specialist": ["INTELLECTUAL_PROPERTY", "CONFIDENTIALITY", "RIGHT",
                              "OBLIGATION"],
            "SLA Auditor": ["SLA", "PENALTY", "OBLIGATION", "CONDITION"],
        }

        relevant_types = relevance_map.get(agent.name, [])

        if not relevant_types:
            return chunks  # Review all if no specific mapping

        # Always include GENERAL chunks too
        return [c for c in chunks if c["clause_type"] in relevant_types or c["clause_type"] == "GENERAL"]

    def _build_graph_context(self, graph_data: Dict) -> str:
        """Build a summary of the knowledge graph for context."""
        entities = [f"{e.name} ({e.entity_type}): {e.description}"
                    for e in graph_data["entities"][:30]]
        rels = [f"{r.source} →[{r.relation_type}]→ {r.target}"
                for r in graph_data["relationships"][:20]]
        return f"Entities:\n" + "\n".join(entities) + f"\n\nRelationships:\n" + "\n".join(rels)

    def _cross_validate(self, agents: List[AnalystAgent]):
        """Agents debate each other's critical/high findings."""
        print("  Running cross-validation debate...")
        critical_findings = []
        for agent in agents:
            for f in agent.findings:
                if f.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
                    critical_findings.append((agent, f))

        chain = self.DEBATE_PROMPT | self.llm | self.parser

        for orig_agent, finding in critical_findings[:10]:  # Cap at 10 debates
            # Pick a different agent to cross-validate
            other_agents = [a for a in agents if a.id != orig_agent.id]
            if not other_agents:
                continue
            reviewer = other_agents[0]

            try:
                result = chain.invoke({
                    "agent_name": reviewer.name,
                    "agent_role": reviewer.role,
                    "other_agent": orig_agent.name,
                    "finding_title": finding.title,
                    "finding_risk": finding.risk_level.value,
                    "finding_description": finding.description,
                    "finding_recommendation": finding.recommendation,
                })

                # Adjust confidence based on cross-validation
                if result.get("agreement") == "agree":
                    finding.confidence = min(1.0, finding.confidence + 0.15)
                elif result.get("agreement") == "disagree":
                    finding.confidence = max(0.1, finding.confidence - 0.2)

            except Exception:
                pass


# =====================================================================
# STAGE 5: REPORT GENERATION
# =====================================================================

class ContractReportGenerator:
    """
    Stage 5: Generate comprehensive contract analysis report.
    Aggregates all agent findings, cross-references with KG,
    and produces an executive-ready report.
    """

    REPORT_PROMPT = ChatPromptTemplate.from_messages([
        ("system", """You are a senior contract review lead producing a final analysis report.
You have findings from multiple domain expert analysts.

Produce a comprehensive report with these sections:

1. EXECUTIVE SUMMARY
   - Contract overview (parties, purpose, value, duration)
   - Overall risk assessment (RED/AMBER/GREEN)
   - Top 3 critical issues requiring immediate attention
   - Signing recommendation (Sign/Negotiate/Reject)

2. RISK DASHBOARD
   - Count by risk level (Critical/High/Medium/Low)
   - Count by category
   - Risk heat map description

3. CRITICAL & HIGH RISK FINDINGS
   - Each finding with: title, description, clause reference,
     recommendation, which analyst flagged it, confidence

4. MEDIUM & LOW RISK FINDINGS
   - Grouped by category, more concise

5. REGULATORY COMPLIANCE CHECK
   - {jurisdiction} specific compliance status
   - {industry} regulatory alignment
   - Gaps requiring attention

6. NEGOTIATION RECOMMENDATIONS
   - Prioritized list of clauses to renegotiate
   - Suggested alternative language where applicable
   - Leverage points and trade-offs

7. MISSING CLAUSES
   - Standard clauses that are absent from this contract
   - Recommended additions

8. APPENDIX
   - Full entity map summary
   - Analyst panel and their perspectives

Be precise, actionable, and data-driven. Use the actual findings provided."""),
        ("human", """Generate the contract analysis report.

Contract Knowledge Graph:
{graph_summary}

Analyst Findings:
{findings_summary}

Configuration:
- Jurisdiction: {jurisdiction}
- Industry: {industry}
- Regulations: {regulations}
- Analysis depth: {depth}"""),
    ])

    def __init__(self, config: ContractAnalysisConfig):
        self.config = config
        self.llm = LLMFactory.create_main_llm(config)

    def generate(
        self,
        graph_data: Dict,
        agents: List[AnalystAgent],
    ) -> str:
        """Generate the final report."""
        print("[Stage 5] Generating contract analysis report...")

        # Compile findings
        findings_summary = self._compile_findings(agents)
        graph_summary = self._summarize_graph(graph_data)

        chain = self.REPORT_PROMPT | self.llm | StrOutputParser()

        report = chain.invoke({
            "graph_summary": graph_summary,
            "findings_summary": findings_summary,
            "jurisdiction": self.config.jurisdiction,
            "industry": self.config.industry,
            "regulations": ", ".join(self.config.regulatory_frameworks),
            "depth": self.config.analysis_depth,
        })

        print("[Stage 5] Report generated")
        return report

    def _compile_findings(self, agents: List[AnalystAgent]) -> str:
        """Compile all findings into a structured summary."""
        lines = []
        for agent in agents:
            lines.append(f"\n### {agent.name} ({agent.role})")
            lines.append(f"Focus: {agent.review_focus}")
            lines.append(f"Findings ({len(agent.findings)}):")

            # Sort by risk level
            sorted_findings = sorted(
                agent.findings,
                key=lambda f: ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"].index(f.risk_level.value)
            )

            for f in sorted_findings:
                lines.append(
                    f"  [{f.risk_level.value}] {f.title} (confidence: {f.confidence:.0%})"
                    f"\n    Clause: {f.clause_ref}"
                    f"\n    Issue: {f.description}"
                    f"\n    Recommendation: {f.recommendation}"
                )

        return "\n".join(lines)

    def _summarize_graph(self, graph_data: Dict) -> str:
        entities = [f"- {e.name} ({e.entity_type}): {e.description}"
                    for e in graph_data["entities"][:40]]
        rels = [f"- {r.source} →[{r.relation_type}]→ {r.target}: {r.description}"
                for r in graph_data["relationships"][:25]]
        return f"ENTITIES:\n" + "\n".join(entities) + f"\n\nRELATIONSHIPS:\n" + "\n".join(rels)


# =====================================================================
# ORCHESTRATOR — Full Pipeline
# =====================================================================

class ContractAnalysisPipeline:
    """
    Full contract analysis pipeline orchestrator.

    Usage:
        config = ContractAnalysisConfig(llm_provider="ollama")
        pipeline = ContractAnalysisPipeline(config)
        report = pipeline.analyze("contract.pdf")
    """

    def __init__(self, config: ContractAnalysisConfig = None):
        self.config = config or ContractAnalysisConfig()

        # Initialize stages
        self.ingestor = ContractIngestor(self.config)
        self.graph_builder = ContractGraphBuilder(self.config)
        self.agent_factory = AnalystAgentFactory(self.config)
        self.review_engine = ContractReviewEngine(self.config)
        self.report_generator = ContractReportGenerator(self.config)

        # State
        self.classified_chunks: List[Dict] = []
        self.graph_data: Dict = {}
        self.agents: List[AnalystAgent] = []

    def analyze(self, file_path: str) -> str:
        """Run full contract analysis pipeline."""
        print("=" * 60)
        print("  Contract Analysis AI")
        print(f"  Provider: {self.config.llm_provider}")
        print(f"  Jurisdiction: {self.config.jurisdiction}")
        print(f"  Industry: {self.config.industry}")
        print("=" * 60)

        # Stage 1: Ingest & classify
        self.classified_chunks = self.ingestor.ingest(file_path)

        # Stage 2: Build knowledge graph
        self.graph_data = self.graph_builder.build_graph(self.classified_chunks)

        # Stage 3: Create analyst agents
        self.agents = self.agent_factory.create_agents(self.graph_data)

        # Stage 4: Multi-agent review
        self.agents = self.review_engine.review(
            self.agents, self.classified_chunks, self.graph_data
        )

        # Stage 5: Generate report
        report = self.report_generator.generate(self.graph_data, self.agents)

        print("=" * 60)
        print("  Analysis Complete!")
        print("=" * 60)
        return report

    def query_contract(self, question: str) -> str:
        """Ask a question about the contract using the knowledge graph."""
        return self.graph_builder.query_graph(question)

    def get_risk_summary(self) -> Dict:
        """Get aggregated risk statistics."""
        all_findings = []
        for agent in self.agents:
            all_findings.extend(agent.findings)

        by_level = {}
        by_category = {}
        by_agent = {}

        for f in all_findings:
            by_level[f.risk_level.value] = by_level.get(f.risk_level.value, 0) + 1
            by_category[f.category] = by_category.get(f.category, 0) + 1
            by_agent[f.agent_name] = by_agent.get(f.agent_name, 0) + 1

        return {
            "total_findings": len(all_findings),
            "by_risk_level": by_level,
            "by_category": by_category,
            "by_agent": by_agent,
            "critical_count": by_level.get("CRITICAL", 0),
            "high_count": by_level.get("HIGH", 0),
        }

    def export_findings_json(self, output_path: str = "findings.json"):
        """Export all findings as structured JSON."""
        findings = []
        for agent in self.agents:
            for f in agent.findings:
                findings.append({
                    "id": f.id,
                    "agent": f.agent_name,
                    "clause_ref": f.clause_ref,
                    "risk_level": f.risk_level.value,
                    "category": f.category,
                    "title": f.title,
                    "description": f.description,
                    "recommendation": f.recommendation,
                    "confidence": f.confidence,
                })

        with open(output_path, "w") as fp:
            json.dump(findings, fp, indent=2)

        print(f"Exported {len(findings)} findings to {output_path}")


# =====================================================================
# MAIN — Example Usage
# =====================================================================

if __name__ == "__main__":

    # ── Option A: Fully Local (Ollama) ──
    config = ContractAnalysisConfig(
        llm_provider="ollama",
        ollama_model="qwen3.5:latest",
        ollama_small_model="qwen3.5:latest",
        jurisdiction="Indonesia",
        industry="Banking",
        analysis_depth="thorough",
    )

    # ── Option B: IBM watsonx.ai ──
    # config = ContractAnalysisConfig(
    #     llm_provider="watsonx",
    #     watsonx_model_id="ibm/granite-3-8b-instruct",
    #     watsonx_project_id="YOUR_PROJECT_ID",
    #     watsonx_api_key="YOUR_API_KEY",
    #     jurisdiction="Indonesia",
    #     industry="Banking",
    #     analysis_depth="thorough",
    # )

    # ── Option C: Hybrid (Ollama embeddings + watsonx reasoning) ──
    # config = ContractAnalysisConfig(
    #     llm_provider="hybrid",
    #     ollama_model="qwen2.5:7b",            # local fallback
    #     watsonx_model_id="ibm/granite-3-8b-instruct",
    #     watsonx_project_id="YOUR_PROJECT_ID",
    #     watsonx_api_key="YOUR_API_KEY",
    #     jurisdiction="Indonesia",
    #     industry="Banking",
    #     analysis_depth="thorough",
    # )

    pipeline = ContractAnalysisPipeline(config)

    # Analyze a contract
    report = pipeline.analyze("sample_contract.txt")
    print("\n" + report)

    # Get risk summary
    summary = pipeline.get_risk_summary()
    print(f"\nRisk Summary: {json.dumps(summary, indent=2)}")

    # Export findings
    pipeline.export_findings_json("contract_findings.json")

    # Query the contract knowledge graph
    # answer = pipeline.query_contract("What are the termination conditions?")
    # print(answer)
