# Database Setup and Configuration Guide

## Current Database Status ✅

Based on your existing Docker setup, the following databases are already running:

### 1. **Neo4j Database** ✅ RUNNING
- **Container**: `local-neo4j`
- **Image**: `neo4j:5.19`
- **Status**: Up 2 days
- **Ports**: 
  - Web Interface: http://localhost:7474
  - Bolt Protocol: bolt://localhost:7687
- **Authentication**: No auth (as mentioned)
- **Purpose**: Primary knowledge graph storage

### 2. **Elasticsearch** ✅ RUNNING  
- **Container**: `elasticsearch-rag`
- **Image**: `docker.elastic.co/elasticsearch/elasticsearch:8.11.0`
- **Status**: Up 34 hours
- **Port**: http://localhost:9200
- **Purpose**: Content search and document storage with LLAMA index integration

## Required Database Schema Setup

### Neo4j Schema Setup (Required for Knowledge Graph)

Since Neo4j is running without auth, you can directly execute these commands:

```bash
# Test Neo4j connection
curl -X POST http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"statement":"MATCH (n) RETURN count(n) as nodeCount"}]}'
```

#### Create Knowledge Graph Schema:
```cypher
# Run these in Neo4j Browser (http://localhost:7474) or via REST API

-- Create constraints for data integrity
CREATE CONSTRAINT IF NOT EXISTS FOR (lo:LearningObjective) REQUIRE lo.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (kc:KnowledgeComponent) REQUIRE kc.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (course:Course) REQUIRE course.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (learner:Learner) REQUIRE learner.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (plt:PersonalizedLearningTree) REQUIRE plt.id IS UNIQUE;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS FOR (lo:LearningObjective) ON (lo.course_id);
CREATE INDEX IF NOT EXISTS FOR (kc:KnowledgeComponent) ON (kc.course_id);
CREATE INDEX IF NOT EXISTS FOR (kc:KnowledgeComponent) ON (kc.name);
CREATE INDEX IF NOT EXISTS FOR (kc:KnowledgeComponent) ON (kc.text);
CREATE INDEX IF NOT EXISTS FOR (plt:PersonalizedLearningTree) ON (plt.learner_id);
CREATE INDEX IF NOT EXISTS FOR (plt:PersonalizedLearningTree) ON (plt.course_id);
```

### Elasticsearch Indices Setup

```bash
# Create course_content index for PDF documents and chunks
curl -X PUT "localhost:9200/course_content" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "course_id": {"type": "keyword"},
      "chunk_id": {"type": "keyword"},
      "content": {"type": "text", "analyzer": "standard"},
      "metadata": {
        "type": "object",
        "properties": {
          "source": {"type": "keyword"},
          "page": {"type": "integer"},
          "chunk_index": {"type": "integer"}
        }
      },
      "embeddings": {"type": "dense_vector", "dims": 384},
      "timestamp": {"type": "date"}
    }
  }
}'

# Create knowledge_components index  
curl -X PUT "localhost:9200/knowledge_components" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "kc_id": {"type": "keyword"},
      "name": {"type": "text"},
      "description": {"type": "text"},
      "course_id": {"type": "keyword"},
      "difficulty": {"type": "keyword"},
      "type": {"type": "keyword"}
    }
  }
}'
```

## Additional Databases to Set Up

### 3. **MongoDB** (For Document Storage)
```bash
# Start MongoDB container
docker run -d \
  --name langgraph_mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:7.0

# Wait for MongoDB to start
sleep 10

# Initialize MongoDB with collections
docker exec -it langgraph_mongodb mongosh --eval "
db = db.getSiblingDB('langgraph_kg');
db.createCollection('learner_profiles');
db.createCollection('personalized_learning_trees');
db.createCollection('learning_sessions');
db.createCollection('course_metadata');
db.createCollection('pdf_documents');

// Create indexes
db.learner_profiles.createIndex({ 'learner_id': 1 }, { unique: true });
db.personalized_learning_trees.createIndex({ 'learner_id': 1, 'course_id': 1 });
db.learning_sessions.createIndex({ 'session_id': 1 }, { unique: true });
db.course_metadata.createIndex({ 'course_id': 1 }, { unique: true });
db.pdf_documents.createIndex({ 'course_id': 1 });
"
```

### 4. **Redis** (For Caching)
```bash
# Start Redis container
docker run -d \
  --name langgraph_redis \
  -p 6379:6379 \
  redis:7.2-alpine

# Test Redis connection
redis-cli ping
```

## Database Configuration Update

Update your system configuration to use existing databases:

```yaml
# config/database_connections.yaml
databases:
  neo4j:
    uri: "bolt://localhost:7687"
    username: null  # No auth as mentioned
    password: null
    database: "neo4j"
    
  elasticsearch:
    host: "localhost"
    port: 9200
    scheme: "http"
    # No auth for localhost initial setup
    indices:
      course_content: "course_content"
      knowledge_components: "knowledge_components"
      
  mongodb:
    uri: "mongodb://localhost:27017"
    database: "langgraph_kg"
    collections:
      learner_profiles: "learner_profiles"
      personalized_learning_trees: "personalized_learning_trees"
      learning_sessions: "learning_sessions"
      course_metadata: "course_metadata"
      pdf_documents: "pdf_documents"
      
  redis:
    host: "localhost"
    port: 6379
    db: 0
    ttl:
      sessions: 3600      # 1 hour
      plt_cache: 86400    # 24 hours
      query_cache: 1800   # 30 minutes
```

## PDF Processing Pipeline

Since you have PDF documents and want to use Elasticsearch with LLAMA index:

```python
# Example PDF processing workflow
from llama_index.core import Document
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from llama_index.core import VectorStoreIndex

# 1. PDF Upload → Elasticsearch (with LLAMA index)
def process_pdf_to_elasticsearch(pdf_path, course_id):
    # Load PDF using existing PDF loader
    documents = load_pdf_documents(pdf_path)
    
    # Create Elasticsearch vector store
    es_store = ElasticsearchStore(
        index_name="course_content",
        es_url="http://localhost:9200"
    )
    
    # Create vector index
    index = VectorStoreIndex.from_documents(
        documents, 
        vector_store=es_store
    )
    
    return index

# 2. Content Processing → Neo4j (Knowledge Graph)
def process_content_to_neo4j(course_id, content_chunks):
    # Your existing content processing pipeline
    # Content Preprocessor → Course Mapper → KLI Application → Knowledge Graph Generator
    pass
```

## Verification Commands

```bash
# Check all databases are running
echo "=== Database Status ==="
echo "Neo4j: $(curl -s http://localhost:7474 | jq -r '.neo4j_version')"
echo "Elasticsearch: $(curl -s http://localhost:9200 | jq -r '.version.number')"
echo "MongoDB: $(docker exec -it langgraph_mongodb mongosh --quiet --eval 'db.version()')"
echo "Redis: $(redis-cli ping)"

# Test database connections
python3 -c "
from neo4j import GraphDatabase
from elasticsearch import Elasticsearch
import pymongo
import redis

# Test Neo4j
driver = GraphDatabase.driver('bolt://localhost:7687')
print('Neo4j: Connected')

# Test Elasticsearch  
es = Elasticsearch(['http://localhost:9200'])
print('Elasticsearch: Connected')

# Test MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017')
print('MongoDB: Connected')

# Test Redis
r = redis.Redis(host='localhost', port=6379, db=0)
print('Redis: Connected')
"
```

## Next Steps

1. **Initialize Neo4j Schema**: Run the Cypher commands above
2. **Create Elasticsearch Indices**: Run the curl commands above  
3. **Set up MongoDB & Redis**: Run the Docker commands above
4. **Test Full Pipeline**: Use your PDF document with the complete pipeline
5. **Update Configuration**: Update `config/database_connections.yaml` with actual connection details

## Production Considerations (Phase 2)

- **Elasticsearch**: Add API key authentication
- **Neo4j**: Enable authentication and RBAC
- **MongoDB**: Add authentication and SSL
- **Redis**: Add password protection
- **Monitoring**: Add database monitoring and alerts
- **Backup**: Implement automated backup strategies
