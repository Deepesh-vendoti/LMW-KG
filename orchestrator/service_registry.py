"""
Service Registry for Cross-Subsystem Orchestration

Provides dynamic service discovery, registration, and routing capabilities
for the universal LangGraph orchestrator.
"""

import uuid
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from orchestrator.state import (
    UniversalState, 
    ServiceDefinition, 
    SubsystemDefinition, 
    SubsystemType, 
    ServiceStatus,
    CrossSubsystemRequest,
    CrossSubsystemResponse
)

@dataclass
class ServiceRegistry:
    """
    Central registry for all microservices across subsystems.
    Supports dynamic service discovery and cross-subsystem routing.
    """
    
    subsystems: Dict[SubsystemType, SubsystemDefinition] = field(default_factory=dict)
    services: Dict[str, ServiceDefinition] = field(default_factory=dict)
    service_instances: Dict[str, Any] = field(default_factory=dict)
    
    def register_subsystem(self, subsystem: SubsystemDefinition) -> None:
        """Register a complete subsystem with all its services."""
        self.subsystems[subsystem.subsystem_type] = subsystem
        
        for service in subsystem.services:
            self.services[service.service_id] = service
            print(f"🔧 Registered service: {service.service_id} ({subsystem.subsystem_type.value})")
    
    def register_service(self, service: ServiceDefinition, subsystem_type: SubsystemType) -> None:
        """Register an individual service."""
        self.services[service.service_id] = service
        
        # Create subsystem if it doesn't exist
        if subsystem_type not in self.subsystems:
            self.subsystems[subsystem_type] = SubsystemDefinition(
                subsystem_type=subsystem_type,
                name=f"{subsystem_type.value.title()} Subsystem",
                description=f"Services for {subsystem_type.value} subsystem",
                services=[],
                entry_points=[]
            )
        
        # Add to subsystem if not already present
        if service not in self.subsystems[subsystem_type].services:
            self.subsystems[subsystem_type].services.append(service)
        
        print(f"🔧 Registered service: {service.service_id} ({subsystem_type.value})")
    
    def get_service(self, service_id: str) -> Optional[ServiceDefinition]:
        """Get service definition by ID."""
        return self.services.get(service_id)
    
    def get_subsystem_services(self, subsystem_type: SubsystemType) -> List[ServiceDefinition]:
        """Get all services for a specific subsystem."""
        if subsystem_type in self.subsystems:
            return self.subsystems[subsystem_type].services
        return []
    
    def get_service_dependencies(self, service_id: str) -> List[str]:
        """Get dependencies for a service."""
        service = self.get_service(service_id)
        return service.dependencies if service else []
    
    def validate_dependencies(self, service_id: str, state: UniversalState) -> tuple[bool, List[str]]:
        """
        Validate that all dependencies for a service are satisfied.
        Returns (is_valid, missing_dependencies)
        """
        service = self.get_service(service_id)
        if not service:
            return False, [f"Service {service_id} not found"]
        
        missing_deps = []
        service_statuses = state.get("service_statuses", {})
        
        for dep_id in service.dependencies:
            dep_status = service_statuses.get(dep_id, ServiceStatus.NOT_STARTED)
            if dep_status != ServiceStatus.COMPLETED:
                missing_deps.append(f"{dep_id} (status: {dep_status})")
        
        return len(missing_deps) == 0, missing_deps
    
    def can_execute_service(self, service_id: str, state: UniversalState) -> tuple[bool, str]:
        """
        Check if a service can be executed given current state.
        Returns (can_execute, reason)
        """
        service = self.get_service(service_id)
        if not service:
            return False, f"Service {service_id} not registered"
        
        # Check dependencies
        deps_valid, missing_deps = self.validate_dependencies(service_id, state)
        if not deps_valid:
            return False, f"Missing dependencies: {', '.join(missing_deps)}"
        
        # Check required inputs
        missing_inputs = []
        for input_field in service.required_inputs:
            if input_field not in state or state[input_field] is None:
                missing_inputs.append(input_field)
        
        if missing_inputs:
            return False, f"Missing required inputs: {', '.join(missing_inputs)}"
        
        return True, "Ready to execute"
    
    def get_executable_services(self, state: UniversalState, subsystem: Optional[SubsystemType] = None) -> List[str]:
        """Get list of services that can be executed given current state."""
        executable = []
        
        services_to_check = self.services.keys()
        if subsystem:
            services_to_check = [s.service_id for s in self.get_subsystem_services(subsystem)]
        
        for service_id in services_to_check:
            can_execute, _ = self.can_execute_service(service_id, state)
            if can_execute:
                service_statuses = state.get("service_statuses", {})
                current_status = service_statuses.get(service_id, ServiceStatus.NOT_STARTED)
                if current_status in [ServiceStatus.NOT_STARTED, ServiceStatus.ERROR]:
                    executable.append(service_id)
        
        return executable
    
    def route_cross_subsystem_request(self, request: CrossSubsystemRequest) -> CrossSubsystemResponse:
        """Route a request between subsystems."""
        start_time = time.time()
        
        try:
            # Get target service
            service = self.get_service(request.service_id)
            if not service:
                return CrossSubsystemResponse(
                    request_id=request.request_id,
                    status=ServiceStatus.ERROR,
                    error=f"Service {request.service_id} not found"
                )
            
            # Execute service
            if hasattr(service.callable, '__call__'):
                result = service.callable(request.payload)
                
                execution_time = int((time.time() - start_time) * 1000)
                
                return CrossSubsystemResponse(
                    request_id=request.request_id,
                    status=ServiceStatus.COMPLETED,
                    result=result,
                    execution_time_ms=execution_time
                )
            else:
                return CrossSubsystemResponse(
                    request_id=request.request_id,
                    status=ServiceStatus.ERROR,
                    error=f"Service {request.service_id} is not callable"
                )
                
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return CrossSubsystemResponse(
                request_id=request.request_id,
                status=ServiceStatus.ERROR,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def list_services(self, subsystem: Optional[SubsystemType] = None) -> Dict[str, Any]:
        """List all registered services with metadata."""
        services_info = {}
        
        services_to_list = self.services.items()
        if subsystem:
            subsystem_services = self.get_subsystem_services(subsystem)
            services_to_list = [(s.service_id, s) for s in subsystem_services]
        
        for service_id, service in services_to_list:
            services_info[service_id] = {
                "name": service.name,
                "subsystem": service.subsystem.value,
                "description": service.description,
                "dependencies": service.dependencies,
                "required_inputs": service.required_inputs,
                "provided_outputs": service.provided_outputs,
                "timeout_seconds": service.timeout_seconds
            }
        
        return services_info

# ===============================
# GLOBAL REGISTRY INSTANCE
# ===============================

# Singleton service registry
_global_registry: Optional[ServiceRegistry] = None

def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ServiceRegistry()
    return _global_registry

def reset_service_registry() -> None:
    """Reset the global service registry (for testing)."""
    global _global_registry
    _global_registry = ServiceRegistry()

# ===============================
# UTILITY FUNCTIONS
# ===============================

def generate_request_id() -> str:
    """Generate unique request ID for cross-subsystem requests."""
    return f"req_{uuid.uuid4().hex[:8]}_{int(time.time())}"

def create_cross_subsystem_request(
    source: SubsystemType,
    target: SubsystemType, 
    service_id: str,
    payload: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> CrossSubsystemRequest:
    """Create a cross-subsystem request."""
    return CrossSubsystemRequest(
        request_id=generate_request_id(),
        source_subsystem=source,
        target_subsystem=target,
        service_id=service_id,
        payload=payload,
        context=context or {},
        timestamp=time.time()
    )

def register_all_services():
    """Register all available services across subsystems."""
    registry = get_service_registry()
    
    # Check if services are already registered to avoid duplicates
    if len(registry.services) > 0:
        print("[INFO] Services already registered, skipping registration")
        return registry
    
    # Clear any existing services to ensure clean registration
    registry.services.clear()
    registry.subsystems.clear()
    
    print("[SYSTEM] Registering services across all subsystems...")
    
    # ===== CONTENT SUBSYSTEM =====
    print("[CONTENT] Registering Content Subsystem services...")
    
    # Content Subsystem Services
    content_services = [
        ("course_manager", "subsystems.content.services.course_manager", "create_course_manager_service"),
        ("content_preprocessor", "subsystems.content.services.content_preprocessor", "create_content_preprocessor_service"),
        ("course_mapper", "subsystems.content.services.course_mapper", "create_course_mapper_service"),
        ("kli_application", "subsystems.content.services.kli_application", "create_kli_application_service"),
        ("knowledge_graph_generator", "subsystems.content.services.knowledge_graph_generator", "create_knowledge_graph_generator_service")
    ]
    
    for service_name, module_path, factory_name in content_services:
        try:
            module = __import__(module_path, fromlist=[factory_name])
            factory = getattr(module, factory_name)
            service = factory()
            registry.register_service(service.get_service_definition(), SubsystemType.CONTENT)
        except (ImportError, AttributeError) as e:
            print(f"[WARNING] Could not register {service_name}: {e}")
    
    # Register content subsystem definition
    content_services = [s for s in registry.services.values() if s.subsystem == SubsystemType.CONTENT]
    if content_services:
        content_subsystem = SubsystemDefinition(
            subsystem_type=SubsystemType.CONTENT,
            name="Content Subsystem",
            description="Handles course content processing and knowledge graph generation",
            services=content_services,
            entry_points=["course_manager"]
        )
        registry.register_subsystem(content_subsystem)
    
    # ===== LEARNER SUBSYSTEM =====
    print("[LEARNER] Registering Learner Subsystem services...")
    
    # Learner Subsystem Services (in correct execution order)
    learner_services = [
        ("query_strategy_manager", "subsystems.learner.services.query_strategy_manager", "create_query_strategy_manager_service"),
        ("graph_query_engine", "subsystems.learner.services.graph_query_engine", "create_graph_query_engine_service"),
        ("learning_tree_handler", "subsystems.learner.services.learning_tree_handler", "create_learning_tree_handler_service")
    ]
    
    for service_name, module_path, factory_name in learner_services:
        try:
            module = __import__(module_path, fromlist=[factory_name])
            factory = getattr(module, factory_name)
            service = factory()
            registry.register_service(service.get_service_definition(), SubsystemType.LEARNER)
        except (ImportError, AttributeError) as e:
            print(f"[WARNING] Could not register {service_name}: {e}") 
    
    # Register learner subsystem definition
    learner_services = [s for s in registry.services.values() if s.subsystem == SubsystemType.LEARNER]
    if learner_services:
        learner_subsystem = SubsystemDefinition(
            subsystem_type=SubsystemType.LEARNER,
            name="Learner Subsystem", 
            description="Handles learner personalization and learning path generation",
            services=learner_services,
            entry_points=["query_strategy_manager"]
        )
        registry.register_subsystem(learner_subsystem)
    
    # ===== SME SUBSYSTEM =====
    print("[SME] Registering SME Subsystem services...")
    # SME services would be registered here when implemented
    
    # ===== ANALYTICS SUBSYSTEM =====
    print("[ANALYTICS] Registering Analytics Subsystem services...")
    # Analytics services would be registered here when implemented
    
    print(f"[SUCCESS] Service registration completed: {len(registry.services)} services registered")
    
    return registry 