#!/usr/bin/env python3
"""
Knowledge Graph Viewer - Shows the structure of the generated knowledge graph
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from utils.database_connections import get_database_manager

def view_knowledge_graph():
    """Display the complete knowledge graph structure."""
    
    # Connect to Neo4j using the database manager
    db_manager = get_database_manager()
    driver = db_manager.get_neo4j_driver()
    
    try:
        with driver.session() as session:
            print("🧠 KNOWLEDGE GRAPH STRUCTURE")
            print("=" * 60)
            
            # Get all nodes with their types
            print("\n📊 NODE COUNTS BY TYPE:")
            print("-" * 30)
            result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC")
            for record in result:
                labels = record["labels"]
                count = record["count"]
                print(f"{', '.join(labels)}: {count}")
            
            # Get all relationship types
            print("\n🔗 RELATIONSHIP COUNTS BY TYPE:")
            print("-" * 30)
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC")
            for record in result:
                rel_type = record["type"]
                count = record["count"]
                print(f"{rel_type}: {count}")
            
            # Sample nodes of different types
            print("\n📌 SAMPLE NODES:")
            print("-" * 30)
            
            # Learning Objectives
            print("\nLearning Objectives (LOs):")
            result = session.run("MATCH (lo:LearningObjective) RETURN lo LIMIT 3")
            for record in result:
                lo = record["lo"]
                print(f"  - {lo.get('name', 'Unnamed LO')}: {lo.get('description', 'No description')}")
            
            # Knowledge Components
            print("\nKnowledge Components (KCs):")
            result = session.run("MATCH (kc:KnowledgeComponent) RETURN kc LIMIT 3")
            for record in result:
                kc = record["kc"]
                print(f"  - {kc.get('name', 'Unnamed KC')}: {kc.get('description', 'No description')}")
            
            # Learning Processes
            print("\nLearning Processes (LPs):")
            result = session.run("MATCH (lp:LearningProcess) RETURN lp LIMIT 3")
            for record in result:
                lp = record["lp"]
                print(f"  - {lp.get('name', 'Unnamed LP')}: {lp.get('description', 'No description')}")
            
            # Instruction Methods
            print("\nInstruction Methods (IMs):")
            result = session.run("MATCH (im:InstructionMethod) RETURN im LIMIT 3")
            for record in result:
                im = record["im"]
                print(f"  - {im.get('name', 'Unnamed IM')}: {im.get('description', 'No description')}")
            
            # Sample relationships
            print("\n🔄 SAMPLE RELATIONSHIPS:")
            print("-" * 30)
            result = session.run("""
                MATCH (a)-[r]->(b)
                RETURN labels(a)[0] as a_type, a.name as a_name, 
                       type(r) as rel_type, 
                       labels(b)[0] as b_type, b.name as b_name
                LIMIT 5
            """)
            for record in result:
                print(f"  - {record['a_type']} '{record['a_name']}' {record['rel_type']} {record['b_type']} '{record['b_name']}'")
            
            # Complete learning chains
            print("\n⛓️ COMPLETE LEARNING CHAINS:")
            print("-" * 30)
            result = session.run("""
                MATCH path = (c:Course)-[:HAS_LEARNING_OBJECTIVE]->(lo:LearningObjective)
                             -[:DECOMPOSED_INTO]->(kc:KnowledgeComponent)
                             -[:REQUIRES]->(lp:LearningProcess)
                             -[:BEST_SUPPORTED_BY]->(im:InstructionMethod)
                RETURN c.name as course, lo.name as lo, kc.name as kc, 
                       lp.name as lp, im.name as im
                LIMIT 3
            """)
            for record in result:
                print(f"Course: {record['course']}")
                print(f"  LO: {record['lo']}")
                print(f"    KC: {record['kc']}")
                print(f"      LP: {record['lp']}")
                print(f"        IM: {record['im']}")
                print()
            
            # Personalized learning trees
            print("\n🌳 PERSONALIZED LEARNING TREES:")
            print("-" * 30)
            result = session.run("""
                MATCH (l:Learner)-[:HAS_PLT]->(plt:PersonalizedLearningTree)
                RETURN l.name as learner, plt.name as plt, plt.description as description
                LIMIT 3
            """)
            for record in result:
                print(f"Learner: {record['learner']}")
                print(f"  PLT: {record['plt']}")
                print(f"  Description: {record['description']}")
                print()
            
            # Course knowledge graphs
            print("\n📚 COURSE KNOWLEDGE GRAPHS:")
            print("-" * 30)
            result = session.run("""
                MATCH (c:Course)
                OPTIONAL MATCH (c)-[:HAS_LEARNING_OBJECTIVE]->(lo:LearningObjective)
                WITH c, count(lo) as lo_count
                RETURN c.name as course, c.id as id, lo_count
                LIMIT 5
            """)
            for record in result:
                print(f"Course: {record['course']} (ID: {record['id']})")
                print(f"  Learning Objectives: {record['lo_count']}")
                print()
                
    except Exception as e:
        print(f"❌ Error accessing Neo4j: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    view_knowledge_graph() 