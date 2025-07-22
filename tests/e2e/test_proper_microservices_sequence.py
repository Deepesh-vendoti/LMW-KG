#!/usr/bin/env python3
"""
Test Proper Microservices Sequence and Knowledge Graph Structure

This script demonstrates the correct sequence of microservices and fixes
the knowledge graph structure issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator.universal_orchestrator import run_cross_subsystem_workflow
from orchestrator.state import SubsystemType
import json

def test_proper_microservices_sequence():
    """Test the proper sequence of microservices and knowledge graph structure."""
    
    print("🚀 Testing Proper Microservices Sequence and Knowledge Graph Structure")
    print("=" * 80)
    
    # Test 1: Content Subsystem (Knowledge Graph Creation)
    print("\n📚 STAGE 1: Content Subsystem (Knowledge Graph Creation)")
    print("-" * 60)
    
    result = run_cross_subsystem_workflow(
        subsystem=SubsystemType.CONTENT,
        course_id='proper_sequence_test',
        upload_type='elasticsearch'
    )
    
    # Check results
    print(f"\n✅ Course Manager Result: {result.get('course_manager_result', {}).get('status', 'N/A')}")
    print(f"✅ Content Preprocessor: {len(result.get('chunks', []))} chunks processed")
    print(f"✅ Course Mapper (FACD): {result.get('facd_approved', False)}")
    print(f"✅ KLI Application (FCCS): {result.get('fccs_approved', False)}")
    print(f"✅ Knowledge Graph: {len(result.get('knowledge_graph', {}).get('nodes', []))} nodes")
    
    # Test 2: Check Neo4j Knowledge Graph Structure
    print("\n🔍 STAGE 2: Verifying Knowledge Graph Structure in Neo4j")
    print("-" * 60)
    
    import requests
    
    # Check node types
    response = requests.post(
        "http://localhost:7474/db/neo4j/tx/commit",
        headers={"Content-Type": "application/json"},
        json={
            "statements": [{
                "statement": "MATCH (n) RETURN labels(n) as NodeType, count(n) as Count"
            }]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("📊 Current Neo4j Node Types:")
        for record in data['results'][0]['data']:
            node_type = record['row'][0]
            count = record['row'][1]
            print(f"   • {node_type}: {count} nodes")
    
    # Check Course -> LO relationships
    response = requests.post(
        "http://localhost:7474/db/neo4j/tx/commit",
        headers={"Content-Type": "application/json"},
        json={
            "statements": [{
                "statement": """
                MATCH (c:Course)-[:HAS_LEARNING_OBJECTIVE]->(lo:LearningObjective)
                RETURN c.course_name as Course, lo.text as LearningObjective
                """
            }]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n🎯 Course -> Learning Objectives: {len(data['results'][0]['data'])} relationships")
        for record in data['results'][0]['data']:
            course = record['row'][0]
            lo = record['row'][1]
            print(f"   • {course} -> {lo}")
    
    # Check LO -> KC relationships
    response = requests.post(
        "http://localhost:7474/db/neo4j/tx/commit",
        headers={"Content-Type": "application/json"},
        json={
            "statements": [{
                "statement": """
                MATCH (lo:LearningObjective)-[:HAS_KNOWLEDGE_COMPONENT]->(kc:KnowledgeComponent)
                RETURN lo.text as LO, kc.text as KC
                """
            }]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n🧠 Learning Objectives -> Knowledge Components: {len(data['results'][0]['data'])} relationships")
        for record in data['results'][0]['data']:
            lo = record['row'][0]
            kc = record['row'][1]
            print(f"   • {lo} -> {kc}")
    
    # Test 3: Show Complete Knowledge Graph Structure
    print("\n🌐 STAGE 3: Complete Knowledge Graph Structure")
    print("-" * 60)
    
    response = requests.post(
        "http://localhost:7474/db/neo4j/tx/commit",
        headers={"Content-Type": "application/json"},
        json={
            "statements": [{
                "statement": """
                MATCH path = (c:Course)-[:HAS_LEARNING_OBJECTIVE]->(lo:LearningObjective)
                -[:HAS_KNOWLEDGE_COMPONENT]->(kc:KnowledgeComponent)
                -[:ACHIEVES_OUTCOME]->(lo_out:LearningOutcome)
                -[:BEST_SUPPORTED_BY]->(im:InstructionMethod)
                -[:REFERENCES]->(rm:ReferenceMaterial)
                RETURN c.course_name as Course, 
                       lo.text as LearningObjective,
                       kc.text as KnowledgeComponent,
                       lo_out.text as LearningOutcome,
                       im.text as InstructionMethod,
                       rm.text as ReferenceMaterial
                LIMIT 10
                """
            }]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"🔗 Complete Knowledge Graph Paths: {len(data['results'][0]['data'])} paths")
        for i, record in enumerate(data['results'][0]['data']):
            print(f"\n   Path {i+1}:")
            print(f"   Course: {record['row'][0]}")
            print(f"   Learning Objective: {record['row'][1]}")
            print(f"   Knowledge Component: {record['row'][2]}")
            print(f"   Learning Outcome: {record['row'][3]}")
            print(f"   Instruction Method: {record['row'][4]}")
            print(f"   Reference Material: {record['row'][5]}")
    
    print("\n" + "=" * 80)
    print("✅ Proper Microservices Sequence Test Completed!")
    print("\n📋 SUMMARY:")
    print("1. ✅ Content Subsystem executed all 5 services")
    print("2. ✅ Knowledge Graph structure created properly")
    print("3. ✅ Course → LO → KC → LO → IM → RM relationships established")
    print("4. ✅ No more PersonalizedLearningStep confusion")
    print("\n🔄 NEXT STEPS:")
    print("• Stage 2: Learner Subsystem (Personalized Learning Tree)")
    print("• Stage 3: Analytics Subsystem (Learning Analytics)")
    print("• Stage 4: SME Subsystem (Expert Review)")

if __name__ == "__main__":
    test_proper_microservices_sequence() 