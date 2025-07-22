#!/usr/bin/env python
"""
Manual Microservice Flow Runner

This script runs each microservice in the content pipeline manually,
one by one, with user input at each step.

Sequence:
1. Course Manager
2. Content Preprocessor
3. Course Mapper
4. KLI Application
5. Knowledge Graph Generator
"""

import sys
import time
import json
from typing import Dict, Any, Optional

# Add project root to path
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# Import required components
from orchestrator.state import UniversalState, SubsystemType, ServiceStatus
from orchestrator.service_registry import get_service_registry, reset_service_registry
from main import register_all_services

# Import service creators
from subsystems.content.services.course_manager import create_course_manager_service
from subsystems.content.services.content_preprocessor import create_content_preprocessor_service
from subsystems.content.services.course_mapper import create_course_mapper_service
from subsystems.content.services.kli_application import create_kli_application_service
from subsystems.content.services.knowledge_graph_generator import create_knowledge_graph_generator_service

def print_separator(title: str):
    """Print a separator with title."""
    print("\n" + "=" * 80)
    print(f"🔷 {title}")
    print("=" * 80)

def print_state_summary(state: Dict[str, Any]):
    """Print a summary of the current state."""
    print("\n📊 Current State Summary:")
    print(f"  Course ID: {state.get('course_id', 'Not set')}")
    print(f"  Faculty ID: {state.get('faculty_id', 'Not set')}")
    print(f"  Upload Type: {state.get('upload_type', 'Not set')}")
    
    # Show specific data based on pipeline stage
    if "course_config" in state:
        print(f"  Course Config: {json.dumps(state['course_config'], indent=2)[:100]}...")
    
    if "chunks" in state:
        print(f"  Content Chunks: {len(state.get('chunks', []))} chunks processed")
    
    if "facd" in state:
        los = state.get("facd", {}).get("learning_objectives", [])
        kcs = state.get("facd", {}).get("draft_kcs", [])
        print(f"  Learning Objectives: {len(los)}")
        print(f"  Knowledge Components: {len(kcs)}")
    
    if "fccs" in state:
        lps = state.get("fccs", {}).get("learning_processes", [])
        ims = state.get("fccs", {}).get("instruction_methods", [])
        print(f"  Learning Processes: {len(lps)}")
        print(f"  Instruction Methods: {len(ims)}")
    
    if "knowledge_graph" in state:
        kg = state.get("knowledge_graph", {})
        nodes = kg.get("nodes", [])
        relationships = kg.get("relationships", [])
        print(f"  Knowledge Graph: {len(nodes)} nodes, {len(relationships)} relationships")

def wait_for_user():
    """Wait for user to press Enter to continue."""
    input("\n👉 Press Enter to continue to the next step...")

def get_user_input(prompt: str, default: str = "") -> str:
    """Get user input with a default value."""
    response = input(f"{prompt} [{default}]: ")
    return response if response else default

def run_course_manager(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the Course Manager microservice."""
    print_separator("COURSE MANAGER")
    print("This service initializes the course and collects faculty inputs.")
    
    # Create service
    service = create_course_manager_service()
    
    # Get user inputs
    print("\n📝 Please provide the following information:")
    course_id = get_user_input("Course ID", "MANUAL_COURSE")
    faculty_id = get_user_input("Faculty ID", "MANUAL_FACULTY")
    course_level = get_user_input("Course Level (undergraduate/graduate)", "undergraduate")
    target_audience = get_user_input("Target Audience", "Computer Science students")
    upload_type = get_user_input("Content Source (pdf/elasticsearch/llm_generated)", "elasticsearch")
    course_duration = get_user_input("Course Duration (weeks)", "12")
    target_los = get_user_input("Target Learning Objectives", "15")
    faculty_comments = get_user_input("Faculty Comments", "Manual microservice flow test")
    
    # Update state with user inputs
    state.update({
        "course_id": course_id,
        "faculty_id": faculty_id,
        "upload_type": upload_type,
        "es_index": "advanced_docs_elasticsearch_v2",
        "course_config": {
            "course_id": course_id,
            "faculty_id": faculty_id,
            "course_level": course_level,
            "target_audience": target_audience,
            "upload_type": upload_type,
            "course_duration": course_duration,
            "target_los": target_los,
            "faculty_comments": faculty_comments
        },
        "service_statuses": {},
        "service_results": {},
        "service_errors": {},
        "execution_history": [],
        "faculty_inputs_collected": True,
        "is_automatic_mode": False,
        "next_step": "content_preprocessing"
    })
    
    # Execute service
    print("\n🔄 Executing Course Manager service...")
    result = service(state)
    
    print("\n✅ Course Manager execution completed!")
    print_state_summary(result)
    
    return result

def run_content_preprocessor(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the Content Preprocessor microservice."""
    print_separator("CONTENT PREPROCESSOR")
    print("This service processes content from the specified source.")
    
    # Create service
    service = create_content_preprocessor_service()
    
    # Get user input for content source details
    print("\n📝 Content Source Configuration:")
    upload_type = state.get("upload_type", "elasticsearch")
    
    if upload_type == "pdf":
        file_path = get_user_input("PDF File Path", "data/sample.pdf")
        state["file_path"] = file_path
    elif upload_type == "elasticsearch":
        es_index = get_user_input("Elasticsearch Index", "advanced_docs_elasticsearch_v2")
        state["es_index"] = es_index
    elif upload_type == "llm_generated":
        raw_content = get_user_input("Raw Content (first few sentences)", "This is a sample course about operating systems.")
        state["raw_content"] = raw_content
    
    # Execute service
    print("\n🔄 Executing Content Preprocessor service...")
    result = service(state)
    
    print("\n✅ Content Preprocessor execution completed!")
    print_state_summary(result)
    
    return result

def run_course_mapper(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the Course Mapper microservice."""
    print_separator("COURSE MAPPER")
    print("This service executes Stage 1 pipeline to generate Learning Objectives and Knowledge Components.")
    
    # Create service
    service = create_course_mapper_service()
    
    # Execute service
    print("\n🔄 Executing Course Mapper service (Stage 1 pipeline)...")
    print("This may take a few minutes as it runs multiple LLM agents...")
    result = service(state)
    
    print("\n✅ Course Mapper execution completed!")
    print_state_summary(result)
    
    # Ask if user wants to see the generated learning objectives
    if "facd" in result and input("\nWould you like to see the generated Learning Objectives? (y/n): ").lower() == 'y':
        los = result.get("facd", {}).get("learning_objectives", [])
        print("\n📚 Generated Learning Objectives:")
        for i, lo in enumerate(los[:5], 1):
            print(f"  {i}. {lo.get('text', 'No text')}")
        if len(los) > 5:
            print(f"  ... and {len(los) - 5} more")
    
    return result

def run_kli_application(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the KLI Application microservice."""
    print_separator("KLI APPLICATION")
    print("This service executes Stage 2 pipeline to tag Learning Processes and Instruction Methods.")
    
    # Create service
    service = create_kli_application_service()
    
    # Check if FACD is approved
    facd_approved = state.get("facd_approved", False)
    if not facd_approved:
        approve = input("\n⚠️ FACD is not yet approved. Would you like to approve it now? (y/n): ")
        if approve.lower() == 'y':
            state["facd_approved"] = True
            print("✅ FACD approved!")
        else:
            print("⚠️ Proceeding with unapproved FACD (draft mode)")
    
    # Execute service
    print("\n🔄 Executing KLI Application service (Stage 2 pipeline)...")
    print("This may take a few minutes as it runs multiple LLM agents...")
    result = service(state)
    
    print("\n✅ KLI Application execution completed!")
    print_state_summary(result)
    
    # Ask if user wants to see the learning processes and instruction methods
    if "fccs" in result and input("\nWould you like to see the generated Learning Processes and Instruction Methods? (y/n): ").lower() == 'y':
        lps = result.get("fccs", {}).get("learning_processes", [])
        ims = result.get("fccs", {}).get("instruction_methods", [])
        
        print("\n🧠 Generated Learning Processes:")
        for i, lp in enumerate(lps[:3], 1):
            print(f"  {i}. {lp.get('name', 'No name')}: {lp.get('description', 'No description')}")
        if len(lps) > 3:
            print(f"  ... and {len(lps) - 3} more")
            
        print("\n📚 Generated Instruction Methods:")
        for i, im in enumerate(ims[:3], 1):
            print(f"  {i}. {im.get('name', 'No name')}: {im.get('description', 'No description')}")
        if len(ims) > 3:
            print(f"  ... and {len(ims) - 3} more")
    
    return result

def run_knowledge_graph_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the Knowledge Graph Generator microservice."""
    print_separator("KNOWLEDGE GRAPH GENERATOR")
    print("This service generates and stores the complete knowledge graph.")
    
    # Create service
    service = create_knowledge_graph_generator_service()
    
    # Check if FCCS is approved
    fccs_approved = state.get("fccs_approved", False)
    if not fccs_approved:
        approve = input("\n⚠️ FCCS is not yet approved. Would you like to approve it now? (y/n): ")
        if approve.lower() == 'y':
            state["fccs_approved"] = True
            print("✅ FCCS approved!")
        else:
            print("⚠️ Proceeding with unapproved FCCS (draft mode)")
    
    # Execute service
    print("\n🔄 Executing Knowledge Graph Generator service...")
    result = service(state)
    
    print("\n✅ Knowledge Graph Generator execution completed!")
    print_state_summary(result)
    
    # Ask if user wants to see the knowledge graph structure
    if "knowledge_graph" in result and input("\nWould you like to see the Knowledge Graph structure? (y/n): ").lower() == 'y':
        kg = result.get("knowledge_graph", {})
        nodes = kg.get("nodes", [])
        relationships = kg.get("relationships", [])
        
        print("\n📊 Knowledge Graph Structure:")
        print(f"  Total Nodes: {len(nodes)}")
        print(f"  Total Relationships: {len(relationships)}")
        
        # Show node types and counts
        node_types = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            if node_type in node_types:
                node_types[node_type] += 1
            else:
                node_types[node_type] = 1
        
        print("\n  Node Types:")
        for node_type, count in node_types.items():
            print(f"    - {node_type}: {count} nodes")
        
        # Show relationship types and counts
        rel_types = {}
        for rel in relationships:
            rel_type = rel.get("type", "unknown")
            if rel_type in rel_types:
                rel_types[rel_type] += 1
            else:
                rel_types[rel_type] = 1
        
        print("\n  Relationship Types:")
        for rel_type, count in rel_types.items():
            print(f"    - {rel_type}: {count} relationships")
    
    return result

def check_services():
    """Check if all required services are available."""
    print("\n🔍 Checking if all required services are available...")
    
    services_to_check = [
        ("Course Manager", "subsystems.content.services.course_manager", "create_course_manager_service"),
        ("Content Preprocessor", "subsystems.content.services.content_preprocessor", "create_content_preprocessor_service"),
        ("Course Mapper", "subsystems.content.services.course_mapper", "create_course_mapper_service"),
        ("KLI Application", "subsystems.content.services.kli_application", "create_kli_application_service"),
        ("Knowledge Graph Generator", "subsystems.content.services.knowledge_graph_generator", "create_knowledge_graph_generator_service")
    ]
    
    all_available = True
    
    for service_name, module_path, function_name in services_to_check:
        try:
            module = __import__(module_path, fromlist=[function_name])
            function = getattr(module, function_name)
            service = function()
            print(f"✅ {service_name} service is available")
        except ImportError:
            print(f"❌ {service_name} service is not available - module {module_path} could not be imported")
            all_available = False
        except AttributeError:
            print(f"❌ {service_name} service is not available - function {function_name} not found in module")
            all_available = False
        except Exception as e:
            print(f"❌ {service_name} service is not available - error: {e}")
            all_available = False
    
    return all_available

def main():
    """Run the manual microservice flow."""
    print_separator("MANUAL MICROSERVICE FLOW")
    print("This script will run each microservice in the content pipeline manually.")
    print("You will be asked for input at each step.")
    
    # Check if services are available
    if not check_services():
        print("\n⚠️ Some services are not available. The script may not work correctly.")
        proceed = input("Do you want to proceed anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Exiting.")
            return
    
    # Initialize registry and services
    try:
        print("Initializing service registry...")
        reset_service_registry()
        register_all_services()
        print("Service registry initialized successfully.")
    except Exception as e:
        print(f"❌ Error initializing service registry: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Initialize state
    state = {}
    
    # Run each service in sequence
    try:
        # 1. Course Manager
        print("\nPreparing to run Course Manager...")
        state = run_course_manager(state)
        wait_for_user()
        
        # 2. Content Preprocessor
        print("\nPreparing to run Content Preprocessor...")
        state = run_content_preprocessor(state)
        wait_for_user()
        
        # 3. Course Mapper
        print("\nPreparing to run Course Mapper...")
        state = run_course_mapper(state)
        wait_for_user()
        
        # 4. KLI Application
        print("\nPreparing to run KLI Application...")
        state = run_kli_application(state)
        wait_for_user()
        
        # 5. Knowledge Graph Generator
        print("\nPreparing to run Knowledge Graph Generator...")
        state = run_knowledge_graph_generator(state)
        
        print_separator("PIPELINE COMPLETED")
        print("✅ All microservices have been executed successfully!")
        print_state_summary(state)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user. Exiting gracefully...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Pipeline execution failed.")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manual Microservice Flow Runner")
    parser.add_argument("--service", choices=["all", "course_manager", "content_preprocessor", "course_mapper", "kli_application", "knowledge_graph_generator"],
                       default="all", help="Run only a specific service")
    
    args = parser.parse_args()
    
    if args.service == "all":
        main()
    else:
        print_separator(f"RUNNING SINGLE SERVICE: {args.service.upper()}")
        
        # Initialize registry and services
        try:
            print("Initializing service registry...")
            reset_service_registry()
            register_all_services()
            print("Service registry initialized successfully.")
        except Exception as e:
            print(f"❌ Error initializing service registry: {e}")
            import traceback
            traceback.print_exc()
            exit(1)
        
        # Initialize state with minimal required fields
        state = {
            "course_id": "TEST_COURSE",
            "faculty_id": "TEST_FACULTY",
            "upload_type": "elasticsearch",
            "es_index": "advanced_docs_elasticsearch_v2",
            "service_statuses": {},
            "service_results": {},
            "service_errors": {},
            "execution_history": []
        }
        
        try:
            if args.service == "course_manager":
                state = run_course_manager(state)
            elif args.service == "content_preprocessor":
                state = run_content_preprocessor(state)
            elif args.service == "course_mapper":
                state = run_course_mapper(state)
            elif args.service == "kli_application":
                state = run_kli_application(state)
            elif args.service == "knowledge_graph_generator":
                state = run_knowledge_graph_generator(state)
                
            print_separator("SERVICE EXECUTION COMPLETED")
            print_state_summary(state)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Service execution failed.")
            import traceback
            traceback.print_exc() 