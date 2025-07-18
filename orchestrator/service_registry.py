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
        
        # Add to subsystem if it exists
        if subsystem_type in self.subsystems:
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
        context=context or {}
    ) 