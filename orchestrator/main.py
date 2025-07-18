"""
Universal LangGraph Orchestrator CLI

Main CLI interface for the universal orchestrator supporting all subsystems.
Provides commands for content, learner, and cross-subsystem workflows.
"""

import argparse
import sys
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator.universal_orchestrator import UniversalOrchestrator, run_cross_subsystem_workflow
from orchestrator.service_registry import get_service_registry, reset_service_registry
from orchestrator.state import UniversalState, SubsystemType, ServiceDefinition, SubsystemDefinition
from config.loader import get_default_course_id, get_default_learner_id, get_elasticsearch_config

def register_all_services():
    """Register all available services across subsystems."""
    registry = get_service_registry()
    
    print("🔧 Registering services across all subsystems...")
    
    # ===== CONTENT SUBSYSTEM =====
    print("📚 Registering Content Subsystem services...")
    
    try:
        from subsystems.content.services.content_preprocessor import create_content_preprocessor_service
        content_preprocessor = create_content_preprocessor_service()
        registry.register_service(content_preprocessor.get_service_definition(), SubsystemType.CONTENT)
    except ImportError as e:
        print(f"⚠️ Could not register content_preprocessor: {e}")
    
    try:
        from subsystems.content.services.course_mapper import create_course_mapper_service
        course_mapper = create_course_mapper_service()
        registry.register_service(course_mapper.get_service_definition(), SubsystemType.CONTENT)
    except ImportError as e:
        print(f"⚠️ Could not register course_mapper: {e}")
    
    try:
        from subsystems.content.services.kli_application import create_kli_application_service
        kli_application = create_kli_application_service()
        registry.register_service(kli_application.get_service_definition(), SubsystemType.CONTENT)
    except ImportError as e:
        print(f"⚠️ Could not register kli_application: {e}")
    
    try:
        from subsystems.content.services.knowledge_graph_generator import create_knowledge_graph_generator_service
        kg_generator = create_knowledge_graph_generator_service()
        registry.register_service(kg_generator.get_service_definition(), SubsystemType.CONTENT)
    except ImportError as e:
        print(f"⚠️ Could not register knowledge_graph_generator: {e}")
    
    # Register content subsystem definition
    content_services = [s for s in registry.services.values() if s.subsystem == SubsystemType.CONTENT]
    if content_services:
        content_subsystem = SubsystemDefinition(
            subsystem_type=SubsystemType.CONTENT,
            name="Content Subsystem",
            description="Handles course content processing and knowledge graph generation",
            services=content_services,
            entry_points=["content_preprocessor"]
        )
        registry.register_subsystem(content_subsystem)
    
    # ===== LEARNER SUBSYSTEM =====
    print("👤 Registering Learner Subsystem services...")
    
    try:
        from subsystems.learner.services.learning_tree_handler import create_learning_tree_handler_service
        learning_tree_handler = create_learning_tree_handler_service()
        registry.register_service(learning_tree_handler.get_service_definition(), SubsystemType.LEARNER)
    except ImportError as e:
        print(f"⚠️ Could not register learning_tree_handler: {e}")
    
    try:
        from subsystems.learner.services.graph_query_engine import create_graph_query_engine_service
        graph_query_engine = create_graph_query_engine_service()
        registry.register_service(graph_query_engine.get_service_definition(), SubsystemType.LEARNER)
    except ImportError as e:
        print(f"⚠️ Could not register graph_query_engine: {e}")
    
    # Register learner subsystem definition
    learner_services = [s for s in registry.services.values() if s.subsystem == SubsystemType.LEARNER]
    if learner_services:
        learner_subsystem = SubsystemDefinition(
            subsystem_type=SubsystemType.LEARNER,
            name="Learner Subsystem", 
            description="Handles learner personalization and learning path generation",
            services=learner_services,
            entry_points=["learning_tree_handler"]
        )
        registry.register_subsystem(learner_subsystem)
    
    # ===== SME SUBSYSTEM =====
    print("👨‍🏫 Registering SME Subsystem services...")
    # SME services would be registered here when implemented
    
    # ===== ANALYTICS SUBSYSTEM =====
    print("📊 Registering Analytics Subsystem services...")
    # Analytics services would be registered here when implemented
    
    print(f"✅ Service registration completed: {len(registry.services)} services registered")
    
    return registry

def run_content_workflow(args):
    """Run content subsystem workflow."""
    print("🚀 Running Content Subsystem Workflow...")
    
    # Build initial state
    workflow_args = {
        "course_id": args.course_id,
        "upload_type": args.upload_type
    }
    
    if args.upload_type == "pdf" and args.file_path:
        workflow_args["file_path"] = args.file_path
    elif args.upload_type == "elasticsearch" and args.es_index:
        workflow_args["es_index"] = args.es_index
    elif args.upload_type == "llm_generated" and args.raw_content:
        workflow_args["raw_content"] = args.raw_content
    
    # Run workflow
    result = run_cross_subsystem_workflow(SubsystemType.CONTENT, **workflow_args)
    
    # Display results
    print("\n📊 Content Workflow Results:")
    print(f"   Session ID: {result.get('session_id')}")
    print(f"   Chunks processed: {len(result.get('chunks', []))}")
    print(f"   Services completed: {len([s for s in result.get('service_statuses', {}).values() if s == 'completed'])}")
    
    return result

def run_learner_workflow(args):
    """Run learner subsystem workflow."""
    print("🚀 Running Learner Subsystem Workflow...")
    
    # Build initial state
    workflow_args = {
        "learner_id": args.learner_id,
        "course_id": args.course_id
    }
    
    if args.learner_profile:
        workflow_args["learner_profile"] = json.loads(args.learner_profile)
    
    # Run workflow
    result = run_cross_subsystem_workflow(SubsystemType.LEARNER, **workflow_args)
    
    # Display results
    print("\n📊 Learner Workflow Results:")
    print(f"   Session ID: {result.get('session_id')}")
    print(f"   Learner ID: {result.get('learner_id')}")
    print(f"   PLT generated: {'Yes' if result.get('personalized_learning_tree') else 'No'}")
    print(f"   Recommendations: {len(result.get('adaptive_recommendations', []))}")
    
    return result

def run_cross_subsystem_workflow_cmd(args):
    """Run cross-subsystem workflow."""
    print("🌍 Running Cross-Subsystem Workflow...")
    
    # Register all services first
    register_all_services()
    
    # Create orchestrator
    orchestrator = UniversalOrchestrator()
    
    # Build initial state for cross-subsystem execution
    initial_state: UniversalState = {
        "course_id": args.course_id,
        "subsystem": SubsystemType.CONTENT,  # Start with content
        "upload_type": args.upload_type,
        "execution_context": {
            "multi_subsystem": True,
            "target_subsystems": ["content", "learner"]
        }
    }
    
    # Add subsystem-specific inputs
    if args.upload_type == "pdf" and args.file_path:
        initial_state["file_path"] = args.file_path
    elif args.upload_type == "elasticsearch" and args.es_index:
        initial_state["es_index"] = args.es_index
    
    # Add learner context if provided
    if args.learner_id:
        initial_state["learner_id"] = args.learner_id
        initial_state["cross_system_payload"] = {
            "service_id": "learning_tree_handler",
            "trigger_after": "content_preprocessor"
        }
        initial_state["source_subsystem"] = SubsystemType.CONTENT
        initial_state["target_subsystem"] = SubsystemType.LEARNER
    
    # Run orchestrator
    result = orchestrator.run(initial_state)
    
    # Display comprehensive results
    print("\n🎉 Cross-Subsystem Workflow Results:")
    print(f"   Session ID: {result.get('session_id')}")
    print(f"   Execution Steps: {len(result.get('execution_history', []))}")
    
    # Service results
    service_statuses = result.get('service_statuses', {})
    completed_services = [sid for sid, status in service_statuses.items() if status == 'completed']
    failed_services = [sid for sid, status in service_statuses.items() if status == 'error']
    
    print(f"   ✅ Completed Services: {completed_services}")
    if failed_services:
        print(f"   ❌ Failed Services: {failed_services}")
    
    return result

def list_services_cmd(args):
    """List all registered services."""
    register_all_services()
    registry = get_service_registry()
    
    services_info = registry.list_services(
        subsystem=SubsystemType(args.subsystem) if args.subsystem else None
    )
    
    print(f"\n📋 Registered Services ({len(services_info)} total):")
    print("=" * 80)
    
    for service_id, info in services_info.items():
        print(f"🔧 {service_id}")
        print(f"   Name: {info['name']}")
        print(f"   Subsystem: {info['subsystem']}")
        print(f"   Description: {info['description']}")
        print(f"   Dependencies: {info['dependencies']}")
        print(f"   Inputs: {info['required_inputs']}")
        print(f"   Outputs: {info['provided_outputs']}")
        print()

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Universal LangGraph Orchestrator")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Get default values from configuration
    default_course_id = get_default_course_id()
    default_learner_id = get_default_learner_id()
    default_es_index = get_elasticsearch_config().get('index', 'advanced_docs_elasticsearch_v2')
    
    # Content workflow command
    content_parser = subparsers.add_parser("content", help="Run content subsystem workflow")
    content_parser.add_argument("--course_id", default=default_course_id, help="Course identifier")
    content_parser.add_argument("--upload_type", choices=["pdf", "elasticsearch", "llm_generated"], 
                               default="elasticsearch", help="Content upload type")
    content_parser.add_argument("--file_path", help="PDF file path (for pdf upload type)")
    content_parser.add_argument("--es_index", default=default_es_index, 
                               help="Elasticsearch index (for elasticsearch upload type)")
    content_parser.add_argument("--raw_content", help="Raw text content (for llm_generated upload type)")
    
    # Learner workflow command
    learner_parser = subparsers.add_parser("learner", help="Run learner subsystem workflow")
    learner_parser.add_argument("--learner_id", default=default_learner_id, help="Learner identifier")
    learner_parser.add_argument("--course_id", default=default_course_id, help="Course identifier")
    learner_parser.add_argument("--learner_profile", help="JSON string of learner profile")
    
    # Cross-subsystem workflow command
    cross_parser = subparsers.add_parser("cross", help="Run cross-subsystem workflow")
    cross_parser.add_argument("--course_id", default=default_course_id, help="Course identifier")
    cross_parser.add_argument("--upload_type", choices=["pdf", "elasticsearch", "llm_generated"],
                             default="elasticsearch", help="Content upload type")
    cross_parser.add_argument("--file_path", help="PDF file path (for pdf upload type)")
    cross_parser.add_argument("--es_index", default=default_es_index,
                             help="Elasticsearch index (for elasticsearch upload type)")
    cross_parser.add_argument("--learner_id", help="Learner ID for cross-subsystem PLT generation")
    
    # List services command
    list_parser = subparsers.add_parser("list", help="List registered services")
    list_parser.add_argument("--subsystem", choices=["content", "learner", "sme", "analytics"],
                            help="Filter by subsystem")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "content":
            register_all_services()
            run_content_workflow(args)
        elif args.command == "learner":
            register_all_services()
            run_learner_workflow(args)
        elif args.command == "cross":
            run_cross_subsystem_workflow_cmd(args)
        elif args.command == "list":
            list_services_cmd(args)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Command failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 