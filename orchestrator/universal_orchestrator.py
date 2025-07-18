"""
Universal LangGraph Orchestrator

Cross-subsystem orchestrator that routes execution across:
- Content Subsystem: Course processing, KG generation
- Learner Subsystem: Personalization, learning paths  
- SME Subsystem: Expert review, validation
- Analytics Subsystem: Performance tracking, insights

Uses LangGraph to orchestrate multiple subgraphs across subsystems.
"""

import uuid
import time
from typing import Dict, List, Optional, Any, Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage

from orchestrator.state import (
    UniversalState,
    SubsystemType,
    ServiceStatus,
    CrossSubsystemRequest,
    CrossSubsystemResponse
)
from orchestrator.service_registry import (
    get_service_registry,
    ServiceRegistry,
    generate_request_id,
    create_cross_subsystem_request
)

class UniversalOrchestrator:
    """
    Universal LangGraph Orchestrator for cross-subsystem coordination.
    
    Features:
    - Dynamic service discovery and routing
    - Cross-subsystem state management
    - Dependency resolution and execution ordering
    - Error handling and rollback capabilities
    - Real-time execution monitoring
    """
    
    def __init__(self):
        self.registry = get_service_registry()
        self.graph = None
        self._build_orchestration_graph()
    
    def _build_orchestration_graph(self) -> None:
        """Build the LangGraph orchestration graph."""
        graph = StateGraph(UniversalState)
        
        # Core orchestration nodes
        graph.add_node("initialize_session", self._initialize_session)
        graph.add_node("route_subsystem", self._route_subsystem)
        graph.add_node("execute_content", self._execute_content_subsystem)
        graph.add_node("execute_learner", self._execute_learner_subsystem)
        graph.add_node("execute_sme", self._execute_sme_subsystem)
        graph.add_node("execute_analytics", self._execute_analytics_subsystem)
        graph.add_node("cross_subsystem_bridge", self._cross_subsystem_bridge)
        graph.add_node("finalize_session", self._finalize_session)
        
        # Set entry point
        graph.set_entry_point("initialize_session")
        
        # Define routing logic
        graph.add_edge("initialize_session", "route_subsystem")
        graph.add_conditional_edges(
            "route_subsystem",
            self._routing_decision,
            {
                "content": "execute_content",
                "learner": "execute_learner", 
                "sme": "execute_sme",
                "analytics": "execute_analytics",
                "cross_system": "cross_subsystem_bridge",
                "end": "finalize_session"
            }
        )
        
        # Connect subsystem executions back to routing
        graph.add_edge("execute_content", "route_subsystem")
        graph.add_edge("execute_learner", "route_subsystem")
        graph.add_edge("execute_sme", "route_subsystem")
        graph.add_edge("execute_analytics", "route_subsystem")
        graph.add_edge("cross_subsystem_bridge", "route_subsystem")
        
        # End the graph
        graph.add_edge("finalize_session", END)
        
        self.graph = graph.compile(
            checkpointer=None, 
            debug=False,
        )
    
    def _initialize_session(self, state: UniversalState) -> UniversalState:
        """Initialize orchestration session."""
        print("🚀 [Universal Orchestrator] Initializing session...")
        
        # Generate session ID if not provided
        if not state.get("session_id"):
            state["session_id"] = f"session_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        # Initialize execution tracking
        if "service_statuses" not in state:
            state["service_statuses"] = {}
        if "service_results" not in state:
            state["service_results"] = {}
        if "service_errors" not in state:
            state["service_errors"] = {}
        if "execution_history" not in state:
            state["execution_history"] = []
        
        # Initialize state validation
        state["state_validated"] = True
        state["validation_errors"] = []
        state["cross_system_compatibility"] = True
        
        # Log initialization
        self._add_execution_log(state, "session_initialized", {
            "session_id": state["session_id"],
            "timestamp": time.time()
        })
        
        print(f"✅ Session initialized: {state['session_id']}")
        return state
    
    def _route_subsystem(self, state: UniversalState) -> UniversalState:
        """Route execution to appropriate subsystem."""
        print("🔀 [Universal Orchestrator] Routing subsystem...")
        
        # Determine target subsystem
        target_subsystem = state.get("subsystem")
        
        if not target_subsystem:
            # Auto-detect subsystem based on available inputs
            target_subsystem = self._auto_detect_subsystem(state)
            state["subsystem"] = target_subsystem
        
        # Get executable services for this subsystem
        executable_services = self.registry.get_executable_services(state, target_subsystem)
        
        self._add_execution_log(state, "subsystem_routed", {
            "target_subsystem": target_subsystem.value if target_subsystem else None,
            "executable_services": executable_services
        })
        
        print(f"📍 Routing to subsystem: {target_subsystem}")
        print(f"📋 Executable services: {executable_services}")
        
        return state
    
    def _auto_detect_subsystem(self, state: UniversalState) -> Optional[SubsystemType]:
        """Auto-detect target subsystem based on state inputs."""
        
        # Content subsystem indicators
        if any(key in state for key in ["upload_type", "file_path", "es_index", "raw_content"]):
            return SubsystemType.CONTENT
        
        # Learner subsystem indicators  
        if any(key in state for key in ["learner_id", "learner_query", "learner_profile"]):
            return SubsystemType.LEARNER
        
        # SME subsystem indicators
        if any(key in state for key in ["sme_id", "content_reviews", "expert_feedback"]):
            return SubsystemType.SME
        
        # Analytics subsystem indicators
        if any(key in state for key in ["learning_metrics", "usage_statistics", "system_performance"]):
            return SubsystemType.ANALYTICS
        
        # Default to content if unclear
        return SubsystemType.CONTENT
    
    def _routing_decision(self, state: UniversalState) -> str:
        """Decide which subsystem to execute next."""
        
        target_subsystem = state.get("subsystem")
        
        # Check if cross-subsystem request exists
        if state.get("cross_system_payload"):
            return "cross_system"
        
        # Check if we have executable services for the current subsystem
        executable_services = self.registry.get_executable_services(state, target_subsystem)
        
        # If no executable services, end the workflow
        if not executable_services:
            return "end"
        
        # Route to specific subsystem
        if target_subsystem == SubsystemType.CONTENT:
            return "content"
        elif target_subsystem == SubsystemType.LEARNER:
            return "learner"
        elif target_subsystem == SubsystemType.SME:
            return "sme"
        elif target_subsystem == SubsystemType.ANALYTICS:
            return "analytics"
        
        # End if no clear routing
        return "end"
    
    def _execute_content_subsystem(self, state: UniversalState) -> UniversalState:
        """Execute content subsystem services."""
        print("📚 [Content Subsystem] Executing...")
        
        # Get executable content services
        executable_services = self.registry.get_executable_services(state, SubsystemType.CONTENT)
        
        if not executable_services:
            print("⚠️ No executable content services found")
            return state
        
        # Execute first available service (in real implementation, this would be more sophisticated)
        service_id = executable_services[0]
        result = self._execute_service(service_id, state)
        
        # Note: Service execution updates state internally, so we don't override here
        
        self._add_execution_log(state, "content_service_executed", {
            "service_id": service_id,
            "result_keys": list(result.keys()) if isinstance(result, dict) else "non_dict_result"
        })
        
        print(f"✅ Content service completed: {service_id}")
        return state
    
    def _execute_learner_subsystem(self, state: UniversalState) -> UniversalState:
        """Execute learner subsystem services."""
        print("👤 [Learner Subsystem] Executing...")
        
        # Get executable learner services
        executable_services = self.registry.get_executable_services(state, SubsystemType.LEARNER)
        
        if not executable_services:
            print("⚠️ No executable learner services found")
            return state
        
        # Execute first available service
        service_id = executable_services[0]
        result = self._execute_service(service_id, state)
        
        # Update state with result
        state["service_results"][service_id] = result
        state["service_statuses"][service_id] = ServiceStatus.COMPLETED
        
        self._add_execution_log(state, "learner_service_executed", {
            "service_id": service_id,
            "learner_id": state.get("learner_id")
        })
        
        print(f"✅ Learner service completed: {service_id}")
        return state
    
    def _execute_sme_subsystem(self, state: UniversalState) -> UniversalState:
        """Execute SME subsystem services."""
        print("👨‍🏫 [SME Subsystem] Executing...")
        
        # Get executable SME services
        executable_services = self.registry.get_executable_services(state, SubsystemType.SME)
        
        if not executable_services:
            print("⚠️ No executable SME services found")
            return state
        
        # Execute first available service
        service_id = executable_services[0]
        result = self._execute_service(service_id, state)
        
        # Update state with result
        state["service_results"][service_id] = result
        state["service_statuses"][service_id] = ServiceStatus.COMPLETED
        
        self._add_execution_log(state, "sme_service_executed", {
            "service_id": service_id,
            "sme_id": state.get("sme_id")
        })
        
        print(f"✅ SME service completed: {service_id}")
        return state
    
    def _execute_analytics_subsystem(self, state: UniversalState) -> UniversalState:
        """Execute analytics subsystem services."""
        print("📊 [Analytics Subsystem] Executing...")
        
        # Get executable analytics services
        executable_services = self.registry.get_executable_services(state, SubsystemType.ANALYTICS)
        
        if not executable_services:
            print("⚠️ No executable analytics services found")
            return state
        
        # Execute first available service
        service_id = executable_services[0]
        result = self._execute_service(service_id, state)
        
        # Update state with result
        state["service_results"][service_id] = result
        state["service_statuses"][service_id] = ServiceStatus.COMPLETED
        
        self._add_execution_log(state, "analytics_service_executed", {
            "service_id": service_id
        })
        
        print(f"✅ Analytics service completed: {service_id}")
        return state
    
    def _cross_subsystem_bridge(self, state: UniversalState) -> UniversalState:
        """Handle cross-subsystem communication."""
        print("🌉 [Cross-Subsystem Bridge] Executing...")
        
        cross_payload = state.get("cross_system_payload")
        if not cross_payload:
            return state
        
        # Create cross-subsystem request
        request = CrossSubsystemRequest(
            request_id=generate_request_id(),
            source_subsystem=state.get("source_subsystem", SubsystemType.CONTENT),
            target_subsystem=state.get("target_subsystem", SubsystemType.LEARNER),
            service_id=cross_payload.get("service_id", ""),
            payload=cross_payload
        )
        
        # Route request
        response = self.registry.route_cross_subsystem_request(request)
        
        # Update state with response
        state["service_results"][request.service_id] = response.result
        state["service_statuses"][request.service_id] = response.status
        
        # Clear cross-system payload
        state["cross_system_payload"] = None
        
        self._add_execution_log(state, "cross_system_bridge_executed", {
            "request_id": request.request_id,
            "source": request.source_subsystem.value,
            "target": request.target_subsystem.value,
            "status": response.status.value
        })
        
        print(f"✅ Cross-subsystem bridge completed: {request.request_id}")
        return state
    
    def _finalize_session(self, state: UniversalState) -> UniversalState:
        """Finalize orchestration session."""
        print("🏁 [Universal Orchestrator] Finalizing session...")
        
        # Generate session summary
        completed_services = [
            service_id for service_id, status in state.get("service_statuses", {}).items()
            if status == ServiceStatus.COMPLETED
        ]
        
        failed_services = [
            service_id for service_id, status in state.get("service_statuses", {}).items()
            if status == ServiceStatus.ERROR
        ]
        
        session_summary = {
            "session_id": state.get("session_id"),
            "completed_services": completed_services,
            "failed_services": failed_services,
            "total_execution_steps": len(state.get("execution_history", [])),
            "finalized_at": time.time()
        }
        
        self._add_execution_log(state, "session_finalized", session_summary)
        
        print(f"✅ Session finalized: {len(completed_services)} services completed, {len(failed_services)} failed")
        return state
    
    def _execute_service(self, service_id: str, state: UniversalState) -> Dict[str, Any]:
        """Execute a specific service."""
        service = self.registry.get_service(service_id)
        if not service:
            return {"error": f"Service {service_id} not found"}
        
        try:
            # Mark service as in progress
            state["service_statuses"][service_id] = ServiceStatus.IN_PROGRESS
            
            # Execute service callable
            if hasattr(service.callable, '__call__'):
                result = service.callable(state)
                return result if isinstance(result, dict) else {"result": result}
            else:
                return {"error": f"Service {service_id} is not callable"}
                
        except Exception as e:
            state["service_statuses"][service_id] = ServiceStatus.ERROR
            state["service_errors"][service_id] = str(e)
            return {"error": str(e)}
    
    def _add_execution_log(self, state: UniversalState, event_type: str, event_data: Dict[str, Any]) -> None:
        """Add entry to execution history."""
        log_entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": event_data
        }
        
        if "execution_history" not in state:
            state["execution_history"] = []
        
        state["execution_history"].append(log_entry)
    
    def run(self, initial_state: UniversalState) -> UniversalState:
        """Run the universal orchestrator."""
        if not self.graph:
            raise RuntimeError("Orchestrator graph not built")
        
        print("🌍 [Universal Orchestrator] Starting cross-subsystem orchestration...")
        print("=" * 80)
        
        try:
            result = self.graph.invoke(initial_state)
            print("=" * 80)
            print("🎉 [Universal Orchestrator] Cross-subsystem orchestration completed!")
            return result
            
        except Exception as e:
            print(f"❌ [Universal Orchestrator] Orchestration failed: {e}")
            raise

# ===============================
# CONVENIENCE FUNCTIONS
# ===============================

def create_universal_orchestrator() -> UniversalOrchestrator:
    """Create a new universal orchestrator instance."""
    return UniversalOrchestrator()

def run_cross_subsystem_workflow(
    subsystem: SubsystemType,
    **kwargs
) -> UniversalState:
    """Run a cross-subsystem workflow."""
    
    orchestrator = create_universal_orchestrator()
    
    initial_state: UniversalState = {
        "subsystem": subsystem,
        "execution_context": kwargs
    }
    
    # Add specific context based on subsystem
    if subsystem == SubsystemType.CONTENT:
        initial_state.update({
            "course_id": kwargs.get("course_id", "default_course"),
            "upload_type": kwargs.get("upload_type", "elasticsearch")
        })
        
        # Add content-specific parameters
        if kwargs.get("file_path"):
            initial_state["file_path"] = kwargs["file_path"]
        if kwargs.get("es_index"):
            initial_state["es_index"] = kwargs["es_index"]
        if kwargs.get("raw_content"):
            initial_state["raw_content"] = kwargs["raw_content"]
            
    elif subsystem == SubsystemType.LEARNER:
        initial_state.update({
            "learner_id": kwargs.get("learner_id", "default_learner"),
            "course_id": kwargs.get("course_id", "default_course")
        })
        
        # Add learner-specific parameters
        if kwargs.get("learner_profile"):
            initial_state["learner_profile"] = kwargs["learner_profile"]
            
    elif subsystem == SubsystemType.SME:
        initial_state.update({
            "sme_id": kwargs.get("sme_id", "default_sme"),
            "course_id": kwargs.get("course_id", "default_course")
        })
    elif subsystem == SubsystemType.ANALYTICS:
        initial_state.update({
            "course_id": kwargs.get("course_id", "default_course")
        })
    
    return orchestrator.run(initial_state) 