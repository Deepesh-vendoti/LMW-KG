"""
Universal Cross-Subsystem State Schema

Supports orchestration across all subsystems:
- Content: Course processing, KG generation
- Learner: Personalization, learning paths  
- SME: Expert review, validation
- Analytics: Performance tracking, insights
"""

from typing import Dict, List, Optional, Any, Literal, Union
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from pydantic import BaseModel
from enum import Enum

# ===============================
# SUBSYSTEM DEFINITIONS
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
# UNIVERSAL STATE SCHEMA
# ===============================

class UniversalState(TypedDict, total=False):
    # ===== CORE ORCHESTRATION =====
    session_id: str
    subsystem: SubsystemType
    active_service: Optional[str]
    execution_context: Dict[str, Any]
    
    # ===== ENTITY IDENTIFIERS =====
    course_id: Optional[str]
    learner_id: Optional[str]
    faculty_id: Optional[str]
    sme_id: Optional[str]
    
    # ===== CROSS-SUBSYSTEM ROUTING =====
    # Request routing between subsystems
    source_subsystem: Optional[SubsystemType]
    target_subsystem: Optional[SubsystemType]
    cross_system_payload: Optional[Dict[str, Any]]
    
    # ===== SERVICE EXECUTION TRACKING =====
    service_statuses: Dict[str, ServiceStatus]  # service_id -> status
    service_results: Dict[str, Dict[str, Any]]  # service_id -> result
    service_errors: Dict[str, str]  # service_id -> error_message
    execution_history: List[Dict[str, Any]]  # chronological execution log
    
    # ===== CONTENT SUBSYSTEM =====
    # Input processing
    upload_type: Optional[Literal["pdf", "elasticsearch", "llm_generated"]]
    file_path: Optional[str]
    es_index: Optional[str]
    raw_content: Optional[str]
    
    # Content processing results
    chunks: List[Dict[str, Any]]
    content_metadata: Dict[str, Any]
    knowledge_graph: Optional[Dict[str, Any]]
    
    # Faculty approval stages
    facd: Optional[Dict[str, Any]]  # Faculty Approved Course Details
    facd_approved: bool
    fccs: Optional[Dict[str, Any]]  # Faculty Confirmed Course Structure
    fccs_approved: bool
    ffcs: Optional[Dict[str, Any]]  # Faculty Finalized Course Structure
    ffcs_approved: bool
    
    # ===== LEARNER SUBSYSTEM =====
    # Learner context and personalization
    learner_profile: Optional[Dict[str, Any]]
    learning_preferences: Optional[Dict[str, Any]]
    learning_history: Optional[List[Dict[str, Any]]]
    
    # Personalized learning outputs
    learning_objectives_prioritized: Optional[List[str]]
    personalized_learning_tree: Optional[Dict[str, Any]]
    adaptive_recommendations: Optional[List[Dict[str, Any]]]
    
    # Query and interaction
    learner_query: Optional[str]
    query_strategy: Optional[Dict[str, Any]]
    query_results: Optional[List[Dict[str, Any]]]
    
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
    
    # ===== LEGACY COMPATIBILITY =====
    # Support for existing agents
    messages: List[BaseMessage]
    
    # ===== STATE VALIDATION =====
    state_validated: bool
    validation_errors: List[str]
    cross_system_compatibility: bool

# ===============================
# SERVICE REGISTRATION SCHEMA
# ===============================

class ServiceDefinition(BaseModel):
    service_id: str
    subsystem: SubsystemType
    name: str
    description: str
    dependencies: List[str]  # service_ids this service depends on
    required_inputs: List[str]  # state fields required
    provided_outputs: List[str]  # state fields this service provides
    callable: Any  # The actual service function/class
    timeout_seconds: Optional[int] = 300

class SubsystemDefinition(BaseModel):
    subsystem_type: SubsystemType
    name: str
    description: str
    services: List[ServiceDefinition]
    entry_points: List[str]  # service_ids that can be entry points

# ===============================
# REQUEST/RESPONSE SCHEMAS
# ===============================

class CrossSubsystemRequest(BaseModel):
    request_id: str
    source_subsystem: SubsystemType
    target_subsystem: SubsystemType
    service_id: str
    payload: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class CrossSubsystemResponse(BaseModel):
    request_id: str
    status: ServiceStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None 