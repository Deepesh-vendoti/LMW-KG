# Database Naming Convention Audit - LMW-MVP System

## 🔍 **Current Database Naming Status**

### **Container Naming: ✅ CORRECT**
All database containers follow the correct `LMW-MVP-{microservice}-{function}` pattern:

- ✅ `LMW-MVP-content-preprocessor-document-storage` (MongoDB)
- ✅ `LMW-MVP-orchestrator-cache-sessions` (Redis)
- ✅ `LMW-MVP-development-database-admin` (Adminer)
- ⚠️ `LMW-MVP-course-manager-faculty-workflows` (PostgreSQL - stopped/missing)
- ⚠️ `LMW-MVP-knowledge-graph-db` (Neo4j - created but not started)
- ⚠️ `LMW-MVP-content-search-db` (Elasticsearch - created but not started)

### **Legacy Containers Still Running:**
- `local-neo4j` (Neo4j 5.19) - Should be replaced by `LMW-MVP-knowledge-graph-db`
- `elasticsearch-rag` (Elasticsearch 8.11.0) - Should be replaced by `LMW-MVP-content-search-db`

---

## ❌ **Internal Database Naming: INCORRECT**

### **MongoDB (LMW-MVP-content-preprocessor-document-storage)**
**Current Issue**: Still using old `langgraph_kg` database names
```javascript
// Current (INCORRECT):
db.getSiblingDB('langgraph_kg');
db.getSiblingDB('content_preprocessor_db');
db.getSiblingDB('kg_snapshots_db');

// Should be (CORRECT):
db.getSiblingDB('lmw_mvp_content_preprocessor');
db.getSiblingDB('lmw_mvp_kg_generator');
db.getSiblingDB('lmw_mvp_course_manager');
```

### **PostgreSQL (LMW-MVP-course-manager-faculty-workflows)**
**Current Issue**: Database name still uses `langgraph_kg`
```yaml
# Current (INCORRECT):
POSTGRES_DB=langgraph_kg

# Should be (CORRECT):
POSTGRES_DB=lmw_mvp_course_manager
```

### **Database Connection Configuration**
**Current Issue**: Connection strings reference old database names
```yaml
# Current (INCORRECT):
mongodb:
  uri: "mongodb://admin:password123@localhost:27017"
  database: "langgraph_kg"

# Should be (CORRECT):
mongodb:
  uri: "mongodb://admin:password123@localhost:27017"
  database: "lmw_mvp_content_preprocessor"
```

---

## 🔧 **Required Fixes**

### **1. Update MongoDB Initialization (init-mongodb.js)**
```javascript
// Replace all instances of:
- 'langgraph_kg' → 'lmw_mvp_orchestrator'
- 'content_preprocessor_db' → 'lmw_mvp_content_preprocessor'
- 'kg_snapshots_db' → 'lmw_mvp_kg_generator'
```

### **2. Update PostgreSQL Configuration**
```yaml
# docker-compose-databases.yml
environment:
  - POSTGRES_DB=lmw_mvp_course_manager  # Changed from langgraph_kg
```

### **3. Update Database Connection Configuration**
```yaml
# config/database_connections.yaml
mongodb:
  database: "lmw_mvp_content_preprocessor"  # Changed from langgraph_kg
postgresql:
  database: "lmw_mvp_course_manager"  # Changed from langgraph_kg
```

### **4. Container Migration Strategy**
```bash
# Stop legacy containers
docker stop elasticsearch-rag local-neo4j

# Start new containers with correct naming
docker compose -f docker-compose-databases.yml up -d
```

---

## 📊 **Microservice-Database Mapping (Corrected)**

### **Content Subsystem**
1. **Content Preprocessor** → `LMW-MVP-content-preprocessor-document-storage` (MongoDB: `lmw_mvp_content_preprocessor`)
2. **Course Manager** → `LMW-MVP-course-manager-faculty-workflows` (PostgreSQL: `lmw_mvp_course_manager`)
3. **Course Mapper** → `LMW-MVP-knowledge-graph-db` (Neo4j: `lmw_mvp_knowledge_graph`)
4. **KLI Application** → `LMW-MVP-knowledge-graph-db` (Neo4j: `lmw_mvp_knowledge_graph`)
5. **Knowledge Graph Generator** → `LMW-MVP-content-preprocessor-document-storage` (MongoDB: `lmw_mvp_kg_generator`)

### **Learner Subsystem**
6. **Learning Tree Handler** → `LMW-MVP-orchestrator-cache-sessions` (Redis: db 1)
7. **Graph Query Engine** → `LMW-MVP-knowledge-graph-db` (Neo4j: `lmw_mvp_knowledge_graph`)
8. **Query Strategy Manager** → `LMW-MVP-orchestrator-cache-sessions` (Redis: db 2)

### **Universal Services**
- **Universal Orchestrator** → `LMW-MVP-orchestrator-cache-sessions` (Redis: db 0)
- **Search/Indexing** → `LMW-MVP-content-search-db` (Elasticsearch: `lmw_mvp_content_index`)

---

## 🎯 **Priority Action Items**

1. **IMMEDIATE**: Update MongoDB initialization script with correct database names
2. **IMMEDIATE**: Update PostgreSQL configuration and recreate container
3. **IMMEDIATE**: Update database connection configuration files
4. **NEXT**: Migrate from legacy containers to new naming convention
5. **NEXT**: Test all microservice database connections
6. **FINAL**: Update all microservice code to use new database names

---

## 🔄 **Migration Impact Assessment**

### **Low Impact** (Container names only)
- Container renames don't affect application code
- Docker networking remains the same
- Port mappings unchanged

### **High Impact** (Database names)
- All microservice code must be updated
- Database connection strings must be changed
- Data migration required for existing data
- Testing required for all database operations

### **Critical Path**
1. Fix naming in configuration files
2. Update initialization scripts
3. Recreate containers with fresh data
4. Test basic connections
5. Update microservice code
6. Full system testing
