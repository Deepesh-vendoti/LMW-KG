# 🎓 Learner Subsystem

## 🏗️ **Service Flow Architecture**

The Learner Subsystem follows a **sequential flow** with **Query Strategy Manager** as the entry point:

```
🥇 Query Strategy Manager → 🥈 Graph Query Engine → 🥉 Learning Tree Handler
```

## 📋 **Service Order and Dependencies**

### **1. 🥇 Query Strategy Manager** (Entry Point)
- **File**: `query_strategy_manager.py` (154 lines) - **FIRST in execution order**
- **Dependencies**: None (entry point)
- **Inputs**: `learner_id`, `learner_context`
- **Outputs**: `query_strategy`, `query_complexity`
- **Purpose**: Determines optimal query strategy based on learner context

### **2. 🥈 Graph Query Engine** (Second)
- **File**: `graph_query_engine.py` (340 lines) - **SECOND in execution order**
- **Dependencies**: `query_strategy_manager`
- **Inputs**: `course_id`, `query_strategy`
- **Outputs**: `query_results`, `knowledge_graph_data`
- **Purpose**: Executes knowledge graph queries using adaptive strategy

### **3. 🥉 Learning Tree Handler** (Third)
- **File**: `learning_tree_handler.py` (273 lines) - **THIRD in execution order**
- **Dependencies**: `query_strategy_manager`, `graph_query_engine`
- **Inputs**: `learner_id`, `course_id`, `query_strategy`, `query_results`
- **Outputs**: `personalized_learning_tree`, `adaptive_recommendations`
- **Purpose**: Generates personalized learning trees with recommendations

## 🔄 **Execution Flow**

### **Step 1: Query Strategy Manager**
```python
# Entry point - determines learner strategy
learner_context = {"learning_style": "visual", "experience_level": "intermediate"}
query_strategy = query_strategy_manager(learner_context)
# Output: {"strategy": "adaptive_queries", "complexity": "medium"}
```

### **Step 2: Graph Query Engine**
```python
# Uses strategy from Step 1 to execute queries
query_results = graph_query_engine(query_strategy)
# Output: {"concepts": [...], "relationships": [...], "learning_objectives": [...]}
```

### **Step 3: Learning Tree Handler**
```python
# Uses both strategy and results to generate PLT
plt = learning_tree_handler(query_strategy, query_results)
# Output: {"learning_path": [...], "recommendations": [...]}
```

## 📊 **Service Statistics**

| Service | Lines of Code | Dependencies | Timeout |
|---------|---------------|--------------|---------|
| Query Strategy Manager | 154 | 0 | 60s |
| Graph Query Engine | 340 | 1 | 300s |
| Learning Tree Handler | 273 | 2 | 600s |

## 🎯 **Key Features**

### **Query Strategy Manager**
- Decision tree-based learner classification
- Adaptive strategy selection
- Complexity optimization
- Performance monitoring

### **Graph Query Engine**
- Neo4j Cypher query execution
- Strategy-guided query generation
- Knowledge graph data extraction
- Query result filtering

### **Learning Tree Handler**
- Personalized learning tree generation
- 6-agent PLT pipeline integration
- Multi-database storage (Neo4j, Redis, PostgreSQL)
- Adaptive recommendation generation

## 🔧 **Integration Points**

### **With Content Subsystem**
- Receives knowledge graph data from Content Subsystem
- Uses course structure and learning objectives

### **With Universal Orchestrator**
- All services implement `__call__` method for orchestrator compatibility
- State management through `UniversalState`
- Service status tracking and error handling

## 📝 **Usage Example**

```python
from orchestrator.service_registry import get_service_registry

# Get learner subsystem services
registry = get_service_registry()
learner_services = registry.get_subsystem_services(SubsystemType.LEARNER)

# Execute in order
state = {
    "learner_id": "R000",
    "learner_context": {"learning_style": "visual"},
    "course_id": "OSN"
}

# Step 1: Query Strategy Manager
strategy_service = registry.get_service("query_strategy_manager")
state = strategy_service.callable(state)

# Step 2: Graph Query Engine
query_service = registry.get_service("graph_query_engine")
state = query_service.callable(state)

# Step 3: Learning Tree Handler
plt_service = registry.get_service("learning_tree_handler")
state = plt_service.callable(state)
```

## 🚀 **Future Enhancements**

- **SME Subsystem Integration**: Expert knowledge validation
- **Analytics Subsystem Integration**: Performance analytics and insights
- **Real-time Adaptation**: Dynamic strategy adjustment based on learner performance
- **Advanced Personalization**: Machine learning-based recommendation engine 