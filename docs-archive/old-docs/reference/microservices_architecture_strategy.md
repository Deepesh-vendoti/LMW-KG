# Microservices Architecture Strategy - Reference Documentation

## 📋 **Overview**

This document captures the **core architectural strategy** for the LangGraph Knowledge Graph system's microservices design. This is a **reference document** for maintaining consistency and understanding the rationale behind our architectural decisions.

**Date**: January 2024  
**Status**: Implemented and Validated  
**Architecture Pattern**: Wrapper Services + Core Logic Separation

---

## 🎯 **Core Strategic Principle**

### **"Preserve graph/ as Core Logic Layer + Expose Everything via Consistent Wrappers"**

**Rationale**: This strategy ensures:
- Single source of truth for business logic
- Consistent service interfaces
- Maximum testability and maintainability
- Clear separation of concerns
- Scalable microservices architecture

---

## 🏗️ **Architecture Layers**

```
📊 Presentation Layer    → CLI/UI/API endpoints
    ↓
🔌 Service Layer        → subsystems/*/services/ (8 microservices)  
    ↓
🧠 Business Logic Layer → graph/ (LangGraph agents, core algorithms)
    ↓  
💾 Data Layer          → Neo4j, Redis, Elasticsearch
```

### **Layer Responsibilities**

#### **🔌 Service Layer (`subsystems/*/services/`)**
- **Purpose**: Thin wrappers providing consistent interfaces
- **Responsibilities**: 
  - Input validation and sanitization
  - State management and orchestration compatibility
  - Error handling and logging
  - Response formatting
- **Anti-pattern**: NO business logic should live here

#### **🧠 Business Logic Layer (`graph/`)**
- **Purpose**: Core algorithms and domain logic
- **Contains**: 
  - LangGraph agents and pipelines
  - Knowledge graph operations
  - PLT generation algorithms
  - Data transformation utilities
- **Principle**: Single source of truth for all business rules

#### **💾 Data Layer**
- **Purpose**: Data persistence and retrieval
- **Technologies**: Neo4j (KG), Redis (cache), Elasticsearch (search)
- **Access**: Only through `graph/db.py` and utility modules

---

## 🎯 **8-Service Target Architecture**

### **Content Subsystem (5 services)**

| Service | File | Core Logic Delegation | Purpose |
|---------|------|----------------------|---------|
| Course Mapper | `course_mapper.py` | → `graph.graph.build_graph_stage_1()` | LO → KC mapping |
| KLI Application | `kli_application.py` | → `graph.graph.build_graph_stage_2()` | LP → IM mapping |
| Knowledge Graph Generator | `knowledge_graph_generator.py` | → `graph.db.*` | KG creation/storage |
| Content Preprocessor | `content_preprocessor.py` | → `graph.pdf_loader` + utilities | Content parsing/chunking |
| Course Manager | `course_manager.py` | → Content workflow orchestration | Input source management |

### **Learner Subsystem (3 services)**

| Service | File | Core Logic Delegation | Purpose |
|---------|------|----------------------|---------|
| Learning Tree Handler | `learning_tree_handler.py` | → `graph.plt_generator.run_plt_generator()` | PLT generation |
| Graph Query Engine | `graph_query_engine.py` | → `graph.db` query functions | KG querying |
| Learner Profile Service | `learner_profile_service.py` | → `graph.learner_profiling.*` | Profile management |

---

## ✅ **Wrapper Pattern Implementation**

### **Template: Correct Wrapper Pattern**

```python
"""
Service Template - Following Wrapper Pattern
Delegates to core logic in graph/
"""

from typing import Dict, Any
from orchestrator.state import UniversalState, ServiceStatus, SubsystemType

class ExampleService:
    """
    Microservice following wrapper pattern.
    
    Architecture: Thin wrapper around graph/example_logic.py
    """
    
    def __init__(self):
        self.service_id = "example_service"
        self.subsystem = SubsystemType.CONTENT  # or LEARNER
        
    def __call__(self, state: UniversalState) -> UniversalState:
        """Main entry point - delegates to core logic."""
        try:
            # 1. Extract and validate inputs
            input_data = self._extract_inputs(state)
            
            # 2. Delegate to core business logic in graph/
            result = self._delegate_to_core_logic(input_data)
            
            # 3. Format response and update state
            state.update({
                "service_result": result,
                "service_status": ServiceStatus.COMPLETED,
                "last_service": self.service_id
            })
            
            return state
            
        except Exception as e:
            # 4. Handle errors consistently
            state.update({
                "service_status": ServiceStatus.FAILED,
                "error": str(e),
                "last_service": self.service_id
            })
            return state
    
    def _delegate_to_core_logic(self, input_data):
        """Delegate to core business logic."""
        # Import core logic from graph/
        from graph.example_logic import process_example
        
        # Delegate to core algorithm
        return process_example(input_data)
```

### **Real Example: Course Mapper Service**

```python
# subsystems/content/services/course_mapper.py
class CourseMapperService:
    def _execute_stage1_pipeline(self, chunks):
        """Execute Stage 1 LangGraph pipeline using existing agents."""
        try:
            # Import existing Stage 1 graph
            from graph.graph import build_graph_stage_1
            from graph.state import GraphState
            
            # Delegate to core business logic
            pipeline = build_graph_stage_1()
            result = pipeline.invoke({"messages": [HumanMessage(content=chunks)]})
            
            return self._extract_structured_output(result)
```

---

## 🏆 **Architecture Benefits**

### **1. 📦 Single Responsibility Principle**
- Each service has ONE clear purpose
- Core logic separated from interface concerns
- Easy to understand and modify

### **2. 🧪 Enhanced Testability**
```python
# Unit Tests: Test core logic independently
def test_plt_generation():
    from graph.plt_generator import run_plt_generator
    result = run_plt_generator("test_learner", "test_course")
    assert result["status"] == "success"

# Integration Tests: Test service wrappers with mocks
def test_learning_tree_handler_service():
    service = LearningTreeHandlerService()
    state = {"learner_id": "test", "course_id": "test"}
    result = service(state)
    assert result["service_status"] == ServiceStatus.COMPLETED
```

### **3. 🔄 Scalability and Flexibility**
- Add new services without touching core logic
- Modify algorithms without breaking service interfaces
- Easy to version and deploy independently
- Clear dependency management

### **4. 🛠️ Maintainability**
- Single source of truth for business logic (`graph/`)
- Consistent service interface pattern
- Clear error handling and logging
- Reduced code duplication

### **5. 🎯 Clear Ownership**
- **Frontend/CLI**: Calls services for specific operations
- **Services**: Handle orchestration and state management
- **Graph**: Contains all domain logic and algorithms
- **Data**: Manages persistence through `graph/db.py`

---

## ❌ **Anti-Patterns to Avoid**

### **1. Logic in Services (BAD)**
```python
# DON'T DO THIS
class CourseMapperService:
    def __call__(self, state):
        # BAD: Complex business logic in service
        los = self._complex_lo_extraction(text)  # 100+ lines
        kcs = self._advanced_kc_mapping(los)     # 200+ lines
        return self._format_response(kcs)        # Business logic here
```

### **2. Direct Data Access from Services (BAD)**
```python
# DON'T DO THIS
class LearningTreeService:
    def __call__(self, state):
        # BAD: Direct database access from service
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687")
        # Direct DB operations here...
```

### **3. Monolithic Services (BAD)**
```python
# DON'T DO THIS
class MonolithicKGService:
    def do_everything(self):
        # BAD: Multiple responsibilities in one service
        self.process_content()     # 500 lines
        self.generate_kg()         # 300 lines  
        self.create_plt()          # 400 lines
        self.manage_courses()      # 200 lines
```

---

## ✅ **Best Practices**

### **1. Service Design**
- **Single Purpose**: Each service handles one domain area
- **Thin Wrappers**: Minimal logic, maximum delegation
- **Consistent Interface**: All services follow same pattern
- **Error Handling**: Standardized error responses

### **2. Core Logic Organization**
- **Domain Separation**: Clear modules for different concerns
- **Reusability**: Functions can be used by multiple services
- **Testing**: Easy to unit test without service overhead
- **Documentation**: Clear APIs and function signatures

### **3. State Management**
- **Universal State**: Consistent state object across services
- **Service Tracking**: Track which service last processed state
- **Error Propagation**: Clear error handling and recovery
- **Status Reporting**: Standardized status reporting

### **4. Import Strategy**
- **Lazy Imports**: Import core logic only when needed
- **Fallback Handling**: Graceful handling of missing modules
- **Dependency Management**: Clear dependency boundaries

---

## 🔧 **Implementation Guidelines**

### **Adding a New Service**

1. **Create Service File**
   ```bash
   touch subsystems/{subsystem}/services/{service_name}.py
   ```

2. **Follow Wrapper Template**
   - Inherit from base service pattern
   - Implement `__call__` method for orchestrator compatibility
   - Delegate to `graph/` modules

3. **Create Core Logic Module** (if needed)
   ```bash
   touch graph/{domain_logic}.py
   ```

4. **Update Subsystem Exports**
   ```python
   # subsystems/{subsystem}/services/__init__.py
   from .{service_name} import {ServiceClass}
   ```

5. **Add Tests**
   ```bash
   touch tests/test_{service_name}.py
   touch tests/test_{core_logic}.py
   ```

### **Refactoring Existing Logic**

1. **Identify Business Logic** in services
2. **Extract to Graph Module**
3. **Update Service to Delegate**
4. **Verify Tests Pass**
5. **Update Documentation**

---

## 📊 **Quality Metrics**

### **Service Quality Indicators**
- **Lines of Code**: Services should be < 200 lines
- **Cyclomatic Complexity**: Low complexity in services
- **Test Coverage**: High coverage for `graph/` modules
- **Dependency Count**: Minimal external dependencies in services

### **Architecture Compliance**
- **✅ All business logic in `graph/`**
- **✅ Services are thin wrappers**
- **✅ Consistent interface patterns**
- **✅ Clear error handling**
- **✅ Proper state management**

---

## 🚀 **Future Considerations**

### **Scaling Strategies**
- **Service Registry**: Dynamic service discovery
- **Health Checks**: Service health monitoring
- **Analytics**: Service usage and performance metrics
- **Versioning**: API versioning for service evolution

### **Advanced Patterns**
- **Circuit Breakers**: Fault tolerance patterns
- **Retry Logic**: Resilient service calls
- **Caching**: Response caching for performance
- **Event Sourcing**: Event-driven architectures

---

## 📚 **Related Documentation**

- `FACULTY_APPROVAL_WORKFLOW.md` - Faculty workflow implementation
- `SYSTEM_ARCHITECTURE_OVERVIEW.md` - Complete system architecture
- `graph/README.md` - Core logic documentation
- `subsystems/README.md` - Subsystem organization

---

## 🎯 **Summary**

The **"Preserve graph/ as Core Logic + Consistent Wrappers"** strategy provides:

1. **🏗️ Clean Architecture**: Clear separation of concerns
2. **🧪 High Testability**: Independent testing of core logic
3. **🔄 Easy Maintenance**: Single source of truth for business rules
4. **📈 Scalability**: Easy to add services and modify logic
5. **🎯 Consistency**: Uniform service interface patterns

This architecture ensures the LangGraph Knowledge Graph system remains **maintainable, testable, and scalable** as it grows in complexity and scope.

**Key Takeaway**: Services are **interfaces**, `graph/` is **intelligence**. 