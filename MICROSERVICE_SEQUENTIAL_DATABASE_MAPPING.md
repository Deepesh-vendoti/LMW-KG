# Microservice Sequential Database Mapping - LMW-MVP System (Refined Architecture)

## 🎯 **Microservices in Sequential Execution Order**

### **Phase 1: Content Processing Pipeline**
*Processing raw content into structured knowledge*

| Execution Order | Microservice | Database(s) | Container Name | Port | Status | Function | Data Flow |
|-----------------|--------------|-------------|----------------|------|--------|----------|-----------|
| **1** | **Content Preprocessor** | MongoDB + Elasticsearch | `LMW-MVP-content-preprocessor-document-storage` + `LMW-MVP-elasticsearch-content-search` | 27017 + 9200 | ✅ Up | Document processing, chunking, search indexing | Raw content → Chunks → Search index |
| **2** | **Course Manager** | PostgreSQL | `LMW-MVP-course-manager-metadata-approvals` | 5432 | ✅ Up | Course lifecycle, faculty workflows, approvals | Course metadata → Faculty approval workflow |
| **3** | **Course Mapper** | Neo4j | `LMW-MVP-course-mapper-knowledge-graph` | 7474,7687 | ✅ Up | Learning objectives, knowledge components | Chunks → Learning Objectives → Knowledge Components |
| **4** | **KLI Application** | Neo4j | `LMW-MVP-kli-app-learning-processes` | 7475,7688 | ✅ Up | Learning processes, instruction methods | Knowledge Components → Learning Processes → Instruction Methods |
| **5** | **Knowledge Graph Generator** | MongoDB + PostgreSQL + Neo4j (Both) | `LMW-MVP-content-preprocessor-document-storage` + `LMW-MVP-course-manager-metadata-approvals` + `LMW-MVP-course-mapper-knowledge-graph` + `LMW-MVP-kli-app-learning-processes` | 27017 + 5432 + 7474,7687 + 7475,7688 | ✅ Up | KG snapshots, metadata, graph storage | All data → Complete Knowledge Graph |

### **Phase 2: Learner Processing Pipeline**
*Personalized learning based on learner context*

| Execution Order | Microservice | Database(s) | Container Name | Port | Status | Function | Data Flow |
|-----------------|--------------|-------------|----------------|------|--------|----------|-----------|
| **6** | **Query Strategy Manager** | PostgreSQL | `LMW-MVP-query-strategy-learner-profiles` | 5433 | ✅ Up | Learner profiles, adaptive strategies | Learner context → Query strategy |
| **7** | **Graph Query Engine** | PostgreSQL | `LMW-MVP-graph-query-executor` | 5434 | ✅ Up | Query performance, caching | Strategy → Graph queries → Results |
| **8** | **Learning Tree Handler** | PostgreSQL | `LMW-MVP-learning-tree-plt-storage` | 5435 | ✅ Up | PLT storage, progress tracking | Query results → Personalized Learning Tree |

### **Phase 3: Orchestration & Configuration**
*Cross-cutting concerns and system management*

| Execution Order | Component | Database(s) | Container Name | Port | Status | Function | Data Flow |
|-----------------|-----------|-------------|----------------|------|--------|----------|-----------|
| **9** | **Universal Orchestrator** | MongoDB + Redis | `LMW-MVP-orchestrator-state-store` + `LMW-MVP-orchestrator-session-cache` | 27018 + 6379 | ✅ Up | State management, session caching | Orchestrates all microservices |
| **10** | **System Configuration** | PostgreSQL | `LMW-MVP-system-config-global-settings` | 5436 | ✅ Up | Global config, feature flags | System-wide configuration |

---

## 🔄 **Complete Data Flow by Phase**

### **Phase 1: Content Processing Pipeline**

```
Raw Content (PDF/DOC/PPT) 
    ↓
[1] Content Preprocessor
    ├── MongoDB: Store processed chunks, metadata
    └── Elasticsearch: Index content for search
    ↓
[2] Course Manager
    └── PostgreSQL: Course metadata, faculty approvals
    ↓
[3] Course Mapper (Stage 1)
    └── Neo4j (Course Mapper): Learning Objectives + Knowledge Components
    ↓
[4] KLI Application (Stage 2)
    └── Neo4j (KLI App): Learning Processes + Instruction Methods
    ↓
[5] Knowledge Graph Generator
    ├── MongoDB: KG snapshots, version control
    ├── PostgreSQL: KG metadata, faculty approvals
    ├── Neo4j (Course Mapper): Learning Objectives + Knowledge Components
    └── Neo4j (KLI App): Learning Processes + Instruction Methods
```

### **Phase 2: Learner Processing Pipeline**

```
Learner Context (Profile, Preferences)
    ↓
[6] Query Strategy Manager
    └── PostgreSQL: Learner profiles, adaptive strategies
    ↓
[7] Graph Query Engine
    └── PostgreSQL: Query performance, caching
    ↓
[8] Learning Tree Handler
    └── PostgreSQL: Personalized Learning Trees, progress
```

### **Phase 3: Orchestration & Configuration**

```
System Operations
    ↓
[9] Universal Orchestrator
    ├── MongoDB: Persistent state storage
    └── Redis: Session caching, cross-service communication
    ↓
[10] System Configuration
    └── PostgreSQL: Global settings, feature flags
```

---

## 🗄️ **Database Usage by Microservice**

### **Content Preprocessor** (Execution Order: 1)
**Databases Used:**
- **MongoDB** (`lmw_mvp_content_preprocessor`): Store processed document chunks, metadata, processing logs
- **Elasticsearch** (`LMW-MVP-elasticsearch-content-search`): Content indexing, full-text search, vector storage

**Data Flow:** Raw content → Chunks → Search index

### **Course Manager** (Execution Order: 2)
**Databases Used:**
- **PostgreSQL** (`lmw_mvp_course_manager`): Course metadata, faculty workflows, approval tracking

**Data Flow:** Course metadata → Faculty approval workflow

### **Course Mapper** (Execution Order: 3)
**Databases Used:**
- **Neo4j** (`LMW-MVP-course-mapper-knowledge-graph`): Learning objectives and knowledge components relationships

**Data Flow:** Chunks → Learning Objectives → Knowledge Components

### **KLI Application** (Execution Order: 4)
**Databases Used:**
- **Neo4j** (`LMW-MVP-kli-app-learning-processes`): Learning processes and instruction methods relationships

**Data Flow:** Knowledge Components → Learning Processes → Instruction Methods

### **Knowledge Graph Generator** (Execution Order: 5)
**Databases Used:**
- **MongoDB** (`lmw_mvp_kg_generator`): Knowledge graph snapshots and version control
- **PostgreSQL** (`lmw_mvp_course_manager`): Knowledge graph metadata and faculty approvals
- **Neo4j** (`LMW-MVP-course-mapper-knowledge-graph`): Learning Objectives + Knowledge Components
- **Neo4j** (`LMW-MVP-kli-app-learning-processes`): Learning Processes + Instruction Methods

**Data Flow:** All data → Complete Knowledge Graph

### **Query Strategy Manager** (Execution Order: 6)
**Databases Used:**
- **PostgreSQL** (`lmw_mvp_query_strategy`): Learner profiles and adaptive strategies

**Data Flow:** Learner context → Query strategy

### **Graph Query Engine** (Execution Order: 7)
**Databases Used:**
- **PostgreSQL** (`lmw_mvp_graph_query`): Query performance tracking and caching

**Data Flow:** Strategy → Graph queries → Results

### **Learning Tree Handler** (Execution Order: 8)
**Databases Used:**
- **PostgreSQL** (`lmw_mvp_learning_tree`): Personalized learning trees and progress tracking

**Data Flow:** Query results → Personalized Learning Tree

### **Universal Orchestrator** (Execution Order: 9)
**Databases Used:**
- **MongoDB** (`LMW-MVP-orchestrator-state-store`): Persistent state storage
- **Redis** (`LMW-MVP-orchestrator-session-cache`): Session caching and cross-service communication

**Data Flow:** Orchestrates all microservices

### **System Configuration** (Execution Order: 10)
**Databases Used:**
- **PostgreSQL** (`lmw_mvp_system_config`): Global configuration and feature flags

**Data Flow:** System-wide configuration

---

## 📊 **Database Utilization Summary**

### **MongoDB Databases** (3 databases)
| Database | Used By | Purpose |
|----------|---------|---------|
| `lmw_mvp_content_preprocessor` | Content Preprocessor | Document processing, chunks, metadata |
| `lmw_mvp_kg_generator` | Knowledge Graph Generator | KG snapshots, version control |
| `lmw_mvp_orchestrator` | Universal Orchestrator | State management, session data |

### **PostgreSQL Databases** (5 databases)
| Database | Used By | Purpose |
|----------|---------|---------|
| `lmw_mvp_course_manager` | Course Manager + Knowledge Graph Generator | Course metadata, faculty workflows, KG metadata |
| `lmw_mvp_query_strategy` | Query Strategy Manager | Learner profiles, strategies |
| `lmw_mvp_graph_query` | Graph Query Engine | Query performance, caching |
| `lmw_mvp_learning_tree` | Learning Tree Handler | PLT storage, progress tracking |
| `lmw_mvp_system_config` | System Configuration | Global config, feature flags |

### **Neo4j Databases** (2 separate instances)
| Database | Used By | Purpose |
|----------|---------|---------|
| **Neo4j Course Mapper** (`LMW-MVP-course-mapper-knowledge-graph`) | Course Mapper + Knowledge Graph Generator | Learning objectives, knowledge components |
| **Neo4j KLI App** (`LMW-MVP-kli-app-learning-processes`) | KLI Application + Knowledge Graph Generator | Learning processes, instruction methods |

### **Specialized Databases** (1 database)
| Database | Used By | Purpose |
|----------|---------|---------|
| **Elasticsearch** (`LMW-MVP-elasticsearch-content-search`) | Content Preprocessor | Content search, indexing |

### **Utility Databases** (2 databases)
| Database | Used By | Purpose |
|----------|---------|---------|
| **Redis** (`LMW-MVP-orchestrator-session-cache`) | Universal Orchestrator | Session caching, communication |
| **Adminer** (`LMW-MVP-development-database-admin`) | Development Team | Database management UI |

---

## 🎯 **Architectural Refinements Benefits**

### **Separated Neo4j Containers** ✅
- **Course Mapper**: Dedicated Neo4j instance for learning objectives and knowledge components
- **KLI Application**: Dedicated Neo4j instance for learning processes and instruction methods
- **Better Isolation**: Each microservice has its own graph database
- **Independent Scaling**: Can scale each Neo4j instance separately

### **Improved Container Naming** ✅
- **Course Manager**: `LMW-MVP-course-manager-metadata-approvals` (clearer responsibility)
- **Graph Query Engine**: `LMW-MVP-graph-query-executor` (reflects actual function)
- **Elasticsearch**: `LMW-MVP-elasticsearch-content-search` (specific purpose)

### **Separated Orchestrator Components** ✅
- **State Store**: `LMW-MVP-orchestrator-state-store` (MongoDB for persistent state)
- **Session Cache**: `LMW-MVP-orchestrator-session-cache` (Redis for fast caching)
- **Better Separation**: Clear distinction between persistent and ephemeral data

### **Enhanced Modularity** ✅
- **Independent Databases**: Each microservice has dedicated database(s)
- **Clear Responsibilities**: Container names reflect specific functions
- **Better Debugging**: Easier to identify and troubleshoot issues
- **Future Scaling**: Can scale components independently

---

## ✅ **Production Readiness**

### **Sequential Execution** ✅
- All microservices execute in logical order
- Each phase depends on previous phase completion
- Faculty approval workflow ensures quality control

### **Database Coverage** ✅
- Every microservice has dedicated database(s)
- No database conflicts or duplications
- Proper data isolation and security

### **Data Flow** ✅
- Clear data flow from content processing to personalized learning
- Each database serves specific microservice needs
- Cross-service communication through Redis

### **Architectural Clarity** ✅
- Separated Neo4j containers for better modularity
- Improved container naming for better debugging
- Separated orchestrator components for better scalability

**The LMW-MVP system now has a refined, modular architecture with improved clarity and scalability!** 🎉 