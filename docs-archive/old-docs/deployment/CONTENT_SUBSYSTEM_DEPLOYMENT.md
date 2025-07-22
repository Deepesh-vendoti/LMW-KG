# Content Subsystem Deployment Guide

## 🎯 **Production-Ready Content Subsystem with Real Database Connections**

This guide provides step-by-step instructions to deploy the **Content Subsystem** with real database connections for production use.

---

## 📋 **Prerequisites**

### **System Requirements**
- Docker and Docker Compose
- Python 3.10+
- 8GB RAM minimum (16GB recommended)
- 20GB disk space

### **Software Dependencies**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify Docker is running
docker --version
docker-compose --version
```

---

## 🚀 **Step 1: Database Infrastructure Setup**

### **1.1 Start Database Containers**

```bash
# Start all databases
docker-compose -f deployment/docker-compose-databases.yml up -d

# Verify containers are running
docker ps --filter "name=langgraph"
```

**Expected Output:**
```
CONTAINER ID   IMAGE                    PORTS                    NAMES
abc123...      neo4j:5.21              0.0.0.0:7474->7474/tcp   langgraph_neo4j
def456...      elasticsearch:8.11.0    0.0.0.0:9200->9200/tcp   langgraph_elasticsearch
ghi789...      mongo:7.0               0.0.0.0:27017->27017/tcp langgraph_mongodb
jkl012...      postgres:15             0.0.0.0:5432->5432/tcp   langgraph_postgresql
mno345...      redis:7.2-alpine        0.0.0.0:6379->6379/tcp   langgraph_redis
pqr678...      adminer:latest          0.0.0.0:8080->8080/tcp   langgraph_adminer
```

### **1.2 Verify Database Access**

```bash
# Test Neo4j (http://localhost:7474)
curl -X POST http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"statement":"RETURN 1 as test"}]}'

# Test Elasticsearch
curl http://localhost:9200

# Test MongoDB
docker exec -it langgraph_mongodb mongosh --eval "db.adminCommand('ping')"

# Test PostgreSQL
docker exec -it langgraph_postgresql psql -U postgres -d langgraph_kg -c "SELECT version();"

# Test Redis
docker exec -it langgraph_redis redis-cli ping
```

---

## 🔧 **Step 2: Database Schema Initialization**

### **2.1 Neo4j Schema Setup**

Access Neo4j Browser at http://localhost:7474 and run:

```cypher
// Create constraints for data integrity
CREATE CONSTRAINT IF NOT EXISTS FOR (lo:LearningObjective) REQUIRE lo.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (kc:KnowledgeComponent) REQUIRE kc.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (course:Course) REQUIRE course.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (learner:Learner) REQUIRE learner.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (plt:PersonalizedLearningTree) REQUIRE plt.id IS UNIQUE;

// Create indexes for performance
CREATE INDEX IF NOT EXISTS FOR (lo:LearningObjective) ON (lo.course_id);
CREATE INDEX IF NOT EXISTS FOR (kc:KnowledgeComponent) ON (kc.course_id);
CREATE INDEX IF NOT EXISTS FOR (kc:KnowledgeComponent) ON (kc.name);
CREATE INDEX IF NOT EXISTS FOR (kc:KnowledgeComponent) ON (kc.text);
CREATE INDEX IF NOT EXISTS FOR (plt:PersonalizedLearningTree) ON (plt.learner_id);
CREATE INDEX IF NOT EXISTS FOR (plt:PersonalizedLearningTree) ON (plt.course_id);
```

### **2.2 Elasticsearch Indices Setup**

```bash
# Create course_content index
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

### **2.3 PostgreSQL Schema Setup**

The schema is automatically initialized via `config/init-databases.sql` when the PostgreSQL container starts.

### **2.4 MongoDB Schema Setup**

The schema is automatically initialized via `config/init-mongodb.js` when the MongoDB container starts.

---

## 🧪 **Step 3: Database Connection Testing**

### **3.1 Run Comprehensive Tests**

```bash
# Test all database connections and Content Subsystem services
python test_database_connections.py
```

**Expected Output:**
```
🚀 LangGraph Knowledge Graph System - Database Connection Tests
======================================================================

🔍 Testing Database Connections for Content Subsystem
============================================================

📊 Database Health Status:
------------------------------
✅ NEO4J: Connected
✅ MONGODB: Connected
✅ POSTGRESQL: Connected
✅ REDIS: Connected
✅ ELASTICSEARCH: Connected

🎉 All database connections are healthy!

🔧 Testing Database Operations
========================================

🟢 Testing Neo4j operations...
   📊 Total nodes in graph: 0
   🔒 Constraints created/verified

🟡 Testing MongoDB operations...
   📚 Available collections: documents, chunks, metadata, processing_logs
   📝 Test document inserted: 507f1f77bcf86cd799439011
   🧹 Test document cleaned up

🔵 Testing PostgreSQL operations...
   🗄️ PostgreSQL version: PostgreSQL 15.5
   📋 Available tables: courses, uploads, faculty, approval_workflows, kg_metadata, version_control, faculty_approvals

🔴 Testing Redis operations...
   💾 Redis test: test_value

🟠 Testing Elasticsearch operations...
   🔍 Elasticsearch version: 8.11.0
   📇 Available indices: course_content, knowledge_components

✅ All database operations tested successfully!

🧪 Testing Content Subsystem Services
==================================================

📚 Testing Content Preprocessor...
✅ Content Preprocessor: Working with real database connections
   📄 Processed 15 chunks
   📊 Metadata: 12500 characters

📋 Testing Course Manager...
✅ Course Manager: Working with real PostgreSQL connections
   🎓 Course: TEST_COURSE_DB

🎉 ALL TESTS PASSED!
==============================
✅ Database connections: Working
✅ Database operations: Working
✅ Content Subsystem services: Working

🚀 Your Content Subsystem is ready for production deployment!
```

---

## 🎯 **Step 4: Content Subsystem Service Testing**

### **4.1 Test Individual Services**

```bash
# Test Content Preprocessor with PDF
python -c "
from orchestrator.universal_orchestrator import run_cross_subsystem_workflow
from orchestrator.state import SubsystemType

result = run_cross_subsystem_workflow(
    SubsystemType.CONTENT,
    course_id='CS101',
    upload_type='pdf',
    file_path='./data/sample.pdf'
)

print(f'Content Preprocessor Status: {result.get(\"service_statuses\", {}).get(\"content_preprocessor\")}')
print(f'Chunks Processed: {len(result.get(\"chunks\", []))}')
"

# Test Course Manager
python -c "
from orchestrator.universal_orchestrator import run_cross_subsystem_workflow
from orchestrator.state import SubsystemType

result = run_cross_subsystem_workflow(
    SubsystemType.CONTENT,
    course_id='CS101',
    upload_type='elasticsearch'
)

print(f'Course Manager Status: {result.get(\"service_statuses\", {}).get(\"course_manager\")}')
print(f'Course Result: {result.get(\"course_manager_result\", {})}')
"

# Test Knowledge Graph Generator
python -c "
from orchestrator.universal_orchestrator import run_cross_subsystem_workflow
from orchestrator.state import SubsystemType

result = run_cross_subsystem_workflow(
    SubsystemType.CONTENT,
    course_id='CS101',
    upload_type='elasticsearch',
    fccs={'learning_objectives': [{'id': 'LO1', 'text': 'Test LO'}]}
)

print(f'KG Generator Status: {result.get(\"service_statuses\", {}).get(\"knowledge_graph_generator\")}')
print(f'Storage Results: {result.get(\"knowledge_graph_generator_result\", {}).get(\"storage_results\", {})}')
"
```

### **4.2 Test Complete Content Pipeline**

```bash
# Test end-to-end content processing
python -c "
from orchestrator.universal_orchestrator import run_cross_subsystem_workflow
from orchestrator.state import SubsystemType

# Run complete content pipeline
result = run_cross_subsystem_workflow(
    SubsystemType.CONTENT,
    course_id='CS101',
    upload_type='elasticsearch',
    es_index='advanced_docs_elasticsearch_v2'
)

# Check all service statuses
service_statuses = result.get('service_statuses', {})
for service, status in service_statuses.items():
    print(f'{service}: {status}')

# Check data flow
print(f'Chunks: {len(result.get(\"chunks\", []))}')
print(f'FACD: {result.get(\"facd\") is not None}')
print(f'FCCS: {result.get(\"fccs\") is not None}')
print(f'FFCS: {result.get(\"ffcs\") is not None}')
"
```

---

## 🚀 **Step 5: Production Deployment**

### **5.1 Environment Configuration**

Create `.env` file for production settings:

```bash
# Database Configuration
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password

ELASTICSEARCH_ENDPOINT=http://your-elasticsearch-host:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=your_secure_password

MONGODB_URI=mongodb://your-mongodb-host:27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=your_secure_password

POSTGRESQL_HOST=your-postgresql-host
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=langgraph_kg
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=your_secure_password

REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_password

# LLM Configuration
OLLAMA_HOST=http://your-ollama-host:11434
LLM_MODEL=qwen3:4b

# System Configuration
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### **5.2 Production Docker Compose**

Create `docker-compose-production.yml`:

```yaml
version: '3.8'

services:
  # Content Subsystem Application
  content-subsystem:
    build: .
    container_name: langgraph_content_subsystem
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env
    depends_on:
      - neo4j
      - elasticsearch
      - mongodb
      - postgresql
      - redis
    restart: unless-stopped
    networks:
      - langgraph_network

  # Database services (same as development)
  neo4j:
    image: neo4j:5.21
    container_name: langgraph_neo4j_prod
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
    volumes:
      - neo4j_data:/data
    restart: unless-stopped
    networks:
      - langgraph_network

  # ... (other database services)

networks:
  langgraph_network:
    driver: bridge

volumes:
  neo4j_data:
  # ... (other volumes)
```

### **5.3 Production Deployment Commands**

```bash
# Deploy to production
docker-compose -f docker-compose-production.yml up -d

# Verify deployment
docker-compose -f docker-compose-production.yml ps

# Check logs
docker-compose -f docker-compose-production.yml logs -f content-subsystem

# Run production tests
python test_database_connections.py
```

---

## 📊 **Step 6: Monitoring and Maintenance**

### **6.1 Health Checks**

```bash
# Database health check script
python -c "
from utils.database_connections import get_database_manager

db_manager = get_database_manager()
health = db_manager.check_all_connections()

for db, status in health.items():
    print(f'{db}: {\"✅ Healthy\" if status else \"❌ Failed\"}')
"
```

### **6.2 Performance Monitoring**

```bash
# Monitor database performance
docker stats langgraph_neo4j langgraph_elasticsearch langgraph_mongodb langgraph_postgresql langgraph_redis

# Check disk usage
docker system df

# Monitor application logs
docker-compose logs -f --tail=100
```

### **6.3 Backup and Recovery**

```bash
# Backup databases
docker exec langgraph_neo4j neo4j-admin dump --database=neo4j --to=/backups/
docker exec langgraph_postgresql pg_dump -U postgres langgraph_kg > backup.sql
docker exec langgraph_mongodb mongodump --db=langgraph_kg --out=/backups/

# Restore databases
docker exec -i langgraph_neo4j neo4j-admin load --from=/backups/neo4j.dump --database=neo4j --force
docker exec -i langgraph_postgresql psql -U postgres langgraph_kg < backup.sql
docker exec langgraph_mongodb mongorestore --db=langgraph_kg /backups/langgraph_kg/
```

---

## 🎉 **Success Criteria**

Your Content Subsystem is **production-ready** when:

✅ **All database connections are healthy**
- Neo4j: Knowledge graph storage working
- MongoDB: Document storage working  
- PostgreSQL: Structured data working
- Redis: Caching working
- Elasticsearch: Search indexing working

✅ **All Content Subsystem services are operational**
- Content Preprocessor: Processing and storing chunks
- Course Manager: Managing course lifecycle
- Course Mapper: Generating LOs and KCs
- KLI Application: Processing LPs and IMs
- Knowledge Graph Generator: Multi-database storage

✅ **End-to-end pipeline is functional**
- Content input → Processing → Storage → Knowledge Graph
- Faculty approval workflow integration
- Cross-subsystem communication working

✅ **Performance meets requirements**
- Response times < 30 seconds for content processing
- Database operations completing successfully
- No connection timeouts or errors

---

## 🆘 **Troubleshooting**

### **Common Issues**

1. **Database Connection Failures**
   ```bash
   # Check if containers are running
   docker ps
   
   # Check container logs
   docker logs langgraph_neo4j
   docker logs langgraph_elasticsearch
   ```

2. **Service Execution Failures**
   ```bash
   # Check service logs
   python -c "from utils.database_connections import get_database_manager; print(get_database_manager().check_all_connections())"
   ```

3. **Performance Issues**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Check database performance
   docker exec langgraph_neo4j neo4j-admin memrec
   ```

### **Support**

For issues not covered in this guide:
1. Check the logs: `docker-compose logs`
2. Verify database connectivity: `python test_database_connections.py`
3. Review service configuration in `config/`
4. Check system resources and Docker settings

---

## 🚀 **Next Steps**

With your Content Subsystem successfully deployed:

1. **Integrate with Learner Subsystem** - Test cross-subsystem workflows
2. **Deploy SME Subsystem** - Add faculty approval workflows
3. **Add Analytics** - Monitor system performance and usage
4. **Scale Infrastructure** - Add load balancing and clustering
5. **Implement Security** - Add authentication and authorization

**Your Content Subsystem is now production-ready with real database connections! 🎉** 