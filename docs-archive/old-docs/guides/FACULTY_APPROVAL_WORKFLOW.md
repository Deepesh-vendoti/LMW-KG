# Faculty Approval Workflow System

## 🎯 Overview

The **Semi-Automatic Faculty Approval Workflow** implements a three-tier approval system that balances automation with essential faculty oversight for academic quality assurance.

### 📋 Three-Tier Faculty Workflow

```
1. Content Upload → LO Generation → 🔵 FACULTY APPROVES → FACD
                                   ↓ (with editing capability)

2. FACD → KC/LP/IM/Resource Generation → 🟡 FACULTY CONFIRMS → FCCS  
                                        ↓ (with editing capability)

3. FCCS → Knowledge Graph Generation → 🟢 FACULTY FINALIZES → FFCS
                                      ↓ (final lock-in)

4. FFCS → Course Structure Locked → 🚀 LEARNER REQUESTS PLT → PLT Generation
```

### 🏛️ Academic Terminology

- **🔵 APPROVE**: Faculty reviews and approves Learning Objectives
- **🟡 CONFIRM**: Faculty reviews and confirms complete course structure  
- **🟢 FINALIZE**: Faculty reviews and finalizes knowledge graph (locks structure)
- **🚀 PLT GENERATION**: Learner-triggered personalized learning tree creation

### 📄 Document Progression

- **FACD**: Faculty Approved Course Details (after LO approval)
- **FCCS**: Faculty Confirmed Course Structure (after structure confirmation)
- **FFCS**: Faculty Finalized Course Structure (after KG finalization)
- **PLT**: Personalized Learning Tree (generated per learner request with context)

## 🚀 Getting Started

### 1. Start Faculty Workflow

```bash
python main.py faculty-start --course_id CSN --faculty_id PROF_123 --source elasticsearch
```

**What happens:**
- Content is processed from specified source
- Learning Objectives are generated automatically
- System pauses for faculty review
- Faculty receives draft LOs for approval

### 2. Faculty Approves Learning Objectives

```bash
python main.py faculty-approve --course_id CSN --action approve
```

**Faculty Actions:**
- `approve`: Accept LOs and proceed to structure generation
- `edit`: Request edits to LOs (requires UI integration)
- `reject`: Reject LOs and request regeneration

**What happens after approval:**
- **FACD** (Faculty Approved Course Details) is generated
- System automatically generates complete course structure (KC→LP→IM→Resources)
- System pauses for faculty confirmation

### 3. Faculty Confirms Course Structure

```bash
python main.py faculty-confirm --course_id CSN --action confirm
```

**What happens after confirmation:**
- **FCCS** (Faculty Confirmed Course Structure) is generated
- System automatically generates knowledge graph
- System pauses for faculty finalization

### 4. Faculty Finalizes Knowledge Graph

```bash
python main.py faculty-finalize --course_id CSN --action finalize
```

**What happens after finalization:**
- **FFCS** (Faculty Finalized Course Structure) is generated
- Course structure is locked
- Course is ready for learner PLT requests
- **Faculty Workflow Complete!**

### 5. Learner Requests PLT Generation

```bash
python main.py learner-plt --course_id CSN --learner_id R001 --learning_style visual --experience_level intermediate
```

**What happens:**
- System verifies course structure is finalized (FFCS exists)
- PLT is generated using learner context and finalized course structure
- Personalized learning path created for specific learner
- **Complete Workflow Finished!**

### 6. Check Workflow Status

```bash
python main.py faculty-status --course_id CSN
```

Shows current stage, approval history, and what documents have been generated.

## 🏗️ Architecture Components

### 1. Faculty Approval States (`orchestrator/approval_states.py`)

**Key Classes:**
- `FacultyApprovalState`: Manages workflow state for a course
- `FacultyWorkflowStage`: Enum defining workflow stages
- `FacultyAction`: Enum defining faculty actions (APPROVE, CONFIRM, FINALIZE)
- `ApprovalStateManager`: Global state management

**Features:**
- Persistent state tracking across approval stages
- Comprehensive approval history logging
- Validation of stage transitions
- Support for editing at each stage

### 2. Semi-Automatic Coordinator (`pipeline/semi_automatic_coordinator.py`)

**Key Class:**
- `SemiAutomaticPipelineCoordinator`: Orchestrates faculty approval workflow

**Methods:**
- `start_course_workflow()`: Begin faculty workflow
- `faculty_approve_learning_objectives()`: Process LO approval
- `faculty_confirm_course_structure()`: Process structure confirmation  
- `faculty_finalize_knowledge_graph()`: Process KG finalization
- `proceed_to_plt_generation()`: Automatic PLT generation

### 3. Enhanced CLI (`main.py`)

**New Commands:**
- `faculty-start`: Start faculty workflow
- `faculty-approve`: Faculty approve LOs
- `faculty-confirm`: Faculty confirm structure
- `faculty-finalize`: Faculty finalize KG
- `faculty-status`: Check workflow status

## 🔄 Workflow States

### Stage Progression

1. **`CONTENT_PROCESSING`**: Initial content processing (automatic)
2. **`AWAITING_LO_APPROVAL`**: ⏸️ Paused for faculty LO approval
3. **`LO_APPROVED`**: LOs approved, FACD generated (automatic structure generation)
4. **`AWAITING_STRUCTURE_CONFIRMATION`**: ⏸️ Paused for faculty structure confirmation
5. **`STRUCTURE_CONFIRMED`**: Structure confirmed, FCCS generated (automatic KG generation)
6. **`AWAITING_KG_FINALIZATION`**: ⏸️ Paused for faculty KG finalization
7. **`KG_FINALIZED`**: KG finalized, FFCS generated (ready for PLT)
8. **`PLT_GENERATION`**: Automatic PLT generation (no faculty input)
9. **`COMPLETED`**: Workflow complete

### Faculty Actions at Each Stage

**LO Approval Stage:**
- `APPROVE`: Accept LOs → FACD generated → Structure generation
- `EDIT`: Request LO edits → Stay in approval stage
- `REJECT`: Reject LOs → Regenerate LOs

**Structure Confirmation Stage:**
- `CONFIRM`: Accept structure → FCCS generated → KG generation
- `EDIT`: Request structure edits → Stay in confirmation stage
- `REJECT`: Reject structure → Regenerate structure

**KG Finalization Stage:**
- `FINALIZE`: Accept KG → FFCS generated → PLT generation
- `EDIT`: Request KG edits → Stay in finalization stage
- `REJECT`: Reject KG → Regenerate KG

## 📊 UI Integration Points

### For Web Interface Integration

**API Endpoints Needed:**
```python
POST /api/faculty/workflow/start
POST /api/faculty/workflow/{course_id}/approve
POST /api/faculty/workflow/{course_id}/confirm  
POST /api/faculty/workflow/{course_id}/finalize
GET  /api/faculty/workflow/{course_id}/status
```

**UI Components Needed:**
1. **LO Review Interface**: Display/edit learning objectives
2. **Structure Review Interface**: Display/edit complete course structure
3. **KG Visualization Interface**: Display/edit knowledge graph
4. **Approval Action Buttons**: Approve/Confirm/Finalize/Edit/Reject
5. **Comments/Feedback Forms**: Faculty feedback at each stage
6. **Progress Tracker**: Visual workflow progress indicator

### UI Data Format

Each stage provides `ui_data` with:
```json
{
  "approval_stage": "🔵 Learning Objectives Approval",
  "instructions": "Please review and approve the generated learning objectives...",
  "actions": ["approve", "edit", "reject"]
}
```

## 🔧 Configuration & Customization

### Approval Workflow Configuration

In `config/config.yaml`:
```yaml
faculty_approval:
  stages:
    - "FACD"  # Faculty Approved Course Design
    - "FCCS"  # Faculty Confirmed Course Structure
    - "FFCS"  # Faculty Finalized Course Specification
  require_approval: true
  allow_editing: true
  auto_proceed_after_approval: true
```

### Timeout & Persistence Settings

```yaml
faculty_approval:
  session_timeout: 86400  # 24 hours
  max_edit_iterations: 3
  auto_save_interval: 300  # 5 minutes
```

## 🧪 Testing the Workflow

### Demo Workflow

```bash
# 1. Start faculty workflow
python main.py faculty-start --course_id DEMO --faculty_id PROF_DEMO --source llm_generated --raw_content "Operating Systems course content"

# 2. Check status
python main.py faculty-status --course_id DEMO

# 3. Approve LOs
python main.py faculty-approve --course_id DEMO --action approve

# 4. Confirm structure  
python main.py faculty-confirm --course_id DEMO --action confirm

# 5. Finalize KG
python main.py faculty-finalize --course_id DEMO --action finalize

# 6. Check final status
python main.py faculty-status --course_id DEMO
```

## 📈 Comparison: Automatic vs Semi-Automatic

### 100% Automatic Pipeline
```bash
python main.py auto --course_id CSN
# Result: Content → LO → KC → KG → PLT (no faculty input)
```

**Pros:** Fast, no human intervention needed
**Cons:** No quality control, no faculty oversight

### Semi-Automatic Faculty Pipeline  
```bash
python main.py faculty-start --course_id CSN --faculty_id PROF_123
# Result: Content → LO → 🔵 Faculty → KC → 🟡 Faculty → KG → 🟢 Faculty → PLT
```

**Pros:** Quality assurance, faculty control, academic standards
**Cons:** Requires faculty time, multiple approval steps

## 🎯 Benefits of Semi-Automatic Approach

### 1. **Academic Quality Assurance**
- Faculty oversight ensures learning objectives align with course goals
- Structure review validates pedagogical soundness
- KG finalization confirms knowledge representation accuracy

### 2. **Flexibility with Control**
- Faculty can edit at each stage without restarting entire workflow
- Maintains academic autonomy while leveraging automation
- Supports institutional approval processes

### 3. **Audit Trail**
- Complete approval history with timestamps
- Faculty comments and feedback preserved
- Compliance with academic governance requirements

### 4. **Scalable Implementation**
- Works with existing LangGraph microservice architecture
- UI-friendly with clear integration points
- Supports multiple concurrent faculty workflows

## 🚀 Production Deployment

### Database Requirements
- Persistent storage for approval states
- Session management for long-running workflows
- Audit logging for compliance

### UI Framework Integration
- React/Vue.js frontend with approval interfaces
- Real-time status updates via WebSocket
- File upload for edited content

### Security Considerations
- Faculty authentication and authorization
- Role-based access control
- Encrypted storage of approval data

---

This semi-automatic faculty approval workflow bridges the gap between full automation and manual oversight, providing the perfect balance for educational institutions requiring both efficiency and academic quality assurance. 