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
        
        # Get LangGraph configuration
        self.langgraph_config = self._get_langgraph_config()
        
        self.graph = graph.compile(
            checkpointer=self.langgraph_config.get("checkpointer"), 
            debug=self.langgraph_config.get("debug", False),
        )
    
    def _initialize_session(self, state: UniversalState) -> UniversalState:
        """Initialize orchestration session."""
        print("🚀 [Universal Orchestrator] Initializing session...")
        
        # Debug: Check initial state
        print(f"🔍 Initial state keys: {list(state.keys())}")
        print(f"🔍 learner_context: {state.get('learner_context')}")
        print(f"🔍 learner_id: {state.get('learner_id')}")
        print(f"🔍 workflow_type: {state.get('workflow_type')}")
        
        # Save workflow_type if present in execution_context or directly in state
        workflow_type = state.get("workflow_type")
        if not workflow_type and "execution_context" in state and isinstance(state["execution_context"], dict):
            workflow_type = state["execution_context"].get("workflow_type")
        
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
        
        # CRITICAL: Always ensure workflow_type is present
        if workflow_type:
            state["workflow_type"] = workflow_type
            print(f"🔍 Restored workflow_type: {workflow_type}")
        else:
            # Default workflow type based on subsystem
            if state.get("subsystem") == SubsystemType.CONTENT:
                state["workflow_type"] = "content_processing"
                print(f"🔍 Set default workflow_type for content: content_processing")
            elif state.get("subsystem") == SubsystemType.LEARNER:
                state["workflow_type"] = "learner_workflow"
                print(f"🔍 Set default workflow_type for learner: learner_workflow")
            else:
                print(f"⚠️ No workflow_type found in state")
        
        # Debug: Check final state
        print(f"🔍 Final state keys: {list(state.keys())}")
        print(f"🔍 learner_context after init: {state.get('learner_context')}")
        print(f"🔍 workflow_type after init: {state.get('workflow_type')}")
        
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
        
        # Debug: Check what fields are in state at routing
        print(f"🔍 Routing - State keys: {list(state.keys())}")
        print(f"🔍 course_config in routing: {'course_config' in state}")
        print(f"🔍 course_manager_result in routing: {'course_manager_result' in state}")
        print(f"🔍 faculty_inputs_collected in routing: {state.get('faculty_inputs_collected')}")
        
        # Determine target subsystem
        target_subsystem = state.get("subsystem")
        
        if not target_subsystem:
            # Auto-detect subsystem based on available inputs
            target_subsystem = self._auto_detect_subsystem(state)
            state["subsystem"] = target_subsystem
        
        # Get executable services for this subsystem
        executable_services = self.registry.get_executable_services(state, target_subsystem)
        
        # Enhanced debugging: Check why services aren't executable
        if not executable_services:
            print(f"⚠️ No executable services found for {target_subsystem}")
            print("🔍 Debugging service availability...")
            
            subsystem_services = self.registry.get_subsystem_services(target_subsystem)
            print(f"   Available services in {target_subsystem}: {[s.service_id for s in subsystem_services]}")
            
            for service in subsystem_services:
                can_execute, reason = self.registry.can_execute_service(service.service_id, state)
                print(f"   {service.service_id}: {'✅' if can_execute else '❌'} - {reason}")
                
                # Check current status
                service_statuses = state.get("service_statuses", {})
                current_status = service_statuses.get(service.service_id, "NOT_STARTED")
                print(f"     Current status: {current_status}")
        
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
        print("\n\n🧠 ORCHESTRATING SUBSYSTEM: CONTENT\n" + "=" * 50)
        print("📚 [Content Subsystem] Executing...")
        
        # Check workflow type to determine which services to execute
        workflow_type = state.get("workflow_type", "full_pipeline")
        print(f"🔍 Content Subsystem - workflow_type: {workflow_type}")
        print(f"🔍 Content Subsystem - state keys: {list(state.keys())}")
        
        if workflow_type == "course_initialization":
            # For course initialization, only run course_manager (Course Manager)
            target_service = "course_manager"
            executable_services = self.registry.get_executable_services(state, SubsystemType.CONTENT)
            
            if target_service in executable_services:
                print(f"🎯 Course Initialization: Executing {target_service} only")
                result = self._execute_service(target_service, state)
                
                # Update state with result
                state["service_results"][target_service] = result
                state["service_statuses"][target_service] = ServiceStatus.COMPLETED
                
                self._add_execution_log(state, "course_initialization_completed", {
                    "service_id": target_service,
                    "workflow_type": workflow_type
                })
                
                print(f"✅ Course initialization completed: {target_service}")
                return state
            else:
                print(f"⚠️ Course initialization service {target_service} not executable")
                print(f"🔍 Available services: {executable_services}")
                return state
        
        else:
            # Full pipeline: execute all executable services
            executable_services = self.registry.get_executable_services(state, SubsystemType.CONTENT)
            
            if not executable_services:
                print("⚠️ No executable content services found")
                return state
            
            # Execute services in logical order for full pipeline
            service_execution_order = ["course_manager", "content_preprocessor", "course_mapper", "kli_application", "knowledge_graph_generator"]
            
            executed_count = 0
            for service_id in service_execution_order:
                if service_id in executable_services:
                    print(f"🔄 Executing {service_id}...")
                    result = self._execute_service(service_id, state)
                    
                    # Update state with result
                    state["service_results"][service_id] = result
                    state["service_statuses"][service_id] = ServiceStatus.COMPLETED
                    
                    # Merge service result fields back into main state
                    if isinstance(result, dict):
                        merged_fields = []
                        for key, value in result.items():
                            # Skip internal orchestrator fields and service management fields
                            if key not in ["error", "result", "session_id", "service_statuses", "service_results", "service_errors", "execution_history", "state_validated", "validation_errors", "cross_system_compatibility", "subsystem", "execution_context"]:
                                state[key] = value
                                merged_fields.append(key)
                        
                        if merged_fields:
                            print(f"🔧 Merged fields from {service_id}: {', '.join(merged_fields)}")
                    
                    self._add_execution_log(state, "content_service_executed", {
                        "service_id": service_id,
                        "execution_order": executed_count + 1
                    })
                    
                    print(f"✅ {service_id} completed")
                    executed_count += 1
                    
                    # Re-check for newly executable services after each execution
                    executable_services = self.registry.get_executable_services(state, SubsystemType.CONTENT)
                else:
                    print(f"⏭️ Skipping {service_id} - not executable")
            
            print(f"✅ Content subsystem completed: {executed_count} services executed")
            
            # Debug: Check what fields are in state after content execution
            print(f"🔍 Content execution completed. State keys: {list(state.keys())}")
            print(f"🔍 course_config in state: {'course_config' in state}")
            print(f"🔍 course_manager_result in state: {'course_manager_result' in state}")
            print(f"🔍 faculty_inputs_collected in state: {state.get('faculty_inputs_collected')}")
            
            # Ensure state modifications are preserved by creating a new state dict
            # This helps LangGraph properly track state changes
            final_state = UniversalState(state)
            print(f"🔧 Returning state with {len(final_state)} keys")
            print(f"🔧 Final state keys: {list(final_state.keys())}")
            
            return final_state
    
    def _execute_learner_subsystem(self, state: UniversalState) -> UniversalState:
        """Execute learner subsystem services."""
        print("\n\n🧠 ORCHESTRATING SUBSYSTEM: LEARNER\n" + "=" * 50)
        print("👤 [Learner Subsystem] Executing...")
        
        # Get executable learner services
        executable_services = self.registry.get_executable_services(state, SubsystemType.LEARNER)
        
        if not executable_services:
            print("⚠️ No executable learner services found")
            return state
        
        # Execute services in logical order: Query Strategy → Graph Query → Learning Tree
        service_execution_order = ["query_strategy_manager", "graph_query_engine", "learning_tree_handler"]
        
        executed_count = 0
        for service_id in service_execution_order:
            if service_id in executable_services:
                print(f"🔄 Executing {service_id}...")
                result = self._execute_service(service_id, state)
                
                # Update state with result
                state["service_results"][service_id] = result
                state["service_statuses"][service_id] = ServiceStatus.COMPLETED
                
                # Merge service result fields back into main state
                if isinstance(result, dict):
                    merged_fields = []
                    for key, value in result.items():
                        # Skip internal orchestrator fields and service management fields
                        if key not in ["error", "result", "session_id", "service_statuses", "service_results", "service_errors", "execution_history", "state_validated", "validation_errors", "cross_system_compatibility", "subsystem", "execution_context"]:
                            state[key] = value
                            merged_fields.append(key)
                    
                    if merged_fields:
                        print(f"🔧 Merged fields from {service_id}: {', '.join(merged_fields)}")
                
                self._add_execution_log(state, "learner_service_executed", {
                    "service_id": service_id,
                    "learner_id": state.get("learner_id"),
                    "execution_order": executed_count + 1
                })
                
                print(f"✅ {service_id} completed")
                executed_count += 1
                
                # Re-check for newly executable services after each execution
                executable_services = self.registry.get_executable_services(state, SubsystemType.LEARNER)
            else:
                print(f"⏭️ Skipping {service_id} - not executable")
        
        print(f"✅ Learner subsystem completed: {executed_count} services executed")
        
        # Ensure state modifications are preserved
        final_state = dict(state)
        return final_state
    
    def _execute_sme_subsystem(self, state: UniversalState) -> UniversalState:
        """Execute SME subsystem services."""
        print("\n\n🧠 ORCHESTRATING SUBSYSTEM: SME\n" + "=" * 50)
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
        print("\n\n🧠 ORCHESTRATING SUBSYSTEM: ANALYTICS\n" + "=" * 50)
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
        
        # Debug: Check what fields are in state at finalization
        print(f"🔍 Finalization - State keys: {list(state.keys())}")
        print(f"🔍 course_config in finalization: {'course_config' in state}")
        print(f"🔍 course_manager_result in finalization: {'course_manager_result' in state}")
        print(f"🔍 faculty_inputs_collected in finalization: {state.get('faculty_inputs_collected')}")
        
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
                
                # Handle different return types
                if isinstance(result, dict):
                    # If it's a dict, it might be the updated state or a result dict
                    # Check if it contains state-like keys
                    if any(key in result for key in ['session_id', 'service_statuses', 'course_id', 'learner_id']):
                        # This is likely the updated state - extract the new fields
                        new_fields = {}
                        for key, value in result.items():
                            if key not in ['session_id', 'service_statuses', 'service_results', 'service_errors', 'execution_history']:
                                new_fields[key] = value
                        return new_fields
                    else:
                        # This is a result dict
                        return result
                else:
                    # Non-dict result
                    return {"result": result}
            else:
                return {"error": f"Service {service_id} is not callable"}
                
        except Exception as e:
            state["service_statuses"][service_id] = ServiceStatus.ERROR
            state["service_errors"][service_id] = str(e)
            return {"error": str(e)}
    
    def _get_langgraph_config(self) -> Dict[str, Any]:
        """Get LangGraph configuration from config file."""
        try:
            from config.loader import config
            return config.get('langgraph', {})
        except Exception as e:
            print(f"⚠️ Could not load LangGraph config: {e}")
            return {
                "recursion_limit": 100,
                "debug": False,
                "checkpointer": None
            }
    
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
        
        start_time = time.time()
        session_id = initial_state.get("session_id", "unknown")
        course_id = initial_state.get("course_id", "unknown")
        workflow_type = initial_state.get("workflow_type", "unknown")
        
        print("🌍 [Universal Orchestrator] Starting cross-subsystem orchestration...")
        print("=" * 80)
        
        # Debug: Check initial state before graph invocation
        print(f"🔍 State before graph.invoke(): {list(initial_state.keys())}")
        print(f"🔍 learner_context before graph.invoke(): {initial_state.get('learner_context')}")
        
        try:
            # Ensure state is properly formatted for LangGraph
            # LangGraph expects a dictionary, not a custom object
            state_dict = dict(initial_state)
            
            # CRITICAL: Ensure workflow_type is preserved
            if "workflow_type" in initial_state:
                print(f"🔍 Preserving workflow_type in state_dict: {initial_state['workflow_type']}")
                state_dict["workflow_type"] = initial_state["workflow_type"]
            
            # Get recursion limit from config
            recursion_limit = self.langgraph_config.get("recursion_limit", 100)
            
            result = self.graph.invoke(
                state_dict,
                config={"recursion_limit": recursion_limit}
            )
            
            # Generate a dynamic session summary
            execution_time = time.time() - start_time
            completed_services = [svc for svc, status in result.get("service_statuses", {}).items() 
                                if status == "completed"]
            error_services = [svc for svc, status in result.get("service_statuses", {}).items() 
                            if status == "error"]
            
            print("=" * 80)
            print("🎉 [Universal Orchestrator] Cross-subsystem orchestration completed!")
            print(f"📊 Session Summary:")
            print(f"   Session ID: {result.get('session_id', session_id)}")
            print(f"   Course ID: {result.get('course_id', course_id)}")
            print(f"   Workflow Type: {result.get('workflow_type', workflow_type)}")
            print(f"   Execution Time: {execution_time:.2f} seconds")
            print(f"   Services Completed: {len(completed_services)}")
            print(f"   Services With Errors: {len(error_services)}")
            if error_services:
                print(f"   Error Services: {', '.join(error_services)}")
            print("=" * 80)
            
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
    
    # Register all services first
    # Import register_all_services from main.py since orchestrator/main.py was removed
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from main import register_all_services
    register_all_services()
    
    orchestrator = create_universal_orchestrator()
    
    initial_state: UniversalState = {
        "subsystem": subsystem,
        "execution_context": kwargs
    }
    
    print(f"🔍 Creating initial state for {subsystem}")
    print(f"🔍 kwargs: {kwargs}")
    
    # Add specific context based on subsystem
    if subsystem == SubsystemType.CONTENT:
        initial_state.update({
            "course_id": kwargs.get("course_id", "default_course"),
            "upload_type": kwargs.get("upload_type", "elasticsearch"),
            "faculty_id": kwargs.get("faculty_id", "auto_faculty")  # Use auto_faculty for automatic mode
        })
        
        # Add workflow type for content subsystem
        if kwargs.get("workflow_type"):
            initial_state["workflow_type"] = kwargs["workflow_type"]
            print(f"🔍 Added workflow_type to initial state: {kwargs['workflow_type']}")
        else:
            print(f"⚠️ No workflow_type provided in kwargs")
        
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
        
        print(f"🔍 After adding learner basics: {list(initial_state.keys())}")
        
        # Add learner-specific parameters
        if kwargs.get("learner_profile"):
            initial_state["learner_profile"] = kwargs["learner_profile"]
            # Query Strategy Manager requires learner_context - map from learner_profile
            initial_state["learner_context"] = kwargs["learner_profile"]
            print(f"🔍 Using provided learner_profile as learner_context")
        else:
            # Provide default learner context if none provided
            initial_state["learner_context"] = {
                "decision_label": "Standard Learner",
                "experience_level": "intermediate",
                "learning_style": "adaptive",
                "performance_score": 5,
                "attempts": 0,
                "confusion_level": 0
            }
            print(f"🔍 Using default learner_context")
        
        print(f"🔍 Final learner state keys: {list(initial_state.keys())}")
        print(f"🔍 learner_context: {initial_state.get('learner_context')}")
            
    elif subsystem == SubsystemType.SME:
        initial_state.update({
            "sme_id": kwargs.get("sme_id", "default_sme"),
            "course_id": kwargs.get("course_id", "default_course")
        })
    elif subsystem == SubsystemType.ANALYTICS:
        initial_state.update({
            "course_id": kwargs.get("course_id", "default_course")
        })
    
    print(f"🔍 Final initial state before orchestrator.run(): {list(initial_state.keys())}")
    
    return orchestrator.run(initial_state) 