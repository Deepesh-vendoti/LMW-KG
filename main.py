"""
Enhanced CLI Runner for LangGraph KG Agent Pipelines

Now supports both legacy manual commands, automatic pipelines, and NEW semi-automatic faculty approval workflows:

SEMI-AUTOMATIC PIPELINES (Faculty Approval Gates):
    python main.py faculty-start --course_id CSN --faculty_id PROF_123    # Start faculty workflow
    python main.py faculty-approve --course_id CSN --action approve       # Faculty approve LOs
    python main.py faculty-confirm --course_id CSN --action confirm       # Faculty confirm structure  
    python main.py faculty-finalize --course_id CSN --action finalize     # Faculty finalize KG
    python main.py faculty-status --course_id CSN                         # Check workflow status

AUTOMATIC PIPELINES (No Faculty Input):
    python main.py auto                    # Run complete automatic pipeline  
    python main.py auto --course_id CSN    # Auto pipeline for specific course
    python main.py content --course_id CSN # Content-only automatic pipeline
    python main.py learner --learner_id R001 # Learner-only automatic pipeline

LEGACY MANUAL COMMANDS (Still supported):
    python main.py stage1                  # Manual Stage 1 only
    python main.py stage2                  # Manual Stage 2 only  
    python main.py plt                     # Manual PLT only
    python main.py es                      # Manual ES pipeline
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from langchain_core.messages import HumanMessage
from graph.graph import build_graph_stage_1, build_graph_stage_2
from graph.plt_generator import run_plt_generator
from graph.db import insert_plt_to_neo4j, get_plt_for_learner
from graph.utils.es_to_kg import transform_es_to_kg, validate_es_connection, get_es_chunk_count
from graph.db import insert_course_kg_to_neo4j, clear_plt_for_learner
# Removed unused import: from graph.orchestrator import run_course_pipeline

# Import automatic pipeline coordinator
from pipeline.coordinator import run_automatic_pipeline, process_course_content, generate_learner_plt
from config.loader import get_default_course_id, get_default_learner_id
from utils.logging import get_orchestrator_logger

# Import NEW semi-automatic pipeline coordinator
from pipeline.semi_automatic_coordinator import (
    start_faculty_workflow, faculty_approve, faculty_confirm, faculty_finalize,
    semi_automatic_coordinator
)

# Enhanced logger
logger = get_orchestrator_logger("main_cli")

def run_automatic_pipeline_cmd(args):
    """
    Run the complete automatic pipeline - REPLACES manual CLI invocation.
    
    This is the new recommended way to run the system.
    """
    logger.info("Starting automatic pipeline execution", 
                course_id=args.course_id,
                source=args.source,
                learner_id=getattr(args, 'learner_id', None))
    
    try:
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
        
        # Execute automatic pipeline
        print("🚀 Running Automatic LangGraph Pipeline")
        print("=" * 50)
        print(f"📚 Course: {args.course_id}")
        print(f"📝 Source: {args.source}")
        if pipeline_kwargs.get("learner_id"):
            print(f"👤 Learner: {pipeline_kwargs['learner_id']}")
        print("=" * 50)
        
        result = run_automatic_pipeline(**pipeline_kwargs)
        
        # Display results
        if result["status"] == "completed":
            print("\n✅ Automatic Pipeline Completed Successfully!")
            print(f"📊 Pipeline Type: {result['pipeline_type']}")
            print(f"📚 Course ID: {result['course_id']}")
            
            if "content_pipeline" in result:
                content_status = result["content_pipeline"]["status"]
                print(f"📝 Content Pipeline: {content_status}")
                if content_status == "completed":
                    stages = result["content_pipeline"].get("stages", [])
                    print(f"   Stages: {' → '.join(stages)}")
            
            if "learner_pipeline" in result and result["learner_pipeline"]:
                learner_status = result["learner_pipeline"]["status"]
                print(f"👤 Learner Pipeline: {learner_status}")
                if learner_status == "completed":
                    print(f"   Learner: {result['learner_id']}")
            
            print("\n🎉 All stages completed automatically!")
        else:
            print(f"\n❌ Pipeline failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="automatic_pipeline_cmd")
        print(f"❌ Automatic pipeline failed: {e}")

def run_content_only_cmd(args):
    """Run content-only automatic pipeline."""
    logger.info("Starting content-only pipeline", course_id=args.course_id, source=args.source)
    
    try:
        print("📝 Running Content-Only Automatic Pipeline")
        print("=" * 50)
        
        result = process_course_content(
            course_id=args.course_id,
            content_source=args.source,
            file_path=getattr(args, 'file_path', None),
            es_index=getattr(args, 'es_index', 'advanced_docs_elasticsearch_v2'),
            raw_content=getattr(args, 'raw_content', '')
        )
        
        if result["status"] == "completed":
            print("✅ Content pipeline completed successfully!")
            print(f"📚 Course: {result['course_id']}")
            print(f"📝 Source: {result['source']}")
            stages = result.get("stages", [])
            print(f"🔄 Stages: {' → '.join(stages)}")
        else:
            print(f"❌ Content pipeline failed: {result.get('error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="content_only_cmd")
        print(f"❌ Content pipeline failed: {e}")

def run_learner_only_cmd(args):
    """Run learner-only automatic pipeline."""
    logger.info("Starting learner-only pipeline", 
                course_id=args.course_id, 
                learner_id=args.learner_id)
    
    try:
        print("👤 Running Learner-Only Automatic Pipeline")
        print("=" * 50)
        
        result = generate_learner_plt(
            course_id=args.course_id,
            learner_id=args.learner_id
        )
        
        if result["status"] == "completed":
            print("✅ Learner pipeline completed successfully!")
            print(f"📚 Course: {result['course_id']}")
            print(f"👤 Learner: {result['learner_id']}")
            stages = result.get("stages", [])
            print(f"🔄 Stages: {' → '.join(stages)}")
        else:
            print(f"❌ Learner pipeline failed: {result.get('error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="learner_only_cmd")
        print(f"❌ Learner pipeline failed: {e}")

def run_faculty_start_cmd(args):
    """Start a new faculty approval workflow."""
    logger.info("Starting faculty approval workflow",
                course_id=args.course_id,
                faculty_id=args.faculty_id)
    
    try:
        print("🔵 Starting Faculty Approval Workflow")
        print("=" * 50)
        print(f"📚 Course: {args.course_id}")
        print(f"👨‍🏫 Faculty: {args.faculty_id}")
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
            print("✅ Content processed and Learning Objectives generated!")
            print(f"📝 Generated {len(result['draft_learning_objectives'])} Learning Objectives")
            print("\n" + result["ui_data"]["approval_stage"])
            print("📋 " + result["ui_data"]["instructions"])
            print(f"🎯 Next Action: {result['next_action_required']}")
            
            print("\n📚 Draft Learning Objectives:")
            for i, lo in enumerate(result['draft_learning_objectives'][:3], 1):
                print(f"   {i}. {lo.get('text', 'N/A')}")
            if len(result['draft_learning_objectives']) > 3:
                print(f"   ... and {len(result['draft_learning_objectives']) - 3} more")
                
            print(f"\n🔄 Use: python main.py faculty-approve --course_id {args.course_id} --action approve")
            
        else:
            print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="faculty_start_cmd")
        print(f"❌ Faculty workflow start failed: {e}")

def run_faculty_approve_cmd(args):
    """Process faculty approval of learning objectives."""
    logger.info("Processing faculty LO approval",
                course_id=args.course_id,
                action=args.action)
    
    try:
        print("🔵 Faculty Learning Objectives Approval")
        print("=" * 50)
        
        result = faculty_approve(
            course_id=args.course_id,
            action=args.action,
            faculty_comments=getattr(args, 'comments', '')
        )
        
        if result["status"] == "awaiting_faculty_confirmation":
            print("✅ Learning Objectives APPROVED!")
            print("📄 FACD (Faculty Approved Course Details) generated")
            print("\n🟡 Moving to Course Structure Confirmation...")
            print("📋 " + result["ui_data"]["instructions"])
            print(f"🎯 Next Action: {result['next_action_required']}")
            print(f"\n🔄 Use: python main.py faculty-confirm --course_id {args.course_id} --action confirm")
            
        elif result["status"] == "awaiting_faculty_approval":
            print("✏️ Learning Objectives edited - awaiting re-approval")
            
        elif result["status"] == "rejected":
            print("❌ Learning Objectives rejected")
            print(f"💬 Comments: {result.get('faculty_comments', 'None')}")
            
        else:
            print(f"❌ Action failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="faculty_approve_cmd")
        print(f"❌ Faculty approval failed: {e}")

def run_faculty_confirm_cmd(args):
    """Process faculty confirmation of course structure."""
    logger.info("Processing faculty structure confirmation",
                course_id=args.course_id,
                action=args.action)
    
    try:
        print("🟡 Faculty Course Structure Confirmation")
        print("=" * 50)
        
        result = faculty_confirm(
            course_id=args.course_id,
            action=args.action,
            faculty_comments=getattr(args, 'comments', '')
        )
        
        if result["status"] == "awaiting_faculty_finalization":
            print("✅ Course Structure CONFIRMED!")
            print("📄 FCCS (Faculty Confirmed Course Structure) generated")
            print("\n🟢 Moving to Knowledge Graph Finalization...")
            print("📋 " + result["ui_data"]["instructions"])
            print(f"🎯 Next Action: {result['next_action_required']}")
            print(f"\n🔄 Use: python main.py faculty-finalize --course_id {args.course_id} --action finalize")
            
        elif result["status"] == "awaiting_faculty_confirmation":
            print("✏️ Course Structure edited - awaiting re-confirmation")
            
        elif result["status"] == "rejected":
            print("❌ Course Structure rejected")
            print(f"💬 Comments: {result.get('faculty_comments', 'None')}")
            
        else:
            print(f"❌ Action failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="faculty_confirm_cmd")
        print(f"❌ Faculty confirmation failed: {e}")

def run_faculty_finalize_cmd(args):
    """Process faculty finalization of knowledge graph."""
    logger.info("Processing faculty KG finalization",
                course_id=args.course_id,
                action=args.action)
    
    try:
        print("🟢 Faculty Knowledge Graph Finalization")
        print("=" * 50)
        
        result = faculty_finalize(
            course_id=args.course_id,
            action=args.action,
            faculty_comments=getattr(args, 'comments', '')
        )
        
        if result["status"] == "course_structure_finalized":
            print("✅ Knowledge Graph FINALIZED!")
            print("📄 FFCS (Faculty Finalized Course Structure) generated")
            print("\n🎉 Faculty Approval Workflow COMPLETE!")
            print("🔒 Course structure is now locked and ready for learner PLT requests")
            print("📋 " + result["ui_data"]["instructions"])
            
            print(f"\n💡 To generate PLT for a learner, use:")
            print(f"   python main.py learner-plt --course_id {args.course_id} --learner_id LEARNER_ID")
            
        elif result["status"] == "awaiting_faculty_finalization":
            print("✏️ Knowledge Graph edited - awaiting re-finalization")
            
        elif result["status"] == "rejected":
            print("❌ Knowledge Graph rejected")
            print(f"💬 Comments: {result.get('faculty_comments', 'None')}")
            
        else:
            print(f"❌ Action failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="faculty_finalize_cmd")
        print(f"❌ Faculty finalization failed: {e}")

def run_learner_plt_cmd(args):
    """Generate PLT for a specific learner after faculty workflow completion."""
    logger.info("Generating PLT for learner",
                course_id=args.course_id,
                learner_id=args.learner_id)
    
    try:
        print("🌳 Generating Personalized Learning Tree (PLT)")
        print("=" * 50)
        print(f"📚 Course: {args.course_id}")
        print(f"👤 Learner: {args.learner_id}")
        print("=" * 50)
        
        # Prepare learner context if provided
        learner_context = {}
        if hasattr(args, 'learning_style') and args.learning_style:
            learner_context['learning_style'] = args.learning_style
        if hasattr(args, 'experience_level') and args.experience_level:
            learner_context['experience_level'] = args.experience_level
        if hasattr(args, 'preferences') and args.preferences:
            learner_context['preferences'] = args.preferences
        
        from pipeline.semi_automatic_coordinator import semi_automatic_coordinator
        result = semi_automatic_coordinator.generate_plt_for_learner(
            course_id=args.course_id,
            learner_id=args.learner_id,
            learner_context=learner_context if learner_context else None
        )
        
        if result["status"] == "plt_generated":
            print("✅ PLT Generated Successfully!")
            print(f"📚 Course: {result['course_id']}")
            print(f"👤 Learner: {result['learner_id']}")
            print(f"🎯 Based on Faculty Finalized Structure: {'✅' if result['based_on_ffcs'] else '❌'}")
            if result.get('learner_context'):
                print(f"🔧 Learner Context Applied: {list(result['learner_context'].keys())}")
            print("\n🎉 Personalized Learning Tree ready for learner!")
            
        else:
            print(f"❌ PLT generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.log_error_with_context(e, operation="learner_plt_cmd")
        print(f"❌ PLT generation failed: {e}")

def run_faculty_status_cmd(args):
    """Check faculty approval workflow status."""
    try:
        print("📊 Faculty Workflow Status")
        print("=" * 50)
        
        status = semi_automatic_coordinator.get_workflow_status(args.course_id)
        
        if status["status"] == "not_found":
            print(f"❌ No workflow found for course {args.course_id}")
            print("🔄 Use: python main.py faculty-start to begin a new workflow")
            return
        
        print(f"📚 Course: {status['course_id']}")
        print(f"👨‍🏫 Faculty: {status['faculty_id']}")
        print(f"🔄 Current Stage: {status['current_stage']}")
        print(f"⏰ Last Updated: {status['last_updated']}")
        print(f"📄 Has FACD: {'✅' if status['has_facd'] else '❌'}")
        print(f"📄 Has FCCS: {'✅' if status['has_fccs'] else '❌'}")
        print(f"📄 Has FFCS: {'✅' if status['has_ffcs'] else '❌'}")
        print(f"🚀 Ready for PLT: {'✅' if status['ready_for_plt'] else '❌'}")
        
        print(f"\n📋 Approval History ({len(status['approval_history'])} actions):")
        for action in status['approval_history'][-3:]:  # Show last 3 actions
            print(f"   • {action['stage']}: {action['action']} at {action['timestamp']}")
        
    except Exception as e:
        logger.log_error_with_context(e, operation="faculty_status_cmd")
        print(f"❌ Status check failed: {e}")

# ... keep existing legacy functions for backward compatibility ...
def run_plt_pipeline():
    """Legacy PLT pipeline function (kept for backward compatibility)"""
    learner_id = get_default_learner_id()
    course_id = get_default_course_id()

    try:
        # Step 1: Generate and insert
        print("1️⃣ Generating Personalized Learning Tree...")
        result = run_plt_generator()
        plt = result["final_plt"]
        print(f"   ✅ Generated PLT with {len(plt['learning_path'])} steps")
        
        print("\n2️⃣ Inserting PLT into Neo4j...")
        insert_plt_to_neo4j(plt, clear_existing=True)
        print("   ✅ Inserted PLT steps into Neo4j (cleared existing data).")

        # Step 2: Query and verify
        print("\n3️⃣ Querying and verifying PLT data...")
        steps = get_plt_for_learner(learner_id, course_id)
        print(f"   ✅ Retrieved {len(steps)} PLT steps from Neo4j.")
        
        print(f"\n4️⃣ PLT Summary for {learner_id} in {course_id}:")
        print("-" * 50)

        for i, step in enumerate(steps[:5], 1):  # Show first 5 steps
            print(f"   {i}. LO: {step.get('lo', 'N/A')}")
            print(f"      KC: {step.get('kc', 'N/A')}")
            print(f"      Priority: {step.get('priority', 'N/A')}")
            print(f"      Sequence: {step.get('sequence', 'N/A')}")
            print()

        print(f"✅ PLT Pipeline completed successfully!")
        print(f"📊 Generated {len(plt['learning_path'])} learning steps")
        print(f"📊 Inserted {len(steps)} steps into Neo4j")

    except Exception as e:
        print(f"❌ PLT Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

def run_es_pipeline():
    """Legacy ES pipeline function (kept for backward compatibility)"""
    print("🚀 ES to KG to PLT Pipeline")
    print("=" * 50)
    
    # Get user input for configuration
    try:
        course_id = input("Enter course ID (default: OSN): ").strip() or get_default_course_id()
        learner_id = input("Enter learner ID (default: R000): ").strip() or get_default_learner_id()
        generate_plt = input("Generate PLT after KG insertion? (y/n, default: y): ").strip().lower() != "n"
        clear_existing = input("Clear existing KG data? (y/n, default: n): ").strip().lower() == "y"
    except Exception as e:
        print(f"⚠️ Using defaults due to input error: {e}")
        course_id = get_default_course_id()
        learner_id = get_default_learner_id()
        generate_plt = True
        clear_existing = False
    
    try:
        # Step 1: Validate Elasticsearch connection
        print(f"\n1️⃣ Validating Elasticsearch connection...")
        if not validate_es_connection():
            print("❌ Elasticsearch validation failed. Please check your ES setup.")
            return
        
        # Get chunk count
        chunk_count = get_es_chunk_count()
        if chunk_count == 0:
            print("❌ No chunks found in Elasticsearch. Please check your index.")
            return
        
        # Step 2: Transform ES chunks to KG format
        print(f"\n2️⃣ Transforming ES chunks to KG format...")
        course_graph = transform_es_to_kg(course_id=course_id)
        
        if not course_graph["learning_objectives"]:
            print("❌ No learning objectives generated. Check your ES data.")
            return
        
        # Step 3: Insert KG into Neo4j
        print(f"\n3️⃣ Inserting KG into Neo4j...")
        insert_course_kg_to_neo4j(course_graph)
        print("✅ Knowledge Graph successfully inserted into Neo4j")
        
        # Step 4: Generate PLT (optional)
        if generate_plt:
            print(f"\n4️⃣ Generating Personalized Learning Tree for {learner_id}...")
            plt_result = run_plt_generator()
            plt = plt_result["final_plt"]
            insert_plt_to_neo4j(plt, clear_existing=clear_existing)
            print("✅ Personalized Learning Tree generated successfully!")
            print(f"📊 Generated {len(plt['learning_path'])} learning steps")
        
        print(f"\n🎉 Pipeline completed successfully!")
        print(f"📚 Course: {course_id}")
        print(f"📊 Learning Objectives: {len(course_graph['learning_objectives'])}")
        print(f"🧠 Knowledge Components: {sum(len(lo.get('kcs', [])) for lo in course_graph['learning_objectives'])}")
        if generate_plt:
            print(f"👤 PLT generated for learner: {learner_id}")

    except Exception as e:
        print(f"❌ ES Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

def run_unified_pipeline():
    """Legacy unified pipeline function (redirects to automatic pipeline)"""
    print("🔄 Redirecting to automatic pipeline...")
    print("Use 'python main.py auto' for the new automatic pipeline interface.")
    
    # Provide basic unified execution
    try:
        result = run_automatic_pipeline(
            content_source="elasticsearch", 
            generate_plt=True
        )
        
        if result["status"] == "completed":
            print("✅ Unified pipeline completed!")
        else:
            print(f"❌ Unified pipeline failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Unified pipeline failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExample semi-automatic commands:")
        print("  python main.py faculty-start --course_id CSN --faculty_id PROF_123")
        print("  python main.py faculty-approve --course_id CSN --action approve")
        print("  python main.py faculty-confirm --course_id CSN --action confirm")
        print("  python main.py faculty-finalize --course_id CSN --action finalize")
        print("  python main.py learner-plt --course_id CSN --learner_id R001  # Generate PLT for learner")
        print("\nExample automatic commands:")
        print("  python main.py auto                           # Complete automatic pipeline")
        print("  python main.py auto --course_id CSN          # Auto pipeline for course CSN")
        print("  python main.py content --course_id CSN       # Content-only pipeline")
        print("  python main.py learner --learner_id R001     # Learner-only pipeline")
        print("\nLegacy commands still supported:")
        print("  python main.py stage1|stage2|plt|es|unified")
        sys.exit(1)

    command = sys.argv[1].lower()
    
    # NEW SEMI-AUTOMATIC FACULTY APPROVAL COMMANDS
    if command == "faculty-start":
        import argparse
        parser = argparse.ArgumentParser(description="Start Faculty Approval Workflow")
        parser.add_argument("--course_id", default=get_default_course_id(), help="Course identifier")
        parser.add_argument("--faculty_id", required=True, help="Faculty member identifier")
        parser.add_argument("--source", choices=["pdf", "elasticsearch", "llm_generated"],
                           default="elasticsearch", help="Content source type")
        parser.add_argument("--file_path", help="PDF file path (for PDF source)")
        parser.add_argument("--es_index", default="advanced_docs_elasticsearch_v2", help="ES index")
        parser.add_argument("--raw_content", help="Raw content (for LLM generated)")
        
        args = parser.parse_args(sys.argv[2:])
        run_faculty_start_cmd(args)
        
    elif command == "faculty-approve":
        import argparse
        parser = argparse.ArgumentParser(description="Faculty Approve Learning Objectives")
        parser.add_argument("--course_id", required=True, help="Course identifier")
        parser.add_argument("--action", choices=["approve", "edit", "reject"], required=True,
                           help="Faculty action")
        parser.add_argument("--comments", help="Faculty comments")
        
        args = parser.parse_args(sys.argv[2:])
        run_faculty_approve_cmd(args)
        
    elif command == "faculty-confirm":
        import argparse
        parser = argparse.ArgumentParser(description="Faculty Confirm Course Structure")
        parser.add_argument("--course_id", required=True, help="Course identifier")
        parser.add_argument("--action", choices=["confirm", "edit", "reject"], required=True,
                           help="Faculty action")
        parser.add_argument("--comments", help="Faculty comments")
        
        args = parser.parse_args(sys.argv[2:])
        run_faculty_confirm_cmd(args)
        
    elif command == "faculty-finalize":
        import argparse
        parser = argparse.ArgumentParser(description="Faculty Finalize Knowledge Graph")
        parser.add_argument("--course_id", required=True, help="Course identifier")
        parser.add_argument("--action", choices=["finalize", "edit", "reject"], required=True,
                           help="Faculty action")
        parser.add_argument("--comments", help="Faculty comments")
        
        args = parser.parse_args(sys.argv[2:])
        run_faculty_finalize_cmd(args)
        
    elif command == "learner-plt":
        import argparse
        parser = argparse.ArgumentParser(description="Generate PLT for Learner (after faculty workflow)")
        parser.add_argument("--course_id", required=True, help="Course identifier")
        parser.add_argument("--learner_id", required=True, help="Learner identifier")
        parser.add_argument("--learning_style", choices=["visual", "auditory", "kinesthetic"], 
                           help="Learner's learning style")
        parser.add_argument("--experience_level", choices=["beginner", "intermediate", "advanced"],
                           help="Learner's experience level")
        parser.add_argument("--preferences", help="Additional learner preferences (JSON string)")
        
        args = parser.parse_args(sys.argv[2:])
        run_learner_plt_cmd(args)
        
    elif command == "faculty-status":
        import argparse
        parser = argparse.ArgumentParser(description="Check Faculty Workflow Status")
        parser.add_argument("--course_id", required=True, help="Course identifier")
        
        args = parser.parse_args(sys.argv[2:])
        run_faculty_status_cmd(args)

    # EXISTING AUTOMATIC COMMANDS (unchanged)
    elif command == "auto":
        import argparse
        parser = argparse.ArgumentParser(description="Automatic LangGraph Pipeline")
        parser.add_argument("--course_id", default=get_default_course_id(), help="Course identifier")
        parser.add_argument("--source", choices=["pdf", "elasticsearch", "llm_generated"], 
                           default="elasticsearch", help="Content source type")
        parser.add_argument("--learner_id", default=get_default_learner_id(), help="Learner identifier")
        parser.add_argument("--file_path", help="PDF file path (for PDF source)")
        parser.add_argument("--es_index", default="advanced_docs_elasticsearch_v2", help="ES index")
        parser.add_argument("--raw_content", help="Raw content (for LLM generated)")
        parser.add_argument("--no-plt", dest="generate_plt", action="store_false", help="Skip PLT generation")
        
        args = parser.parse_args(sys.argv[2:])
        run_automatic_pipeline_cmd(args)
        
    # LEGACY COMMANDS (still supported)
    elif command == "stage1":
        print("🔍 Running Stage 1: Knowledge Structuring Pipeline")
        print("=" * 50)
        
        content = "Explain the concept of virtual memory in operating systems and how it relates to physical memory management."
        messages = [HumanMessage(content=content)]
        
        graph = build_graph_stage_1()
        result = graph.invoke({"messages": messages})
        
        print("✅ Stage 1 completed!")
        print(f"📊 Generated {len(result['messages'])} agent responses")
        
    elif command == "stage2":
        print("🎯 Running Stage 2: Learning Process & Instruction Pipeline")
        print("=" * 50)
        
        content = """
        Learning Objective: Understand virtual memory concepts and implementation
        Knowledge Components: Virtual memory mapping, page tables, memory allocation
        """
        messages = [HumanMessage(content=content)]
        
        graph = build_graph_stage_2()
        result = graph.invoke({"messages": messages})
        
        print("✅ Stage 2 completed!")
        print(f"📊 Generated {len(result['messages'])} agent responses")
        
    elif command == "plt":
        run_plt_pipeline()
        
    elif command == "es":
        run_es_pipeline()
        
    elif command == "unified":
        run_unified_pipeline()
        
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)