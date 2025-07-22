# 🔄 Corrected Microservices Sequential Flow - LangGraph Knowledge Graph System

## 🎯 **Updated Sequential Execution Order**

### **Phase 1: Content Processing Pipeline (CORRECTED)**

| Order | Service | Purpose | Input | Process | Output | Database |
|-------|---------|---------|--------|---------|---------|-----------|
| **1** | **Course Manager** | Course Initialization | Faculty input (course purpose, objectives) | LLM course outline generation | Draft outline → Faculty approval → Document upload request | PostgreSQL |
| **2** | **Content Preprocessor** | Document Processing | Documents uploaded after Course Manager approval | Chunking, metadata extraction, indexing | Structured chunks | MongoDB + Elasticsearch |
| **3** | **Course Mapper** | Learning Structure | Content chunks | 5-agent LangGraph pipeline | Learning Objectives + Knowledge Components | Neo4j |
| **4** | **KLI Application** | Process Tagging | LOs + KCs | 2-agent LangGraph pipeline | Learning Processes + Instruction Methods | Neo4j |
| **5** | **Knowledge Graph Generator** | Graph Creation | All structured data | Complete KG assembly | Final Knowledge Graph | Multi-database |

## 🔄 **Corrected Data Flow**

### **Complete Faculty-Driven Workflow**

```
1. Faculty Input: Course Purpose & Context
   ↓
2. Course Manager: LLM Course Outline Generation
   ↓
3. Faculty Approval Gate: Confirm Outline + Upload Documents
   ↓
4. Content Preprocessor: Process Uploaded Documents
   ↓
5. Course Mapper: Extract Learning Objectives & Knowledge Components
   ↓
6. KLI Application: Identify Learning Processes & Instruction Methods
   ↓
7. Knowledge Graph Generator: Create Complete Knowledge Graph
   ↓
8. Learner Pipeline: Query Strategy → Graph Query → PLT Generation
```

## 🏗️ **Required Code Implementation Changes**

### **1. Universal Orchestrator Service Execution Order**

**File**: `orchestrator/universal_orchestrator.py`

**Current Issue**: 
```python
service_execution_order = ["content_preprocessor", "course_mapper", "kli_application", "knowledge_graph_generator"]
```

**Required Fix**:
```python
service_execution_order = ["course_manager", "content_preprocessor", "course_mapper", "kli_application", "knowledge_graph_generator"]
```

### **2. Service Registry Dependencies**

**File**: `orchestrator/service_registry.py`

**Current Issue**: Content Preprocessor has no dependencies
**Required Fix**: Content Preprocessor should depend on Course Manager

```python
# In ServiceDefinition for content_preprocessor
dependencies=["course_manager"]  # Add this dependency
```

### **3. Course Manager Service Enhancement**

**File**: `subsystems/content/services/course_manager.py`

**Required Enhancements**:
```python
class CourseManagerService:
    def generate_course_outline(self, faculty_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate LLM-based course outline from faculty input
        
        Args:
            faculty_input: {
                "course_purpose": str,
                "target_audience": str,
                "learning_goals": List[str],
                "duration": str,
                "complexity_level": str
            }
        
        Returns:
            {
                "course_outline": Dict,
                "requires_faculty_approval": bool,
                "suggested_content_areas": List[str]
            }
        """
        # LLM integration for course outline generation
        
    def request_document_upload(self, course_id: str, outline_approved: bool) -> Dict[str, Any]:
        """
        After faculty approval, request document upload
        """
        # Document upload workflow initiation
```

### **4. Faculty Approval Workflow Integration**

**File**: `orchestrator/approval_states.py`

**Required New Stage**:
```python
class FacultyWorkflowStage(str, Enum):
    # Add new initial stage
    AWAITING_COURSE_OUTLINE_APPROVAL = "awaiting_course_outline_approval"
    COURSE_OUTLINE_APPROVED = "course_outline_approved"
    DOCUMENTS_UPLOAD_REQUESTED = "documents_upload_requested"
    
    # Existing stages follow...
```

### **5. Content Preprocessor Dependency Check**

**File**: `subsystems/content/services/content_preprocessor.py`

**Required Enhancement**:
```python
def can_execute(self, state: UniversalState) -> Tuple[bool, str]:
    """
    Content Preprocessor can only execute after Course Manager completion
    """
    course_manager_status = state.get("service_statuses", {}).get("course_manager")
    
    if course_manager_status != ServiceStatus.COMPLETED:
        return False, "Course Manager must complete first - faculty outline approval required"
    
    # Check if documents are uploaded
    if not state.get("uploaded_documents"):
        return False, "No documents uploaded after Course Manager approval"
        
    return True, "Ready to process uploaded documents"
```

### **6. State Management Updates**

**File**: `orchestrator/state.py`

**Required State Fields**:
```python
class UniversalState(TypedDict, total=False):
    # Add course initialization fields
    course_outline: Optional[Dict[str, Any]]
    faculty_outline_approved: Optional[bool]
    uploaded_documents: Optional[List[Dict[str, Any]]]
    course_initialization_complete: Optional[bool]
```

## 🚀 **Implementation Steps**

### **Step 1: Update Service Execution Order**
```bash
# Edit orchestrator/universal_orchestrator.py
# Change service_execution_order to start with course_manager
```

### **Step 2: Update Service Dependencies**
```bash
# Edit orchestrator/service_registry.py  
# Add course_manager as dependency for content_preprocessor
```

### **Step 3: Enhance Course Manager Service**
```bash
# Edit subsystems/content/services/course_manager.py
# Add LLM course outline generation
# Add document upload request functionality
```

### **Step 4: Update Content Preprocessor**
```bash
# Edit subsystems/content/services/content_preprocessor.py
# Add dependency check for course_manager completion
# Add document upload validation
```

### **Step 5: Update Approval Workflow**
```bash
# Edit orchestrator/approval_states.py
# Add course outline approval stage
# Update workflow progression
```

### **Step 6: Update State Management**
```bash
# Edit orchestrator/state.py
# Add course initialization state fields
```

### **Step 7: Test the Corrected Flow**
```bash
# Run integration tests
python test_universal_orchestrator.py

# Test faculty workflow
python main.py faculty-start --course_id TEST_COURSE --faculty_id PROF_123
```

## ✅ **Verification Checklist**

- [ ] Course Manager executes first in content pipeline
- [ ] Course Manager generates LLM course outline from faculty input
- [ ] Faculty approval gate before document upload
- [ ] Content Preprocessor waits for Course Manager completion
- [ ] Document upload happens after Course Manager approval
- [ ] Service dependencies properly configured
- [ ] State management tracks course initialization
- [ ] Faculty workflow includes outline approval
- [ ] Integration tests pass with new flow

## 📊 **Expected Behavior After Implementation**

### **Correct Flow Sequence:**
1. **Faculty starts course** → Provides course purpose, objectives, context
2. **Course Manager activates** → Uses LLM to generate broad course outline
3. **Faculty reviews outline** → Approves/edits/rejects the generated outline  
4. **Document upload requested** → Faculty uploads relevant course materials
5. **Content Preprocessor starts** → Processes uploaded documents into chunks
6. **Pipeline continues** → Course Mapper → KLI → Knowledge Graph Generator

This ensures that the **Course Manager is the true entry point** that initializes the entire content processing pipeline with proper faculty governance from the very beginning.
