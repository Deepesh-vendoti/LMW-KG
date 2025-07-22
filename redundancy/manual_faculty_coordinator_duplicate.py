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

class ManualFacultyCoordinator:
    """
    Manual faculty approval pipeline coordinator.
    
    Provides complete faculty control over course development with:
    - Manual approval gates at each critical stage
    - Faculty editing capabilities  
    - Comprehensive review and confirmation processes
    - Production-ready workflow state management
    """
    
    def __init__(self):
        self.logger = get_orchestrator_logger("manual_faculty_pipeline")
        
        # Default configurations
        self.default_course_id = get_default_course_id()
        self.default_learner_id = get_default_learner_id()
        
        self.logger.info("Initialized Manual Faculty Pipeline Coordinator")
    
    def start_course_workflow(self,
                            course_id: str = None,
                            faculty_id: str = None,
                            content_source: str = "elasticsearch",
                            **content_kwargs) -> Dict[str, Any]:
        """
        Start a new course workflow with faculty approval gates.
        
        Step 1: Course Manager → Pause for Faculty Approval
        Step 2: Content Processing → LO Generation → Pause for Faculty Approval
        
        Args:
            course_id: Course identifier
            faculty_id: Faculty member ID
            content_source: Source type ("pdf", "elasticsearch", "llm_generated")
            **content_kwargs: Additional content processing arguments
            
        Returns:
            Workflow start result with course initialization for faculty review
        """
        course_id = course_id or self.default_course_id
        operation_id = self.logger.start_operation("start_course_workflow")
        
        try:
            # Create faculty approval workflow
            approval_workflow = create_approval_workflow(course_id, faculty_id)
            
            self.logger.info("Starting course workflow with faculty approval gates",
                           course_id=course_id,
                           faculty_id=faculty_id,
                           content_source=content_source)
            
            # Step 1: Course Manager (course initialization and faculty workflow setup)
            print("📋 [Course Manager] Initializing course and faculty workflow...")
            course_manager_result = run_cross_subsystem_workflow(
                subsystem=SubsystemType.CONTENT,
                course_id=course_id,
                upload_type=content_source,
                faculty_id=faculty_id,
                workflow_type="course_initialization",
                **content_kwargs
            )
            
            # Set course initialization result in approval workflow
            approval_workflow.set_course_initialization(course_manager_result)
            
            result = {
                "status": "awaiting_faculty_approval",
                "stage": "course_initialization",
                "course_id": course_id,
                "faculty_id": faculty_id,
                "course_manager_result": course_manager_result,
                "next_action_required": "faculty_approve_course_initialization",
                "ui_data": {
                    "approval_stage": "🔵 Course Initialization Approval",
                    "instructions": "Course Manager has initialized the course and faculty workflow. Please approve to proceed to content processing.",
                    "actions": ["approve", "edit", "reject"],
                    "course_details": {
                        "course_id": course_id,
                        "faculty_id": faculty_id,
                        "content_source": content_source,
                        "initialization_status": "completed"
                    }
                }
            }
            
            self.logger.end_operation(operation_id, success=True,
                                    course_id=course_id,
                                    stage="awaiting_course_approval")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="start_course_workflow",
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "stage": "course_initialization",
                "course_id": course_id
            }
    
    def faculty_approve_course_initialization(self,
                                            course_id: str,
                                            action: str,
                                            faculty_comments: str = "") -> Dict[str, Any]:
        """
        Process faculty approval of course initialization.
        
        Args:
            course_id: Course identifier
            action: Faculty action ("approve", "reject")
            faculty_comments: Optional faculty feedback
            
        Returns:
            Result of approval action
        """
        operation_id = self.logger.start_operation("faculty_approve_course")
        
        try:
            # Get approval workflow
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow:
                raise ValueError(f"No approval workflow found for course {course_id}")
            
            self.logger.info("Processing faculty course approval",
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
                    "status": "course_approved",
                    "course_id": course_id,
                    "approval_result": approval_result
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="course_approved")
                
            elif faculty_action == FacultyAction.REJECT:
                result = {
                    "status": "rejected",
                    "course_id": course_id,
                    "faculty_comments": faculty_comments,
                    "approval_result": approval_result
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="rejected")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="faculty_approve_course",
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id
            }
    
    def process_content_after_course_approval(self, course_id: str) -> Dict[str, Any]:
        """
        Process content and generate LOs after course approval.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Result with draft LOs for faculty review
        """
        operation_id = self.logger.start_operation("process_content_after_course_approval")
        
        try:
            # Get approval workflow
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow:
                raise ValueError(f"No approval workflow found for course {course_id}")
            
            if approval_workflow.current_stage != FacultyWorkflowStage.COURSE_APPROVED:
                raise ValueError(f"Course must be approved before content processing. Current stage: {approval_workflow.current_stage}")
            
            self.logger.info("Processing content after course approval",
                           course_id=course_id)
            
            # Process content and generate draft LOs
            draft_los = self._process_content_and_generate_los(
                course_id=course_id,
                content_source="elasticsearch",  # Default for now
                faculty_id=approval_workflow.faculty_id
            )
            
            # Set draft LOs in approval workflow (moves to AWAITING_LO_APPROVAL)
            approval_workflow.set_draft_learning_objectives(draft_los)
            
            result = {
                "status": "awaiting_faculty_approval",
                "stage": "lo_approval",
                "course_id": course_id,
                "draft_learning_objectives": draft_los,
                "next_action_required": "faculty_review_and_approve_los",
                "ui_data": {
                    "approval_stage": "🔵 Learning Objectives Approval",
                    "instructions": "Please review and approve the generated learning objectives. You can edit them if necessary.",
                    "actions": ["approve", "edit", "reject"]
                }
            }
            
            self.logger.end_operation(operation_id, success=True,
                                    course_id=course_id,
                                    lo_count=len(draft_los),
                                    stage="awaiting_lo_approval")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="process_content_after_course_approval",
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id
            }
    
    def faculty_approve_learning_objectives(self,
                                          course_id: str,
                                          action: str,
                                          edited_los: Optional[List[Dict[str, Any]]] = None,
                                          faculty_comments: str = "") -> Dict[str, Any]:
        """
        Process faculty approval of learning objectives.
        
        If approved, automatically proceeds to structure generation and pauses for confirmation.
        
        Args:
            course_id: Course identifier
            action: Faculty action ("approve", "edit", "reject")
            edited_los: Faculty-edited LOs (if provided)
            faculty_comments: Optional faculty feedback
            
        Returns:
            Result of approval action and next steps
        """
        operation_id = self.logger.start_operation("faculty_approve_los")
        
        try:
            # Get approval workflow
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow:
                raise ValueError(f"No approval workflow found for course {course_id}")
            
            self.logger.info("Processing faculty LO approval",
                           course_id=course_id,
                           action=action,
                           has_edits=bool(edited_los))
            
            # Process faculty action
            faculty_action = FacultyAction(action.lower())
            approval_result = approval_workflow.faculty_approve_los(
                action=faculty_action,
                edited_los=edited_los,
                faculty_comments=faculty_comments
            )
            
            if faculty_action == FacultyAction.APPROVE:
                # FACD generated, proceed to structure generation
                self.logger.info("Faculty approved LOs, proceeding to structure generation",
                               course_id=course_id)
                
                # Automatically generate course structure
                draft_structure = self._generate_course_structure(
                    course_id=course_id,
                    facd=approval_workflow.facd
                )
                
                # Set draft structure (moves to AWAITING_STRUCTURE_CONFIRMATION)
                approval_workflow.set_draft_course_structure(draft_structure)
                
                result = {
                    "status": "awaiting_faculty_confirmation", 
                    "stage": "structure_confirmation",
                    "course_id": course_id,
                    "facd_generated": True,
                    "draft_course_structure": draft_structure,
                    "next_action_required": "faculty_review_and_confirm_structure",
                    "ui_data": {
                        "approval_stage": "🟡 Course Structure Confirmation",
                        "instructions": "Please review the complete course structure (LO→KC→LP→IM→Resources) and confirm or edit as needed.",
                        "actions": ["confirm", "edit", "reject"]
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="facd_generated_structure_ready")
                
            elif faculty_action == FacultyAction.EDIT:
                result = {
                    "status": "awaiting_faculty_approval",
                    "stage": "lo_approval", 
                    "course_id": course_id,
                    "draft_learning_objectives": approval_workflow.draft_los,
                    "faculty_edits_applied": True,
                    "next_action_required": "faculty_review_and_approve_los",
                    "ui_data": {
                        "approval_stage": "🔵 Learning Objectives Approval (Edited)",
                        "instructions": "Your edits have been applied. Please review and approve.",
                        "actions": ["approve", "edit", "reject"]
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="edited_resubmission")
                
            elif faculty_action == FacultyAction.REJECT:
                result = {
                    "status": "rejected",
                    "stage": "lo_approval",
                    "course_id": course_id,
                    "faculty_comments": faculty_comments,
                    "next_action_required": "regenerate_learning_objectives",
                    "ui_data": {
                        "approval_stage": "🔵 Learning Objectives Rejected",
                        "instructions": "Learning objectives rejected. System will regenerate new LOs.",
                        "actions": ["regenerate"]
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="rejected_regeneration_needed")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="faculty_approve_los",
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
        Process faculty confirmation of course structure.
        
        If confirmed, automatically proceeds to KG generation and pauses for finalization.
        
        Args:
            course_id: Course identifier
            action: Faculty action ("confirm", "edit", "reject")
            edited_structure: Faculty-edited structure (if provided)
            faculty_comments: Optional faculty feedback
            
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
                # FCCS generated, proceed to KG generation
                self.logger.info("Faculty confirmed structure, proceeding to KG generation",
                               course_id=course_id)
                
                # Automatically generate knowledge graph
                draft_kg = self._generate_knowledge_graph(
                    course_id=course_id,
                    fccs=approval_workflow.fccs
                )
                
                # Set draft KG (moves to AWAITING_KG_FINALIZATION)
                approval_workflow.set_draft_knowledge_graph(draft_kg)
                
                result = {
                    "status": "awaiting_faculty_finalization",
                    "stage": "kg_finalization", 
                    "course_id": course_id,
                    "fccs_generated": True,
                    "draft_knowledge_graph": draft_kg,
                    "next_action_required": "faculty_review_and_finalize_kg",
                    "ui_data": {
                        "approval_stage": "🟢 Knowledge Graph Finalization",
                        "instructions": "Please review the generated knowledge graph and finalize. This will lock the course structure.",
                        "actions": ["finalize", "edit", "reject"]
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="fccs_generated_kg_ready")
                
            elif faculty_action == FacultyAction.EDIT:
                result = {
                    "status": "awaiting_faculty_confirmation",
                    "stage": "structure_confirmation",
                    "course_id": course_id,
                    "draft_course_structure": approval_workflow.draft_structure,
                    "faculty_edits_applied": True,
                    "next_action_required": "faculty_review_and_confirm_structure",
                    "ui_data": {
                        "approval_stage": "🟡 Course Structure Confirmation (Edited)",
                        "instructions": "Your edits have been applied. Please review and confirm.",
                        "actions": ["confirm", "edit", "reject"]
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="edited_resubmission")
                
            elif faculty_action == FacultyAction.REJECT:
                result = {
                    "status": "rejected",
                    "stage": "structure_confirmation",
                    "course_id": course_id,
                    "faculty_comments": faculty_comments,
                    "next_action_required": "regenerate_course_structure",
                    "ui_data": {
                        "approval_stage": "🟡 Course Structure Rejected",
                        "instructions": "Course structure rejected. System will regenerate structure.",
                        "actions": ["regenerate"]
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
    
    def faculty_finalize_knowledge_graph(self,
                                       course_id: str,
                                       action: str,
                                       edited_kg: Optional[Dict[str, Any]] = None,
                                       faculty_comments: str = "") -> Dict[str, Any]:
        """
        Process faculty finalization of knowledge graph.
        
        If finalized, course structure is locked and ready for learner-triggered PLT generation.
        
        Args:
            course_id: Course identifier
            action: Faculty action ("finalize", "edit", "reject")
            edited_kg: Faculty-edited KG (if provided)
            faculty_comments: Optional faculty feedback
            
        Returns:
            Result of finalization action and next steps
        """
        operation_id = self.logger.start_operation("faculty_finalize_kg")
        
        try:
            # Get approval workflow
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow:
                raise ValueError(f"No approval workflow found for course {course_id}")
            
            self.logger.info("Processing faculty KG finalization",
                           course_id=course_id,
                           action=action,
                           has_edits=bool(edited_kg))
            
            # Process faculty action
            faculty_action = FacultyAction(action.lower())
            finalization_result = approval_workflow.faculty_finalize_kg(
                action=faculty_action,
                edited_kg=edited_kg,
                faculty_comments=faculty_comments
            )
            
            if faculty_action == FacultyAction.FINALIZE:
                # FFCS generated, workflow complete - ready for learner-triggered PLT generation
                self.logger.info("Faculty finalized KG, course structure locked - ready for learner PLT requests",
                               course_id=course_id)
                
                result = {
                    "status": "course_structure_finalized",
                    "stage": "ready_for_learner_plt",
                    "course_id": course_id,
                    "ffcs_generated": True,
                    "ready_for_learner_plt": True,
                    "next_action_required": "learner_triggered_plt_generation",
                    "ui_data": {
                        "approval_stage": "✅ Faculty Workflow Complete",
                        "instructions": "Knowledge graph finalized! Course structure is now locked. PLT can be generated when learners request personalized learning paths.",
                        "actions": ["await_learner_requests"]
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="ffcs_generated_ready_for_learner_plt")
                
            elif faculty_action == FacultyAction.EDIT:
                result = {
                    "status": "awaiting_faculty_finalization",
                    "stage": "kg_finalization",
                    "course_id": course_id,
                    "draft_knowledge_graph": approval_workflow.draft_kg,
                    "faculty_edits_applied": True,
                    "next_action_required": "faculty_review_and_finalize_kg",
                    "ui_data": {
                        "approval_stage": "🟢 Knowledge Graph Finalization (Edited)",
                        "instructions": "Your edits have been applied. Please review and finalize.",
                        "actions": ["finalize", "edit", "reject"]
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="edited_resubmission")
                
            elif faculty_action == FacultyAction.REJECT:
                result = {
                    "status": "rejected",
                    "stage": "kg_finalization",
                    "course_id": course_id,
                    "faculty_comments": faculty_comments,
                    "next_action_required": "regenerate_knowledge_graph",
                    "ui_data": {
                        "approval_stage": "🟢 Knowledge Graph Rejected",
                        "instructions": "Knowledge graph rejected. System will regenerate KG.",
                        "actions": ["regenerate"]
                    }
                }
                
                self.logger.end_operation(operation_id, success=True,
                                        course_id=course_id,
                                        result="rejected_regeneration_needed")
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="faculty_finalize_kg",
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id
            }
    
    def generate_plt_for_learner(self,
                               course_id: str,
                               learner_id: str,
                               learner_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate PLT for a specific learner AFTER faculty has finalized the course structure.
        
        This is learner-triggered, not automatic.
        
        Args:
            course_id: Course identifier  
            learner_id: Learner identifier
            learner_context: Learner profile, preferences, history, etc.
            
        Returns:
            PLT generation result
        """
        operation_id = self.logger.start_operation("generate_plt_for_learner")
        
        try:
            # Verify course structure is finalized
            approval_workflow = get_approval_workflow(course_id)
            if not approval_workflow or not approval_workflow.can_proceed_to_plt_generation():
                raise ValueError(f"Course {course_id} structure not finalized. Faculty must complete approval workflow first.")
            
            self.logger.info("Generating PLT for learner",
                           course_id=course_id,
                           learner_id=learner_id,
                           has_context=bool(learner_context))
            
            # Execute PLT generation via orchestrator with learner context
            plt_result = run_cross_subsystem_workflow(
                subsystem=SubsystemType.LEARNER,
                course_id=course_id,
                learner_id=learner_id,
                workflow_type="personalized_learning",
                learner_context=learner_context or {},
                ffcs_data=approval_workflow.ffcs
            )
            
            result = {
                "status": "plt_generated",
                "course_id": course_id,
                "learner_id": learner_id,
                "plt_generated": True,
                "plt_result": plt_result,
                "learner_context": learner_context,
                "based_on_ffcs": bool(approval_workflow.ffcs)
            }
            
            self.logger.end_operation(operation_id, success=True,
                                    course_id=course_id,
                                    learner_id=learner_id)
            
            return result
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="generate_plt_for_learner",
                                             course_id=course_id,
                                             learner_id=learner_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id,
                "learner_id": learner_id
            }
    
    def get_workflow_status(self, course_id: str) -> Dict[str, Any]:
        """Get current status of faculty approval workflow."""
        approval_workflow = get_approval_workflow(course_id)
        if not approval_workflow:
            return {
                "status": "not_found",
                "course_id": course_id,
                "message": "No workflow found for this course"
            }
        
        return approval_workflow.get_approval_summary()
    
    # Private helper methods for pipeline stages
    def _process_content_and_generate_los(self,
                                        course_id: str,
                                        content_source: str,
                                        faculty_id: str = None,
                                        **kwargs) -> List[Dict[str, Any]]:
        """Process content and generate draft learning objectives."""
        self.logger.info("Processing content and generating LOs",
                        course_id=course_id,
                        source=content_source)
        
        # Step 1: Course Manager (course initialization and faculty workflow setup)
        print("📋 [Course Manager] Initializing course and faculty workflow...")
        course_manager_result = run_cross_subsystem_workflow(
            subsystem=SubsystemType.CONTENT,
            course_id=course_id,
            upload_type=content_source,
            faculty_id=faculty_id,
            workflow_type="course_initialization",
            **kwargs
        )
        
        # Step 2: Content Processing + LO Generation
        print("📚 [Content Processing] Processing content and generating LOs...")
        result = run_cross_subsystem_workflow(
            subsystem=SubsystemType.CONTENT,
            course_id=course_id,
            upload_type=content_source,
            workflow_type="lo_generation_only",
            **kwargs
        )
        
        # Extract learning objectives from result
        # This would be the output from the course_mapper (Stage 1) service
        draft_los = result.get("learning_objectives", [])
        
        return draft_los
    
    def _generate_course_structure(self,
                                 course_id: str,
                                 facd: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete course structure from FACD."""
        self.logger.info("Generating course structure from FACD",
                        course_id=course_id)
        
        # Execute structure generation (Stage 2) via orchestrator
        result = run_cross_subsystem_workflow(
            subsystem=SubsystemType.CONTENT,
            course_id=course_id,
            workflow_type="structure_generation",
            facd_data=facd
        )
        
        return result
    
    def _generate_knowledge_graph(self,
                                course_id: str,
                                fccs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate knowledge graph from FCCS."""
        self.logger.info("Generating knowledge graph from FCCS",
                        course_id=course_id)
        
        # Execute KG generation via orchestrator
        result = run_cross_subsystem_workflow(
            subsystem=SubsystemType.CONTENT,
            course_id=course_id,
            workflow_type="kg_generation",
            fccs_data=fccs
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
                "has_facd": approval_workflow.facd is not None,
                "has_fccs": approval_workflow.fccs is not None,
                "has_ffcs": approval_workflow.ffcs is not None,
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
manual_faculty_coordinator = ManualFacultyCoordinator()

# Convenience functions for UI integration
def start_faculty_workflow(course_id: str, faculty_id: str, **kwargs) -> Dict[str, Any]:
    """Start a new manual faculty approval workflow."""
    return manual_faculty_coordinator.start_course_workflow(
        course_id=course_id,
        faculty_id=faculty_id,
        **kwargs
    )

def faculty_approve_course(course_id: str, action: str, **kwargs) -> Dict[str, Any]:
    """Process faculty course approval action."""
    return manual_faculty_coordinator.faculty_approve_course_initialization(
        course_id=course_id,
        action=action,
        **kwargs
    )

def process_content_after_course_approval(course_id: str) -> Dict[str, Any]:
    """Execute content processing after course approval."""
    return manual_faculty_coordinator.process_content_after_course_approval(course_id)

def faculty_approve(course_id: str, action: str, **kwargs) -> Dict[str, Any]:
    """Process faculty learning objectives approval."""
    return manual_faculty_coordinator.faculty_approve_learning_objectives(
        course_id=course_id,
        action=action,
        **kwargs
    )

def faculty_confirm(course_id: str, action: str, **kwargs) -> Dict[str, Any]:
    """Process faculty structure confirmation."""
    return manual_faculty_coordinator.faculty_confirm_course_structure(
        course_id=course_id,
        action=action,
        **kwargs
    )

def faculty_finalize(course_id: str, action: str, **kwargs) -> Dict[str, Any]:
    """Process faculty knowledge graph finalization."""
    return manual_faculty_coordinator.faculty_finalize_knowledge_graph(
        course_id=course_id,
        action=action,
        **kwargs
    ) 