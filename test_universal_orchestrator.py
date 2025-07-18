"""
Universal Orchestrator Test Suite

Tests the cross-subsystem orchestration capabilities and service registration.
"""

import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from orchestrator.state import UniversalState, SubsystemType, ServiceStatus
from orchestrator.service_registry import get_service_registry, reset_service_registry
from orchestrator.universal_orchestrator import UniversalOrchestrator, run_cross_subsystem_workflow
from orchestrator.main import register_all_services

def test_service_registration():
    """Test service registration across subsystems."""
    print("🧪 Testing Service Registration...")
    
    # Reset registry for clean test
    reset_service_registry()
    
    # Register all services
    registry = register_all_services()
    
    # Verify services are registered
    all_services = registry.list_services()
    print(f"   ✅ Registered {len(all_services)} services")
    
    # Check subsystem distribution
    content_services = registry.list_services(SubsystemType.CONTENT)
    learner_services = registry.list_services(SubsystemType.LEARNER)
    
    print(f"   📚 Content services: {len(content_services)}")
    print(f"   👤 Learner services: {len(learner_services)}")
    
    # Verify specific services exist
    expected_services = ["content_preprocessor", "learning_tree_handler"]
    for service_id in expected_services:
        service = registry.get_service(service_id)
        if service:
            print(f"   ✅ Service '{service_id}' registered")
        else:
            print(f"   ❌ Service '{service_id}' missing")
    
    return len(all_services) > 0

def test_content_subsystem():
    """Test content subsystem workflow."""
    print("\n🧪 Testing Content Subsystem...")
    
    try:
        # Register services
        register_all_services()
        
        # Run content workflow
        result = run_cross_subsystem_workflow(
            SubsystemType.CONTENT,
            course_id="TEST_COURSE",
            upload_type="llm_generated",
            raw_content="This is test content for knowledge graph generation. It covers operating systems, memory management, and process scheduling."
        )
        
        # Check results
        session_id = result.get("session_id")
        chunks = result.get("chunks", [])
        service_statuses = result.get("service_statuses", {})
        
        print(f"   ✅ Session ID: {session_id}")
        print(f"   ✅ Chunks processed: {len(chunks)}")
        print(f"   ✅ Service statuses: {service_statuses}")
        
        # Verify content preprocessor ran
        if "content_preprocessor" in service_statuses:
            status = service_statuses["content_preprocessor"]
            print(f"   ✅ Content Preprocessor status: {status}")
            return status == ServiceStatus.COMPLETED
        else:
            print(f"   ❌ Content Preprocessor not executed")
            return False
            
    except Exception as e:
        print(f"   ❌ Content subsystem test failed: {e}")
        return False

def test_learner_subsystem():
    """Test learner subsystem workflow."""
    print("\n🧪 Testing Learner Subsystem...")
    
    try:
        # Register services
        register_all_services()
        
        # Run learner workflow
        result = run_cross_subsystem_workflow(
            SubsystemType.LEARNER,
            learner_id="TEST_LEARNER",
            course_id="TEST_COURSE",
            learner_profile={"learning_style": "visual", "pace": "moderate"}
        )
        
        # Check results
        session_id = result.get("session_id")
        plt = result.get("personalized_learning_tree")
        recommendations = result.get("adaptive_recommendations", [])
        service_statuses = result.get("service_statuses", {})
        
        print(f"   ✅ Session ID: {session_id}")
        print(f"   ✅ PLT generated: {'Yes' if plt else 'No'}")
        print(f"   ✅ Recommendations: {len(recommendations)}")
        print(f"   ✅ Service statuses: {service_statuses}")
        
        # Verify learning tree handler ran
        if "learning_tree_handler" in service_statuses:
            status = service_statuses["learning_tree_handler"]
            print(f"   ✅ Learning Tree Handler status: {status}")
            return status == ServiceStatus.COMPLETED
        else:
            print(f"   ❌ Learning Tree Handler not executed")
            return False
            
    except Exception as e:
        print(f"   ❌ Learner subsystem test failed: {e}")
        return False

def test_cross_subsystem_workflow():
    """Test cross-subsystem workflow."""
    print("\n🧪 Testing Cross-Subsystem Workflow...")
    
    try:
        # Register services
        register_all_services()
        
        # Create orchestrator
        orchestrator = UniversalOrchestrator()
        
        # Build cross-subsystem state
        initial_state: UniversalState = {
            "course_id": "CROSS_TEST",
            "subsystem": SubsystemType.CONTENT,
            "upload_type": "llm_generated",
            "raw_content": "Cross-subsystem test content about operating systems and memory management.",
            "learner_id": "CROSS_LEARNER",
            "execution_context": {
                "multi_subsystem": True,
                "target_subsystems": ["content", "learner"]
            }
        }
        
        # Run orchestrator
        result = orchestrator.run(initial_state)
        
        # Check results
        session_id = result.get("session_id")
        execution_history = result.get("execution_history", [])
        service_statuses = result.get("service_statuses", {})
        
        print(f"   ✅ Session ID: {session_id}")
        print(f"   ✅ Execution steps: {len(execution_history)}")
        print(f"   ✅ Service statuses: {service_statuses}")
        
        # Check if multiple subsystems were involved
        completed_services = [sid for sid, status in service_statuses.items() if status == ServiceStatus.COMPLETED]
        print(f"   ✅ Completed services: {completed_services}")
        
        return len(completed_services) > 0
        
    except Exception as e:
        print(f"   ❌ Cross-subsystem workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_dependencies():
    """Test service dependency resolution."""
    print("\n🧪 Testing Service Dependencies...")
    
    try:
        # Register services
        registry = register_all_services()
        
        # Test dependency validation
        state: UniversalState = {
            "upload_type": "llm_generated",
            "raw_content": "Test content",
            "learner_id": "TEST",
            "course_id": "TEST"
        }
        
        # Check if learning_tree_handler can execute without content_preprocessor
        can_execute_before, reason_before = registry.can_execute_service("learning_tree_handler", state)
        print(f"   📋 Learning Tree Handler can execute before Content Preprocessor: {can_execute_before}")
        if not can_execute_before:
            print(f"      Reason: {reason_before}")
        
        # Mark content_preprocessor as completed
        state["service_statuses"] = {"content_preprocessor": ServiceStatus.COMPLETED}
        
        # Check again
        can_execute_after, reason_after = registry.can_execute_service("learning_tree_handler", state)
        print(f"   📋 Learning Tree Handler can execute after Content Preprocessor: {can_execute_after}")
        if not can_execute_after:
            print(f"      Reason: {reason_after}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Service dependency test failed: {e}")
        return False

def test_state_management():
    """Test universal state management."""
    print("\n🧪 Testing State Management...")
    
    try:
        # Create test state
        state: UniversalState = {
            "session_id": "test_session",
            "course_id": "TEST",
            "subsystem": SubsystemType.CONTENT,
            "upload_type": "llm_generated",
            "raw_content": "Test content"
        }
        
        # Test state validation
        required_fields = ["session_id", "course_id", "subsystem"]
        missing_fields = [field for field in required_fields if field not in state]
        
        print(f"   ✅ Required fields present: {len(missing_fields) == 0}")
        if missing_fields:
            print(f"      Missing: {missing_fields}")
        
        # Test state updates
        state["service_statuses"] = {}
        state["service_results"] = {}
        state["execution_history"] = []
        
        print(f"   ✅ State structure initialized")
        
        # Test subsystem auto-detection
        from orchestrator.universal_orchestrator import UniversalOrchestrator
        orchestrator = UniversalOrchestrator()
        detected_subsystem = orchestrator._auto_detect_subsystem(state)
        
        print(f"   ✅ Auto-detected subsystem: {detected_subsystem}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ State management test failed: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    print("🚀 Universal Orchestrator Test Suite")
    print("=" * 80)
    
    tests = [
        ("Service Registration", test_service_registration),
        ("Content Subsystem", test_content_subsystem), 
        ("Learner Subsystem", test_learner_subsystem),
        ("Cross-Subsystem Workflow", test_cross_subsystem_workflow),
        ("Service Dependencies", test_service_dependencies),
        ("State Management", test_state_management)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        start_time = time.time()
        try:
            result = test_func()
            duration = time.time() - start_time
            results[test_name] = ("PASS" if result else "FAIL", duration)
            print(f"   🎯 {test_name}: {'PASS' if result else 'FAIL'} ({duration:.2f}s)")
        except Exception as e:
            duration = time.time() - start_time
            results[test_name] = ("ERROR", duration)
            print(f"   💥 {test_name}: ERROR ({duration:.2f}s) - {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("🎯 Test Summary")
    print("="*80)
    
    passed = sum(1 for status, _ in results.values() if status == "PASS")
    failed = sum(1 for status, _ in results.values() if status == "FAIL")
    errors = sum(1 for status, _ in results.values() if status == "ERROR")
    total_time = sum(duration for _, duration in results.values())
    
    for test_name, (status, duration) in results.items():
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "💥"
        print(f"{status_emoji} {test_name}: {status} ({duration:.2f}s)")
    
    print(f"\n📊 Results: {passed} passed, {failed} failed, {errors} errors")
    print(f"⏱️ Total time: {total_time:.2f}s")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Universal orchestrator is working correctly.")
        return True
    else:
        print(f"\n⚠️ {failed + errors} test(s) failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 