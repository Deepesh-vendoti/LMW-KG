"""
Faculty Approval States Management for LangGraph Knowledge Graph System

Handles the three-tier faculty workflow:
1. APPROVE → FACD (Faculty Approved Course Details)
2. CONFIRM → FCCS (Faculty Confirmed Course Structure)  
3. FINALIZE → FFCS (Faculty Finalized Course Structure)
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
from pathlib import Path
import sys
import json
import pickle

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator.state import UniversalState, SubsystemType
from config.loader import config
from utils.logging import get_orchestrator_logger

class FacultyWorkflowStage(str, Enum):
    """Faculty workflow stages in sequence."""
    
    # Stage 0: Course Initialization (requires faculty approval)
    AWAITING_COURSE_APPROVAL = "awaiting_course_approval"
    COURSE_APPROVED = "course_approved"  # Course initialized
    
    # Stage 1: Content Processing (automatic)
    CONTENT_PROCESSING = "content_processing"
    
    # Stage 2: Learning Objectives Review
    AWAITING_LO_APPROVAL = "awaiting_lo_approval"
    LO_APPROVED = "lo_approved"  # FACD generated
    
    # Stage 3: Course Structure Review  
    AWAITING_STRUCTURE_CONFIRMATION = "awaiting_structure_confirmation"
    STRUCTURE_CONFIRMED = "structure_confirmed"  # FCCS generated
    
    # Stage 4: Knowledge Graph Review
    AWAITING_KG_FINALIZATION = "awaiting_kg_finalization" 
    KG_FINALIZED = "kg_finalized"  # FFCS generated
    
    # Final automated stage
    PLT_GENERATION = "plt_generation"
    COMPLETED = "completed"

class FacultyAction(str, Enum):
    """Faculty actions at each stage."""
    APPROVE = "approve"        # Stage 1: LO approval
    CONFIRM = "confirm"        # Stage 2: Structure confirmation
    FINALIZE = "finalize"      # Stage 3: KG finalization
    EDIT = "edit"             # Edit and re-submit for review
    REJECT = "reject"         # Reject and send back

class ApprovalStatus(str, Enum):
    """Status of approval processes."""
    PENDING = "pending"
    APPROVED = "approved"
    CONFIRMED = "confirmed" 
    FINALIZED = "finalized"
    REJECTED = "rejected"
    EDITED = "edited"

class FacultyApprovalState:
    """
    Manages faculty approval state for a course workflow.
    
    Tracks progression through the three-tier approval process with
    persistent state management and editing capabilities.
    """
    
    def __init__(self, course_id: str, faculty_id: str = None):
        self.course_id = course_id
        self.faculty_id = faculty_id or "default_faculty"
        self.logger = get_orchestrator_logger("faculty_approval")
        
        # Workflow state
        self.current_stage = FacultyWorkflowStage.AWAITING_COURSE_APPROVAL
        self.approval_history: List[Dict[str, Any]] = []
        
        # Stage-specific data
        self.course_initialization: Dict[str, Any] = {}  # Course Manager result
        
        self.draft_los: List[Dict[str, Any]] = []
        self.facd: Dict[str, Any] = {}  # Faculty Approved Course Details
        
        self.draft_structure: Dict[str, Any] = {}
        self.fccs: Dict[str, Any] = {}  # Faculty Confirmed Course Structure
        
        self.draft_kg: Dict[str, Any] = {}
        self.ffcs: Dict[str, Any] = {}  # Faculty Finalized Course Structure
        
        # Timestamps
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        self.logger.info("Initialized faculty approval workflow",
                        course_id=course_id,
                        faculty_id=self.faculty_id,
                        stage=self.current_stage)
    
    def set_course_initialization(self, course_init_result: Dict[str, Any]) -> None:
        """
        Set course initialization result and move to course approval stage.
        
        Args:
            course_init_result: Course Manager initialization result
        """
        self.course_initialization = course_init_result
        self.current_stage = FacultyWorkflowStage.AWAITING_COURSE_APPROVAL
        self.last_updated = datetime.now()
        
        # Save to persistent storage
        approval_state_manager.save_workflow(self.course_id)
        
        self.logger.info("Course initialization set, awaiting faculty approval",
                        course_id=self.course_id,
                        stage=self.current_stage)
    
    def faculty_approve_course_initialization(self,
                                            action: FacultyAction,
                                            faculty_comments: str = "") -> Dict[str, Any]:
        """
        Process faculty approval of course initialization.
        
        Args:
            action: Faculty action (APPROVE, REJECT)
            faculty_comments: Optional faculty feedback
            
        Returns:
            Result of approval action
        """
        if self.current_stage != FacultyWorkflowStage.AWAITING_COURSE_APPROVAL:
            raise ValueError(f"Invalid stage for course approval: {self.current_stage}")
        
        approval_record = {
            "stage": "course_initialization",
            "action": action,
            "timestamp": datetime.now(),
            "faculty_id": self.faculty_id,
            "comments": faculty_comments,
            "course_init_result": self.course_initialization
        }
        
        if action == FacultyAction.APPROVE:
            self.current_stage = FacultyWorkflowStage.COURSE_APPROVED
            approval_record["result"] = "course_approved"
            
            self.logger.info("Faculty approved course initialization",
                           course_id=self.course_id,
                           faculty_id=self.faculty_id)
            
        elif action == FacultyAction.REJECT:
            approval_record["result"] = "rejected"
            # Stay in AWAITING_COURSE_APPROVAL stage
            
        self.approval_history.append(approval_record)
        self.last_updated = datetime.now()
        
        # Save to persistent storage
        approval_state_manager.save_workflow(self.course_id)
        
        return approval_record
    
    def set_draft_learning_objectives(self, draft_los: List[Dict[str, Any]]) -> None:
        """
        Set draft learning objectives and move to LO approval stage.
        
        Args:
            draft_los: List of generated learning objectives
        """
        self.draft_los = draft_los
        self.current_stage = FacultyWorkflowStage.AWAITING_LO_APPROVAL
        self.last_updated = datetime.now()
        
        # Save to persistent storage
        approval_state_manager.save_workflow(self.course_id)
        
        self.logger.info("Draft LOs set, awaiting faculty approval",
                        course_id=self.course_id,
                        lo_count=len(draft_los),
                        stage=self.current_stage)
    
    def faculty_approve_los(self, 
                           action: FacultyAction,
                           edited_los: Optional[List[Dict[str, Any]]] = None,
                           faculty_comments: str = "") -> Dict[str, Any]:
        """
        Process faculty approval of learning objectives.
        
        Args:
            action: Faculty action (APPROVE, EDIT, REJECT)
            edited_los: Faculty-edited LOs (if action is EDIT or APPROVE)
            faculty_comments: Optional faculty feedback
            
        Returns:
            Result of approval action
        """
        if self.current_stage != FacultyWorkflowStage.AWAITING_LO_APPROVAL:
            raise ValueError(f"Invalid stage for LO approval: {self.current_stage}")
        
        approval_record = {
            "stage": "lo_approval",
            "action": action,
            "timestamp": datetime.now(),
            "faculty_id": self.faculty_id,
            "comments": faculty_comments,
            "original_los": self.draft_los.copy(),
            "edited_los": edited_los
        }
        
        if action == FacultyAction.APPROVE:
            # Use edited LOs if provided, otherwise use originals
            approved_los = edited_los if edited_los else self.draft_los
            
            # Generate FACD (Faculty Approved Course Details)
            self.facd = {
                "course_id": self.course_id,
                "approved_learning_objectives": approved_los,
                "approval_timestamp": datetime.now(),
                "faculty_id": self.faculty_id,
                "approval_comments": faculty_comments,
                "facd_status": ApprovalStatus.APPROVED
            }
            
            self.current_stage = FacultyWorkflowStage.LO_APPROVED
            approval_record["result"] = "facd_generated"
            
            self.logger.info("Faculty approved LOs, FACD generated",
                           course_id=self.course_id,
                           faculty_id=self.faculty_id,
                           lo_count=len(approved_los))
            
        elif action == FacultyAction.EDIT:
            # Faculty edited, need re-submission
            if edited_los:
                self.draft_los = edited_los
            approval_record["result"] = "edited_resubmission_required"
            # Stay in AWAITING_LO_APPROVAL stage
            
        elif action == FacultyAction.REJECT:
            approval_record["result"] = "rejected_regeneration_required"
            # Stay in AWAITING_LO_APPROVAL stage
            
        self.approval_history.append(approval_record)
        self.last_updated = datetime.now()
        
        # Save to persistent storage
        approval_state_manager.save_workflow(self.course_id)
        
        return approval_record
    
    def set_draft_course_structure(self, draft_structure: Dict[str, Any]) -> None:
        """
        Set draft course structure and move to structure confirmation stage.
        
        Args:
            draft_structure: Complete course structure (LO→KC→LP→IM→Resources)
        """
        if self.current_stage != FacultyWorkflowStage.LO_APPROVED:
            raise ValueError(f"Must have approved LOs before setting structure. Current stage: {self.current_stage}")
        
        self.draft_structure = draft_structure
        self.current_stage = FacultyWorkflowStage.AWAITING_STRUCTURE_CONFIRMATION
        self.last_updated = datetime.now()
        
        self.logger.info("Draft structure set, awaiting faculty confirmation",
                        course_id=self.course_id,
                        stage=self.current_stage)
    
    def faculty_confirm_structure(self,
                                action: FacultyAction,
                                edited_structure: Optional[Dict[str, Any]] = None,
                                faculty_comments: str = "") -> Dict[str, Any]:
        """
        Process faculty confirmation of course structure.
        
        Args:
            action: Faculty action (CONFIRM, EDIT, REJECT)
            edited_structure: Faculty-edited structure (if action is EDIT or CONFIRM)
            faculty_comments: Optional faculty feedback
            
        Returns:
            Result of confirmation action
        """
        if self.current_stage != FacultyWorkflowStage.AWAITING_STRUCTURE_CONFIRMATION:
            raise ValueError(f"Invalid stage for structure confirmation: {self.current_stage}")
        
        confirmation_record = {
            "stage": "structure_confirmation",
            "action": action,
            "timestamp": datetime.now(),
            "faculty_id": self.faculty_id,
            "comments": faculty_comments,
            "original_structure": self.draft_structure.copy(),
            "edited_structure": edited_structure
        }
        
        if action == FacultyAction.CONFIRM:
            # Use edited structure if provided, otherwise use original
            confirmed_structure = edited_structure if edited_structure else self.draft_structure
            
            # Generate FCCS (Faculty Confirmed Course Structure)
            self.fccs = {
                "course_id": self.course_id,
                "confirmed_structure": confirmed_structure,
                "confirmation_timestamp": datetime.now(),
                "faculty_id": self.faculty_id,
                "confirmation_comments": faculty_comments,
                "fccs_status": ApprovalStatus.CONFIRMED,
                "based_on_facd": self.facd
            }
            
            self.current_stage = FacultyWorkflowStage.STRUCTURE_CONFIRMED
            confirmation_record["result"] = "fccs_generated"
            
            self.logger.info("Faculty confirmed structure, FCCS generated",
                           course_id=self.course_id,
                           faculty_id=self.faculty_id)
            
        elif action == FacultyAction.EDIT:
            if edited_structure:
                self.draft_structure = edited_structure
            confirmation_record["result"] = "edited_resubmission_required"
            
        elif action == FacultyAction.REJECT:
            confirmation_record["result"] = "rejected_regeneration_required"
            
        self.approval_history.append(confirmation_record)
        self.last_updated = datetime.now()
        
        return confirmation_record
    
    def set_draft_knowledge_graph(self, draft_kg: Dict[str, Any]) -> None:
        """
        Set draft knowledge graph and move to KG finalization stage.
        
        Args:
            draft_kg: Generated knowledge graph
        """
        if self.current_stage != FacultyWorkflowStage.STRUCTURE_CONFIRMED:
            raise ValueError(f"Must have confirmed structure before setting KG. Current stage: {self.current_stage}")
        
        self.draft_kg = draft_kg
        self.current_stage = FacultyWorkflowStage.AWAITING_KG_FINALIZATION
        self.last_updated = datetime.now()
        
        self.logger.info("Draft KG set, awaiting faculty finalization",
                        course_id=self.course_id,
                        stage=self.current_stage)
    
    def faculty_finalize_kg(self,
                          action: FacultyAction,
                          edited_kg: Optional[Dict[str, Any]] = None,
                          faculty_comments: str = "") -> Dict[str, Any]:
        """
        Process faculty finalization of knowledge graph.
        
        Args:
            action: Faculty action (FINALIZE, EDIT, REJECT)
            edited_kg: Faculty-edited KG (if action is EDIT or FINALIZE)
            faculty_comments: Optional faculty feedback
            
        Returns:
            Result of finalization action
        """
        if self.current_stage != FacultyWorkflowStage.AWAITING_KG_FINALIZATION:
            raise ValueError(f"Invalid stage for KG finalization: {self.current_stage}")
        
        finalization_record = {
            "stage": "kg_finalization",
            "action": action,
            "timestamp": datetime.now(),
            "faculty_id": self.faculty_id,
            "comments": faculty_comments,
            "original_kg": self.draft_kg.copy(),
            "edited_kg": edited_kg
        }
        
        if action == FacultyAction.FINALIZE:
            # Use edited KG if provided, otherwise use original
            finalized_kg = edited_kg if edited_kg else self.draft_kg
            
            # Generate FFCS (Faculty Finalized Course Structure)
            self.ffcs = {
                "course_id": self.course_id,
                "finalized_knowledge_graph": finalized_kg,
                "finalization_timestamp": datetime.now(),
                "faculty_id": self.faculty_id,
                "finalization_comments": faculty_comments,
                "ffcs_status": ApprovalStatus.FINALIZED,
                "based_on_fccs": self.fccs,
                "workflow_complete": True
            }
            
            self.current_stage = FacultyWorkflowStage.KG_FINALIZED
            finalization_record["result"] = "ffcs_generated_workflow_complete"
            
            self.logger.info("Faculty finalized KG, FFCS generated - workflow complete",
                           course_id=self.course_id,
                           faculty_id=self.faculty_id)
            
        elif action == FacultyAction.EDIT:
            if edited_kg:
                self.draft_kg = edited_kg
            finalization_record["result"] = "edited_resubmission_required"
            
        elif action == FacultyAction.REJECT:
            finalization_record["result"] = "rejected_regeneration_required"
            
        self.approval_history.append(finalization_record)
        self.last_updated = datetime.now()
        
        return finalization_record
    
    def can_proceed_to_plt_generation(self) -> bool:
        """Check if workflow is ready for automated PLT generation."""
        return self.current_stage == FacultyWorkflowStage.KG_FINALIZED
    
    def get_approval_summary(self) -> Dict[str, Any]:
        """Get complete approval workflow summary."""
        return {
            "course_id": self.course_id,
            "faculty_id": self.faculty_id,
            "current_stage": self.current_stage,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "approval_history": self.approval_history,
            "has_facd": bool(self.facd),
            "has_fccs": bool(self.fccs),
            "has_ffcs": bool(self.ffcs),
            "ready_for_plt": self.can_proceed_to_plt_generation()
        }

# Global approval state manager
class ApprovalStateManager:
    """Manages approval states for multiple courses with persistent storage."""
    
    def __init__(self):
        self.active_workflows: Dict[str, FacultyApprovalState] = {}
        self.logger = get_orchestrator_logger("approval_state_manager")
        self.storage_dir = Path("logs/approval_workflows")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing workflows from storage
        self._load_workflows()
    
    def _get_workflow_file(self, course_id: str) -> Path:
        """Get file path for workflow storage."""
        return self.storage_dir / f"{course_id}_workflow.pkl"
    
    def _save_workflow(self, workflow: FacultyApprovalState) -> None:
        """Save workflow to persistent storage."""
        try:
            workflow_file = self._get_workflow_file(workflow.course_id)
            with open(workflow_file, 'wb') as f:
                pickle.dump(workflow, f)
            self.logger.info("Saved workflow to storage", course_id=workflow.course_id)
        except Exception as e:
            self.logger.error("Failed to save workflow", course_id=workflow.course_id, error=str(e))
    
    def _load_workflows(self) -> None:
        """Load all workflows from persistent storage."""
        try:
            for workflow_file in self.storage_dir.glob("*_workflow.pkl"):
                course_id = workflow_file.stem.replace("_workflow", "")
                with open(workflow_file, 'rb') as f:
                    workflow = pickle.load(f)
                    self.active_workflows[course_id] = workflow
                self.logger.info("Loaded workflow from storage", course_id=course_id)
        except Exception as e:
            self.logger.error("Failed to load workflows", error=str(e))
    
    def create_workflow(self, course_id: str, faculty_id: str = None) -> FacultyApprovalState:
        """Create new approval workflow for a course."""
        if course_id in self.active_workflows:
            self.logger.warning("Workflow already exists for course", course_id=course_id)
            return self.active_workflows[course_id]
        
        workflow = FacultyApprovalState(course_id, faculty_id)
        self.active_workflows[course_id] = workflow
        
        # Save to persistent storage
        self._save_workflow(workflow)
        
        self.logger.info("Created new approval workflow", course_id=course_id)
        return workflow
    
    def get_workflow(self, course_id: str) -> Optional[FacultyApprovalState]:
        """Get existing workflow for a course."""
        workflow = self.active_workflows.get(course_id)
        if workflow:
            return workflow
        
        # Try to load from storage if not in memory
        try:
            workflow_file = self._get_workflow_file(course_id)
            if workflow_file.exists():
                with open(workflow_file, 'rb') as f:
                    workflow = pickle.load(f)
                    self.active_workflows[course_id] = workflow
                    self.logger.info("Loaded workflow from storage", course_id=course_id)
                    return workflow
        except Exception as e:
            self.logger.error("Failed to load workflow from storage", course_id=course_id, error=str(e))
        
        return None
    
    def save_workflow(self, course_id: str) -> None:
        """Explicitly save a workflow to storage."""
        workflow = self.active_workflows.get(course_id)
        if workflow:
            self._save_workflow(workflow)
    
    def get_workflows_by_stage(self, stage: FacultyWorkflowStage) -> List[FacultyApprovalState]:
        """Get all workflows currently at a specific stage."""
        return [workflow for workflow in self.active_workflows.values() 
                if workflow.current_stage == stage]

# Global instance
approval_state_manager = ApprovalStateManager()

# Convenience functions
def create_approval_workflow(course_id: str, faculty_id: str = None) -> FacultyApprovalState:
    """Create new faculty approval workflow."""
    return approval_state_manager.create_workflow(course_id, faculty_id)

def get_approval_workflow(course_id: str) -> Optional[FacultyApprovalState]:
    """Get existing faculty approval workflow."""
    return approval_state_manager.get_workflow(course_id) 