#!/usr/bin/env python3
"""
LangGraph Knowledge Graph System - Command Line Interface

This is the main CLI entry point for the LangGraph Knowledge Graph System.
It provides access to all the main workflows and pipelines.

Usage:
    python main.py COMMAND [OPTIONS]

Commands:
    stage1      Run Stage 1: Research & Knowledge Component Pipeline
    stage2      Run Stage 2: Learning Process & Instruction Pipeline
    plt         Run PLT: Personalized Learning Tree Pipeline
    es          Run ES: Elasticsearch to Knowledge Graph Pipeline
    unified     Run Unified: Complete End-to-End Pipeline
    kg          Generate and visualize a knowledge graph
"""

import sys
import os
import time
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# LangChain imports
from langchain_core.messages import HumanMessage

# LangGraph imports
from langgraph.graph import StateGraph, END

# Local imports
from graph.graph import build_graph_stage_1, build_graph_stage_2
from graph.plt_generator import run_plt_generator
from orchestrator.state import UniversalState, SubsystemType
from orchestrator.service_registry import get_service_registry, register_all_services
from utils.database_connections import get_database_manager
from graph.utils.es_to_kg import transform_es_to_kg, validate_es_connection, get_es_chunk_count

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from graph.graph import build_graph_stage_1, build_graph_stage_2
from graph.plt_generator import run_plt_generator
from utils.database_manager import insert_plt_to_neo4j, get_plt_for_learner
from graph.utils.es_to_kg import transform_es_to_kg, validate_es_connection, get_es_chunk_count
from utils.database_manager import insert_course_kg_to_neo4j, clear_neo4j_database
# Removed unused import: from graph.orchestrator import run_course_pipeline

# Import automatic pipeline coordinator (for testing/development)
from pipeline.automatic_coordinator import run_automatic_pipeline, process_course_content, generate_learner_plt
from config.loader import get_default_course_id, get_default_learner_id
from utils.logging import get_orchestrator_logger

# Import manual approval pipeline coordinator (for production)
from pipeline.manual_coordinator import (
    start_faculty_workflow, faculty_approve_course, process_content_after_course_approval,
    faculty_approve, faculty_confirm, faculty_finalize,
    manual_coordinator
)

# Import orchestrator components for service registration
from orchestrator.service_registry import get_service_registry, reset_service_registry
from orchestrator.state import UniversalState, SubsystemType, ServiceDefinition, SubsystemDefinition
from orchestrator.universal_orchestrator import UniversalOrchestrator, run_cross_subsystem_workflow

# Enhanced logger
logger = get_orchestrator_logger("main_cli")



def run_automatic_pipeline_cmd(args):
    """
    Run the complete automatic pipeline using microservices architecture.
    
    This uses the proper microservices instead of the old stage-based approach.
    """
    logger.info("Starting microservices automatic pipeline execution", 
                course_id=args.course_id,
                source=args.source,
                learner_id=getattr(args, 'learner_id', None))
    
    try:
        # Import the new microservices coordinator
        from pipeline.automatic_coordinator import microservices_coordinator
        
        # Prepare pipeline arguments
        pipeline_kwargs = {
            "content_source": args.source,
            "course_id": args.course_id,
            "generate_plt": getattr(args, 'generate_plt', True)
        }
        
        # Add source-specific arguments
        if args.source == "pdf" and hasattr(args, 'file_path') and args.file_path:
            pipeline_kwargs["file_path"] = args.file_path
        elif args.source == "elasticsearch":
            pipeline_kwargs["es_index"] = getattr(args, 'es_index', 'advanced_docs_elasticsearch_v2')
        elif args.source == "llm_generated":
            pipeline_kwargs["raw_content"] = getattr(args, 'raw_content', '')
        
        # Add learner information if specified
        if hasattr(args, 'learner_id') and args.learner_id:
            pipeline_kwargs["learner_id"] = args.learner_id
        
        # Execute microservices pipeline
        result = microservices_coordinator.run_complete_pipeline(**pipeline_kwargs)
        
        # Display final results
        if result["status"] == "completed":
            print("\n🎉 [SUCCESS] Microservices Pipeline Completed Successfully!")
            print(f"📊 Pipeline Type: {result['pipeline_type']}")
            print(f"📚 Course: {result['course_id']}")
            
            if result.get("learner_id"):
                print(f"👤 Learner: {result['learner_id']}")
            
            if result.get("content_pipeline"):
                content_pipeline = result["content_pipeline"]
                print(f"🗺️ Knowledge Graph: {'✅ Generated' if content_pipeline['status'] == 'completed' else '❌ Failed'}")
                if content_pipeline.get("services_executed"):
                    print(f"   Services: {', '.join(content_pipeline['services_executed'])}")
            
            if result.get("learner_pipeline"):
                learner_pipeline = result["learner_pipeline"]
                print(f"🌳 Learning Tree: {'✅ Generated' if learner_pipeline['status'] == 'completed' else '❌ Failed'}")
                if learner_pipeline.get("services_executed"):
                    print(f"   Services: {', '.join(learner_pipeline['services_executed'])}")
            
            print(f"🕒 Total Time: {result.get('total_execution_time_ms', 0)}ms")
            print("\n🚀 [COMPLETE] All microservices executed successfully!")
            
        elif result["status"] == "partial":
            print("\n⚠️ [PARTIAL] Pipeline completed with some failures")
            print(f"📚 Course: {result['course_id']}")
            print("Check the detailed output above for specific failures.")
            
        else:
            print(f"\n❌ [ERROR] Pipeline failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="automatic_pipeline_cmd")
        print(f"[ERROR] Microservices automatic pipeline failed: {e}")

def run_content_only_cmd(args):
    """Run content-only automatic pipeline."""
    logger.info("Starting content-only pipeline", course_id=args.course_id, source=args.source)
    
    try:
        print("[CONTENT] Running Content-Only Automatic Pipeline")
        print("=" * 50)
        
        result = process_course_content(
            course_id=args.course_id,
            content_source=args.source,
            file_path=getattr(args, 'file_path', None),
            es_index=getattr(args, 'es_index', 'advanced_docs_elasticsearch_v2'),
            raw_content=getattr(args, 'raw_content', '')
        )
        
        if result["status"] == "completed":
            print("[SUCCESS] Content pipeline completed successfully!")
            print(f"[COURSE] Course: {result['course_id']}")
            print(f"[CONTENT] Source: {result['source']}")
            stages = result.get("stages", [])
            print(f"[NEXT] Stages: {' -> '.join(stages)}")
        else:
            print(f"[ERROR] Content pipeline failed: {result.get('error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="content_only_cmd")
        print(f"[ERROR] Content pipeline failed: {e}")

def run_learner_only_cmd(args):
    """Run learner-only automatic pipeline."""
    logger.info("Starting learner-only pipeline", 
                course_id=args.course_id, 
                learner_id=args.learner_id)
    
    try:
        print("[LEARNER] Running Learner-Only Automatic Pipeline")
        print("=" * 50)
        
        result = generate_learner_plt(
            course_id=args.course_id,
            learner_id=args.learner_id
        )
        
        if result["status"] == "completed":
            print("[SUCCESS] Learner pipeline completed successfully!")
            print(f"[COURSE] Course: {result['course_id']}")
            print(f"[LEARNER] Learner: {result['learner_id']}")
            stages = result.get("stages", [])
            print(f"[NEXT] Stages: {' -> '.join(stages)}")
        else:
            print(f"[ERROR] Learner pipeline failed: {result.get('error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="learner_only_cmd")
        print(f"[ERROR] Learner pipeline failed: {e}")

def run_faculty_start_cmd(args):
    """Start a new faculty approval workflow."""
    logger.info("Starting faculty approval workflow",
                course_id=args.course_id,
                faculty_id=args.faculty_id)
    
    try:
        print("[WORKFLOW] Starting Faculty Approval Workflow")
        print("=" * 50)
        print(f"[COURSE] Course: {args.course_id}")
        print(f"[FACULTY] Faculty: {args.faculty_id}")
        print("=" * 50)
        
        result = start_faculty_workflow(
            course_id=args.course_id,
            faculty_id=args.faculty_id,
            content_source=args.source,
            file_path=getattr(args, 'file_path', None),
            es_index=getattr(args, 'es_index', 'advanced_docs_elasticsearch_v2'),
            raw_content=getattr(args, 'raw_content', '')
        )
        
        if result["status"] == "awaiting_faculty_approval":
            if result["stage"] == "course_initialization_approval":
                print("[SUCCESS] Course Manager completed course initialization!")
                print("\n" + result["ui_data"]["approval_stage"])
                print("[INFO] " + result["ui_data"]["instructions"])
                print(f"[TARGET] Next Action: {result['next_action_required']}")
                print(f"[ACTIONS] Available Actions: {', '.join(result['ui_data']['actions'])}")
                
                print("\n[INFO] Course Details:")
                course_details = result["ui_data"]["course_details"]
                print(f"   Course ID: {course_details['course_id']}")
                print(f"   Faculty ID: {course_details['faculty_id']}")
                print(f"   Content Source: {course_details['content_source']}")
                print(f"   Status: {course_details['initialization_status']}")
                
                print(f"\n[NEXT] Use: python main.py faculty-approve-course --course_id {args.course_id} --action approve")
                
            elif result["stage"] == "lo_approval":
                print("[SUCCESS] Content processed and Learning Objectives generated!")
                print(f"[CONTENT] Generated {len(result['draft_learning_objectives'])} Learning Objectives")
                print("\n" + result["ui_data"]["approval_stage"])
                print("[INFO] " + result["ui_data"]["instructions"])
                print(f"[TARGET] Next Action: {result['next_action_required']}")
                
                print("\n[COURSE] Draft Learning Objectives:")
                for i, lo in enumerate(result['draft_learning_objectives'][:3], 1):
                    print(f"   {i}. {lo.get('text', 'N/A')}")
                if len(result['draft_learning_objectives']) > 3:
                    print(f"   ... and {len(result['draft_learning_objectives']) - 3} more")
                    
                print(f"\n[NEXT] Use: python main.py faculty-approve --course_id {args.course_id} --action approve")
            
        else:
            print(f"[ERROR] Workflow failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="faculty_start_cmd")
        print(f"[ERROR] Faculty workflow start failed: {e}")

def run_faculty_approve_course_cmd(args):
    """Process faculty approval of course setup."""
    logger.info("Processing faculty course setup approval",
                course_id=args.course_id,
                action=args.action)
    
    try:
        print("[WORKFLOW] Faculty Course Setup Approval")
        print("=" * 50)
        
        result = faculty_approve_course(
            course_id=args.course_id,
            action=args.action,
            faculty_comments=getattr(args, 'comments', '')
        )
        
        if result["status"] == "course_approved":
            print("[SUCCESS] Course setup APPROVED!")
            print("[COURSE] Proceeding to Content Processing + LO Generation + Structure Generation...")
            print("[NEXT] This will take a few minutes...")
            
            # Automatically proceed to content processing and structure generation
            content_result = process_content_after_course_approval(args.course_id)
            
            if content_result["status"] == "awaiting_faculty_confirmation":
                print("[SUCCESS] Content processed and course structure generated!")
                print("[INFO] Complete course structure ready for faculty confirmation")
                print("\n" + content_result["ui_data"]["approval_stage"])
                print("[INFO] " + content_result["ui_data"]["instructions"])
                
                print("\n[COURSE] Draft Learning Objectives:")
                for i, lo in enumerate(content_result['draft_learning_objectives'][:3], 1):
                    print(f"   {i}. {lo.get('text', 'N/A')}")
                if len(content_result['draft_learning_objectives']) > 3:
                    print(f"   ... and {len(content_result['draft_learning_objectives']) - 3} more")
                    
                print(f"\n[NEXT] Use: python main.py faculty-approve --course_id {args.course_id} --action approve")
            
        elif result["status"] == "rejected":
            print("[ERROR] Course initialization rejected.")
            print(f"[CONTENT] Faculty Comments: {result.get('faculty_comments', 'None')}")
            
        else:
            print(f"[ERROR] Course approval failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="faculty_approve_course_cmd")
        print(f"[ERROR] Faculty course approval failed: {e}")

def run_faculty_approve_cmd(args):
    """Process faculty approval of learning objectives."""
    logger.info("Processing faculty learning objectives approval",
                course_id=args.course_id,
                action=args.action)
    
    try:
        print("[CONTENT] Faculty Learning Objectives Approval")
        print("=" * 50)
        
        result = faculty_approve(
            course_id=args.course_id,
            action=args.action,
            faculty_comments=getattr(args, 'comments', '')
        )
        
        if result["status"] == "awaiting_faculty_confirmation":
            print("[SUCCESS] Learning Objectives APPROVED!")
            print("[TARGET] Course structure generated - awaiting faculty confirmation")
            print("[INFO] " + result["ui_data"]["approval_stage"])
            print("[INFO] " + result["ui_data"]["instructions"])
            print(f"[NEXT] Use: python main.py faculty-confirm --course_id {args.course_id} --action confirm")
            
        elif result["status"] == "awaiting_faculty_approval":
            print("[EDIT] Learning objectives edited - awaiting re-approval")
            
        elif result["status"] == "rejected":
            print("[ERROR] Learning Objectives rejected")
            print(f"[COMMENT] Comments: {result.get('faculty_comments', 'None')}")
            
        else:
            print(f"[ERROR] Action failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="faculty_approve_cmd")
        print(f"[ERROR] Faculty approval failed: {e}")

def run_faculty_confirm_cmd(args):
    """Process faculty confirmation of course structure."""
    logger.info("Processing faculty course structure confirmation",
                course_id=args.course_id,
                action=args.action)
    
    try:
        print("[STRUCTURE] Faculty Course Structure Confirmation")
        print("=" * 50)
        
        result = faculty_confirm(
            course_id=args.course_id,
            action=args.action,
            faculty_comments=getattr(args, 'comments', '')
        )
        
        if result["status"] == "awaiting_faculty_finalization":
            print("[SUCCESS] Course Structure CONFIRMED!")
            print("[STATS] Knowledge Graph generated - awaiting faculty finalization")
            print("[INFO] " + result["ui_data"]["approval_stage"])
            print("[INFO] " + result["ui_data"]["instructions"])
            print(f"[NEXT] Use: python main.py faculty-finalize --course_id {args.course_id} --action finalize")
            
        elif result["status"] == "awaiting_faculty_confirmation":
            print("[EDIT] Course structure edited - awaiting re-confirmation")
            
        elif result["status"] == "rejected":
            print("[ERROR] Course structure rejected")
            print(f"[COMMENT] Comments: {result.get('faculty_comments', 'None')}")
            
        else:
            print(f"[ERROR] Action failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="faculty_confirm_cmd")
        print(f"[ERROR] Faculty confirmation failed: {e}")

def run_faculty_finalize_cmd(args):
    """Process faculty finalization of knowledge graph."""
    logger.info("Processing faculty knowledge graph finalization",
                course_id=args.course_id,
                action=args.action)
    
    try:
        print("[FINALIZE] Faculty Knowledge Graph Finalization")
        print("=" * 50)
        
        result = faculty_finalize(
            course_id=args.course_id,
            action=args.action,
            faculty_comments=getattr(args, 'comments', '')
        )
        
        if result["status"] == "course_structure_finalized":
            print("[SUCCESS] Knowledge Graph FINALIZED!")
            print("[COMPLETE] Faculty workflow completed successfully!")
            print("[INFO] " + result["ui_data"]["approval_stage"])
            print("[INFO] " + result["ui_data"]["instructions"])
            print(f"[TARGET] Course is now ready for personalized learning tree generation")
            print(f"[NEXT] Use: python main.py learner-plt --course_id {args.course_id} --learner_id <LEARNER_ID>")
            
        elif result["status"] == "awaiting_faculty_finalization":
            print("[EDIT] Knowledge graph edited - awaiting re-finalization")
            
        elif result["status"] == "rejected":
            print("[ERROR] Knowledge Graph rejected")
            print(f"[COMMENT] Comments: {result.get('faculty_comments', 'None')}")
            
        else:
            print(f"[ERROR] Action failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="faculty_finalize_cmd")
        print(f"[ERROR] Faculty finalization failed: {e}")

def run_learner_plt_cmd(args):
    """Generate PLT for a specific learner after faculty workflow completion."""
    logger.info("Generating PLT for learner",
                course_id=args.course_id,
                learner_id=args.learner_id)
    
    try:
        print("[PLT] Generating Personalized Learning Tree (PLT)")
        print("=" * 50)
        print(f"[COURSE] Course: {args.course_id}")
        print(f"[LEARNER] Learner: {args.learner_id}")
        print("=" * 50)
        
        # Prepare learner context if provided
        learner_context = {}
        if hasattr(args, 'learning_style') and args.learning_style:
            learner_context['learning_style'] = args.learning_style
        if hasattr(args, 'experience_level') and args.experience_level:
            learner_context['experience_level'] = args.experience_level
        if hasattr(args, 'preferences') and args.preferences:
            learner_context['preferences'] = args.preferences
        
        result = manual_coordinator.generate_plt_for_learner(
            course_id=args.course_id,
            learner_id=args.learner_id,
            learner_context=learner_context if learner_context else None
        )
        
        if result["status"] == "plt_generated":
            print("[SUCCESS] PLT Generated Successfully!")
            print(f"[COURSE] Course: {result['course_id']}")
            print(f"[LEARNER] Learner: {result['learner_id']}")
            print(f"[TARGET] Based on Faculty Finalized Structure: {'[SUCCESS]' if result['based_on_ffcs'] else '[ERROR]'}")
            if result.get('learner_context'):
                print(f"[SERVICE] Learner Context Applied: {list(result['learner_context'].keys())}")
            print("\n[COMPLETE] Personalized Learning Tree ready for learner!")
            
        else:
            print(f"[ERROR] PLT generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="learner_plt_cmd")
        print(f"[ERROR] PLT generation failed: {e}")

def run_faculty_status_cmd(args):
    """Check faculty approval workflow status."""
    try:
        print("[STATS] Faculty Workflow Status")
        print("=" * 50)
        
        status = manual_coordinator.get_workflow_status(args.course_id)
        
        if status["status"] == "not_found":
            print(f"[ERROR] No workflow found for course {args.course_id}")
            print("[NEXT] Use: python main.py faculty-start to begin a new workflow")
            return
        elif status["status"] == "error":
            print(f"[ERROR] Error retrieving workflow status: {status.get('error', 'Unknown error')}")
            return
        
        print(f"[COURSE] Course: {status['course_id']}")
        print(f"[FACULTY] Faculty: {status['faculty_id']}")
        print(f"[NEXT] Current Stage: {status['current_stage']}")
        print(f"[TIME] Last Updated: {status.get('last_updated', 'Unknown')}")
        print(f"[INFO] FACD Generated: {'[SUCCESS]' if status.get('has_facd') else '[ERROR]'}")
        print(f"[STRUCTURE] FCCS Generated: {'[SUCCESS]' if status.get('has_fccs') else '[ERROR]'}")
        print(f"[INFO] FFCS Generated: {'[SUCCESS]' if status.get('has_ffcs') else '[ERROR]'}")
        print(f"[PIPELINE] Ready for PLT: {'[SUCCESS]' if status.get('ready_for_plt') else '[ERROR]'}")
        
    except Exception as e:
        logger.log_error_with_context(e, operation="faculty_status_cmd")
        print(f"[ERROR] Status check failed: {e}")

def run_cross_subsystem_workflow_cmd(args):
    """Run cross-subsystem workflow."""
    print("[CROSS-SYSTEM] Running Cross-Subsystem Workflow...")
    
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
            "trigger_after": "course_manager"
        }
        initial_state["source_subsystem"] = SubsystemType.CONTENT
        initial_state["target_subsystem"] = SubsystemType.LEARNER
    
    # Run orchestrator
    result = orchestrator.run(initial_state)
    
    # Display comprehensive results
    print("\n[COMPLETE] Cross-Subsystem Workflow Results:")
    print(f"   Session ID: {result.get('session_id')}")
    print(f"   Execution Steps: {len(result.get('execution_history', []))}")
    
    # Service results
    service_statuses = result.get('service_statuses', {})
    completed_services = [sid for sid, status in service_statuses.items() if status == 'completed']
    failed_services = [sid for sid, status in service_statuses.items() if status == 'error']
    
    print(f"   [SUCCESS] Completed Services: {completed_services}")
    if failed_services:
        print(f"   [ERROR] Failed Services: {failed_services}")
    
    return result

def list_services_cmd(args):
    """List all registered services."""
    register_all_services()
    registry = get_service_registry()
    
    services_info = registry.list_services(
        subsystem=SubsystemType(args.subsystem) if args.subsystem else None
    )
    
    print(f"\n[INFO] Registered Services ({len(services_info)} total):")
    print("=" * 80)
    
    for service_id, info in services_info.items():
        print(f"[SERVICE] {service_id}")
        print(f"   Name: {info['name']}")
        print(f"   Subsystem: {info['subsystem']}")
        print(f"   Description: {info['description']}")
        print(f"   Dependencies: {info['dependencies']}")
        print(f"   Inputs: {info['required_inputs']}")
        print(f"   Outputs: {info['provided_outputs']}")
        print()

# ... keep existing legacy functions for backward compatibility ...
def run_plt_cmd(args):
    """Run the Personalized Learning Tree (PLT) generation pipeline."""
    print("[PLT] Generating Personalized Learning Tree (PLT)")
    print("=" * 50)
    print(f"[COURSE] Course: {args.course_id}")
    print(f"[LEARNER] Learner: {args.learner_id}")
    
    # Prepare learner context if provided
    learner_context = {}
    if hasattr(args, 'learning_style') and args.learning_style:
        learner_context['learning_style'] = args.learning_style
    if hasattr(args, 'experience_level') and args.experience_level:
        learner_context['experience_level'] = args.experience_level
    if hasattr(args, 'preferences') and args.preferences:
        learner_context['preferences'] = args.preferences
    
    try:
        # Import PLT generator
        from graph.plt_generator import run_plt_generator
        
        # Run PLT generation
        plt_result = run_plt_generator()
        
        if "final_plt" in plt_result:
            final_plt = plt_result["final_plt"]
            
            print("[SUCCESS] PLT Generated Successfully!")
            print(f"[COURSE] Course: {args.course_id}")
            print(f"[LEARNER] Learner: {args.learner_id}")
            
            # Print PLT stats
            print(f"\n[STATS] Total Learning Steps: {len(final_plt.get('learning_path', []))}")
            print(f"[STATS] Estimated Duration: {final_plt.get('estimated_duration', 'Unknown')}")
            
            # Print sample learning path
            print("\n[SAMPLE] Learning Path (first 3 steps):")
            for i, step in enumerate(final_plt.get('learning_path', [])[:3], 1):
                print(f"  {i}. {step.get('lo', 'Unknown LO')}")
                print(f"     KC: {step.get('kc', 'Unknown KC')}")
                print(f"     Method: {step.get('instruction_method', 'Unknown Method')}")
            
            return final_plt
        else:
            print("[ERROR] PLT generation failed - no final PLT in result")
            return None
    
    except Exception as e:
        print(f"[ERROR] PLT generation failed: {e}")
        return None

def run_es_pipeline(args=None):
    """Run the Elasticsearch to Knowledge Graph pipeline."""
    # Use default values if args is not provided
    course_id = getattr(args, 'course_id', 'OSN') if args else 'OSN'
    learner_id = getattr(args, 'learner_id', 'R000') if args else 'R000'
    generate_plt = getattr(args, 'generate_plt', False) if args else False
    clear_existing = getattr(args, 'clear_existing', False) if args else False
    
    print("[ES] Elasticsearch to Knowledge Graph Pipeline")
    print("=" * 50)
    print(f"[COURSE] Course: {course_id}")
    if generate_plt:
        print(f"[LEARNER] Learner: {learner_id}")
    print(f"[CONFIG] Generate PLT: {generate_plt}")
    print(f"[CONFIG] Clear Existing: {clear_existing}")
    
    try:
        # Step 1: Validate Elasticsearch connection
        print(f"\n[STEP-1] Validating Elasticsearch connection...")
        if not validate_es_connection():
            print("[ERROR] Elasticsearch validation failed. Please check your ES setup.")
            return
        
        # Get chunk count
        chunk_count = get_es_chunk_count()
        if chunk_count == 0:
            print("[ERROR] No chunks found in Elasticsearch. Please check your index.")
            return
        
        # Step 2: Transform ES chunks to KG format
        print(f"\n[STEP-2] Transforming ES chunks to KG format...")
        course_graph = transform_es_to_kg(course_id=course_id)
        
        if not course_graph["learning_objectives"]:
            print("[ERROR] No learning objectives generated. Check your ES data.")
            return
        
        # Step 3: Insert KG into Neo4j
        print(f"\n[STEP-3] Inserting KG into Neo4j...")
        insert_course_kg_to_neo4j(course_graph)
        print("[SUCCESS] Knowledge Graph successfully inserted into Neo4j")
        
        # Step 4: Generate PLT (optional)
        if generate_plt:
            print(f"\n[STEP-4] Generating Personalized Learning Tree for {learner_id}...")
            plt_result = run_plt_generator()
            plt = plt_result["final_plt"]
            insert_plt_to_neo4j(plt, clear_existing=clear_existing)
            print("[SUCCESS] Personalized Learning Tree generated successfully!")
            print(f"[STATS] Generated {len(plt['learning_path'])} learning steps")
        
        print(f"\n[COMPLETE] Pipeline completed successfully!")
        print(f"[COURSE] Course: {course_id}")
        print(f"[STATS] Learning Objectives: {len(course_graph['learning_objectives'])}")
        print(f"[KNOWLEDGE] Knowledge Components: {sum(len(lo.get('kcs', [])) for lo in course_graph['learning_objectives'])}")
        if generate_plt:
            print(f"[LEARNER] PLT generated for learner: {learner_id}")
            
    except Exception as e:
        print(f"[ERROR] ES Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

def run_unified_pipeline(args=None):
    """Run the unified end-to-end pipeline."""
    print("[UNIFIED] Complete End-to-End Pipeline")
    print("=" * 50)
    
    try:
        # Step 1: Run Stage 1 Pipeline (Research & Knowledge Component)
        print("\n[STEP-1] Running Stage 1: Research & Knowledge Component Pipeline...")
        content = """
        Operating Systems Course: Understand the principles of virtual memory, 
        process scheduling, and file systems in modern operating systems.
        """
        messages = [HumanMessage(content=content)]
        
        graph_stage1 = build_graph_stage_1()
        result_stage1 = graph_stage1.invoke({"messages": messages})
        
        print(f"✅ Stage 1 completed with {len(result_stage1['messages'])} agent responses")
        
        # Extract knowledge components from Stage 1 result
        kcs = []
        for msg in result_stage1["messages"]:
            if "Knowledge Components:" in msg.content:
                kc_text = msg.content.split("Knowledge Components:")[1].strip()
                kcs = [kc.strip() for kc in kc_text.split("-") if kc.strip()]
                break
        
        # Step 2: Run Stage 2 Pipeline (Learning Process & Instruction)
        print("\n[STEP-2] Running Stage 2: Learning Process & Instruction Pipeline...")
        content = f"""
        Learning Objective: Understand operating system principles
        Knowledge Components: {', '.join(kcs[:3])}
        """
        messages = [HumanMessage(content=content)]
        
        graph_stage2 = build_graph_stage_2()
        result_stage2 = graph_stage2.invoke({"messages": messages})
        
        print(f"✅ Stage 2 completed with {len(result_stage2['messages'])} agent responses")
        
        # Step 3: Generate PLT
        print("\n[STEP-3] Generating Personalized Learning Tree...")
        plt_result = run_plt_generator()
        
        if "final_plt" in plt_result:
            final_plt = plt_result["final_plt"]
            print(f"✅ PLT generated with {len(final_plt.get('learning_path', []))} learning steps")
        else:
            print("❌ PLT generation failed")
        
        print("\n[COMPLETE] Unified pipeline completed successfully!")
        return {
            "stage1_result": result_stage1,
            "stage2_result": result_stage2,
            "plt_result": plt_result if "final_plt" in plt_result else None
        }
        
    except Exception as e:
        print(f"[ERROR] Unified pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_kg_visualization(args):
    """Generate and visualize a knowledge graph."""
    from tools.generate_and_visualize_kg import main as kg_main
    
    # Pass all arguments to the kg_main function
    sys.argv = ['generate_and_visualize_kg.py']
    
    if hasattr(args, 'course_id') and args.course_id:
        sys.argv.append('--course_id')
        sys.argv.append(args.course_id)
    
    if hasattr(args, 'clear_existing') and args.clear_existing:
        sys.argv.append('--clear_existing')
    
    if hasattr(args, 'output') and args.output:
        sys.argv.append('--output')
        sys.argv.append(args.output)
    
    return kg_main()

def main():
    """Main CLI entry point."""
    # Validate configuration before proceeding
    try:
        from config.loader import config
        validation_results = config.validate_configuration()
        missing_configs = [k for k, v in validation_results.items() if not v]
        if missing_configs:
            print(f"⚠️ Warning: Missing configuration for: {', '.join(missing_configs)}")
            print("Some features may not work correctly.")
    except Exception as e:
        print(f"⚠️ Warning: Configuration validation failed: {e}")
    
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Stage 1 command
    parser_stage1 = subparsers.add_parser('stage1', help='Run Stage 1: Research & Knowledge Component Pipeline')
    
    # Stage 2 command
    parser_stage2 = subparsers.add_parser('stage2', help='Run Stage 2: Learning Process & Instruction Pipeline')
    
    # PLT command
    parser_plt = subparsers.add_parser('plt', help='Run PLT: Personalized Learning Tree Pipeline')
    parser_plt.add_argument('--course_id', default='OSN', help='Course ID (default: OSN)')
    parser_plt.add_argument('--learner_id', default='R000', help='Learner ID (default: R000)')
    parser_plt.add_argument('--learning_style', help='Learning style (visual, auditory, kinesthetic)')
    parser_plt.add_argument('--experience_level', help='Experience level (beginner, intermediate, advanced)')
    parser_plt.add_argument('--preferences', help='Learner preferences (comma-separated)')
    
    # ES command
    parser_es = subparsers.add_parser('es', help='Run ES: Elasticsearch to Knowledge Graph Pipeline')
    parser_es.add_argument('--course_id', default='OSN', help='Course ID (default: OSN)')
    parser_es.add_argument('--learner_id', default='R000', help='Learner ID (default: R000)')
    parser_es.add_argument('--generate_plt', action='store_true', help='Generate PLT after KG')
    parser_es.add_argument('--clear_existing', action='store_true', help='Clear existing data')
    
    # Unified command
    parser_unified = subparsers.add_parser('unified', help='Run Unified: Complete End-to-End Pipeline')
    
    # Automatic Pipeline command (microservices-based)
    parser_auto = subparsers.add_parser('auto', help='Run automatic pipeline using microservices')
    parser_auto.add_argument('--course_id', default='OSN', help='Course ID (default: OSN)')
    parser_auto.add_argument('--source', default='elasticsearch', choices=['pdf', 'elasticsearch', 'llm_generated'], help='Content source (default: elasticsearch)')
    parser_auto.add_argument('--learner_id', help='Learner ID for PLT generation')
    parser_auto.add_argument('--file_path', help='PDF file path (required for pdf source)')
    parser_auto.add_argument('--es_index', default='advanced_docs_elasticsearch_v2', help='Elasticsearch index (default: advanced_docs_elasticsearch_v2)')
    parser_auto.add_argument('--raw_content', help='Raw content for llm_generated source')
    parser_auto.add_argument('--generate_plt', action='store_true', default=True, help='Generate personalized learning tree (default: True)')
    
    # Knowledge Graph Visualization command
    parser_kg = subparsers.add_parser('kg', help='Generate and visualize a knowledge graph')
    parser_kg.add_argument('--course_id', default='OSN', help='Course ID (default: OSN)')
    parser_kg.add_argument('--clear_existing', action='store_true', help='Clear existing data before generation')
    parser_kg.add_argument('--output', help='Output file for visualization (default: kg_diagram.md)')
    
    args = parser.parse_args()
    
    if args.command == "stage1":
        print("[TARGET] Running Stage 1: Research & Knowledge Component Pipeline")
        print("=" * 50)
        
        content = """
        Operating Systems Course: Understand the principles of virtual memory, 
        process scheduling, and file systems in modern operating systems.
        """
        messages = [HumanMessage(content=content)]
        
        graph = build_graph_stage_1()
        result = graph.invoke({"messages": messages})
        
        print("[SUCCESS] Stage 1 completed!")
        print(f"[STATS] Generated {len(result['messages'])} agent responses")
        
    elif args.command == "stage2":
        print("[TARGET] Running Stage 2: Learning Process & Instruction Pipeline")
        print("=" * 50)
        
        content = """
        Learning Objective: Understand virtual memory concepts and implementation
        Knowledge Components: Virtual memory mapping, page tables, memory allocation
        """
        messages = [HumanMessage(content=content)]
        
        graph = build_graph_stage_2()
        result = graph.invoke({"messages": messages})
        
        print("[SUCCESS] Stage 2 completed!")
        print(f"[STATS] Generated {len(result['messages'])} agent responses")
        
    elif args.command == "plt":
        run_plt_cmd(args)
        
    elif args.command == "es":
        run_es_pipeline(args)
        
    elif args.command == "unified":
        run_unified_pipeline(args)
        
    elif args.command == "auto":
        run_automatic_pipeline_cmd(args)
        
    elif args.command == "kg":
        run_kg_visualization(args)
        
    else:
        print(f"[ERROR] Unknown command: {args.command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()