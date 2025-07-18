# LangGraph Knowledge Graph System - Complete Architecture Overview

## 📁 Project Structure

```
langgraph-kg/
├── 📂 config/                          # Configuration Management
│   ├── config.yaml                     # Main system configuration
│   ├── database_architecture.yaml      # Database schemas
│   └── loader.py                       # Configuration loader utility
│
├── 📂 orchestrator/                     # Universal Orchestration Layer
│   ├── __init__.py
│   ├── approval_states.py              # Faculty approval workflow states
│   ├── main.py                         # Orchestrator CLI interface
│   ├── service_registry.py             # Dynamic service discovery
│   ├── state.py                        # Universal state schemas
│   └── universal_orchestrator.py       # LangGraph cross-subsystem coordinator
│
├── 📂 subsystems/                       # Microservices Architecture
│   ├── 📂 content/                     # Content Processing Subsystem
│   │   ├── __init__.py
│   │   └── 📂 services/
│   │       ├── __init__.py
│   │       ├── content_preprocessor.py  # File/ES/LLM content processing
│   │       ├── course_manager.py        # Course lifecycle management
│   │       ├── course_mapper.py         # Stage 1: LO+KC generation wrapper
│   │       ├── kli_application.py       # Stage 2: LP+IM tagging wrapper
│   │       └── knowledge_graph_generator.py # Neo4j KG generation wrapper
│   │
│   ├── 📂 learner/                     # Learner Processing Subsystem
│   │   ├── __init__.py
│   │   └── 📂 services/
│   │       ├── __init__.py
│   │       ├── graph_query_engine.py    # Neo4j query service
│   │       └── learning_tree_handler.py # PLT generation service
│   │
│   ├── 📂 sme/                         # Subject Matter Expert Subsystem (placeholder)
│   └── 📂 analytics/                   # Analytics Subsystem (placeholder)
│
├── 📂 pipeline/                         # Pipeline Coordination
│   ├── coordinator.py                  # Automatic pipeline coordinator
│   └── semi_automatic_coordinator.py   # Faculty approval workflow coordinator
│
├── 📂 graph/                           # Core LangGraph Components
│   ├── agents.py                       # Stage 1 & 2 LangGraph agents
│   ├── agents_plt.py                   # PLT generation agents (6 agents)
│   ├── config.py                       # LLM configuration
│   ├── db.py                           # Neo4j database functions
│   ├── edges.py                        # LangGraph routing logic
│   ├── graph.py                        # Stage 1 & 2 LangGraph definitions
│   ├── learner_flow.py                 # Learner workflow logic
│   ├── pdf_loader.py                   # PDF processing utilities
│   ├── plt_generator.py                # PLT LangGraph pipeline
│   ├── state.py                        # LangGraph state schemas
│   ├── unified_state.py                # Unified state management
│   └── 📂 utils/
│       ├── __init__.py
│       └── es_to_kg.py                 # Elasticsearch to KG transformation
│
├── 📂 utils/                           # System Utilities
│   └── logging.py                      # Enhanced logging with performance tracking
│
├── 📂 prompts/                         # Agent Prompts
│   ├── 📂 stage1/                     # Stage 1 agent prompts
│   │   ├── analyst.txt
│   │   ├── curator.txt
│   │   ├── kc_classifier.txt
│   │   ├── lo_generator.txt
│   │   └── researcher.txt
│   └── 📂 stage2/                     # Stage 2 agent prompts
│       ├── instruction_agent.txt
│       └── lp_identifier.txt
│
├── 📂 data_large/                      # Sample/Test Data
│   ├── memory_management.txt
│   ├── operating_systems_intro.txt
│   └── process_scheduling.txt
│
├── 📂 archive/                         # Archived Legacy Components
│   └── 📂 legacy_orchestrators/
│       ├── manual_orchestrator.py
│       ├── orchestrator.py
│       └── test_unified_orchestrator.py
│
├── 📂 Alternatives/                    # Alternative Implementations
│   └── es_to_kg.py
│
├── 📂 logs/                           # System Logs
│   ├── content_preprocessor.log
│   ├── performance_tracker.log
│   └── test.log
│
├── 🔧 Configuration Files
├── main.py                            # Enhanced CLI (automatic + semi-automatic + legacy)
├── config.yaml                        # System configuration
├── requirements.txt                    # Python dependencies
├── docker-compose.yml                 # Docker orchestration
│
├── 📊 Data Files
├── knowledge_extracts.json            # Extracted knowledge data
├── ostep_chunks.json                  # OS textbook chunks
│
├── 🧪 Test Files
├── test_es_integration.py             # Elasticsearch integration tests
├── test_generate_plt.py               # PLT generation tests
├── test_insert_os_data.py             # Database insertion tests
├── test_plt_clean.py                  # PLT cleanup tests
├── test_universal_orchestrator.py     # Orchestrator tests
│
├── 📚 Documentation
├── README.md                          # Main project documentation
├── RESOURCE_SCHEMA.md                 # Resource schema definitions
├── MICROSERVICES_MIGRATION_SUMMARY.md # Migration documentation
├── FACULTY_APPROVAL_WORKFLOW.md       # Faculty workflow documentation
├── SYSTEM_ARCHITECTURE_OVERVIEW.md    # This file
│
└── 🔧 Utility Scripts
    └── generate_kg_from_es.py         # ES to KG pipeline script
```

## 🏗️ System Architecture Overview

### 🎯 Core Design Principles

1. **Hybrid Monorepo with Subsystem Organization**
2. **LangGraph-based Multi-Agent Orchestration** 
3. **Faculty Approval Gates for Academic Quality**
4. **Microservices with Wrapper Pattern (preserves existing agents)**
5. **Configuration-Driven (no hardcoded values)**
6. **Enhanced Observability & Logging**

### 🔄 Three Pipeline Modes

#### 1. 🤖 Fully Automatic Pipeline
```bash
python main.py auto --course_id CSN
# Content → LO → KC → KG → PLT (no human intervention)
```

#### 2. 🎓 Semi-Automatic Faculty Approval Pipeline  
```bash
python main.py faculty-start --course_id CSN --faculty_id PROF_123
# Content → LO → 🔵 Faculty Approval → KC → 🟡 Faculty Confirmation → KG → 🟢 Faculty Finalization → PLT (with learner input)
```

#### 3. 🔧 Manual Legacy Pipeline
```bash
python main.py stage1  # Individual stage execution
```

### 🏛️ Faculty Approval Workflow (3-Tier)

```
Stage 1: 🔵 APPROVE  → FACD (Faculty Approved Course Details)
Stage 2: 🟡 CONFIRM  → FCCS (Faculty Confirmed Course Structure)  
Stage 3: 🟢 FINALIZE → FFCS (Faculty Finalized Course Structure)
Stage 4: 🚀 PLT Generation (with learner input)
```

### 🔧 Microservices (8 Total)

#### Content Subsystem (5 services)
1. **Content Preprocessor**: File/ES/LLM processing
2. **Course Manager**: Course lifecycle management
3. **Course Mapper**: Stage 1 LO+KC generation (wrapper)
4. **KLI Application**: Stage 2 LP+IM tagging (wrapper)
5. **Knowledge Graph Generator**: Neo4j KG creation (wrapper)

#### Learner Subsystem (2 services)
6. **Learning Tree Handler**: PLT generation (wrapper)
7. **Graph Query Engine**: Neo4j queries

#### Planned Subsystems
8. **SME Subsystem**: Subject Matter Expert workflows
9. **Analytics Subsystem**: Cross-cutting analytics

### 🤖 LangGraph Agent Architecture

#### Stage 1 Pipeline (5 agents)
```
Researcher → LO Generator → Curator → Analyst → KC Classifier
```

#### Stage 2 Pipeline (2 agents)  
```
LP Identifier → Instruction Agent
```

#### PLT Pipeline (6 agents)
```
Accept Learner → Prioritize LOs → Map KCs → Sequence KCs → Match IMs → Link Resources
```

### 🗄️ Database Integration

- **Neo4j**: Knowledge graphs, PLTs, relationships
- **Elasticsearch**: Content indexing, chunk storage
- **MongoDB**: Document storage (planned)
- **PostgreSQL**: Structured data, faculty approvals (planned)
- **Redis**: Session management, queues (planned)

### 🔌 Key Technologies

- **LangGraph**: Multi-agent orchestration
- **LangChain**: LLM integration  
- **Ollama**: Local LLM (Qwen3:4b)
- **Neo4j**: Graph database
- **Elasticsearch**: Search engine
- **FastAPI**: API framework (planned)
- **Docker**: Containerization

### 🎯 Workflow Execution Patterns

#### Content Processing Flow
```
PDF/ES/LLM → Content Preprocessor → Course Mapper (Stage 1) → KLI Application (Stage 2) → KG Generator
```

#### Learner Processing Flow  
```
Learner Context → Learning Tree Handler (PLT) → Graph Query Engine → Personalized Results
```

#### Faculty Approval Flow
```
Draft LOs → Faculty Review → FACD → Draft Structure → Faculty Review → FCCS → Draft KG → Faculty Review → FFCS
```

### 🚀 Deployment Architecture

- **Development**: Local Ollama + Neo4j + ES
- **Production**: Docker Compose orchestration
- **Scalability**: Kubernetes-ready microservices
- **UI Integration**: REST API endpoints + WebSocket

### 📊 Current Status

- ✅ **Universal Orchestrator**: Working with 6 microservices
- ✅ **Faculty Approval Workflow**: Complete 3-tier system
- ✅ **Configuration Management**: YAML-based, no hardcoded values
- ✅ **Enhanced Logging**: Performance tracking, structured logs
- ✅ **Automatic Pipelines**: End-to-end automation working
- ✅ **Semi-Automatic Pipelines**: Faculty gates implemented
- ✅ **Legacy Compatibility**: All existing functions preserved

### 🔄 Integration Points for UI

#### API Endpoints (Planned)
```
POST /api/faculty/workflow/start
POST /api/faculty/workflow/{course_id}/approve
POST /api/faculty/workflow/{course_id}/confirm  
POST /api/faculty/workflow/{course_id}/finalize
GET  /api/faculty/workflow/{course_id}/status
POST /api/learner/plt/generate
GET  /api/courses/{course_id}/structure
```

### 🎯 Next Development Priorities

1. **REST API Layer**: FastAPI integration
2. **Persistent Storage**: Database migrations
3. **UI Framework**: React/Vue.js frontend  
4. **Authentication**: Faculty/learner auth
5. **Testing**: Comprehensive pytest suite
6. **Documentation**: API documentation

This architecture successfully bridges the gap between full automation and academic oversight, providing a production-ready educational system with proper faculty governance while maintaining the power of LangGraph multi-agent orchestration. 