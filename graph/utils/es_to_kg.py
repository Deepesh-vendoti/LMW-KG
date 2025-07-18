"""
Transforms course content stored in Elasticsearch chunks into a
standardized KG dictionary format expected by the Neo4j insertion pipeline.

Used when you want to avoid PDF re-chunking and directly use existing ES content.

"""

import os
from typing import Dict, List, Optional
from llama_index.core import StorageContext
from llama_index.vector_stores.elasticsearch import ElasticsearchStore


def transform_es_to_kg(course_id: str, 
                      es_endpoint: str = "http://localhost:9200",
                      index_name: str = "advanced_docs_elasticsearch_v2",
                      vector_store_dir: str = "./elasticsearch_storage_v2") -> dict:
    """
    Converts ES chunks into internal KG format:
    {
        "course_id": "OSN",
        "title": "Operating Systems & Networks",
        "learning_objectives": [
            {
                "lo_id": "LO_001",
                "text": "Understand Memory Management",
                "kcs": [
                    {
                        "kc_id": "KC_001",
                        "text": "Define Paging",
                        "instruction_methods": [],
                        "learning_process": "",
                    },
                    ...
                ]
            },
            ...
        ]
    }
    
    Args:
        course_id: The course identifier (e.g., "OSN")
        es_endpoint: Elasticsearch endpoint URL
        index_name: Elasticsearch index name
        vector_store_dir: Directory containing the vector store data
        
    Returns:
        dict: Course graph in the expected KG format
    """
    print(f"🔄 Loading ES chunks from {es_endpoint}/{index_name}")
    
    try:
        # Initialize Elasticsearch store
        vector_store = ElasticsearchStore(
            index_name=index_name,
            es_url=es_endpoint
        )

        # Load storage context
        storage_context = StorageContext.from_defaults(
            persist_dir=vector_store_dir,
            vector_store=vector_store
        )

        # Compose course KG structure
        course_graph = {
            "course_id": course_id,
            "title": f"{course_id} (from ES)",
            "learning_objectives": []
        }

        # Get all documents from storage
        docs = list(storage_context.docstore.docs.items())
        print(f"📚 Found {len(docs)} chunks in Elasticsearch")
        
        if not docs:
            print("⚠️  No documents found in Elasticsearch. Check your ES setup.")
            return course_graph

        # Group chunks by section to create learning objectives
        section_groups = {}
        
        for idx, (node_id, node) in enumerate(docs):
            section_title = node.metadata.get("section", f"Section {idx+1}")
            content = node.get_content().strip()
            
            if section_title not in section_groups:
                section_groups[section_title] = []
            
            section_groups[section_title].append({
                "content": content,
                "node_id": node_id,
                "metadata": node.metadata
            })

        # Convert sections to learning objectives
        for lo_idx, (section_title, chunks) in enumerate(section_groups.items()):
            lo = {
                "lo_id": f"LO_{lo_idx+1:03}",
                "text": section_title,
                "kcs": []
            }
            
            # Convert chunks to knowledge components
            for kc_idx, chunk in enumerate(chunks):
                kc = {
                    "kc_id": f"KC_{lo_idx+1:03}_{kc_idx+1:03}",
                    "text": chunk["content"],
                    "instruction_methods": [],
                    "learning_process": "",
                }
                lo["kcs"].append(kc)
            
            course_graph["learning_objectives"].append(lo)

        print(f"✅ Transformed {len(docs)} chunks into {len(course_graph['learning_objectives'])} learning objectives")
        print(f"📊 Total knowledge components: {sum(len(lo['kcs']) for lo in course_graph['learning_objectives'])}")
        
        return course_graph
        
    except Exception as e:
        print(f"❌ Error loading from Elasticsearch: {str(e)}")
        print("💡 Make sure Elasticsearch is running and the index exists")
        return {
            "course_id": course_id,
            "title": f"{course_id} (Error loading from ES)",
            "learning_objectives": []
        }


def validate_es_connection(es_endpoint: str = "http://localhost:9200", 
                         index_name: str = "advanced_docs_elasticsearch_v2") -> bool:
    """
    Validate that Elasticsearch is accessible and the index exists.
    
    Args:
        es_endpoint: Elasticsearch endpoint URL
        index_name: Elasticsearch index name
        
    Returns:
        bool: True if connection and index are valid
    """
    try:
        import requests
        
        # Test ES connection
        response = requests.get(f"{es_endpoint}/_cluster/health")
        if response.status_code != 200:
            print(f"❌ Cannot connect to Elasticsearch at {es_endpoint}")
            return False
            
        # Test index existence
        response = requests.get(f"{es_endpoint}/{index_name}")
        if response.status_code != 200:
            print(f"❌ Index '{index_name}' not found in Elasticsearch")
            return False
            
        print(f"✅ Elasticsearch connection and index '{index_name}' validated")
        return True
        
    except Exception as e:
        print(f"❌ Error validating Elasticsearch: {str(e)}")
        return False


def get_es_chunk_count(es_endpoint: str = "http://localhost:9200",
                      index_name: str = "advanced_docs_elasticsearch_v2") -> int:
    """
    Get the total number of chunks in the Elasticsearch index.
    
    Args:
        es_endpoint: Elasticsearch endpoint URL
        index_name: Elasticsearch index name
        
    Returns:
        int: Number of chunks in the index
    """
    try:
        import requests
        
        response = requests.get(f"{es_endpoint}/{index_name}/_count")
        if response.status_code == 200:
            count = response.json()["count"]
            print(f"📊 Found {count} chunks in Elasticsearch index '{index_name}'")
            return count
        else:
            print(f"❌ Could not get chunk count from index '{index_name}'")
            return 0
            
    except Exception as e:
        print(f"❌ Error getting chunk count: {str(e)}")
        return 0 