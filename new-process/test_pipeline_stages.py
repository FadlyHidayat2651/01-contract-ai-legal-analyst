#!/usr/bin/env python3
"""
Test each stage of the pipeline individually
"""

import sys
from pathlib import Path
from contract_analysis_pipeline_simplified import (
    ContractAnalysisConfig,
    ContractIngestor,
    ContractGraphBuilder,
    AnalystAgentFactory,
    ContractReviewEngine,
    ContractReportGenerator
)

def test_stage_1():
    """Test document ingestion"""
    print("\n" + "="*60)
    print("TESTING STAGE 1: Document Ingestion")
    print("="*60)
    
    config = ContractAnalysisConfig()
    ingestor = ContractIngestor(config)
    
    try:
        documents = ingestor.ingest("sample_contract.txt")
        print(f"✅ Stage 1 PASSED: Created {len(documents)} chunks")
        return documents
    except Exception as e:
        print(f"❌ Stage 1 FAILED: {e}")
        return None

def test_stage_2(documents):
    """Test knowledge graph build"""
    print("\n" + "="*60)
    print("TESTING STAGE 2: Knowledge Graph Build")
    print("="*60)
    
    if not documents:
        print("❌ Skipping - no documents from Stage 1")
        return None
    
    config = ContractAnalysisConfig()
    
    try:
        builder = ContractGraphBuilder(config)
        graph_data = builder.build_graph(documents[:2])  # Test with 2 chunks
        print(f"✅ Stage 2 PASSED: Built graph with {len(graph_data['entities'])} entities")
        return graph_data
    except Exception as e:
        print(f"❌ Stage 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_stage_3():
    """Test analyst agent generation"""
    print("\n" + "="*60)
    print("TESTING STAGE 3: Analyst Agent Generation")
    print("="*60)
    
    config = ContractAnalysisConfig()
    factory = AnalystAgentFactory(config)
    
    try:
        agents = factory.create_agents()
        print(f"✅ Stage 3 PASSED: Created {len(agents)} agents")
        return agents
    except Exception as e:
        print(f"❌ Stage 3 FAILED: {e}")
        return None

def test_stage_4(documents, graph_data, agents):
    """Test multi-agent review"""
    print("\n" + "="*60)
    print("TESTING STAGE 4: Multi-Agent Review")
    print("="*60)
    
    if not all([documents, graph_data, agents]):
        print("❌ Skipping - missing prerequisites")
        return None
    
    config = ContractAnalysisConfig()
    
    try:
        engine = ContractReviewEngine(config, agents[:2])  # Test with 2 agents
        findings = engine.review(documents[:2], graph_data)
        print(f"✅ Stage 4 PASSED: Generated {len(findings)} findings")
        return findings
    except Exception as e:
        print(f"❌ Stage 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_stage_5(findings, graph_data):
    """Test report generation"""
    print("\n" + "="*60)
    print("TESTING STAGE 5: Report Generation")
    print("="*60)
    
    if not findings:
        print("❌ Skipping - no findings from Stage 4")
        return None
    
    config = ContractAnalysisConfig()
    generator = ContractReportGenerator(config)
    
    try:
        report = generator.generate(findings, graph_data or {})
        print(f"✅ Stage 5 PASSED: Generated report with {report['summary']['total_findings']} findings")
        return report
    except Exception as e:
        print(f"❌ Stage 5 FAILED: {e}")
        return None

def main():
    """Run all stage tests"""
    print("\n" + "#"*60)
    print("# CONTRACT ANALYSIS PIPELINE - STAGE TESTING")
    print("#"*60)
    
    # Test each stage
    documents = test_stage_1()
    graph_data = test_stage_2(documents)
    agents = test_stage_3()
    findings = test_stage_4(documents, graph_data, agents)
    report = test_stage_5(findings, graph_data)
    
    # Summary
    print("\n" + "#"*60)
    print("# TEST SUMMARY")
    print("#"*60)
    print(f"Stage 1 (Ingestion):     {'✅ PASS' if documents else '❌ FAIL'}")
    print(f"Stage 2 (Graph Build):   {'✅ PASS' if graph_data else '❌ FAIL'}")
    print(f"Stage 3 (Agents):        {'✅ PASS' if agents else '❌ FAIL'}")
    print(f"Stage 4 (Review):        {'✅ PASS' if findings else '❌ FAIL'}")
    print(f"Stage 5 (Report):        {'✅ PASS' if report else '❌ FAIL'}")
    print("#"*60 + "\n")

if __name__ == "__main__":
    main()

# Made with Bob
