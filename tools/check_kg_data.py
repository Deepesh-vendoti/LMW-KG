#!/usr/bin/env python3

from neo4j import GraphDatabase
import json

def check_kg_data():
    # Connect to Neo4j with no auth
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=None)
    
    with driver.session() as session:
        # Check all nodes and their labels
        print("🔍 ALL NODES IN KNOWLEDGE GRAPH:")
        print("=" * 50)
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
        for record in result:
            print(f"  {record['labels']}: {record['count']} nodes")
        
        print("\n🔍 LEARNING OBJECTIVE CONTENT:")
        print("=" * 50)
        result = session.run("MATCH (lo:LearningObjective) RETURN lo.content as content, lo.id as id")
        for record in result:
            print(f"ID: {record['id']}")
            content = record['content']
            if content:
                # Try to parse as JSON, if not, show as text
                try:
                    parsed = json.loads(content)
                    print("Content (parsed):")
                    print(json.dumps(parsed, indent=2))
                except:
                    print("Content (raw):")
                    print(content[:500] + "..." if len(content) > 500 else content)
            print()
        
        print("🔍 ALL RELATIONSHIPS:")
        print("=" * 50)
        result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
        for record in result:
            print(f"  {record['type']}: {record['count']} relationships")

if __name__ == "__main__":
    check_kg_data() 