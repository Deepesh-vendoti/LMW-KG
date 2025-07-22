"""
Step-by-Step Interactive Test: LlamaIndex → LangGraph → Neo4j Pipeline

This script runs each step separately and shows the output before proceeding.
You can see exactly what's happening at each stage.

Usage: python test_llamaindex_step_by_step.py
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def step1_llamaindex_data_retrieval():
    """Step 1: Retrieve data from LlamaIndex Elasticsearch index."""
    print("\n" + "="*60)
    print("🧪 STEP 1: LlamaIndex Data Retrieval")
    print("="*60)
    
    try:
        from utils.llamaindex_content_processor import LlamaIndexContentProcessor
        
        processor = LlamaIndexContentProcessor(
            index_name="course_docs_ostep_2025"
        )
        
        # Get index stats
        stats = processor.get_index_stats()
        print(f"📊 Index stats: {stats}")
        
        # Get chunks
        chunks = processor.query_content("operating systems", top_k=3)
        print(f"📄 Retrieved {len(chunks)} chunks from LlamaIndex")
        
        if chunks:
            print("\n📝 SAMPLE CHUNK CONTENT:")
            print("-" * 40)
            sample_chunk = chunks[0]
            print(f"Content (first 300 chars):")
            print(f"{sample_chunk['content'][:300]}...")
            print(f"\n🏷️ Metadata:")
            print(f"  • Course ID: {sample_chunk['metadata'].get('course_id', 'N/A')}")
            print(f"  • Page: {sample_chunk['metadata'].get('page_label', 'N/A')}")
            print(f"  • File: {sample_chunk['metadata'].get('file_name', 'N/A')}")
            print(f"  • Score: {sample_chunk.get('score', 'N/A')}")
            
            return chunks
        else:
            print("❌ No chunks retrieved from LlamaIndex")
            return None
            
    except Exception as e:
        print(f"❌ LlamaIndex data retrieval failed: {e}")
        return None

def step2_langgraph_agents(chunks):
    """Step 2: Run LangGraph agents on chunk data."""
    print("\n" + "="*60)
    print("🧪 STEP 2: LangGraph Agents Processing")
    print("="*60)
    
    if not chunks:
        print("❌ No chunks provided for LangGraph testing")
        return None
    
    try:
        from graph.agents import create_researcher_agent, create_lo_generator_agent
        from utils.unified_state_manager import UnifiedState
        from langchain_core.messages import HumanMessage
        
        # Create agents
        researcher_agent = create_researcher_agent()
        lo_generator_agent = create_lo_generator_agent()
        
        # Test with first chunk
        test_chunk = chunks[0]
        chunk_content = test_chunk['content'][:1000]  # Limit content for testing
        
        print(f"🔍 Processing chunk content:")
        print("-" * 40)
        print(f"{chunk_content[:200]}...")
        print(f"\n📏 Content length: {len(chunk_content)} characters")
        
        # Create initial state
        initial_state = GraphState(
            messages=[HumanMessage(content=f"Analyze this content and extract key concepts: {chunk_content}")]
        )
        
        # Run researcher agent
        print("\n🔍 Running Researcher Agent...")
        print("-" * 20)
        researcher_result = researcher_agent.invoke(initial_state)
        print(f"✅ Researcher completed. Messages: {len(researcher_result.messages)}")
        
        # Show researcher output
        if len(researcher_result.messages) > 1:
            researcher_output = researcher_result.messages[-1].content
            print(f"\n📋 Researcher Analysis (first 300 chars):")
            print(f"{researcher_output[:300]}...")
        
        # Run LO generator agent
        print("\n📝 Running LO Generator Agent...")
        print("-" * 20)
        lo_result = lo_generator_agent.invoke(researcher_result)
        print(f"✅ LO Generator completed. Messages: {len(lo_result.messages)}")
        
        # Extract the generated LO
        if lo_result.messages:
            last_message = lo_result.messages[-1]
            generated_lo = last_message.content
            print(f"\n🎯 Generated Learning Objective:")
            print("-" * 40)
            print(f"{generated_lo[:500]}...")
            print(f"\n📏 LO length: {len(generated_lo)} characters")
            return generated_lo
        else:
            print("❌ No LO generated")
            return None
            
    except Exception as e:
        print(f"❌ LangGraph agents test failed: {e}")
        return None

def step3_neo4j_insertion(learning_objective, chunk_metadata):
    """Step 3: Insert LO into Neo4j Knowledge Graph."""
    print("\n" + "="*60)
    print("🧪 STEP 3: Neo4j Knowledge Graph Insertion")
    print("="*60)
    
    try:
        from graph.config import NEO4J_COURSE_MAPPER_URI, NEO4J_COURSE_MAPPER_AUTH
        from neo4j import GraphDatabase
        
        print(f"🔗 Connecting to Neo4j: {NEO4J_COURSE_MAPPER_URI}")
        
        # Connect to Neo4j
        if NEO4J_COURSE_MAPPER_AUTH == "none":
            # No authentication
            driver = GraphDatabase.driver(NEO4J_COURSE_MAPPER_URI)
        else:
            # With authentication
            driver = GraphDatabase.driver(
                NEO4J_COURSE_MAPPER_URI,
                auth=NEO4J_COURSE_MAPPER_AUTH
            )
        
        with driver.session() as session:
            # Create LO node
            cypher_query = """
            CREATE (lo:LearningObjective {
                id: $lo_id,
                content: $content,
                course_id: $course_id,
                source_chunk: $source_chunk,
                created_at: $created_at,
                processor: $processor
            })
            RETURN lo
            """
            
            lo_id = f"LO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"📝 Creating LO node with ID: {lo_id}")
            print(f"📚 Course ID: {chunk_metadata.get('course_id', 'OSTEP_2025')}")
            print(f"📄 Source chunk: {chunk_metadata.get('chunk_id', 'unknown')}")
            
            result = session.run(
                cypher_query,
                lo_id=lo_id,
                content=learning_objective,
                course_id=chunk_metadata.get('course_id', 'OSTEP_2025'),
                source_chunk=chunk_metadata.get('chunk_id', 'unknown'),
                created_at=datetime.now().isoformat(),
                processor="llamaindex_langgraph_test"
            )
            
            # Verify insertion
            node = result.single()
            if node:
                print(f"✅ LO node created successfully!")
                print(f"📊 Node properties:")
                node_props = dict(node['lo'])
                for key, value in node_props.items():
                    if key == 'content':
                        print(f"  • {key}: {str(value)[:100]}...")
                    else:
                        print(f"  • {key}: {value}")
                return True
            else:
                print("❌ LO node creation failed")
                return False
                
    except Exception as e:
        print(f"❌ Neo4j insertion failed: {e}")
        return False

def main():
    """Main interactive test function."""
    print("🚀 Starting Step-by-Step LlamaIndex → LangGraph → Neo4j Pipeline Test")
    print("="*80)
    
    # Step 1: LlamaIndex data retrieval
    print("\n🔄 Starting Step 1...")
    chunks = step1_llamaindex_data_retrieval()
    
    if not chunks:
        print("\n❌ Step 1 failed. Stopping.")
        return False
    
    # Ask user to continue
    input("\n⏸️  Press Enter to continue to Step 2 (LangGraph Agents)...")
    
    # Step 2: LangGraph agents
    print("\n🔄 Starting Step 2...")
    learning_objective = step2_langgraph_agents(chunks)
    
    if not learning_objective:
        print("\n❌ Step 2 failed. Stopping.")
        return False
    
    # Ask user to continue
    input("\n⏸️  Press Enter to continue to Step 3 (Neo4j Insertion)...")
    
    # Step 3: Neo4j insertion
    print("\n🔄 Starting Step 3...")
    chunk_metadata = chunks[0]['metadata']
    success = step3_neo4j_insertion(learning_objective, chunk_metadata)
    
    if success:
        print("\n" + "="*80)
        print("🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("📋 Final Summary:")
        print(f"   • Step 1 (LlamaIndex): ✅ {len(chunks)} chunks retrieved")
        print(f"   • Step 2 (LangGraph): ✅ LO generated ({len(learning_objective)} chars)")
        print(f"   • Step 3 (Neo4j): ✅ LO node inserted")
        print("\n🎯 Your end-to-end pipeline is working perfectly!")
        return True
    else:
        print("\n❌ Step 3 failed. Pipeline incomplete.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 