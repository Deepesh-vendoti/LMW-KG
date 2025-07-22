# Microservice-Database Mapping for LMW-MVP

## 🗄️ **Techno-Functional Database Naming Convention**

All database containers follow the pattern: `LMW-MVP-{microservice-name}-{functional-component}`

**Examples:**
- `LMW-MVP-content-preprocessor-document-storage` (MongoDB for Content Preprocessor)
- `LMW-MVP-course-manager-faculty-workflows` (PostgreSQL for Course Manager)
- `LMW-MVP-orchestrator-cache-sessions` (Redis for Universal Orchestrator)
- `LMW-MVP-development-database-admin` (Adminer for Development/Admin)

---

## 📊 **Content Subsystem Microservices & Their Databases**

### **1. Content Preprocessor Microservice**
**Purpose**: Process and chunk content from various sources
**Databases Used**:
- **LMW-MVP-content-preprocessor-document-storage** (MongoDB)
  - Database: `lmw_mvp_content_preprocessor`
  - Collections: `documents`, `chunks`, `metadata`, `processing_logs`
  - Purpose: Store processed chunks and document metadata
- **elasticsearch-rag** (Existing Elasticsearch)
  - Indices: `course_content`, `knowledge_components`
  - Purpose: Content search and indexing

### **2. Course Manager Microservice**
**Purpose**: Manage course lifecycle and faculty workflows
**Databases Used**:
- **LMW-MVP-course-manager-faculty-workflows** (PostgreSQL)
  - Database: `lmw_mvp_course_manager`
  - Tables: `courses`, `uploads`, `faculty`, `approval_workflows`
  - Purpose: Course metadata, upload tracking, faculty approvals

### **3. Course Mapper Microservice (Stage 1)**
**Purpose**: Generate Learning Objectives and Knowledge Components
**Databases Used**:
- **local-neo4j** (Existing Neo4j)
  - Nodes: `LearningObjective`, `KnowledgeComponent`
  - Relationships: `DECOMPOSED_INTO`, `BELONGS_TO_COURSE`
  - Purpose: Store LO-KC relationships and course structure

### **4. KLI Application Microservice (Stage 2)**
**Purpose**: Process Learning Processes and Instruction Methods
**Databases Used**:
- **local-neo4j** (Existing Neo4j)
  - Nodes: `LearningProcess`, `InstructionMethod`
  - Relationships: `REQUIRES`, `IMPLEMENTED_BY`
  - Purpose: Store LP-IM relationships and instructional design

### **5. Knowledge Graph Generator Microservice**
**Purpose**: Generate and store complete knowledge graphs
**Databases Used**:
- **local-neo4j** (Existing Neo4j)
  - Purpose: Primary knowledge graph storage
- **LMW-MVP-content-preprocessor-document-storage** (MongoDB)
  - Database: `lmw_mvp_kg_generator`
  - Collections: `course_snapshots`, `kg_versions`, `export_logs`
  - Purpose: Knowledge graph snapshots and version control
  - **LMW-MVP-course-manager-faculty-workflows** (PostgreSQL)
  - Database: `lmw_mvp_course_manager`
  - Tables: `kg_metadata`, `version_control`, `faculty_approvals`
  - Purpose: KG metadata and faculty approval tracking

### **6. Universal Orchestrator Microservice**
**Purpose**: Coordinate cross-subsystem workflows and manage state
**Databases Used**:
- **LMW-MVP-orchestrator-cache-sessions** (Redis)
  - Purpose: Session caching and temporary state storage
- **LMW-MVP-content-preprocessor-document-storage** (MongoDB)
  - Database: `lmw_mvp_orchestrator`
  - Collections: `learner_profiles`, `personalized_learning_trees`, `learning_sessions`, `session_cache`, `query_cache`
  - Purpose: Persistent state storage and caching

---

## 🔄 **Shared Infrastructure**

### **LMW-MVP-orchestrator-cache-sessions** (Redis)
**Used by**: Universal Orchestrator (manages all microservices)
**Purpose**: 
- Session management for all microservices
- Query result caching
- Temporary data storage
- Rate limiting
- Cross-subsystem communication

### **LMW-MVP-development-database-admin** (Adminer)
**Used by**: Development team and administrators
**Purpose**: 
- Database management UI
- Query execution
- Schema inspection
- Data visualization
- Development and debugging

---

## 🏗️ **Database Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTENT SUBSYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Content         │    │ Course          │                │
│  │ Preprocessor    │    │ Manager         │                │
│  │                 │    │                 │                │
│  │ MongoDB         │    │ PostgreSQL      │                │
│  │ Elasticsearch   │    │                 │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                        │
│           └───────────────────────┼────────────────────────┘
│                                   │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Course Mapper   │    │ KLI Application │                │
│  │ (Stage 1)       │    │ (Stage 2)       │                │
│  │                 │    │                 │                │
│  │ Neo4j           │    │ Neo4j           │                │
│  └─────────────────┘    └─────────────────┘                │
│                                   │                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Knowledge Graph Generator                               ││
│  │                                                         ││
│  │ Neo4j + MongoDB + PostgreSQL                           ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SHARED INFRASTRUCTURE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Redis Cache     │    │ Adminer UI      │                │
│  │ & Sessions      │    │                 │                │
│  │                 │    │ Database Admin  │                │
│  │ Orchestrator    │    │ Interface       │                │
│  │ Managed         │    │                 │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 **Container Management Commands**

### **Start New Databases**
```bash
docker-compose -f docker-compose-databases.yml up -d
```

### **Check Container Status**
```bash
docker ps --filter "name=LMW-MVP" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### **View Logs**
```bash
# All databases
docker-compose -f docker-compose-databases.yml logs

# Specific database
docker logs LMW-MVP-content-preprocessor-document-storage
docker logs LMW-MVP-course-manager-faculty-workflows
docker logs LMW-MVP-orchestrator-cache-sessions
```

### **Access Database Management UI**
- **Adminer**: http://localhost:8080
- **Neo4j Browser**: http://localhost:7474 (existing)

---

## 📋 **Database Connection Details**

| Container Name | Database Type | Port | Microservice | Functional Component |
|----------------|---------------|------|--------------|---------------------|
| `LMW-MVP-content-preprocessor-document-storage` | MongoDB | 27017 | Content Preprocessor | Document Storage |
| `LMW-MVP-course-manager-faculty-workflows` | PostgreSQL | 5432 | Course Manager | Faculty Workflows |
| `LMW-MVP-orchestrator-cache-sessions` | Redis | 6379 | Universal Orchestrator | Cache & Sessions |
| `LMW-MVP-development-database-admin` | Adminer | 8080 | Development Team | Database Admin |
| `local-neo4j` (existing) | Neo4j | 7474, 7687 | Course Mapper, KLI App, KG Generator | Knowledge Graph |
| `elasticsearch-rag` (existing) | Elasticsearch | 9200 | Content Preprocessor | Content Search |

---

## 🎯 **Benefits of Techno-Functional Naming Convention**

1. **Clear Microservice Ownership**: Immediately shows which microservice owns/uses the database
2. **Functional Purpose**: Indicates the specific function the database serves
3. **Easy Troubleshooting**: Quick identification of which database to check for specific issues
4. **Scalability Planning**: Clear pattern for adding new databases for new microservices
5. **Team Communication**: Non-technical team members can understand the purpose

### **Naming Pattern Examples:**
- `LMW-MVP-{microservice}-{function}`
- `LMW-MVP-content-preprocessor-document-storage`
- `LMW-MVP-course-manager-faculty-workflows`
- `LMW-MVP-orchestrator-cache-sessions`
- `LMW-MVP-development-database-admin`
- `LMW-MVP-learner-subsystem-profiles`

This naming convention makes it crystal clear which microservice uses which database and for what purpose! 🎉

---

## 🤔 **Regarding "Adapters" - Context Check**

You mentioned faculty talking about "adapters" - this might refer to:

1. **Database Adapters**: Interfaces between microservices and different database types
2. **API Adapters**: Interfaces for external service integrations
3. **Content Adapters**: Interfaces for different content formats (PDF, DOC, etc.)
4. **Faculty Approval Adapters**: Interfaces for different approval workflows

Could you clarify what specific "adapters" the faculty mentioned? This would help ensure we're not missing any architectural components in our database setup. 