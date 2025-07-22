"""
Unified State Schema for LangGraph Orchestrator

This schema supports all 8 microservice responsibilities:
1. Course Manager
2. Content Preprocessor  
3. Course Content Mapper (Stage 1)
4. KLI Application (Stage 2)
5. Knowledge Graph Generator
6. Query Strategy Manager
7. Graph Query Engine
8. Learning Tree Handler

Includes faculty approval stages: FACD, FCCS, FFCS
"""

from typing import Dict, List, Optional, Any, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from pydantic import BaseModel

# ===============================
# UNIFIED STATE SCHEMA
# ===============================

class UnifiedState(TypedDict, total=False):
    # ===== CORE IDENTIFIERS =====
    course_id: str
    learner_id: Optional[str]
    faculty_id: Optional[str]
    session_id: str
    
    # ===== INPUT PROCESSING =====
    # Course Manager inputs
    upload_type: Literal["pdf", "elasticsearch", "llm_generated"]
    file_path: Optional[str]
    es_index: Optional[str]
    raw_content: Optional[str]
    
    # Content Preprocessor outputs
    chunks: List[Dict[str, Any]]  # [{"content": "...", "metadata": {...}}]
    content_metadata: Dict[str, Any]  # {"title": "...", "total_chunks": N}
    
    # ===== AGENT COMMUNICATION =====
    # Shared across Stage 1 & Stage 2 (your existing agents)
    messages: List[BaseMessage]
    
    # ===== SERVICE INTEGRATION LAYER =====
    # Individual service results (structured)
    course_manager_result: Optional[Dict[str, Any]]
    content_preprocessor_result: Optional[Dict[str, Any]]
    course_content_mapper_result: Optional[Dict[str, Any]]
    kli_application_result: Optional[Dict[str, Any]]
    knowledge_graph_generator_result: Optional[Dict[str, Any]]
    query_strategy_manager_result: Optional[Dict[str, Any]]
    graph_query_engine_result: Optional[Dict[str, Any]]
    learning_tree_handler_result: Optional[Dict[str, Any]]
    
    # ===== VALIDATION FLAGS =====
    state_validated: bool  # Track if state has been validated
    required_fields_present: bool  # Track if all required fields are present
    service_compatibility_checked: bool  # Track service integration status
    
    # ===== FACULTY APPROVAL STAGES =====
    # Stage 1 Output: Faculty Approved Course Details (FACD)
    facd: Optional[Dict[str, Any]]  # {"learning_objectives": [...], "draft_kcs": [...]}
    facd_approved: bool
    
    # Stage 2 Output: Faculty Confirmed Course Structure (FCCS)  
    fccs: Optional[Dict[str, Any]]  # {"los": [...], "kcs": [...], "learning_processes": [...]}
    fccs_approved: bool
    
    # KG Generator Output: Faculty Finalized Course Structure (FFCS)
    ffcs: Optional[Dict[str, Any]]  # Final structure ready for KG
    ffcs_approved: bool
    
    # ===== KNOWLEDGE GRAPH DATA =====
    # Knowledge Graph Generator outputs
    neo4j_graph: Optional[Dict[str, Any]]
    mongodb_snapshot: Optional[Dict[str, Any]]
    postgresql_ffcs: Optional[Dict[str, Any]]
    
    # ===== LEARNER-SPECIFIC DATA =====
    # Query Strategy Manager
    learner_context: Optional[Dict[str, Any]]  # {"decision_label": "...", "flagged_rules": [...]}
    query_strategy: Optional[str]  # "recommendation", "subgraph", "plt_generation"
    
    # Graph Query Engine
    cypher_queries: List[str]
    query_results: List[Dict[str, Any]]
    subgraph_data: Optional[Dict[str, Any]]
    
    # Learning Tree Handler
    plt_data: Optional[Dict[str, Any]]  # Generated PLT
    redis_plt: Optional[str]  # Active PLT key
    postgresql_plt_version: Optional[int]
    
    # ===== EXECUTION CONTROL =====
    current_stage: str  # Track which subgraph is executing
    errors: List[str]  # Collect errors across subgraphs
    completed_stages: List[str]  # Track completion
    next_action: Optional[str]  # Manual routing if needed

# ===============================
# INDIVIDUAL SUBGRAPH STATES  
# ===============================

class CourseManagerState(TypedDict, total=False):
    """State for Course Manager subgraph"""
    course_id: str
    faculty_id: str
    upload_type: Literal["pdf", "elasticsearch", "llm_generated"]
    file_path: Optional[str]
    es_index: Optional[str]
    trigger_next: bool

class ContentProcessorState(TypedDict, total=False):
    """State for Content Preprocessor subgraph"""
    file_path: Optional[str]
    es_index: Optional[str]
    chunks: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_complete: bool

class KGGeneratorState(TypedDict, total=False):
    """State for Knowledge Graph Generator subgraph"""
    fccs: Dict[str, Any]
    neo4j_inserted: bool
    mongodb_saved: bool
    postgresql_saved: bool
    ffcs: Dict[str, Any]

class QueryStrategyState(TypedDict, total=False):
    """State for Query Strategy Manager subgraph"""
    learner_id: str
    course_id: str
    learner_context: Dict[str, Any]
    strategy_decision: str
    next_engine: str

class GraphQueryState(TypedDict, total=False):
    """State for Graph Query Engine subgraph"""
    strategy: str
    cypher_queries: List[str]
    results: List[Dict[str, Any]]
    subgraph_ready: bool

class PLTHandlerState(TypedDict, total=False):
    """State for Learning Tree Handler subgraph"""
    learner_id: str
    course_id: str
    graph_data: Dict[str, Any]
    plt_generated: Dict[str, Any]
    redis_stored: bool
    postgresql_versioned: bool

# ===============================
# FACULTY APPROVAL SCHEMAS
# ===============================

class FACDSchema(BaseModel):
    """Faculty Approved Course Details - Stage 1 Output"""
    course_id: str
    learning_objectives: List[Dict[str, str]]  # [{"lo_id": "LO_001", "text": "..."}]
    draft_knowledge_components: List[Dict[str, str]]
    faculty_notes: Optional[str]
    approval_timestamp: Optional[str]
    requires_revision: bool = False

class FCCSSchema(BaseModel):
    """Faculty Confirmed Course Structure - Stage 2 Output"""
    course_id: str
    finalized_los: List[Dict[str, Any]]
    finalized_kcs: List[Dict[str, Any]]
    learning_processes: List[Dict[str, str]]  # KLI tags
    instruction_methods: List[Dict[str, str]]
    faculty_notes: Optional[str]
    approval_timestamp: Optional[str]
    requires_revision: bool = False

class FFCSSchema(BaseModel):
    """Faculty Finalized Course Structure - KG Ready"""
    course_id: str
    final_structure: Dict[str, Any]  # Complete course graph structure
    neo4j_ready: bool
    faculty_final_approval: bool
    approval_timestamp: Optional[str] 

# ===============================
# STATE VALIDATION & BRIDGE UTILITIES
# ===============================

def validate_unified_state(state: UnifiedState) -> Dict[str, Any]:
    """
    Validate UnifiedState integrity and return validation results.
    
    Returns:
        Dict with validation status and missing fields
    """
    validation_result = {
        "valid": True,
        "missing_fields": [],
        "warnings": [],
        "errors": []
    }
    
    # Check required core fields
    required_fields = ["course_id", "session_id"]
    for field in required_fields:
        if not state.get(field):
            validation_result["missing_fields"].append(field)
            validation_result["valid"] = False
    
    # Check stage consistency
    completed_stages = state.get("completed_stages", [])
    current_stage = state.get("current_stage")
    
    if current_stage and current_stage not in completed_stages:
        validation_result["warnings"].append(f"Current stage {current_stage} not in completed stages")
    
    # Check service result consistency
    service_stages = {
        "course_manager": "course_manager_result",
        "content_preprocessor": "content_preprocessor_result",
        "course_content_mapper": "course_content_mapper_result",
        "kli_application": "kli_application_result",
        "knowledge_graph_generator": "knowledge_graph_generator_result",
        "query_strategy_manager": "query_strategy_manager_result", 
        "graph_query_engine": "graph_query_engine_result",
        "learning_tree_handler": "learning_tree_handler_result"
    }
    
    for stage, result_field in service_stages.items():
        if stage in completed_stages and not state.get(result_field):
            validation_result["warnings"].append(f"Stage {stage} completed but {result_field} missing")
    
    return validation_result

def bridge_to_agent_state(state: UnifiedState, agent_type: str = "stage1") -> "GraphState":
    """
    Bridge UnifiedState to GraphState for agent compatibility.
    
    Args:
        state: UnifiedState from orchestrator
        agent_type: Type of agents ("stage1", "stage2", "plt")
        
    Returns:
        GraphState compatible with existing agents
    """
    from graph.state import GraphState
    from langchain_core.messages import HumanMessage
    
    # Extract or create messages based on available content
    messages = state.get("messages", [])
    
    # If no messages but have content, create initial message
    if not messages and state.get("chunks"):
        # Use first chunk as initial content for agents
        first_chunk = state["chunks"][0]
        content = first_chunk.get("content", "No content available")
        messages = [HumanMessage(content=content)]
    elif not messages and state.get("raw_content"):
        messages = [HumanMessage(content=state["raw_content"])]
    elif not messages:
        # Fallback message
        messages = [HumanMessage(content=f"Process course content for {state.get('course_id', 'unknown course')}")]
    
    return GraphState(messages=messages)

def bridge_from_agent_state(agent_state: "GraphState", unified_state: UnifiedState) -> UnifiedState:
    """
    Bridge agent results back to UnifiedState.
    
    Args:
        agent_state: GraphState from agent execution
        unified_state: Original UnifiedState to update
        
    Returns:
        Updated UnifiedState with agent results
    """
    # Update messages in unified state
    unified_state["messages"] = agent_state.messages
    
    # Extract structured data from agent messages if possible
    if agent_state.messages:
        last_message = agent_state.messages[-1]
        if hasattr(last_message, 'content'):
            # Store agent output for further processing
            current_stage = unified_state.get("current_stage", "unknown")
            result_field = f"{current_stage}_agent_output"
            unified_state[result_field] = last_message.content
    
    return unified_state

def ensure_state_compatibility(state: UnifiedState) -> UnifiedState:
    """
    Ensure state compatibility across all microservices.
    
    Args:
        state: UnifiedState to validate and fix
        
    Returns:
        State with compatibility issues resolved
    """
    # Initialize required lists if missing
    if "messages" not in state:
        state["messages"] = []
    if "chunks" not in state:
        state["chunks"] = []
    if "errors" not in state:
        state["errors"] = []
    if "completed_stages" not in state:
        state["completed_stages"] = []
    
    # Set validation flags
    validation_result = validate_unified_state(state)
    state["state_validated"] = validation_result["valid"]
    state["required_fields_present"] = len(validation_result["missing_fields"]) == 0
    state["service_compatibility_checked"] = True
    
    return state 