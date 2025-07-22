"""
Minimal Test Script: LlamaIndex → LangGraph → Neo4j KG Pipeline

This script tests the end-to-end pipeline without going through the faculty workflow:
1. Get data from course_docs_ostep_2025 index
2. Run LangGraph agents on one chunk
3. Insert LO node into Neo4j
4. Verify the complete flow works

Usage: python test_llamaindex_langgraph_pipeline.py
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_llamaindex_data_retrieval():
    """Test 1: Retrieve data from LlamaIndex Elasticsearch index."""
    logger.info("🧪 Test 1: Retrieving data from LlamaIndex Elasticsearch index")
    
    try:
        from utils.llamaindex_content_processor import LlamaIndexContentProcessor
        
        processor = LlamaIndexContentProcessor(
            index_name="course_docs_ostep_2025"
        )
        
        # Get index stats
        stats = processor.get_index_stats()
        logger.info(f"📊 Index stats: {stats}")
        
        # Get a few chunks
        chunks = processor.query_content("operating systems", top_k=3)
        logger.info(f"📄 Retrieved {len(chunks)} chunks from LlamaIndex")
        
        if chunks:
            sample_chunk = chunks[0]
            logger.info(f"📝 Sample chunk content (first 200 chars): {sample_chunk['content'][:200]}...")
            logger.info(f"🏷️ Sample chunk metadata: {sample_chunk['metadata']}")
            return chunks
        else:
            logger.error("❌ No chunks retrieved from LlamaIndex")
            return None
            
    except Exception as e:
        logger.error(f"❌ LlamaIndex data retrieval failed: {e}")
        return None

def test_langgraph_agents(chunks):
    """Test 2: Run LangGraph agents on chunk data."""
    logger.info("🧪 Test 2: Running LangGraph agents on chunk data")
    
    if not chunks:
        logger.error("❌ No chunks provided for LangGraph testing")
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
        
        logger.info(f"🔍 Testing with chunk: {chunk_content[:100]}...")
        
        # Create initial state
        initial_state = GraphState(
            messages=[HumanMessage(content=f"Analyze this content and extract key concepts: {chunk_content}")]
        )
        
        # Run researcher agent
        logger.info("🔍 Running Researcher Agent...")
        researcher_result = researcher_agent.invoke(initial_state)
        logger.info(f"✅ Researcher completed. Messages: {len(researcher_result.messages)}")
        
        # Run LO generator agent
        logger.info("📝 Running LO Generator Agent...")
        lo_result = lo_generator_agent.invoke(researcher_result)
        logger.info(f"✅ LO Generator completed. Messages: {len(lo_result.messages)}")
        
        # Extract the generated LO
        if lo_result.messages:
            last_message = lo_result.messages[-1]
            generated_lo = last_message.content
            logger.info(f"🎯 Generated LO: {generated_lo[:200]}...")
            return generated_lo
        else:
            logger.error("❌ No LO generated")
            return None
            
    except Exception as e:
        logger.error(f"❌ LangGraph agents test failed: {e}")
        return None

def test_neo4j_insertion(learning_objective, chunk_metadata):
    """Test 3: Insert LO into Neo4j Knowledge Graph."""
    logger.info("🧪 Test 3: Inserting LO into Neo4j Knowledge Graph")
    
    try:
        from graph.config import NEO4J_COURSE_MAPPER_URI, NEO4J_COURSE_MAPPER_AUTH
        from neo4j import GraphDatabase
        
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
                logger.info(f"✅ LO node created successfully: {lo_id}")
                logger.info(f"📊 Node properties: {dict(node['lo'])}")
                return True
            else:
                logger.error("❌ LO node creation failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Neo4j insertion failed: {e}")
        return False

def main():
    """Main test function."""
    logger.info("🚀 Starting LlamaIndex → LangGraph → Neo4j Pipeline Test")
    logger.info("=" * 60)
    
    # Test 1: LlamaIndex data retrieval
    chunks = test_llamaindex_data_retrieval()
    if not chunks:
        logger.error("❌ Test 1 failed. Stopping.")
        return False
    
    # Test 2: LangGraph agents
    learning_objective = test_langgraph_agents(chunks)
    if not learning_objective:
        logger.error("❌ Test 2 failed. Stopping.")
        return False
    
    # Test 3: Neo4j insertion
    chunk_metadata = chunks[0]['metadata']
    success = test_neo4j_insertion(learning_objective, chunk_metadata)
    
    if success:
        logger.info("🎉 ALL TESTS PASSED! End-to-end pipeline is working.")
        logger.info("=" * 60)
        logger.info("📋 Summary:")
        logger.info(f"   • LlamaIndex chunks: {len(chunks)}")
        logger.info(f"   • LangGraph agents: ✅ Working")
        logger.info(f"   • Neo4j insertion: ✅ Working")
        logger.info(f"   • Generated LO: {learning_objective[:100]}...")
        return True
    else:
        logger.error("❌ Test 3 failed. Pipeline incomplete.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 