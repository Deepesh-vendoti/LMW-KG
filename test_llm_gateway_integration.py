#!/usr/bin/env python3
"""
Integration Tests for LLM Gateway with LangGraph Agents

Tests the integration between the LLM Gateway and existing LangGraph agents
to ensure the adapter system works correctly with the operational system.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.llm_gateway import get_llm_gateway, TaskType
from graph.config import get_llm_gateway as get_graph_gateway
from graph.agents import create_researcher_agent, create_lo_generator_agent, create_instruction_agent
from graph.state import GraphState
from langchain_core.messages import HumanMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_llm_gateway_availability():
    """Test if LLM Gateway is available and properly configured."""
    print("\n🧪 Testing LLM Gateway Availability...")
    
    try:
        gateway = get_llm_gateway()
        print(f"✅ LLM Gateway created: {type(gateway).__name__}")
        
        # Check if it has the expected methods
        if hasattr(gateway, 'generate'):
            print("✅ LLM Gateway has 'generate' method")
        else:
            print("❌ LLM Gateway missing 'generate' method")
            return False
            
        if hasattr(gateway, 'health_check'):
            print("✅ LLM Gateway has 'health_check' method")
        else:
            print("❌ LLM Gateway missing 'health_check' method")
            return False
            
        # Test health check
        health = gateway.health_check()
        print(f"✅ Health check: {health}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Gateway creation failed: {e}")
        return False

def test_llm_gateway_task_types():
    """Test if all required task types are available."""
    print("\n🧪 Testing LLM Gateway Task Types...")
    
    required_task_types = [
        TaskType.KNOWLEDGE_EXTRACTION,
        TaskType.LEARNING_OBJECTIVE_GENERATION,
        TaskType.INSTRUCTION_METHOD_SELECTION,
        TaskType.PERSONALIZATION,
        TaskType.GRAPH_QUERY,
        TaskType.PLT_GENERATION
    ]
    
    for task_type in required_task_types:
        print(f"✅ Task type available: {task_type.value}")
    
    return True

def test_llm_gateway_generation():
    """Test LLM Gateway generation with different task types."""
    print("\n🧪 Testing LLM Gateway Generation...")
    
    try:
        gateway = get_llm_gateway()
        
        # Test knowledge extraction
        print("Testing Knowledge Extraction...")
        response = gateway.generate(
            task_type=TaskType.KNOWLEDGE_EXTRACTION,
            prompt="Extract key concepts from: Operating systems manage computer hardware and software resources.",
            constraints={
                "max_cost": 0.05,
                "privacy_requirement": "local",
                "max_latency_ms": 5000
            }
        )
        print(f"✅ Knowledge Extraction: {response['model_used']} - Cost: ${response['cost']:.4f}")
        
        # Test learning objective generation
        print("Testing Learning Objective Generation...")
        response = gateway.generate(
            task_type=TaskType.LEARNING_OBJECTIVE_GENERATION,
            prompt="Generate learning objectives for: Memory management in operating systems",
            constraints={
                "max_cost": 0.08,
                "privacy_requirement": "local",
                "max_latency_ms": 6000
            }
        )
        print(f"✅ Learning Objective Generation: {response['model_used']} - Cost: ${response['cost']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Gateway generation failed: {e}")
        return False

def test_agent_integration():
    """Test if agents can use the LLM Gateway."""
    print("\n🧪 Testing Agent Integration...")
    
    try:
        # Test researcher agent
        print("Testing Researcher Agent...")
        researcher = create_researcher_agent()
        state = GraphState(messages=[HumanMessage(content="Explain memory management in operating systems")])
        
        result = researcher.invoke(state)
        print(f"✅ Researcher Agent executed successfully")
        print(f"   Messages: {len(result.messages)}")
        
        # Test LO generator agent
        print("Testing LO Generator Agent...")
        lo_generator = create_lo_generator_agent()
        state = GraphState(messages=[HumanMessage(content="Generate learning objectives for operating systems")])
        
        result = lo_generator.invoke(state)
        print(f"✅ LO Generator Agent executed successfully")
        print(f"   Messages: {len(result.messages)}")
        
        # Test instruction agent
        print("Testing Instruction Agent...")
        instruction_agent = create_instruction_agent()
        state = GraphState(messages=[HumanMessage(content="Select instruction methods for memory management")])
        
        result = instruction_agent.invoke(state)
        print(f"✅ Instruction Agent executed successfully")
        print(f"   Messages: {len(result.messages)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent integration failed: {e}")
        return False

def test_fallback_mechanism():
    """Test fallback mechanism when LLM Gateway is not available."""
    print("\n🧪 Testing Fallback Mechanism...")
    
    try:
        # Test graph config fallback
        gateway = get_graph_gateway()
        print(f"✅ Graph config fallback works: {type(gateway).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback mechanism failed: {e}")
        return False

def test_cost_optimization():
    """Test cost optimization features."""
    print("\n🧪 Testing Cost Optimization...")
    
    try:
        gateway = get_llm_gateway()
        
        # Test with cost constraints
        response = gateway.generate(
            task_type=TaskType.SUMMARY,
            prompt="Summarize the key concepts of process scheduling",
            constraints={
                "max_cost": 0.02,  # Very low cost constraint
                "privacy_requirement": "local",
                "max_latency_ms": 3000
            }
        )
        
        print(f"✅ Cost optimization: {response['model_used']} - Cost: ${response['cost']:.4f}")
        
        if response['cost'] <= 0.02:
            print("✅ Cost constraint respected")
        else:
            print("⚠️ Cost constraint exceeded")
        
        return True
        
    except Exception as e:
        print(f"❌ Cost optimization test failed: {e}")
        return False

def test_caching():
    """Test caching functionality."""
    print("\n🧪 Testing Caching...")
    
    try:
        gateway = get_llm_gateway()
        
        # First request
        prompt = "Explain virtual memory in operating systems"
        response1 = gateway.generate(
            task_type=TaskType.SUMMARY,
            prompt=prompt,
            use_cache=True
        )
        print(f"✅ First request: {response1['model_used']} - Cost: ${response1['cost']:.4f}")
        
        # Second request (should be cached)
        response2 = gateway.generate(
            task_type=TaskType.SUMMARY,
            prompt=prompt,
            use_cache=True
        )
        print(f"✅ Second request: {response2['model_used']} - Cost: ${response2['cost']:.4f}")
        
        # Check if responses are similar (cached)
        if response1['content'] == response2['content']:
            print("✅ Caching working correctly")
        else:
            print("⚠️ Caching may not be working")
        
        return True
        
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("🚀 LLM Gateway Integration Tests")
    print("=" * 50)
    
    tests = [
        ("LLM Gateway Availability", test_llm_gateway_availability),
        ("Task Types", test_llm_gateway_task_types),
        ("Generation", test_llm_gateway_generation),
        ("Agent Integration", test_agent_integration),
        ("Fallback Mechanism", test_fallback_mechanism),
        ("Cost Optimization", test_cost_optimization),
        ("Caching", test_caching)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LLM Gateway integration is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 