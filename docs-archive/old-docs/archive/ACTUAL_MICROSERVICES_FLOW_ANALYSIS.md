# 🔍 **ACTUAL MICROSERVICES FLOW ANALYSIS**
## Based on Real Code Implementation (Not Documentation)

### 🚨 **CRITICAL FINDING**: Course Manager is NOT in execution flow!

After examining the actual code in `/Users/drg/Projects/langgraph-kg/orchestrator/universal_orchestrator.py`, here's the **REAL microservices execution order**:

---

## 🤖 **1. AUTOMATIC PIPELINE** (Full Pipeline)

### **Content Subsystem Execution Order** (Line 289 in universal_orchestrator.py):

```python
service_execution_order = ["content_preprocessor", "course_mapper", "kli_application", "knowledge_graph_generator"]
```

**ACTUAL FLOW:**
```
1️⃣ Content Preprocessor → Document processing & chunking
2️⃣ Course Mapper → 5 LangGraph agents (LO + KC extraction)  
3️⃣ KLI Application → 2 LangGraph agents (LP + IM tagging)
4️⃣ Knowledge Graph Generator → Neo4j storage
```

### **Learner Subsystem Execution Order** (Line 329 in universal_orchestrator.py):

```python
service_execution_order = ["query_strategy_manager", "graph_query_engine", "learning_tree_handler"]
```

**ACTUAL FLOW:**
```
1️⃣ Query Strategy Manager → Learner classification & routing
2️⃣ Graph Query Engine → Neo4j query execution
3️⃣ Learning Tree Handler → 6 LangGraph agents (PLT generation)
```

**COMMAND:**
```bash
python main.py auto --course_id CSN --source elasticsearch
```

---

## 📚 **2. CONTENT-ONLY PIPELINE**

**ACTUAL EXECUTION ORDER:**
```
Content Preprocessor → Course Mapper → KLI Application → Knowledge Graph Generator
```

**IMPLEMENTATION:** `pipeline/coordinator.py` - `process_course_content()` function

**COMMAND:**
```bash
python main.py content --course_id CSN --upload_type elasticsearch
```

---

## 👤 **3. LEARNER-ONLY PIPELINE**

**ACTUAL EXECUTION ORDER:**
```
Query Strategy Manager → Graph Query Engine → Learning Tree Handler
```

**IMPLEMENTATION:** `pipeline/coordinator.py` - `generate_learner_plt()` function

**COMMAND:**
```bash
python main.py learner --learner_id R001 --course_id CSN
```

---

## 🎓 **4. SEMI-AUTOMATIC FACULTY PIPELINE**

**ACTUAL IMPLEMENTATION:** `pipeline/semi_automatic_coordinator.py`

### **Stage 1: Faculty Start**
```bash
python main.py faculty-start --course_id CSN --faculty_id PROF_123
```

### **Stage 2: Faculty Course Approval** 
```bash
python main.py faculty-approve-course --course_id CSN --action approve
```

### **Stage 3: Faculty LO Approval**
```bash
python main.py faculty-approve --course_id CSN --action approve
```

### **Stage 4: Faculty Structure Confirmation**
```bash
python main.py faculty-confirm --course_id CSN --action confirm
```

### **Stage 5: Faculty KG Finalization**
```bash
python main.py faculty-finalize --course_id CSN --action finalize
```

### **Stage 6: Learner PLT Generation**
```bash
python main.py learner-plt --course_id CSN --learner_id R001
```

---

## 🏛️ **5. CROSS-SUBSYSTEM WORKFLOW** (New Universal Orchestrator)

**IMPLEMENTATION:** `orchestrator/main.py` - `run_cross_subsystem_workflow_cmd()`

**EXECUTION ORDER:**
```
Content Subsystem (4 services) → Learner Subsystem (3 services)
```

**COMMAND:**
```bash
python orchestrator/main.py cross-subsystem --course_id CSN --upload_type elasticsearch --learner_id R001
```

---

## 📜 **6. LEGACY PIPELINES** (Backward Compatibility)

### **Stage 1 Pipeline** (5 LangGraph Agents)
```bash
python main.py stage1
```
**Agents:** Researcher → LO Generator → Curator → Analyst → KC Classifier

### **Stage 2 Pipeline** (2 LangGraph Agents)  
```bash
python main.py stage2
```
**Agents:** LP Identifier → Instruction Agent

### **PLT Pipeline** (6 LangGraph Agents)
```bash
python main.py plt
```
**Agents:** Accept Learner → Prioritize LOs → Map KCs → Sequence KCs → Match IMs → Link Resources

### **Elasticsearch Pipeline**
```bash
python main.py es
```
**Flow:** ES chunks → KG transformation → Neo4j insertion → PLT generation

---

## 🚨 **KEY FINDINGS FROM ACTUAL CODE:**

### **1. Course Manager Issue**
- **DOCUMENTED:** Course Manager is first service in pipeline
- **ACTUAL CODE:** Course Manager is NOT in service execution order!
- **LOCATION:** `orchestrator/universal_orchestrator.py:289`
- **IMPACT:** Documentation is incorrect - Content Preprocessor is actually first

### **2. Service Registration vs Execution**
- **REGISTERED SERVICES:** `orchestrator/main.py` registers course_manager (line 33)
- **EXECUTION ORDER:** `universal_orchestrator.py` does NOT include course_manager
- **ISSUE:** Service is registered but not executed in pipeline!

### **3. Multiple Pipeline Entry Points**

#### **Main Entry Points:**
1. **`main.py`** - Legacy + Semi-automatic faculty workflows
2. **`orchestrator/main.py`** - New universal orchestrator workflows  
3. **`pipeline/coordinator.py`** - Automatic pipeline coordination

#### **Actual Service Execution:**
- **Content:** `universal_orchestrator.py:289`
- **Learner:** `universal_orchestrator.py:329`
- **Faculty:** `semi_automatic_coordinator.py`

---

## 🔧 **MICROSERVICES BY ACTUAL IMPLEMENTATION:**

### **Content Subsystem (4 Services - NOT 5!)**
1. **Content Preprocessor** ✅ (First in execution)
2. **Course Mapper** ✅ 
3. **KLI Application** ✅
4. **Knowledge Graph Generator** ✅
5. **Course Manager** ❌ (Registered but NOT executed!)

### **Learner Subsystem (3 Services)**
1. **Query Strategy Manager** ✅
2. **Graph Query Engine** ✅  
3. **Learning Tree Handler** ✅

### **LangGraph Agent Distribution:**
- **Course Mapper:** 5 agents (Stage 1)
- **KLI Application:** 2 agents (Stage 2)  
- **Learning Tree Handler:** 6 agents (PLT)
- **Total:** 13 agents

---

## 📊 **PIPELINE SUMMARY BY USAGE:**

| Pipeline Type | Command | Entry Point | Services Executed | Faculty Control |
|--------------|---------|-------------|-------------------|-----------------|
| **Automatic** | `python main.py auto` | `main.py` | 7 services (4 content + 3 learner) | None |
| **Content Only** | `python main.py content` | `main.py` | 4 content services | None |
| **Learner Only** | `python main.py learner` | `main.py` | 3 learner services | None |
| **Semi-Automatic** | `python main.py faculty-*` | `main.py` | Variable by stage | Full faculty control |
| **Cross-Subsystem** | `python orchestrator/main.py cross-subsystem` | `orchestrator/main.py` | 7 services | None |
| **Legacy Stage 1** | `python main.py stage1` | `main.py` | 5 agents only | None |
| **Legacy Stage 2** | `python main.py stage2` | `main.py` | 2 agents only | None |
| **Legacy PLT** | `python main.py plt` | `main.py` | 6 agents only | None |
| **Legacy ES** | `python main.py es` | `main.py` | Full ES → KG → PLT | None |

---

## ⚠️ **IMPLEMENTATION GAPS IDENTIFIED:**

1. **Course Manager Not Executed:** Registered but missing from execution order
2. **Documentation Mismatch:** All docs show Course Manager first, code shows Content Preprocessor first
3. **Faculty Workflow Separation:** Semi-automatic coordinator exists but not integrated with main pipeline
4. **Multiple Entry Points:** Confusing array of different commands and coordinators

---

*🔍 **Analysis Based On:** Actual code examination of `universal_orchestrator.py`, `main.py`, `orchestrator/main.py`, `pipeline/coordinator.py`, and `pipeline/semi_automatic_coordinator.py`*
