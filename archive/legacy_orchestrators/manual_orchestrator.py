#!/usr/bin/env python3
"""
Manual Orchestrator CLI

Provides "Click to Action" interface for microservices.
Each service can be executed independently with manual control.

Usage:
    python manual_orchestrator.py
"""

import sys
import os
from typing import Dict, Any
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.orchestration_controller import orchestration_controller, ServiceStatus

def print_banner():
    """Print the application banner."""
    print("=" * 80)
    print("🚀 LangGraph Knowledge Graph - Manual Orchestrator")
    print("📋 Click-to-Action Microservice Controller")
    print("=" * 80)

def print_service_status():
    """Print current status of all services."""
    print("\n📊 Service Status Overview:")
    print("-" * 60)
    
    statuses = orchestration_controller.get_all_statuses()
    status_colors = {
        "not_started": "⚪",
        "ready": "🟢", 
        "running": "🟡",
        "completed": "✅",
        "error": "❌",
        "skipped": "⏸️"
    }
    
    for i, (service, status) in enumerate(statuses.items(), 1):
        color = status_colors.get(status, "⚪")
        service_name = service.replace("_", " ").title()
        print(f"{i:2d}. {color} {service_name:25} [{status.upper()}]")

def print_menu():
    """Print the main menu options."""
    print("\n🎯 Available Actions:")
    print("-" * 40)
    print("1-8. Execute Service 1-8")
    print("9.   Skip Service")
    print("10.  Reset Service")
    print("11.  Show Service Details")
    print("12.  Show Execution Summary")
    print("13.  Initialize Course")
    print("0.   Exit")

def get_service_details(service_name: str):
    """Get detailed information about a service."""
    readiness = orchestration_controller.is_service_ready(service_name)
    status = orchestration_controller.get_service_status(service_name)
    
    print(f"\n🔍 Service Details: {service_name.replace('_', ' ').title()}")
    print("-" * 50)
    print(f"Current Status: {status.value.upper()}")
    print(f"Ready to Execute: {'✅ YES' if readiness['ready'] else '❌ NO'}")
    
    if not readiness['ready']:
        if readiness['missing_dependencies']:
            print(f"Missing Dependencies: {', '.join(readiness['missing_dependencies'])}")
        if readiness['missing_state']:
            print(f"Missing State: {', '.join(readiness['missing_state'])}")
    
    # Show service description
    descriptions = {
        "course_manager": "Handles faculty upload/ES fetch/LLM fallback triggers",
        "content_preprocessor": "File upload, chunking, metadata extraction",
        "course_content_mapper": "Stage 1 agents (LO + KC extraction) → FACD",
        "kli_application": "Stage 2 agents (Learning Process + Instruction) → FCCS",
        "knowledge_graph_generator": "Neo4j + MongoDB + PostgreSQL outputs → FFCS",
        "query_strategy_manager": "Learner decision routing based on context",
        "graph_query_engine": "Cypher query generation and execution",
        "learning_tree_handler": "PLT generation and storage with Redis + PostgreSQL"
    }
    
    print(f"Description: {descriptions.get(service_name, 'No description available')}")

def execute_service_interactive(service_index: int):
    """Execute a service interactively."""
    services = orchestration_controller.available_services
    if service_index < 1 or service_index > len(services):
        print("❌ Invalid service number!")
        return
    
    service_name = services[service_index - 1]
    
    print(f"\n🚀 Executing: {service_name.replace('_', ' ').title()}")
    print("-" * 50)
    
    # Check readiness first
    readiness = orchestration_controller.is_service_ready(service_name)
    if not readiness['ready']:
        print("❌ Service is not ready to execute!")
        get_service_details(service_name)
        return
    
    # Get service-specific parameters
    kwargs = {}
    
    if service_name == "course_manager":
        print("📝 Course Manager Configuration:")
        course_id = input("Enter Course ID (default: OSN): ").strip() or "OSN"
        upload_type = input("Upload Type (pdf/elasticsearch/llm_generated, default: llm_generated): ").strip() or "llm_generated"
        
        kwargs = {
            "course_id": course_id,
            "upload_type": upload_type
        }
        
        if upload_type == "pdf":
            file_path = input("Enter PDF file path: ").strip()
            kwargs["file_path"] = file_path
        elif upload_type == "elasticsearch":
            es_index = input("Enter ES index (default: advanced_docs_elasticsearch_v2): ").strip() or "advanced_docs_elasticsearch_v2"
            kwargs["es_index"] = es_index
        elif upload_type == "llm_generated":
            topic = input("Enter topic (default: Operating Systems): ").strip() or "Operating Systems"
            kwargs["topic"] = topic
    
    elif service_name == "query_strategy_manager":
        print("📝 Query Strategy Configuration:")
        decision_label = input("Learner decision label (default: Standard Learner): ").strip() or "Standard Learner"
        kwargs = {
            "learner_context": {"decision_label": decision_label}
        }
    
    elif service_name == "learning_tree_handler":
        print("📝 Learning Tree Handler Configuration:")
        learner_id = input("Enter Learner ID (default: R000): ").strip() or "R000"
        kwargs = {
            "learner_id": learner_id
        }
    
    # Execute the service
    print(f"\n⏳ Executing {service_name}...")
    result = orchestration_controller.execute_service(service_name, **kwargs)
    
    # Display results
    if result.get("success"):
        print(f"✅ {service_name.replace('_', ' ').title()} completed successfully!")
        
        # Show specific results
        if "execution_time_ms" in result:
            print(f"⏱️  Execution time: {result['execution_time_ms']:.2f}ms")
        
        if service_name == "course_content_mapper" and "facd" in result:
            print(f"📋 FACD created with {len(result['facd']['learning_objectives'])} Learning Objectives")
        elif service_name == "kli_application" and "fccs" in result:
            print(f"📋 FCCS created with {len(result['fccs']['finalized_los'])} Finalized LOs")
        elif service_name == "knowledge_graph_generator" and "nodes_created" in result:
            print(f"🧩 Knowledge Graph created with {result['nodes_created']} LO nodes")
        elif service_name == "learning_tree_handler" and "learning_steps" in result:
            print(f"🌳 PLT generated with {result['learning_steps']} learning steps")
        
    else:
        print(f"❌ {service_name.replace('_', ' ').title()} failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        
        if "readiness" in result:
            print("\nReadiness Issues:")
            readiness = result["readiness"]
            if readiness.get("missing_dependencies"):
                print(f"  Missing Dependencies: {', '.join(readiness['missing_dependencies'])}")
            if readiness.get("missing_state"):
                print(f"  Missing State: {', '.join(readiness['missing_state'])}")

def skip_service_interactive():
    """Skip a service interactively."""
    print("\n⏸️  Skip Service")
    print("-" * 30)
    
    services = orchestration_controller.available_services
    for i, service in enumerate(services, 1):
        status = orchestration_controller.get_service_status(service)
        if status == ServiceStatus.NOT_STARTED:
            print(f"{i}. {service.replace('_', ' ').title()}")
    
    try:
        choice = int(input("\nSelect service to skip (number): "))
        if 1 <= choice <= len(services):
            service_name = services[choice - 1]
            reason = input("Reason for skipping (optional): ").strip() or "Manually skipped"
            
            result = orchestration_controller.skip_service(service_name, reason)
            if result["success"]:
                print(f"⏸️  {service_name.replace('_', ' ').title()} skipped: {reason}")
            else:
                print("❌ Failed to skip service")
        else:
            print("❌ Invalid service number!")
    except ValueError:
        print("❌ Invalid input!")

def reset_service_interactive():
    """Reset a service interactively."""
    print("\n🔄 Reset Service")
    print("-" * 30)
    
    services = orchestration_controller.available_services
    for i, service in enumerate(services, 1):
        status = orchestration_controller.get_service_status(service)
        if status != ServiceStatus.NOT_STARTED:
            print(f"{i}. {service.replace('_', ' ').title()} [{status.value.upper()}]")
    
    try:
        choice = int(input("\nSelect service to reset (number): "))
        if 1 <= choice <= len(services):
            service_name = services[choice - 1]
            
            confirm = input(f"Reset {service_name.replace('_', ' ').title()}? (y/N): ").strip().lower()
            if confirm == 'y':
                result = orchestration_controller.reset_service(service_name)
                if result["success"]:
                    print(f"🔄 {service_name.replace('_', ' ').title()} reset to NOT_STARTED")
                else:
                    print("❌ Failed to reset service")
            else:
                print("Reset cancelled")
        else:
            print("❌ Invalid service number!")
    except ValueError:
        print("❌ Invalid input!")

def show_execution_summary():
    """Show execution summary."""
    summary = orchestration_controller.get_execution_summary()
    
    print("\n📊 Execution Summary")
    print("-" * 50)
    print(f"Total Services: {summary['total_services']}")
    print(f"Completed: {summary['completed']}")
    print(f"Errors: {summary['errors']}")
    print(f"Ready: {summary['ready']}")
    
    if summary['completed_services']:
        print(f"\n✅ Completed Services:")
        for service in summary['completed_services']:
            print(f"  • {service.replace('_', ' ').title()}")
    
    if summary['error_services']:
        print(f"\n❌ Error Services:")
        for service in summary['error_services']:
            print(f"  • {service.replace('_', ' ').title()}")
    
    if summary['ready_services']:
        print(f"\n🟢 Ready Services:")
        for service in summary['ready_services']:
            print(f"  • {service.replace('_', ' ').title()}")
    
    print(f"\n📝 Current State Keys: {len(summary['current_state_keys'])}")
    if summary['current_state_keys']:
        print(f"  Keys: {', '.join(summary['current_state_keys'][:5])}{'...' if len(summary['current_state_keys']) > 5 else ''}")

def initialize_course():
    """Initialize a new course session."""
    print("\n🎯 Initialize New Course")
    print("-" * 40)
    
    course_id = input("Enter Course ID (default: OSN): ").strip() or "OSN"
    session_id = input("Enter Session ID (default: session_001): ").strip() or "session_001"
    
    # Reset controller state
    orchestration_controller.state = {
        "course_id": course_id,
        "session_id": session_id
    }
    orchestration_controller._initialize_service_statuses()
    orchestration_controller.execution_log = []
    
    print(f"✅ Course {course_id} initialized with session {session_id}")
    print("🔄 All services reset to NOT_STARTED status")

def main():
    """Main application loop."""
    print_banner()
    
    # Initialize with default course
    orchestration_controller.state = {
        "course_id": "OSN",
        "session_id": "default_session"
    }
    
    while True:
        print_service_status()
        print_menu()
        
        try:
            choice = input("\n➤ Select action (0-13): ").strip()
            
            if choice == "0":
                print("\n👋 Goodbye!")
                break
            elif choice in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                execute_service_interactive(int(choice))
            elif choice == "9":
                skip_service_interactive()
            elif choice == "10":
                reset_service_interactive()
            elif choice == "11":
                services = orchestration_controller.available_services
                print("\nSelect service for details:")
                for i, service in enumerate(services, 1):
                    print(f"{i}. {service.replace('_', ' ').title()}")
                
                try:
                    service_choice = int(input("Service number: "))
                    if 1 <= service_choice <= len(services):
                        get_service_details(services[service_choice - 1])
                    else:
                        print("❌ Invalid service number!")
                except ValueError:
                    print("❌ Invalid input!")
            elif choice == "12":
                show_execution_summary()
            elif choice == "13":
                initialize_course()
            else:
                print("❌ Invalid choice! Please select 0-13.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 