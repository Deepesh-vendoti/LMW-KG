# 🗄️ Database Schemas for 8 Microservices

## 📊 **LangGraph Knowledge Graph System - Database Architecture**

This document provides detailed database schemas for each of the 8 microservices in the LMW-KG system, organized by subsystem.

---

```sql
-- Faculty information
CREATE TABLE faculty (
    faculty_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    department VARCHAR(255),
    permissions JSONB
);

-- Learner profiles
CREATE TABLE learners (
    learner_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    learning_style VARCHAR(50), -- visual, auditory, kinesthetic, reading
    pace VARCHAR(50), -- slow, medium, fast
    experience_level VARCHAR(50), -- beginner, intermediate, advanced
    preferences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🏗️ **Content Subsystem (5 Microservices)**

### **1. Course Manager Service**
**Database**: PostgreSQL (`lmw_mvp_course_manager`)  
**Container**: `LMW-MVP-course-manager-faculty-workflows`  
**Port**: 5432

#### **Tables Schema**:

```sql
-- Courses management
CREATE TABLE courses (
    course_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    faculty_id VARCHAR(50),
    faculty_inputs JSONB,         --difficulty, graduate/undergrad level, number of weeks
    upload_type VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- File tracking
CREATE TABLE uploads (
    upload_id SERIAL PRIMARY KEY,
    course_id VARCHAR(50) REFERENCES courses(course_id),
    file_path TEXT,
    upload_type VARCHAR(50),
    status VARCHAR(50),
    metadata JSONB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Approval workflows (3-tier: FACD, FCCS, FFCS)
CREATE TABLE approval_workflows (
    workflow_id SERIAL PRIMARY KEY,
    course_id VARCHAR(50) REFERENCES courses(course_id),
    stage VARCHAR(50), -- FACD, FCCS, FFCS
    status VARCHAR(50),
    faculty_id VARCHAR(50) REFERENCES faculty(faculty_id),
    approved_at TIMESTAMP,
    comments TEXT
);

```

---

### **2. Content Preprocessor Service**
**Database**: MongoDB (`lmw_mvp_content_preprocessor`)  
**Container**: `LMW-MVP-content-preprocessor-document-storage`  
**Port**: 27017

#### **Collections Schema**:

```javascript
// Processed documents collection
{
  _id: ObjectId,
  course_id: String,
  document_id: String,
  file_path: String,
  content_type: String, // pdf, text, elasticsearch
  metadata: {
    file_size: Number,
    page_count: Number,
    processing_date: Date,
    checksum: String
  },
  status: String, // processing, completed, error
  created_at: Date,
  updated_at: Date
}

// Content chunks collection
{
  _id: ObjectId,
  document_id: String,
  course_id: String,
  chunk_id: String,
  content: String,
  chunk_index: Number,
  chunk_size: Number,
  overlap_size: Number,
  embeddings: [Number], // Vector embeddings (add llama indexing to be able to use the chunks for reference)
  metadata: {
    page_number: Number,
    section_title: String,
    chunk_type: String
  },
  created_at: Date
}

// Processing logs collection
{
  _id: ObjectId,
  course_id: String,
  document_id: String,
  operation: String, // chunk, embed, index
  status: String, // success, error, in_progress
  duration_ms: Number,
  error_message: String,
  timestamp: Date
}
```

#### **Additional Database**: Elasticsearch
**Host**: localhost:9200  
**Container**: `elasticsearch-rag`

```json
// course_content index mapping
{
  "mappings": {
    "properties": {
      "course_id": {"type": "keyword"},
      "chunk_id": {"type": "keyword"},
      "content": {"type": "text"},
      "embeddings": {"type": "dense_vector", "dims": 384},
      "metadata": {"type": "object"},
      "timestamp": {"type": "date"}
    }
  }
}

// knowledge_components index mapping
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
}
```

---

### **3. Course Mapper Service**
**Database**: Neo4j (Instance 1)  (TBD can we use any other database)
**Container**: `local-neo4j`
**Port**: 7687 (Bolt), 7474 (HTTP)

#### **Node Labels and Properties**:

```cypher
// Course nodes
CREATE (course:Course {
    id: String,
    name: String,
    description: String,
    faculty_id: String,
    status: String,
    created_at: DateTime
});

// Learning Objective nodes
CREATE (lo:LearningObjective {
    id: String,
    name: String,
    text: String,
    description: String,
    difficulty_level: String,
    course_id: String,
    bloom_level: String,
    cognitive_level: String
});

// Knowledge Component nodes
CREATE (kc:KnowledgeComponent {
    id: String,
    name: String,
    text: String,
    description: String,
    type: String,
    difficulty: String,
    course_id: String,
    prerequisites: [String]
});

// Relationships
CREATE (course)-[:HAS_LEARNING_OBJECTIVE]->(lo);
CREATE (lo)-[:REQUIRES_KNOWLEDGE_COMPONENT]->(kc);
CREATE (kc)-[:PREREQUISITE_FOR]->(kc2:KnowledgeComponent);
```

---

### **4. KLI Application Service**
**Database**: Neo4j (Same instance as Course Mapper)  
**Container**: `local-neo4j`

#### **Additional Node Labels**:

```cypher
// Learning Process nodes
CREATE (lp:LearningProcess {
    id: String,
    type: String, // Understanding, Application, Analysis, Synthesis, Evaluation
    description: String,
    bloom_taxonomy: String,
    cognitive_load: String
});

// Instruction Method nodes
CREATE (im:InstructionMethod {
    id: String,
    name: String,
    type: String, // Lecture, Tutorial, Lab, Project, Assessment
    description: String,
    delivery_mode: String, // online, offline, hybrid
    estimated_duration: Integer
});

// Additional relationships
CREATE (kc)-[:REQUIRES_LEARNING_PROCESS]->(lp);
CREATE (lp)-[:USES_INSTRUCTION_METHOD]->(im);
CREATE (lo)-[:ACHIEVED_THROUGH]->(lp);
```

---

### **5. Knowledge Graph Generator Service**
**Primary Database**: Neo4j (Same instance)  
**Secondary Database**: MongoDB (`lmw_mvp_kg_generator`)  
**Tertiary Database**: PostgreSQL (`lmw_mvp_kg_generator_relational`)  
**Container**: `LMW-MVP-kg-generator-versioning`  
**Port**: 5437

#### **PostgreSQL Tables for KG Management**:

```sql
-- Main Knowledge Graph table (stores latest version)
CREATE TABLE knowledge_graphs (
    kg_id SERIAL PRIMARY KEY,
    course_id VARCHAR(50) UNIQUE,
    version_number INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft', -- draft, approved, published
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    metadata JSONB,
    node_count INTEGER DEFAULT 0,
    relationship_count INTEGER DEFAULT 0,
    complexity_score DECIMAL(5,2)
);

-- Knowledge Graph Versions table (stores all versions)
CREATE TABLE kg_versions (
    version_id SERIAL PRIMARY KEY,
    kg_id INTEGER REFERENCES knowledge_graphs(kg_id),
    version_number INTEGER,
    kg_data JSONB, -- Complete KG structure for this version
    neo4j_export JSONB, -- Neo4j cypher queries for recreation
    status VARCHAR(50), -- draft, approved, published, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50),
    change_summary TEXT,
    metadata JSONB,
    node_count INTEGER DEFAULT 0,
    relationship_count INTEGER DEFAULT 0,
    complexity_score DECIMAL(5,2)
);

-- Tabular view for faculty display
CREATE TABLE kg_tabular_view (
    table_id SERIAL PRIMARY KEY,
    kg_id INTEGER REFERENCES knowledge_graphs(kg_id),
    version_number INTEGER,
    component_type VARCHAR(50), -- learning_objective, knowledge_component, relationship
    component_id VARCHAR(100),
    component_name VARCHAR(255),
    component_description TEXT,
    properties JSONB,
    parent_component VARCHAR(100),
    child_components TEXT[], -- Array of child component IDs
    difficulty_level VARCHAR(50),
    bloom_taxonomy VARCHAR(50),
    prerequisites TEXT[],
    relationships_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **MongoDB Collections for KG Management**:

```javascript
// export_logs collection
{
  _id: ObjectId,
  kg_id: Number,
  version_number: Number,
  export_format: String, // neo4j, json, graphml, tabular
  export_status: String,
  file_path: String,
  exported_at: Date,
  error_details: String
}

// kg_processing_logs collection
{
  _id: ObjectId,
  kg_id: Number,
  version_number: Number,
  operation: String, // generate, update, approve, publish
  status: String, // in_progress, completed, failed
  duration_ms: Number,
  error_message: String,
  timestamp: Date
}
```

---

## 🎓 **Learner Subsystem (3 Microservices)**

### **6. Query Strategy Manager Service**
**Database**: PostgreSQL (`lmw_mvp_query_strategy`)  
**Container**: `LMW-MVP-query-strategy-learner-profiles`  
**Port**: 5433

#### **Tables Schema**:

```sql

-- Query strategies
CREATE TABLE strategies (
    strategy_id SERIAL PRIMARY KEY,
    learner_id VARCHAR(50) REFERENCES learners(learner_id),
    course_id VARCHAR(50),
    decision_tree_inputs VARCHAR(50),
    context JSONB,
    strategy_output VARCHAR(50),
    success_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **7. Graph Query Engine Service** (Further allignment with others are needed - expectations from plt)
**Database**: PostgreSQL (`lmw_mvp_graph_query`)  
**Container**: `LMW-MVP-graph-query-performance-logs`  
**Port**: 5434

#### **Tables Schema**:

```sql
-- Query execution history
CREATE TABLE query_history (
    query_id SERIAL PRIMARY KEY,
    learner_id VARCHAR(50),
    course_id VARCHAR(50),
    cypher_query TEXT,
    execution_time_ms INTEGER,
    result_count INTEGER,
    memory_usage_mb DECIMAL(8,2),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query result caching
CREATE TABLE cached_results (
    cache_id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64),
    query_text TEXT,
    result_data JSONB,
    expires_at TIMESTAMP,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query patterns and templates
CREATE TABLE query_patterns (
    pattern_id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(100),
    cypher_template TEXT,
    parameters JSONB,
    usage_count INTEGER DEFAULT 0,
    avg_performance_ms FLOAT,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query optimization suggestions
CREATE TABLE optimization_suggestions (
    suggestion_id SERIAL PRIMARY KEY,
    query_pattern_id INTEGER REFERENCES query_patterns(pattern_id),
    suggestion_type VARCHAR(50), -- index, rewrite, cache
    description TEXT,
    estimated_improvement_percent DECIMAL(5,2),
    implemented BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **8. Learning Tree Handler Service** (Needs further clarification especially with SME)
**Database**: PostgreSQL (`lmw_mvp_learning_tree`)  
**Container**: `LMW-MVP-learning-tree-plt-storage`  
**Port**: 5435

#### **Tables Schema**:

```sql
-- Personalized Learning Trees (PLT)
CREATE TABLE personalized_trees (
    plt_id SERIAL PRIMARY KEY,
    learner_id VARCHAR(50),
    course_id VARCHAR(50),
    tree_data JSONB,
    complexity_score DECIMAL(5,2),
    estimated_duration_hours INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learning paths within PLTs
CREATE TABLE learning_paths (
    path_id SERIAL PRIMARY KEY,
    plt_id INTEGER REFERENCES personalized_trees(plt_id),
    sequence_order INTEGER,
    learning_objective TEXT,
    knowledge_component TEXT,
    instruction_method TEXT,
    priority VARCHAR(20), -- high, medium, low
    difficulty_level VARCHAR(20), -- beginner, intermediate, advanced
    estimated_time_minutes INTEGER,
    status VARCHAR(50) DEFAULT 'pending' -- pending, in_progress, completed, skipped
);

-- Progress tracking for learners
CREATE TABLE progress_tracking (
    progress_id SERIAL PRIMARY KEY,
    path_id INTEGER REFERENCES learning_paths(path_id),
    learner_id VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    time_spent INTEGER, -- in minutes
    performance_score DECIMAL(5,2),
    difficulty_rating INTEGER, -- 1-5 scale
    feedback TEXT
);

-- PLT metadata and configurations
CREATE TABLE plt_metadata (
    metadata_id SERIAL PRIMARY KEY,
    plt_id INTEGER REFERENCES personalized_trees(plt_id),
    metadata_key VARCHAR(100),
    metadata_value JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adaptive recommendations
CREATE TABLE recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    learner_id VARCHAR(50),
    plt_id INTEGER REFERENCES personalized_trees(plt_id),
    recommendation_type VARCHAR(50), -- next_topic, review, skip, additional_practice
    content JSONB,
    confidence_score DECIMAL(5,2),
    applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---