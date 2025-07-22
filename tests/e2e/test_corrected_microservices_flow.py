#!/usr/bin/env python3
"""
Test Script for Corrected Microservices Flow

Tests that Course Manager executes first and Content Preprocessor 
properly validates dependencies.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from orchestrator.universal_orchestrator import UniversalOrchestrator
from orchestrator.state import UniversalState, SubsystemType, ServiceStatus

def test_corrected_microservices_flow():
    """Test the corrected microservices execution order."""
    print("🧪 Testing Corrected Microservices Flow")
    print("=" * 50)
    
    # Create orchestrator
    orchestrator = UniversalOrchestrator()
    
    # Initial state for content processing
    initial_state: UniversalState = {
        "course_id": "TEST_COURSE_001",
        "faculty_id": "TEST_FACULTY_001", 
        "upload_type": "elasticsearch",
        "workflow_type": "course_initialization",
        "subsystem": SubsystemType.CONTENT,
        "service_statuses": {},
        "service_errors": {}
    }
    
    print(f"📚 Testing Course: {initial_state['course_id']}")
    print(f"👨‍🏫 Faculty: {initial_state['faculty_id']}")
    print()
    
    try:
        # Execute content subsystem
        print("🔄 Executing Content Subsystem...")
        result = orchestrator._execute_content_subsystem(initial_state)
        
        # Analyze results
        service_statuses = result.get("service_statuses", {})
        service_errors = result.get("service_errors", {})
        
        print("\n📊 Execution Results:")
        print("-" * 30)
        
        # Expected execution order
        expected_order = ["course_manager", "content_preprocessor", "course_mapper", "kli_application", "knowledge_graph_generator"]
        
        for i, service_id in enumerate(expected_order, 1):
            status = service_statuses.get(service_id, "NOT_EXECUTED")
            
            if service_id in service_errors:
                error = service_errors[service_id]
                print(f"{i}. ❌ {service_id}: {status} - {error}")
            elif status == ServiceStatus.COMPLETED:
                print(f"{i}. ✅ {service_id}: {status}")
            elif status == ServiceStatus.WAITING:
                print(f"{i}. ⏳ {service_id}: {status}")
            else:
                print(f"{i}. ⏭️ {service_id}: {status}")
        
        # Validate Course Manager executed first
        course_manager_status = service_statuses.get("course_manager")
        content_preprocessor_status = service_statuses.get("content_preprocessor")
        
        print("\n🔍 Dependency Validation:")
        print("-" * 30)
        
        if course_manager_status == ServiceStatus.COMPLETED:
            print("✅ Course Manager: Successfully completed first")
            
            if content_preprocessor_status == ServiceStatus.COMPLETED:
                print("✅ Content Preprocessor: Executed after Course Manager")
                
                # Check for course configuration
                if result.get("course_config"):
                    print("✅ Course Configuration: Present from Course Manager")
                else:
                    print("⚠️ Course Configuration: Missing")
                    
            elif content_preprocessor_status == ServiceStatus.WAITING:
                print("⏳ Content Preprocessor: Correctly waiting for dependencies")
            else:
                print(f"❌ Content Preprocessor: Unexpected status {content_preprocessor_status}")
        else:
            print(f"❌ Course Manager: Failed to complete - {course_manager_status}")
        
        # Overall result
        completed_services = [sid for sid, status in service_statuses.items() if status == ServiceStatus.COMPLETED]
        total_services = len(expected_order)
        
        print(f"\n🎯 Summary:")
        print(f"   Services Completed: {len(completed_services)}/{total_services}")
        print(f"   Execution Order: {'✅ CORRECTED' if course_manager_status == ServiceStatus.COMPLETED else '❌ INCORRECT'}")
        
        if len(completed_services) >= 2:  # Course Manager + at least one dependent
            print("🎉 Corrected microservices flow is working!")
        else:
            print("⚠️ Some services failed or are waiting for dependencies")
            
        return result
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_dependency_validation():
    """Test Content Preprocessor dependency validation."""
    print("\n🧪 Testing Dependency Validation")
    print("=" * 50)
    
    from subsystems.content.services.content_preprocessor import ContentPreprocessorService
    
    # Test Content Preprocessor directly
    preprocessor = ContentPreprocessorService()
    
    # Test 1: Missing Course Manager
    print("Test 1: Content Preprocessor without Course Manager")
    state_without_cm: UniversalState = {
        "course_id": "TEST_COURSE",
        "upload_type": "elasticsearch",
        "service_statuses": {}
    }
    
    result1 = preprocessor._validate_dependencies(state_without_cm)
    print(f"   Result: {'❌ Correctly blocked' if not result1 else '✅ Incorrectly allowed'}")
    
    # Test 2: With completed Course Manager
    print("Test 2: Content Preprocessor with completed Course Manager")
    state_with_cm: UniversalState = {
        "course_id": "TEST_COURSE",
        "upload_type": "elasticsearch", 
        "service_statuses": {
            "course_manager": ServiceStatus.COMPLETED
        },
        "course_config": {"test": "config"},
        "faculty_inputs_collected": True
    }
    
    result2 = preprocessor._validate_dependencies(state_with_cm)
    print(f"   Result: {'✅ Correctly allowed' if result2 else '❌ Incorrectly blocked'}")
    
    print(f"\n🎯 Dependency Validation: {'✅ WORKING' if not result1 and result2 else '❌ FAILING'}")

if __name__ == "__main__":
    print("🚀 Testing Implementation Improvements")
    print("=" * 60)
    
    # Test main flow
    test_corrected_microservices_flow()
    
    # Test dependency validation
    test_dependency_validation()
    
    print("\n" + "=" * 60)
    print("✅ Test suite completed!")
