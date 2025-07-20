#!/usr/bin/env python3
"""
Knowledge Graph Viewer - Shows the structure of the generated knowledge graph
"""

from neo4j import GraphDatabase
from graph.config import NEO4J_URI, NEO4J_AUTH

def view_knowledge_graph():
    """Display the complete knowledge graph structure."""
    
    # Connect to Neo4j (handle no-auth case)
    if NEO4J_AUTH == "none" or NEO4J_AUTH is None:
        driver = GraphDatabase.driver(NEO4J_URI, auth=None)
    else:
        driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    
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
                print(f"🔹 {labels}: {count} nodes")
            
            # Get all relationship types
            print("\n🔗 RELATIONSHIP COUNTS BY TYPE:")
            print("-" * 30)
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC")
            for record in result:
                rel_type = record["type"]
                count = record["count"]
                print(f"🔸 {rel_type}: {count} relationships")
            
            # Show sample nodes by type
            print("\n📋 SAMPLE NODES BY TYPE:")
            print("-" * 30)
            
            # Learning Objectives
            print("\n🎯 LEARNING OBJECTIVES:")
            result = session.run("MATCH (lo:LearningObjective) RETURN lo.text as text, lo.id as id LIMIT 5")
            for record in result:
                print(f"  • {record['text']} (ID: {record['id']})")
            
            # Knowledge Components
            print("\n🧠 KNOWLEDGE COMPONENTS:")
            result = session.run("MATCH (kc:KnowledgeComponent) RETURN kc.text as text, kc.id as id LIMIT 5")
            for record in result:
                print(f"  • {record['text']} (ID: {record['id']})")
            
            # Learning Processes
            print("\n🔄 LEARNING PROCESSES:")
            result = session.run("MATCH (lp:LearningProcess) RETURN lp.type as type, lp.id as id LIMIT 5")
            for record in result:
                print(f"  • {record['type']} (ID: {record['id']})")
            
            # Instruction Methods
            print("\n📚 INSTRUCTION METHODS:")
            result = session.run("MATCH (im:InstructionMethod) RETURN im.description as desc, im.id as id LIMIT 5")
            for record in result:
                print(f"  • {record['desc']} (ID: {record['id']})")
            
            # Show relationships
            print("\n🔗 SAMPLE RELATIONSHIPS:")
            print("-" * 30)
            result = session.run("""
                MATCH (a)-[r]->(b) 
                RETURN type(r) as type, 
                       labels(a) as from_labels, 
                       labels(b) as to_labels,
                       a.text as from_text, 
                       b.text as to_text
                LIMIT 10
            """)
            for record in result:
                rel_type = record["type"]
                from_labels = record["from_labels"]
                to_labels = record["to_labels"]
                from_text = record["from_text"][:50] if record["from_text"] else "No text"
                to_text = record["to_text"][:50] if record["to_text"] else "No text"
                
                print(f"  {from_labels} --[{rel_type}]--> {to_labels}")
                print(f"    From: {from_text}...")
                print(f"    To: {to_text}...")
                print()
            
            # Show complete LO → KC → LP → IM chains
            print("\n🔄 COMPLETE LEARNING CHAINS:")
            print("-" * 30)
            result = session.run("""
                MATCH path = (lo:LearningObjective)-[:DECOMPOSED_INTO]->(kc:KnowledgeComponent)
                       -[:REQUIRES]->(lp:LearningProcess)-[:BEST_SUPPORTED_BY]->(im:InstructionMethod)
                RETURN lo.text as lo_text, kc.text as kc_text, lp.type as lp_type, im.description as im_desc
                LIMIT 5
            """)
            for i, record in enumerate(result, 1):
                print(f"Chain {i}:")
                print(f"  🎯 LO: {record['lo_text']}")
                print(f"  🧠 KC: {record['kc_text']}")
                print(f"  🔄 LP: {record['lp_type']}")
                print(f"  📚 IM: {record['im_desc']}")
                print()
            
            # Show Personalized Learning Trees if any
            print("\n🌳 PERSONALIZED LEARNING TREES:")
            print("-" * 30)
            result = session.run("MATCH (plt:PersonalizedLearningStep) RETURN plt.learner_id as learner, plt.course_id as course, count(plt) as steps LIMIT 5")
            for record in result:
                learner = record["learner"]
                course = record["course"]
                steps = record["steps"]
                print(f"  👤 Learner {learner} in Course {course}: {steps} learning steps")
            
            # Show course knowledge graphs
            print("\n📚 COURSE KNOWLEDGE GRAPHS:")
            print("-" * 30)
            result = session.run("MATCH (c:Course) RETURN c.course_id as course_id, c.title as title LIMIT 5")
            for record in result:
                course_id = record["course_id"]
                title = record["title"]
                print(f"  📖 Course {course_id}: {title}")
    
    finally:
        driver.close()

if __name__ == "__main__":
    view_knowledge_graph() 