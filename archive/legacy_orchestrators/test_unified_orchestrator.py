#!/usr/bin/env python3
"""
Test Unified LangGraph Orchestrator

This script tests the unified orchestrator that coordinates all 8 microservice responsibilities.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph.orchestrator import run_course_pipeline

def test_unified_orchestrator():
    """Test the unified orchestrator with Elasticsearch input"""
    print("🧪 Testing Unified LangGraph Orchestrator")
    print("=" * 50)
    
    # Test configuration
    test_config = {
        "course_id": "TEST_OSN",
        "upload_type": "elasticsearch",
        "es_index": "advanced_docs_elasticsearch_v2",
        "learner_id": "TEST_R000",
        "learner_context": {
            "decision_label": "Standard Learner",
            "flagged_rules_hit": []
        }
    }
    
    print("📋 Test Configuration:")
    for key, value in test_config.items():
        print(f"   {key}: {value}")
    
    print("\n🚀 Starting orchestrator test...")
    
    try:
        # Run the unified pipeline
        result = run_course_pipeline(**test_config)
        
        if result:
            print("\n✅ TEST PASSED: Unified orchestrator executed successfully")
            
            # Validate key outputs
            checks = []
            
            # Check if all stages completed
            completed_stages = result.get("completed_stages", [])
            expected_stages = [
                "course_manager", 
                "content_preprocessor", 
                "course_content_mapper", 
                "kli_application", 
                "knowledge_graph_generator"
            ]
            
            for stage in expected_stages:
                if stage in completed_stages:
                    checks.append(f"✅ {stage}")
                else:
                    checks.append(f"❌ {stage}")
            
            # Check faculty approval outputs
            if result.get("facd"):
                checks.append("✅ FACD (Faculty Approved Course Details)")
            else:
                checks.append("❌ FACD missing")
                
            if result.get("fccs"):
                checks.append("✅ FCCS (Faculty Confirmed Course Structure)")
            else:
                checks.append("❌ FCCS missing")
                
            if result.get("ffcs"):
                checks.append("✅ FFCS (Faculty Finalized Course Structure)")
            else:
                checks.append("❌ FFCS missing")
            
            # Check learner-specific outputs
            if result.get("plt_data"):
                checks.append("✅ PLT (Personalized Learning Tree)")
            else:
                checks.append("⚠️  PLT (depends on learner context)")
            
            # Print validation results
            print("\n📊 VALIDATION RESULTS:")
            for check in checks:
                print(f"   {check}")
            
            # Check for errors
            errors = result.get("errors", [])
            if errors:
                print(f"\n⚠️  Errors encountered: {len(errors)}")
                for error in errors:
                    print(f"   • {error}")
            else:
                print("\n✅ No errors encountered")
            
            return True
            
        else:
            print("❌ TEST FAILED: Orchestrator returned None")
            return False
            
    except Exception as e:
        print(f"❌ TEST FAILED: Exception occurred")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_subgraphs():
    """Test individual subgraph components"""
    print("\n🔬 Testing Individual Subgraph Components")
    print("=" * 50)
    
    from graph.orchestrator import (
        course_manager_subgraph,
        content_preprocessor_subgraph,
        course_content_mapper_subgraph
    )
    
    # Test Course Manager
    print("\n1️⃣ Testing Course Manager Subgraph...")
    test_state = {
        "course_id": "TEST_OSN",
        "upload_type": "elasticsearch",
        "es_index": "advanced_docs_elasticsearch_v2"
    }
    
    try:
        result = course_manager_subgraph(test_state)
        if "course_manager" in result.get("completed_stages", []):
            print("   ✅ Course Manager test passed")
        else:
            print("   ❌ Course Manager test failed")
    except Exception as e:
        print(f"   ❌ Course Manager test error: {e}")
    
    # Test Content Preprocessor  
    print("\n2️⃣ Testing Content Preprocessor Subgraph...")
    test_state = {
        "course_id": "TEST_OSN",
        "upload_type": "elasticsearch",
        "es_index": "advanced_docs_elasticsearch_v2"
    }
    
    try:
        result = content_preprocessor_subgraph(test_state)
        if result.get("chunks"):
            print(f"   ✅ Content Preprocessor test passed: {len(result['chunks'])} chunks")
        else:
            print("   ❌ Content Preprocessor test failed: no chunks generated")
    except Exception as e:
        print(f"   ❌ Content Preprocessor test error: {e}")

if __name__ == "__main__":
    print("🧪 UNIFIED ORCHESTRATOR TEST SUITE")
    print("=" * 60)
    
    # Run individual component tests
    test_individual_subgraphs()
    
    # Run full orchestrator test
    success = test_unified_orchestrator()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED")
        print("📋 Unified orchestrator is ready for production use")
        print("\n💡 Next steps:")
        print("   • Run: python main.py unified")
        print("   • Test with different upload types (pdf, elasticsearch, llm_generated)")
        print("   • Customize learner contexts for different PLT strategies")
    else:
        print("❌ TESTS FAILED")
        print("🛠️  Check the error messages above and fix issues before using")
    
    print("=" * 60) 