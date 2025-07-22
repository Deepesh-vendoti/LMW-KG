"""
Unified State Manager

Consolidates all state management operations across the system:
- Universal state for orchestration
- Subsystem-specific state management
- State validation and compatibility
- State bridging between different systems
"""

from typing import Dict, List, Optional, Any, Literal, Union
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from pydantic import BaseModel
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# ===============================
# ENUMERATIONS
# ===============================

class SubsystemType(str, Enum):
    CONTENT = "content"
    LEARNER = "learner" 
    SME = "sme"
    ANALYTICS = "analytics"

class ServiceStatus(str, Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"

# ===============================
# UNIFIED STATE SCHEMA
# ===============================

class UnifiedState(TypedDict, total=False):
    """
    Unified state schema that supports all subsystems and workflows.
    
    This consolidates the functionality from:
    - orchestrator/state.py (UniversalState)
    - graph/unified_state.py (UnifiedState)
    - graph/state.py (GraphState)
    """
    
    # ===== CORE IDENTIFIERS =====
    session_id: str
    course_id: Optional[str]
    learner_id: Optional[str]
    faculty_id: Optional[str]
    sme_id: Optional[str]
    
    # ===== ORCHESTRATION CONTROL =====
    subsystem: Optional[SubsystemType]
    active_service: Optional[str]
    execution_context: Dict[str, Any]
    current_stage: Optional[str]
    next_action: Optional[str]
    
    # ===== CROSS-SUBSYSTEM ROUTING =====
    source_subsystem: Optional[SubsystemType]
    target_subsystem: Optional[SubsystemType]
    cross_system_payload: Optional[Dict[str, Any]]
    
    # ===== SERVICE EXECUTION TRACKING =====
    service_statuses: Dict[str, ServiceStatus]  # service_id -> status
    service_results: Dict[str, Dict[str, Any]]  # service_id -> result
    service_errors: Dict[str, str]  # service_id -> error_message
    execution_history: List[Dict[str, Any]]  # chronological execution log
    
    # ===== INPUT PROCESSING =====
    upload_type: Optional[Literal["pdf", "elasticsearch", "llm_generated"]]
    file_path: Optional[str]
    es_index: Optional[str]
    raw_content: Optional[str]
    
    # ===== CONTENT PROCESSING =====
    chunks: List[Dict[str, Any]]  # [{"content": "...", "metadata": {...}}]
    content_metadata: Dict[str, Any]  # {"title": "...", "total_chunks": N}
    knowledge_graph: Optional[Dict[str, Any]]
    
    # ===== COURSE MANAGER =====
    course_config: Optional[Dict[str, Any]]
    course_manager_result: Optional[Dict[str, Any]]
    faculty_inputs_collected: Optional[bool]
    is_automatic_mode: Optional[bool]
    next_step: Optional[str]
    
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
    neo4j_graph: Optional[Dict[str, Any]]
    mongodb_snapshot: Optional[Dict[str, Any]]
    postgresql_ffcs: Optional[Dict[str, Any]]
    
    # ===== LEARNER SUBSYSTEM =====
    # Learner context and personalization
    learner_profile: Optional[Dict[str, Any]]
    learner_context: Optional[Dict[str, Any]]  # Required by Query Strategy Manager
    learning_preferences: Optional[Dict[str, Any]]
    learning_history: Optional[List[Dict[str, Any]]]
    
    # Personalized learning outputs
    learning_objectives_prioritized: Optional[List[str]]
    personalized_learning_tree: Optional[Dict[str, Any]]
    
    # Query and interaction
    learner_query: Optional[str]
    query_strategy: Optional[Dict[str, Any]]
    query_results: Optional[List[Dict[str, Any]]]
    
    # Graph Query Engine
    cypher_queries: List[str]
    subgraph_data: Optional[Dict[str, Any]]
    
    # Learning Tree Handler
    plt_data: Optional[Dict[str, Any]]  # Generated PLT
    redis_plt: Optional[str]  # Active PLT key
    postgresql_plt_version: Optional[int]
    
    # ===== SME SUBSYSTEM =====
    # Expert review and validation
    sme_assignments: Optional[List[Dict[str, Any]]]
    content_reviews: Optional[List[Dict[str, Any]]]
    quality_assessments: Optional[List[Dict[str, Any]]]
    expert_annotations: Optional[List[Dict[str, Any]]]
    
    # SME workflow
    review_status: Optional[ServiceStatus]
    validation_results: Optional[Dict[str, Any]]
    expert_feedback: Optional[List[Dict[str, Any]]]
    
    # ===== ANALYTICS SUBSYSTEM =====
    # Learning analytics
    learning_metrics: Optional[Dict[str, Any]]
    engagement_data: Optional[List[Dict[str, Any]]]
    performance_indicators: Optional[Dict[str, Any]]
    
    # System analytics
    usage_statistics: Optional[Dict[str, Any]]
    system_performance: Optional[Dict[str, Any]]
    service_metrics: Optional[Dict[str, Dict[str, Any]]]
    
    # ===== AGENT COMMUNICATION =====
    # Shared across Stage 1 & Stage 2 (LangChain agents)
    messages: List[BaseMessage]
    
    # ===== VALIDATION AND COMPATIBILITY =====
    state_validated: bool
    validation_errors: List[str]
    cross_system_compatibility: bool
    required_fields_present: bool
    service_compatibility_checked: bool
    
    # ===== ERROR HANDLING =====
    errors: List[str]  # Collect errors across subsystems

# ===============================
# SUBSYSTEM-SPECIFIC STATE SCHEMAS
# ===============================

class ContentSubsystemState(TypedDict, total=False):
    """State specific to Content subsystem operations."""
    course_id: str
    faculty_id: str
    upload_type: Literal["pdf", "elasticsearch", "llm_generated"]
    file_path: Optional[str]
    es_index: Optional[str]
    chunks: List[Dict[str, Any]]
    content_metadata: Dict[str, Any]
    knowledge_graph: Optional[Dict[str, Any]]
    facd: Optional[Dict[str, Any]]
    fccs: Optional[Dict[str, Any]]
    ffcs: Optional[Dict[str, Any]]

class LearnerSubsystemState(TypedDict, total=False):
    """State specific to Learner subsystem operations."""
    learner_id: str
    course_id: str
    learner_context: Dict[str, Any]
    learning_preferences: Dict[str, Any]
    personalized_learning_tree: Optional[Dict[str, Any]]
    query_strategy: Optional[str]
    query_results: Optional[List[Dict[str, Any]]]

class SMESubsystemState(TypedDict, total=False):
    """State specific to SME subsystem operations."""
    sme_id: str
    course_id: str
    review_assignments: List[Dict[str, Any]]
    review_status: ServiceStatus
    expert_feedback: List[Dict[str, Any]]

class AnalyticsSubsystemState(TypedDict, total=False):
    """State specific to Analytics subsystem operations."""
    course_id: Optional[str]
    learner_id: Optional[str]
    learning_metrics: Dict[str, Any]
    engagement_data: List[Dict[str, Any]]
    performance_indicators: Dict[str, Any]

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
# UNIFIED STATE MANAGER
# ===============================

class UnifiedStateManager:
    """
    Unified state manager for all state operations.
    
    Consolidates state management from:
    - orchestrator/state.py
    - graph/unified_state.py
    - graph/state.py
    """
    
    def __init__(self):
        """Initialize the state manager."""
        logger.info("UnifiedStateManager initialized")
    
    def create_initial_state(self, session_id: str, **kwargs) -> UnifiedState:
        """
        Create initial unified state with required fields.
        
        Args:
            session_id: Unique session identifier
            **kwargs: Additional initial state values
            
        Returns:
            Initialized unified state
        """
        initial_state = UnifiedState(
            session_id=session_id,
            messages=[],
            service_statuses={},
            service_results={},
            service_errors={},
            execution_history=[],
            chunks=[],
            cypher_queries=[],
            validation_errors=[],
            errors=[],
            state_validated=False,
            cross_system_compatibility=False,
            required_fields_present=False,
            service_compatibility_checked=False,
            facd_approved=False,
            fccs_approved=False,
            ffcs_approved=False,
            **kwargs
        )
        
        logger.info(f"Created initial state for session: {session_id}")
        return initial_state
    
    def validate_state(self, state: UnifiedState) -> Dict[str, Any]:
        """
        Validate unified state for completeness and consistency.
        
        Args:
            state: State to validate
            
        Returns:
            Validation result dictionary
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing_fields": [],
            "inconsistent_fields": []
        }
        
        # Check required fields
        required_fields = ["session_id"]
        for field in required_fields:
            if field not in state or state[field] is None:
                validation_result["missing_fields"].append(field)
                validation_result["valid"] = False
        
        # Check subsystem-specific requirements
        if state.get("subsystem"):
            subsystem = state["subsystem"]
            if subsystem == SubsystemType.CONTENT:
                if not state.get("course_id"):
                    validation_result["warnings"].append("Content subsystem should have course_id")
            
            elif subsystem == SubsystemType.LEARNER:
                if not state.get("learner_id"):
                    validation_result["warnings"].append("Learner subsystem should have learner_id")
        
        # Check faculty approval consistency
        if state.get("facd_approved") and not state.get("facd"):
            validation_result["inconsistent_fields"].append("facd_approved=True but no facd data")
        
        if state.get("fccs_approved") and not state.get("fccs"):
            validation_result["inconsistent_fields"].append("fccs_approved=True but no fccs data")
        
        if state.get("ffcs_approved") and not state.get("ffcs"):
            validation_result["inconsistent_fields"].append("ffcs_approved=True but no ffcs data")
        
        # Update state validation status
        state["state_validated"] = validation_result["valid"]
        state["validation_errors"] = validation_result["errors"]
        state["required_fields_present"] = len(validation_result["missing_fields"]) == 0
        
        return validation_result
    
    def update_service_status(self, state: UnifiedState, service_id: str, status: ServiceStatus, 
                            result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> UnifiedState:
        """
        Update service status in unified state.
        
        Args:
            state: Current state
            service_id: Service identifier
            status: New service status
            result: Service result (optional)
            error: Service error (optional)
            
        Returns:
            Updated state
        """
        if "service_statuses" not in state:
            state["service_statuses"] = {}
        if "service_results" not in state:
            state["service_results"] = {}
        if "service_errors" not in state:
            state["service_errors"] = {}
        
        state["service_statuses"][service_id] = status
        
        if result:
            state["service_results"][service_id] = result
        
        if error:
            state["service_errors"][service_id] = error
        
        # Add to execution history
        if "execution_history" not in state:
            state["execution_history"] = []
        
        state["execution_history"].append({
            "timestamp": "now",  # TODO: Add proper timestamp
            "service_id": service_id,
            "status": status,
            "result": result,
            "error": error
        })
        
        return state
    
    def get_subsystem_state(self, state: UnifiedState, subsystem: SubsystemType) -> Dict[str, Any]:
        """
        Extract subsystem-specific state from unified state.
        
        Args:
            state: Unified state
            subsystem: Target subsystem
            
        Returns:
            Subsystem-specific state dictionary
        """
        if subsystem == SubsystemType.CONTENT:
            return {
                "course_id": state.get("course_id"),
                "faculty_id": state.get("faculty_id"),
                "upload_type": state.get("upload_type"),
                "file_path": state.get("file_path"),
                "es_index": state.get("es_index"),
                "chunks": state.get("chunks", []),
                "content_metadata": state.get("content_metadata", {}),
                "knowledge_graph": state.get("knowledge_graph"),
                "facd": state.get("facd"),
                "fccs": state.get("fccs"),
                "ffcs": state.get("ffcs")
            }
        
        elif subsystem == SubsystemType.LEARNER:
            return {
                "learner_id": state.get("learner_id"),
                "course_id": state.get("course_id"),
                "learner_context": state.get("learner_context"),
                "learning_preferences": state.get("learning_preferences"),
                "personalized_learning_tree": state.get("personalized_learning_tree"),
                "query_strategy": state.get("query_strategy"),
                "query_results": state.get("query_results")
            }
        
        elif subsystem == SubsystemType.SME:
            return {
                "sme_id": state.get("sme_id"),
                "course_id": state.get("course_id"),
                "review_assignments": state.get("sme_assignments", []),
                "review_status": state.get("review_status"),
                "expert_feedback": state.get("expert_feedback", [])
            }
        
        elif subsystem == SubsystemType.ANALYTICS:
            return {
                "course_id": state.get("course_id"),
                "learner_id": state.get("learner_id"),
                "learning_metrics": state.get("learning_metrics", {}),
                "engagement_data": state.get("engagement_data", []),
                "performance_indicators": state.get("performance_indicators", {})
            }
        
        return {}
    
    def merge_subsystem_state(self, state: UnifiedState, subsystem: SubsystemType, 
                            subsystem_state: Dict[str, Any]) -> UnifiedState:
        """
        Merge subsystem-specific state back into unified state.
        
        Args:
            state: Current unified state
            subsystem: Source subsystem
            subsystem_state: Subsystem-specific state to merge
            
        Returns:
            Updated unified state
        """
        # Update state with subsystem data
        for key, value in subsystem_state.items():
            if value is not None:
                state[key] = value
        
        return state
    
    def bridge_to_agent_state(self, state: UnifiedState, agent_type: str = "stage1") -> Dict[str, Any]:
        """
        Bridge unified state to LangChain agent state format.
        
        Args:
            state: Unified state
            agent_type: Type of agent ("stage1", "stage2", etc.)
            
        Returns:
            Agent-compatible state dictionary
        """
        agent_state = {
            "messages": state.get("messages", []),
            "session_id": state.get("session_id"),
            "course_id": state.get("course_id")
        }
        
        # Add agent-specific data
        if agent_type == "stage1":
            agent_state.update({
                "chunks": state.get("chunks", []),
                "content_metadata": state.get("content_metadata", {}),
                "facd": state.get("facd")
            })
        elif agent_type == "stage2":
            agent_state.update({
                "facd": state.get("facd"),
                "fccs": state.get("fccs")
            })
        
        return agent_state
    
    def bridge_from_agent_state(self, agent_state: Dict[str, Any], unified_state: UnifiedState) -> UnifiedState:
        """
        Bridge LangChain agent state back to unified state.
        
        Args:
            agent_state: Agent state dictionary
            unified_state: Current unified state
            
        Returns:
            Updated unified state
        """
        # Update messages
        if "messages" in agent_state:
            unified_state["messages"] = agent_state["messages"]
        
        # Update other fields
        for key, value in agent_state.items():
            if key != "messages" and value is not None:
                unified_state[key] = value
        
        return unified_state

# Global state manager instance
state_manager = UnifiedStateManager()

# Convenience functions for backward compatibility
def create_unified_state(session_id: str, **kwargs) -> UnifiedState:
    """Convenience function for creating unified state."""
    return state_manager.create_initial_state(session_id, **kwargs)

def validate_unified_state(state: UnifiedState) -> Dict[str, Any]:
    """Convenience function for validating unified state."""
    return state_manager.validate_state(state)

def update_service_status(state: UnifiedState, service_id: str, status: ServiceStatus, 
                         result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> UnifiedState:
    """Convenience function for updating service status."""
    return state_manager.update_service_status(state, service_id, status, result, error) 