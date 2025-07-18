# Elasticsearch Direct Integration Refactor

## 📋 **TODO: Future Architectural Improvement**

**Status**: Identified for future implementation  
**Priority**: Medium  
**Estimated Effort**: 2-3 hours  
**Dependencies**: None (simplification)

---

## 🎯 **Problem Statement**

The current Elasticsearch integration uses **LlamaIndex** as a middleman, creating unnecessary complexity:

```
Current: ES → LlamaIndex → ElasticsearchStore → StorageContext → KG Format → Neo4j
Proposed: ES → Direct Python Client → KG Format → Neo4j
```

**Issues with Current Approach:**
1. **Dependency Overhead**: Requires `llama-index-vector-stores-elasticsearch`
2. **Local Storage Requirement**: Needs `./elasticsearch_storage_v2` directory
3. **Double Abstraction**: ES → LlamaIndex → Your KG format
4. **Deployment Complexity**: Additional files and dependencies

---

## 💡 **Proposed Solution**

### **New Architecture**
```
📊 Elasticsearch (Content Indexing)
    ↓
🔌 Direct ES Python Client (elasticsearch-py)
    ↓
🔄 Custom Chunk Processing
    ↓
🧠 LangGraph Knowledge Structuring
    ↓
📈 Neo4j Knowledge Graph Storage
```

### **Benefits**
- **🎯 Simpler Pipeline**: Remove LlamaIndex abstraction layer
- **📦 Reduced Dependencies**: Only need `elasticsearch-py`
- **🚀 Better Performance**: Direct ES queries without overhead
- **🔧 More Control**: Custom chunk processing and metadata handling
- **🚀 Cleaner Deployment**: No local vector store files needed

---

## 🛠️ **Implementation Plan**

### **Step 1: Update Requirements**
```diff
# requirements.txt
- llama-index
- llama-index-vector-stores-elasticsearch
+ elasticsearch>=8.0.0
```

### **Step 2: New Direct ES Integration**

Create `graph/utils/es_to_kg_direct.py`:

```python
"""
Direct Elasticsearch to KG Transformation (No LlamaIndex)
Simplified pipeline for ES chunk processing without external abstractions.
"""

from elasticsearch import Elasticsearch
from typing import Dict, List, Optional
import json


def transform_es_to_kg_direct(
    course_id: str,
    es_endpoint: str = "http://localhost:9200",
    index_name: str = "advanced_docs_elasticsearch_v2",
    max_chunks: int = 10000
) -> dict:
    """
    Direct ES to KG transformation without LlamaIndex dependency.
    
    Args:
        course_id: Course identifier (e.g., "OSN")
        es_endpoint: Elasticsearch endpoint URL
        index_name: ES index name
        max_chunks: Maximum chunks to retrieve
        
    Returns:
        dict: Course graph in expected KG format
    """
    print(f"🔄 Loading ES chunks directly from {es_endpoint}/{index_name}")
    
    try:
        # Initialize direct ES client
        es = Elasticsearch([es_endpoint])
        
        # Verify connection
        if not es.ping():
            raise ConnectionError(f"Cannot connect to Elasticsearch at {es_endpoint}")
        
        # Query all documents
        query = {
            "query": {"match_all": {}},
            "size": max_chunks,
            "_source": True
        }
        
        response = es.search(index=index_name, body=query)
        hits = response["hits"]["hits"]
        
        print(f"📚 Found {len(hits)} chunks in Elasticsearch")
        
        if not hits:
            print("⚠️  No documents found in Elasticsearch index")
            return _empty_course_graph(course_id)
        
        # Process chunks directly
        chunks = []
        for hit in hits:
            source = hit["_source"]
            chunks.append({
                "id": hit["_id"],
                "content": source.get("text", source.get("content", "")),
                "metadata": {
                    "section": source.get("section", "Unknown Section"),
                    "chapter": source.get("chapter"),
                    "page": source.get("page"),
                    "document": source.get("document"),
                    **{k: v for k, v in source.items() if k not in ["text", "content"]}
                }
            })
        
        # Transform to KG format
        course_graph = _process_chunks_to_kg(chunks, course_id)
        
        print(f"✅ Transformed {len(chunks)} chunks into {len(course_graph['learning_objectives'])} learning objectives")
        return course_graph
        
    except Exception as e:
        print(f"❌ Error loading from Elasticsearch: {str(e)}")
        return _empty_course_graph(course_id)


def _process_chunks_to_kg(chunks: List[Dict], course_id: str) -> dict:
    """Convert chunks to KG format using section-based grouping."""
    
    # Group chunks by section
    section_groups = {}
    for chunk in chunks:
        section = chunk["metadata"].get("section", "General")
        if section not in section_groups:
            section_groups[section] = []
        section_groups[section].append(chunk)
    
    # Convert sections to learning objectives
    learning_objectives = []
    for lo_idx, (section_title, section_chunks) in enumerate(section_groups.items()):
        lo = {
            "lo_id": f"LO_{lo_idx+1:03}",
            "text": section_title,
            "kcs": []
        }
        
        # Convert chunks to knowledge components
        for kc_idx, chunk in enumerate(section_chunks):
            kc = {
                "kc_id": f"KC_{lo_idx+1:03}_{kc_idx+1:03}",
                "text": chunk["content"][:500] + "..." if len(chunk["content"]) > 500 else chunk["content"],
                "instruction_methods": [],
                "learning_process": "",
                "metadata": chunk["metadata"]
            }
            lo["kcs"].append(kc)
        
        learning_objectives.append(lo)
    
    return {
        "course_id": course_id,
        "title": f"{course_id} (Direct ES)",
        "learning_objectives": learning_objectives
    }


def _empty_course_graph(course_id: str) -> dict:
    """Return empty course graph structure."""
    return {
        "course_id": course_id,
        "title": f"{course_id} (Empty - ES Error)",
        "learning_objectives": []
    }


def validate_es_connection_direct(
    es_endpoint: str = "http://localhost:9200",
    index_name: str = "advanced_docs_elasticsearch_v2"
) -> bool:
    """
    Validate ES connection using direct client.
    
    Returns:
        bool: True if connection and index are valid
    """
    try:
        es = Elasticsearch([es_endpoint])
        
        # Test connection
        if not es.ping():
            print(f"❌ Cannot connect to Elasticsearch at {es_endpoint}")
            return False
        
        # Test index existence
        if not es.indices.exists(index=index_name):
            print(f"❌ Index '{index_name}' not found in Elasticsearch")
            return False
        
        # Get document count
        count_response = es.count(index=index_name)
        doc_count = count_response["count"]
        
        print(f"✅ Elasticsearch connection validated")
        print(f"📊 Index '{index_name}' contains {doc_count} documents")
        return True
        
    except Exception as e:
        print(f"❌ Error validating Elasticsearch: {str(e)}")
        return False


def get_es_chunk_count_direct(
    es_endpoint: str = "http://localhost:9200",
    index_name: str = "advanced_docs_elasticsearch_v2"
) -> int:
    """Get document count using direct ES client."""
    try:
        es = Elasticsearch([es_endpoint])
        response = es.count(index=index_name)
        return response["count"]
    except Exception as e:
        print(f"❌ Error getting chunk count: {str(e)}")
        return 0
```

### **Step 3: Update Main Integration File**

Replace `graph/utils/es_to_kg.py` with the direct implementation:

```python
# graph/utils/es_to_kg.py
"""
UPDATED: Direct Elasticsearch Integration (LlamaIndex Removed)
"""

from .es_to_kg_direct import (
    transform_es_to_kg_direct as transform_es_to_kg,
    validate_es_connection_direct as validate_es_connection,
    get_es_chunk_count_direct as get_es_chunk_count
)

# Maintain backward compatibility with existing imports
__all__ = ["transform_es_to_kg", "validate_es_connection", "get_es_chunk_count"]
```

### **Step 4: Remove LlamaIndex Dependencies**

```bash
# Remove LlamaIndex packages
pip uninstall llama-index llama-index-vector-stores-elasticsearch

# Install direct ES client
pip install elasticsearch>=8.0.0

# Update requirements.txt accordingly
```

---

## 🧪 **Testing Strategy**

### **Validation Tests**
```python
# test_direct_es_integration.py
def test_direct_es_connection():
    """Test direct ES connection without LlamaIndex"""
    result = validate_es_connection_direct()
    assert isinstance(result, bool)

def test_direct_chunk_retrieval():
    """Test direct chunk retrieval and processing"""
    course_graph = transform_es_to_kg_direct("TEST_COURSE")
    assert "learning_objectives" in course_graph
    assert course_graph["course_id"] == "TEST_COURSE"
```

### **Migration Verification**
1. **Before Migration**: Run existing ES pipeline, capture output
2. **After Migration**: Run new direct ES pipeline, compare output
3. **Validate**: Ensure identical KG structure and content

---

## 📊 **Impact Assessment**

### **Files to Modify**
- `requirements.txt` (remove LlamaIndex, add elasticsearch)
- `graph/utils/es_to_kg.py` (replace with direct implementation)
- `graph/utils/es_to_kg_direct.py` (new file)
- `test_es_integration.py` (update tests)

### **Files NOT Affected**
- `generate_kg_from_es.py` (interface remains the same)
- `main.py` (ES pipeline commands unchanged)
- `graph/db.py` (Neo4j insertion unchanged)
- All LangGraph agents and pipelines

### **Deployment Impact**
- **✅ Simpler**: No vector store directory required
- **✅ Fewer Dependencies**: Reduced package count
- **✅ Cleaner**: Direct ES queries
- **⚠️ Migration Required**: One-time update needed

---

## 🎯 **Success Criteria**

1. **Functional Parity**: Same KG output as current LlamaIndex approach
2. **Simplified Dependencies**: Only `elasticsearch-py` needed
3. **Performance**: Equal or better query performance
4. **Maintainability**: Cleaner, more readable ES integration code
5. **Deployment**: No local vector store files required

---

## 📅 **Future Implementation Notes**

**When to Implement:**
- During next major refactoring cycle
- When ES integration issues arise
- When deployment simplification is needed
- Before production deployment

**Risks to Consider:**
- Ensure ES query compatibility across versions
- Verify chunk metadata preservation
- Test with various ES index structures
- Validate backward compatibility

**Success Metrics:**
- Reduced dependency count
- Faster ES query execution
- Simplified deployment process
- Maintained KG quality 