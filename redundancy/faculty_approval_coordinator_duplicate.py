"""
Manual Faculty Approval Pipeline Coordinator

Implements the complete manual faculty approval workflow with clear stages:

Stage 1: Course Initialization → 🔵 FACULTY APPROVAL GATE
Stage 2: Content Processing + LO Generation + Structure Generation → 🟡 FACULTY CONFIRMATION GATE  
Stage 3: KLI Application → 🟢 FACULTY FINALIZATION GATE
Stage 4: Knowledge Graph Generation (Post-Finalization)
Stage 5: Personalized Learning Tree (Separate Workflow)

Designed for production use with comprehensive faculty control at each stage.
"""

from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator.approval_states import (
    FacultyApprovalState, FacultyWorkflowStage, FacultyAction,
    create_approval_workflow, get_approval_workflow
)
from orchestrator.universal_orchestrator import run_cross_subsystem_workflow
from orchestrator.state import SubsystemType
from config.loader import get_default_course_id, get_default_learner_id
from utils.logging import get_orchestrator_logger, performance_tracker

class FacultyApprovalCoordinator:
    """
    Manual faculty approval pipeline coordinator.
    
    Provides complete faculty control over course development with:
    - Manual approval gates at each critical stage
    - Faculty editing capabilities
    - Comprehensive review and confirmation processes
    - UI-friendly workflow state management
    """
    
    def __init__(self):
        self.logger = get_orchestrator_logger("faculty_approval_pipeline")
        
        # Default configurations
        self.default_course_id = get_default_course_id()
        self.default_learner_id = get_default_learner_id()
        
        self.logger.info("Initialized Faculty Approval Pipeline Coordinator")
    
    def start_course_development(self,
                               course_id: str = None,
                               faculty_id: str = None,
                               content_source: str = "elasticsearch",
                               **content_kwargs) -> Dict[str, Any]:
        """
        Start a new course development workflow with faculty approval gates.
        
        Stage 1: Course Manager executes → Faculty reviews and approves course setup
        
        Args:
            course_id: Course identifier
            faculty_id: Faculty member ID
            content_source: Source type ("pdf", "elasticsearch", "llm_generated")
            **content_kwargs: Additional content processing arguments
            
        Returns:
            Course initialization result awaiting faculty approval
        """
        course_id = course_id or self.default_course_id
        operation_id = self.logger.start_operation("start_course_development")
        
        try:
            # Create faculty approval workflow
            approval_workflow = create_approval_workflow(course_id, faculty_id)
            
            self.logger.info("Starting course development with faculty approval workflow",
                           course_id=course_id,
                           faculty_id=faculty_id,
                           content_source=content_source)
            
            # Stage 1: Course Manager (course initialization)
            print("📋 [Stage 1] Course Manager - Initializing course development...")
            course_init_result = run_cross_subsystem_workflow(
                subsystem=SubsystemType.CONTENT,
                course_id=course_id,
                upload_type=content_source,
                faculty_id=faculty_id,
                workflow_type="course_initialization",
                **content_kwargs
            )
            
            # Set course initialization result in approval workflow
            approval_workflow.set_course_initialization(course_init_result)
            
            result = {
                "status": "awaiting_faculty_approval",
                "stage": "course_initialization_approval",
                "course_id": course_id,
                "faculty_id": faculty_id,
                "course_initialization": course_init_result,
                "next_action_required": "faculty_approve_course_setup",
                "faculty_controls": {
                    "approval_stage": "🔵 Course Setup Approval",
                    "description": "Course Manager has completed initial course setup. Please review and approve to proceed to content processing.",
                    "available_actions": ["approve", "reject", "request_changes"],
                    "review_data": {
                        "course_structure": course_init_result.get('course_structure'),
                        "faculty_inputs": course_init_result.get('faculty_inputs'),
                        "initialization_summary": course_init_result.get('summary')
                    }
                }
            }
            
            self.logger.end_operation(operation_id, success=True,
                                    course_id=course_id,
                                    stage="awaiting_course_approval")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="start_course_development",
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id
            }
    
    def faculty_approve_course_setup(self,
                                   course_id: str,
                                   action: str,
                                   faculty_comments: str = "",
                                   requested_changes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process faculty approval of course setup.
        
        Args:
            course_id: Course identifier
            action: Faculty action ("approve", "reject", "request_changes")
            faculty_comments: Faculty feedback
            requested_changes: Specific changes requested by faculty
            
        Returns:
            Result of faculty action and next steps
        """
        operation_id = self.logger.start_operation("faculty_approve_course_setup")
        
        try:
            # Get approval workflow
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow:
                raise ValueError(f"No approval workflow found for course {course_id}")
            
            self.logger.info("Processing faculty course setup approval",
                           course_id=course_id,
                           action=action)
            
            # Process faculty action
            faculty_action = FacultyAction(action.lower())
            approval_result = approval_workflow.faculty_approve_course_initialization(
                action=faculty_action,
                faculty_comments=faculty_comments
            )
            
            if faculty_action == FacultyAction.APPROVE:
                result = {
                    "status": "course_setup_approved",
                    "stage": "ready_for_content_processing",
                    "course_id": course_id,
                    "approval_result": approval_result,
                    "next_action_required": "proceed_to_content_processing",
                    "faculty_controls": {
                        "message": "✅ Course setup approved! Ready to proceed to content processing stage.",
                        "next_stage": "Content Processing + LO Generation + Structure Generation"
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="course_setup_approved")
                
            elif faculty_action == FacultyAction.REJECT:
                result = {
                    "status": "course_setup_rejected",
                    "stage": "course_initialization_approval",
                    "course_id": course_id,
                    "faculty_comments": faculty_comments,
                    "approval_result": approval_result,
                    "next_action_required": "revise_course_setup",
                    "faculty_controls": {
                        "message": "❌ Course setup rejected. Please revise and resubmit.",
                        "rejection_reason": faculty_comments
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="rejected")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="faculty_approve_course_setup",
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id
            }
    
    def process_content_and_structure(self, course_id: str) -> Dict[str, Any]:
        """
        Execute Stage 2: Content Processing + LO Generation + Structure Generation.
        
        This stage combines:
        - Content Preprocessor
        - Course Mapper (LO Generation + Structure Generation)
        
        Args:
            course_id: Course identifier
            
        Returns:
            Complete course structure awaiting faculty confirmation
        """
        operation_id = self.logger.start_operation("process_content_and_structure")
        
        try:
            # Get approval workflow
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow:
                raise ValueError(f"No approval workflow found for course {course_id}")
            
            if approval_workflow.current_stage != FacultyWorkflowStage.COURSE_APPROVED:
                raise ValueError(f"Course must be approved before content processing. Current stage: {approval_workflow.current_stage}")
            
            self.logger.info("Processing content and generating course structure",
                           course_id=course_id)
            
            print("📚 [Stage 2] Content Processing + LO Generation + Structure Generation...")
            
            # Execute content processing and structure generation
            structure_result = self._execute_content_processing_and_structure_generation(
                course_id=course_id,
                faculty_id=approval_workflow.faculty_id
            )
            
            # Set course structure in approval workflow (moves to AWAITING_STRUCTURE_CONFIRMATION)
            approval_workflow.set_draft_course_structure(structure_result)
            
            result = {
                "status": "awaiting_faculty_confirmation",
                "stage": "course_structure_confirmation",
                "course_id": course_id,
                "course_structure": structure_result,
                "next_action_required": "faculty_confirm_course_structure",
                "faculty_controls": {
                    "approval_stage": "🟡 Course Structure Confirmation",
                    "description": "Content processing completed. Complete course structure generated (LO→KC→LP→IM→Resources). Please review and confirm.",
                    "available_actions": ["confirm", "edit", "reject"],
                    "review_data": {
                        "learning_objectives": structure_result.get('learning_objectives'),
                        "knowledge_components": structure_result.get('knowledge_components'),
                        "learning_processes": structure_result.get('learning_processes'),
                        "instruction_methods": structure_result.get('instruction_methods'),
                        "resource_references": structure_result.get('resource_references'),
                        "course_structure_summary": structure_result.get('summary')
                    }
                }
            }
            
            self.logger.end_operation(operation_id, success=True,
                                    course_id=course_id,
                                    stage="awaiting_structure_confirmation")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="process_content_and_structure",
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id
            }
    
    def faculty_confirm_course_structure(self,
                                       course_id: str,
                                       action: str,
                                       edited_structure: Optional[Dict[str, Any]] = None,
                                       faculty_comments: str = "") -> Dict[str, Any]:
        """
        Process faculty confirmation of complete course structure.
        
        Args:
            course_id: Course identifier
            action: Faculty action ("confirm", "edit", "reject")
            edited_structure: Faculty-edited structure (if provided)
            faculty_comments: Faculty feedback
            
        Returns:
            Result of confirmation action and next steps
        """
        operation_id = self.logger.start_operation("faculty_confirm_structure")
        
        try:
            # Get approval workflow
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow:
                raise ValueError(f"No approval workflow found for course {course_id}")
            
            self.logger.info("Processing faculty structure confirmation",
                           course_id=course_id,
                           action=action,
                           has_edits=bool(edited_structure))
            
            # Process faculty action
            faculty_action = FacultyAction(action.lower())
            confirmation_result = approval_workflow.faculty_confirm_structure(
                action=faculty_action,
                edited_structure=edited_structure,
                faculty_comments=faculty_comments
            )
            
            if faculty_action == FacultyAction.CONFIRM:
                result = {
                    "status": "course_structure_confirmed",
                    "stage": "ready_for_kli_application",
                    "course_id": course_id,
                    "confirmation_result": confirmation_result,
                    "next_action_required": "proceed_to_kli_application",
                    "faculty_controls": {
                        "message": "✅ Course structure confirmed! Ready to proceed to KLI Application stage.",
                        "next_stage": "KLI Application (Knowledge Learning Indicators)"
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="structure_confirmed")
                
            elif faculty_action == FacultyAction.EDIT:
                result = {
                    "status": "awaiting_faculty_confirmation",
                    "stage": "course_structure_confirmation",
                    "course_id": course_id,
                    "course_structure": approval_workflow.draft_structure,
                    "faculty_edits_applied": True,
                    "next_action_required": "faculty_confirm_course_structure",
                    "faculty_controls": {
                        "approval_stage": "🟡 Course Structure Confirmation (Edited)",
                        "description": "Your edits have been applied. Please review and confirm the updated course structure.",
                        "available_actions": ["confirm", "edit", "reject"]
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="edited_resubmission")
                
            elif faculty_action == FacultyAction.REJECT:
                result = {
                    "status": "course_structure_rejected",
                    "stage": "course_structure_confirmation",
                    "course_id": course_id,
                    "faculty_comments": faculty_comments,
                    "next_action_required": "regenerate_course_structure",
                    "faculty_controls": {
                        "message": "❌ Course structure rejected. System will regenerate structure based on your feedback.",
                        "rejection_reason": faculty_comments
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="rejected_regeneration_needed")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="faculty_confirm_structure",
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id
            }
    
    def apply_kli_and_finalize_content(self, course_id: str) -> Dict[str, Any]:
        """
        Execute Stage 3: KLI Application.
        
        This stage applies Knowledge Learning Indicators to:
        - Learning Objectives use Course Learning Objects
        - Knowledge Components and related learning processes
        - Related instruction methods
        - Related reference names of the content
        
        Args:
            course_id: Course identifier
            
        Returns:
            KLI application results awaiting faculty finalization
        """
        operation_id = self.logger.start_operation("apply_kli_and_finalize_content")
        
        try:
            # Get approval workflow
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow:
                raise ValueError(f"No approval workflow found for course {course_id}")
            
            self.logger.info("Applying KLI and preparing content for finalization",
                           course_id=course_id)
            
            print("🎯 [Stage 3] KLI Application - Applying Knowledge Learning Indicators...")
            
            # Execute KLI application
            kli_result = self._execute_kli_application(
                course_id=course_id,
                confirmed_structure=approval_workflow.fccs
            )
            
            # Set KLI application result for faculty finalization
            approval_workflow.set_kli_application_result(kli_result)
            
            result = {
                "status": "awaiting_faculty_finalization",
                "stage": "content_finalization",
                "course_id": course_id,
                "kli_application": kli_result,
                "next_action_required": "faculty_finalize_course_content",
                "faculty_controls": {
                    "approval_stage": "🟢 Course Content Finalization",
                    "description": "KLI Application completed. All course learning objects, knowledge components, learning processes, instruction methods, and resource references are mapped. Please finalize course content.",
                    "available_actions": ["finalize", "edit", "reject"],
                    "review_data": {
                        "learning_objects": kli_result.get('learning_objects'),
                        "mapped_knowledge_components": kli_result.get('mapped_knowledge_components'),
                        "learning_processes": kli_result.get('learning_processes'),
                        "instruction_methods": kli_result.get('instruction_methods'),
                        "resource_references": kli_result.get('resource_references'),
                        "kli_application_summary": kli_result.get('summary')
                    }
                }
            }
            
            self.logger.end_operation(operation_id, success=True,
                                    course_id=course_id,
                                    stage="awaiting_content_finalization")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="apply_kli_and_finalize_content",
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id
            }
    
    def faculty_finalize_course_content(self,
                                      course_id: str,
                                      action: str,
                                      final_edits: Optional[Dict[str, Any]] = None,
                                      faculty_comments: str = "") -> Dict[str, Any]:
        """
        Process faculty finalization of course content.
        
        Args:
            course_id: Course identifier
            action: Faculty action ("finalize", "edit", "reject")
            final_edits: Final faculty edits (if provided)
            faculty_comments: Faculty feedback
            
        Returns:
            Result of finalization action and next steps
        """
        operation_id = self.logger.start_operation("faculty_finalize_content")
        
        try:
            # Get approval workflow
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow:
                raise ValueError(f"No approval workflow found for course {course_id}")
            
            self.logger.info("Processing faculty content finalization",
                           course_id=course_id,
                           action=action,
                           has_edits=bool(final_edits))
            
            # Process faculty action
            faculty_action = FacultyAction(action.lower())
            finalization_result = approval_workflow.faculty_finalize_content(
                action=faculty_action,
                final_edits=final_edits,
                faculty_comments=faculty_comments
            )
            
            if faculty_action == FacultyAction.FINALIZE:
                result = {
                    "status": "course_content_finalized",
                    "stage": "ready_for_knowledge_graph",
                    "course_id": course_id,
                    "finalization_result": finalization_result,
                    "next_action_required": "proceed_to_knowledge_graph_generation",
                    "faculty_controls": {
                        "message": "🎉 Course content finalized! Ready to generate knowledge graph.",
                        "next_stage": "Knowledge Graph Generation"
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="content_finalized")
                
            elif faculty_action == FacultyAction.EDIT:
                result = {
                    "status": "awaiting_faculty_finalization",
                    "stage": "content_finalization",
                    "course_id": course_id,
                    "kli_application": approval_workflow.kli_result,
                    "faculty_edits_applied": True,
                    "next_action_required": "faculty_finalize_course_content",
                    "faculty_controls": {
                        "approval_stage": "🟢 Course Content Finalization (Edited)",
                        "description": "Your edits have been applied. Please review and finalize the course content.",
                        "available_actions": ["finalize", "edit", "reject"]
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="edited_resubmission")
                
            elif faculty_action == FacultyAction.REJECT:
                result = {
                    "status": "course_content_rejected",
                    "stage": "content_finalization",
                    "course_id": course_id,
                    "faculty_comments": faculty_comments,
                    "next_action_required": "revise_kli_application",
                    "faculty_controls": {
                        "message": "❌ Course content rejected. KLI Application will be revised based on your feedback.",
                        "rejection_reason": faculty_comments
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="rejected_revision_needed")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="faculty_finalize_content",
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id
            }
    
    def generate_knowledge_graph(self, course_id: str) -> Dict[str, Any]:
        """
        Execute Stage 4: Knowledge Graph Generation (Post-Faculty Finalization).
        
        Args:
            course_id: Course identifier
            
        Returns:
            Knowledge graph generation results
        """
        operation_id = self.logger.start_operation("generate_knowledge_graph")
        
        try:
            # Get approval workflow
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow:
                raise ValueError(f"No approval workflow found for course {course_id}")
            
            self.logger.info("Generating knowledge graph from finalized content",
                           course_id=course_id)
            
            print("📊 [Stage 4] Knowledge Graph Generation...")
            
            # Execute knowledge graph generation
            kg_result = self._execute_knowledge_graph_generation(
                course_id=course_id,
                finalized_content=approval_workflow.ffcs
            )
            
            # Complete the workflow
            approval_workflow.complete_course_development(kg_result)
            
            result = {
                "status": "course_development_completed",
                "stage": "knowledge_graph_generated",
                "course_id": course_id,
                "knowledge_graph": kg_result,
                "course_ready_for": "personalized_learning_tree_generation",
                "faculty_controls": {
                    "message": "🎉 Course development completed! Knowledge graph generated successfully.",
                    "completion_summary": {
                        "total_stages": 4,
                        "faculty_approvals": 3,
                        "knowledge_graph_nodes": kg_result.get('node_count', 0),
                        "knowledge_graph_relationships": kg_result.get('relationship_count', 0)
                    },
                    "next_available": "Personalized Learning Tree generation for individual learners"
                }
            }
            
            self.logger.end_operation(operation_id, success=True,
                                    course_id=course_id,
                                    result="course_development_completed")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="generate_knowledge_graph",
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id
            }
    
    def start_personalized_learning_workflow(self,
                                           course_id: str,
                                           learner_id: str,
                                           learner_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Stage 5: Personalized Learning Tree Generation (Separate Workflow).
        
        This runs independently after course development is complete.
        
        Args:
            course_id: Course identifier
            learner_id: Learner identifier
            learner_profile: Learner profile data
            
        Returns:
            Personalized learning tree generation results
        """
        operation_id = self.logger.start_operation("start_personalized_learning_workflow")
        
        try:
            self.logger.info("Starting personalized learning workflow",
                           course_id=course_id,
                           learner_id=learner_id)
            
            print("👤 [Stage 5] Personalized Learning Tree Generation...")
            
            # Execute learner subsystem workflow
            plt_result = run_cross_subsystem_workflow(
                subsystem=SubsystemType.LEARNER,
                course_id=course_id,
                learner_id=learner_id,
                learner_profile=learner_profile,
                workflow_type="personalized_learning"
            )
            
            result = {
                "status": "personalized_learning_completed",
                "stage": "plt_generated",
                "course_id": course_id,
                "learner_id": learner_id,
                "personalized_learning_tree": plt_result,
                "learner_controls": {
                    "message": "🎯 Personalized Learning Tree generated successfully!",
                    "learning_path": plt_result.get('learning_path'),
                    "adaptive_recommendations": plt_result.get('adaptive_recommendations'),
                    "learning_tree_summary": plt_result.get('summary')
                }
            }
            
            self.logger.end_operation(operation_id, success=True,
                                    course_id=course_id,
                                    learner_id=learner_id,
                                    result="plt_generated")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="start_personalized_learning_workflow",
                                             course_id=course_id,
                                             learner_id=learner_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id,
                "learner_id": learner_id
            }
    
    # Private helper methods
    def _execute_content_processing_and_structure_generation(self,
                                                            course_id: str,
                                                            faculty_id: str) -> Dict[str, Any]:
        """Execute content preprocessing and course mapping together."""
        self.logger.info("Executing content processing and structure generation",
                        course_id=course_id)
        
        # Execute content processing and structure generation via orchestrator
        result = run_cross_subsystem_workflow(
            subsystem=SubsystemType.CONTENT,
            course_id=course_id,
            faculty_id=faculty_id,
            workflow_type="content_processing_and_structure",
            services=["content_preprocessor", "course_mapper"]
        )
        
        return result
    
    def _execute_kli_application(self,
                               course_id: str,
                               confirmed_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Execute KLI application."""
        self.logger.info("Executing KLI application",
                        course_id=course_id)
        
        # Execute KLI application via orchestrator
        result = run_cross_subsystem_workflow(
            subsystem=SubsystemType.CONTENT,
            course_id=course_id,
            workflow_type="kli_application",
            structure_data=confirmed_structure
        )
        
        return result
    
    def _execute_knowledge_graph_generation(self,
                                          course_id: str,
                                          finalized_content: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge graph generation."""
        self.logger.info("Executing knowledge graph generation",
                        course_id=course_id)
        
        # Execute knowledge graph generation via orchestrator
        result = run_cross_subsystem_workflow(
            subsystem=SubsystemType.CONTENT,
            course_id=course_id,
            workflow_type="knowledge_graph_generation",
            content_data=finalized_content
        )
        
        return result
    
    def get_workflow_status(self, course_id: str) -> Dict[str, Any]:
        """Get the current status of a faculty approval workflow."""
        try:
            # Get approval workflow
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow:
                return {
                    "status": "not_found",
                    "course_id": course_id
                }
            
            return {
                "status": "active",
                "course_id": course_id,
                "faculty_id": approval_workflow.faculty_id,
                "current_stage": approval_workflow.current_stage.value,
                "last_updated": approval_workflow.last_updated,
                "course_setup_approved": approval_workflow.current_stage.value != "AWAITING_COURSE_APPROVAL",
                "structure_confirmed": approval_workflow.fccs is not None,
                "content_finalized": approval_workflow.ffcs is not None,
                "ready_for_plt": approval_workflow.current_stage.value == "COMPLETED"
            }
            
        except Exception as e:
            self.logger.log_error_with_context(e, operation="get_workflow_status",
                                             course_id=course_id)
            return {
                "status": "error",
                "error": str(e),
                "course_id": course_id
            }

# Global coordinator instance
faculty_approval_coordinator = FacultyApprovalCoordinator()

# Convenience functions for UI integration
def start_faculty_course_development(course_id: str, faculty_id: str, **kwargs) -> Dict[str, Any]:
    """Start a new manual faculty approval course development workflow."""
    return faculty_approval_coordinator.start_course_development(
        course_id=course_id,
        faculty_id=faculty_id,
        **kwargs
    )

def faculty_approve_course_setup(course_id: str, action: str, **kwargs) -> Dict[str, Any]:
    """Process faculty course setup approval."""
    return faculty_approval_coordinator.faculty_approve_course_setup(
        course_id=course_id,
        action=action,
        **kwargs
    )

def proceed_to_content_processing(course_id: str) -> Dict[str, Any]:
    """Execute content processing and structure generation stage."""
    return faculty_approval_coordinator.process_content_and_structure(course_id)

def faculty_confirm_structure(course_id: str, action: str, **kwargs) -> Dict[str, Any]:
    """Process faculty structure confirmation."""
    return faculty_approval_coordinator.faculty_confirm_course_structure(
        course_id=course_id,
        action=action,
        **kwargs
    )

def proceed_to_kli_application(course_id: str) -> Dict[str, Any]:
    """Execute KLI application stage."""
    return faculty_approval_coordinator.apply_kli_and_finalize_content(course_id)

def faculty_finalize_content(course_id: str, action: str, **kwargs) -> Dict[str, Any]:
    """Process faculty content finalization."""
    return faculty_approval_coordinator.faculty_finalize_course_content(
        course_id=course_id,
        action=action,
        **kwargs
    )

def proceed_to_knowledge_graph_generation(course_id: str) -> Dict[str, Any]:
    """Execute knowledge graph generation stage."""
    return faculty_approval_coordinator.generate_knowledge_graph(course_id)

def generate_personalized_learning_tree(course_id: str, learner_id: str, **kwargs) -> Dict[str, Any]:
    """Generate personalized learning tree for a learner."""
    return faculty_approval_coordinator.start_personalized_learning_workflow(
        course_id=course_id,
        learner_id=learner_id,
        **kwargs
    )
