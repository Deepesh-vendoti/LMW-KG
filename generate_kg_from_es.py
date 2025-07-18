#!/usr/bin/env python3
"""
Comprehensive ES to KG to PLT Pipeline

This script:
1. Loads chunks from Elasticsearch
2. Transforms them to internal KG format
3. Inserts the full KG into Neo4j
4. Optionally generates personalized learning trees

Usage:
    python generate_kg_from_es.py --course_id OSN --learner_id R000 --generate_plt
    python generate_kg_from_es.py --course_id OSN --validate_only
"""

import argparse
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph.utils.es_to_kg import transform_es_to_kg, validate_es_connection, get_es_chunk_count
from graph.db import insert_course_kg_to_neo4j, clear_plt_for_learner
from graph.plt_generator import run_plt_generator


def main():
    parser = argparse.ArgumentParser(description="Generate KG from Elasticsearch and optionally create PLT")
    parser.add_argument("--course_id", default="OSN", help="Course ID (default: OSN)")
    parser.add_argument("--learner_id", default="R000", help="Learner ID for PLT generation (default: R000)")
    parser.add_argument("--es_endpoint", default="http://localhost:9200", help="Elasticsearch endpoint")
    parser.add_argument("--index_name", default="advanced_docs_elasticsearch_v2", help="ES index name")
    parser.add_argument("--vector_store_dir", default="./elasticsearch_storage_v2", help="Vector store directory")
    parser.add_argument("--generate_plt", action="store_true", help="Generate personalized learning tree after KG insertion")
    parser.add_argument("--validate_only", action="store_true", help="Only validate ES connection and count chunks")
    parser.add_argument("--clear_existing", action="store_true", help="Clear existing KG data before insertion")
    
    args = parser.parse_args()
    
    print("🚀 ES to KG to PLT Pipeline")
    print("=" * 50)
    
    # Step 1: Validate Elasticsearch connection
    print(f"\n1️⃣ Validating Elasticsearch connection...")
    if not validate_es_connection(args.es_endpoint, args.index_name):
        print("❌ Elasticsearch validation failed. Please check your ES setup.")
        return 1
    
    # Get chunk count
    chunk_count = get_es_chunk_count(args.es_endpoint, args.index_name)
    if chunk_count == 0:
        print("❌ No chunks found in Elasticsearch. Please check your index.")
        return 1
    
    if args.validate_only:
        print("✅ Validation complete. Use --generate_plt to run the full pipeline.")
        return 0
    
    # Step 2: Transform ES chunks to KG format
    print(f"\n2️⃣ Transforming ES chunks to KG format...")
    course_graph = transform_es_to_kg(
        course_id=args.course_id,
        es_endpoint=args.es_endpoint,
        index_name=args.index_name,
        vector_store_dir=args.vector_store_dir
    )
    
    if not course_graph["learning_objectives"]:
        print("❌ No learning objectives generated. Check your ES data.")
        return 1
    
    # Step 3: Insert KG into Neo4j
    print(f"\n3️⃣ Inserting KG into Neo4j...")
    try:
        insert_course_kg_to_neo4j(course_graph, clear_existing=args.clear_existing)
        print("✅ Knowledge Graph successfully inserted into Neo4j")
    except Exception as e:
        print(f"❌ Error inserting KG into Neo4j: {str(e)}")
        return 1
    
    # Step 4: Generate PLT if requested
    if args.generate_plt:
        print(f"\n4️⃣ Generating Personalized Learning Tree for {args.learner_id}...")
        try:
            # Clear existing PLT for this learner
            clear_plt_for_learner(args.learner_id, args.course_id)
            
            # Generate PLT
            plt_result = run_plt_generator(
                learner_id=args.learner_id,
                course_id=args.course_id
            )
            
            if plt_result and "final_plt" in plt_result:
                print("✅ Personalized Learning Tree generated successfully!")
                print(f"📊 Generated {len(plt_result['final_plt']['learning_path'])} learning steps")
            else:
                print("❌ PLT generation failed or returned empty result")
                return 1
                
        except Exception as e:
            print(f"❌ Error generating PLT: {str(e)}")
            return 1
    
    print(f"\n🎉 Pipeline completed successfully!")
    print(f"📚 Course: {args.course_id}")
    print(f"📊 Learning Objectives: {len(course_graph['learning_objectives'])}")
    print(f"🧠 Knowledge Components: {sum(len(lo['kcs']) for lo in course_graph['learning_objectives'])}")
    
    if args.generate_plt:
        print(f"👤 PLT generated for learner: {args.learner_id}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 