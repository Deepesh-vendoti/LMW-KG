"""
Course Manager Service - Content Subsystem

Handles course initialization and faculty input collection.
This is the FIRST step in the faculty approval workflow.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from pathlib import Path

from orchestrator.state import UniversalState, ServiceStatus, SubsystemType
from utils.database_connections import get_database_manager

logger = logging.getLogger(__name__)

class CourseManagerService:
    """
    Course Manager microservice for the content subsystem.
    
    Responsibilities:
    - Collect faculty inputs for course design
    - Manage course initialization workflow
    - Handle content source selection
    - Store course configuration in database
    """
    
    def __init__(self):
        self.service_id = "course_manager"
        self.subsystem = SubsystemType.CONTENT
        self.db_manager = get_database_manager()
    
    def __call__(self, state: UniversalState) -> UniversalState:
        """
        Main entry point for course management.
        Collects faculty inputs and initializes course configuration.
        """
        print(f"📋 [Course Manager] Initializing course and faculty workflow...")
        
        try:
            # Extract required inputs
            course_id = state.get("course_id", "default_course")
            faculty_id = state.get("faculty_id", "auto_faculty")  # Default for automatic mode
            workflow_type = state.get("workflow_type", "course_initialization")
            
            # Determine if this is automatic mode (no faculty_id provided)
            is_automatic_mode = faculty_id == "auto_faculty" or not state.get("faculty_id")
            
            if workflow_type == "course_initialization":
                # This is the FIRST step - collect faculty inputs
                course_config = self._collect_faculty_inputs(state)
                
                # Store course configuration in database
                storage_result = self._store_course_configuration(course_config, course_id, faculty_id)
                
                # Generate course initialization result
                initialization_result = {
                    "course_id": course_id,
                    "faculty_id": faculty_id,
                    "course_config": course_config,
                    "storage_result": storage_result,
                    "initialization_timestamp": datetime.now().isoformat(),
                    "status": "auto_approved" if is_automatic_mode else "awaiting_faculty_approval"
                }
                
                # Update state with results
                state.update({
                    "course_config": course_config,
                    "course_manager_result": initialization_result,
                    "faculty_inputs_collected": True,
                    "is_automatic_mode": is_automatic_mode,
                    "next_step": "content_preprocessor" if is_automatic_mode else "faculty_approve_course_initialization"
                })
                
                # Mark service as completed
                if "service_statuses" not in state:
                    state["service_statuses"] = {}
                state["service_statuses"][self.service_id] = ServiceStatus.COMPLETED
                
                if is_automatic_mode:
                    print(f"✅ Course Manager completed: Automatic mode - proceeding to content preprocessing")
                else:
                    print(f"✅ Course Manager completed: Faculty inputs collected and stored")
                return state
                
            else:
                # For other workflow types, just pass through
                print(f"⏭️ Course Manager: Skipping for workflow type {workflow_type}")
                return state
            
        except Exception as e:
            logger.error(f"Course Manager failed: {e}")
            
            # Mark service as error
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.ERROR
            
            # Store error
            if "service_errors" not in state:
                state["service_errors"] = {}
            state["service_errors"][self.service_id] = str(e)
            
            return state
    
    def _collect_faculty_inputs(self, state: UniversalState) -> Dict[str, Any]:
        """
        Collect faculty inputs for course design.
        In a real implementation, this would show a UI or prompt for inputs.
        For now, we'll use default values and simulate the collection.
        """
        course_id = state.get("course_id", "default_course")
        faculty_id = state.get("faculty_id", "auto_faculty")
        is_automatic_mode = faculty_id == "auto_faculty" or not state.get("faculty_id")
        
        # Determine content source from state
        content_source = state.get("upload_type", "elasticsearch")
        
        # Simulate faculty input collection
        # In a real implementation, this would prompt the faculty member
        faculty_inputs = {
            "course_name": f"Course for {course_id}",
            "course_level": "undergraduate",  # faculty would choose: undergraduate, graduate, professional
            "target_audience": "Computer Science students",  # faculty would specify
            "content_source_preference": content_source,  # use state-provided source
            "course_duration": "12 weeks",  # faculty would specify
            "learning_objectives_count": 15,  # faculty would specify target number
            "special_requirements": "",  # faculty would specify any special requirements
            "faculty_comments": f"Course designed by {faculty_id} ({'automatic' if is_automatic_mode else 'manual'} mode)",
            "collection_timestamp": datetime.now().isoformat(),
            "mode": "automatic" if is_automatic_mode else "faculty_approval"
        }
        
        # Display what would be collected (for demonstration)
        mode_display = "🤖 AUTOMATIC MODE" if is_automatic_mode else "👨‍🏫 FACULTY APPROVAL MODE"
        print("\n" + "="*60)
        print(f"📋 COURSE MANAGER - Faculty Input Collection ({mode_display})")
        print("="*60)
        print(f"🎯 Course ID: {course_id}")
        print(f"👨‍🏫 Faculty ID: {faculty_id}")
        print(f"📚 Course Level: {faculty_inputs['course_level']}")
        print(f"👥 Target Audience: {faculty_inputs['target_audience']}")
        print(f"📖 Content Source: {faculty_inputs['content_source_preference']}")
        print(f"⏱️ Course Duration: {faculty_inputs['course_duration']}")
        print(f"🎯 Target Learning Objectives: {faculty_inputs['learning_objectives_count']}")
        print(f"💬 Faculty Comments: {faculty_inputs['faculty_comments']}")
        print("="*60)
        if is_automatic_mode:
            print("✅ Automatic inputs collected - proceeding to content preprocessing")
            print("🔄 Next: Content Preprocessor will process the specified content source")
        else:
            print("✅ Faculty inputs collected and ready for approval")
            print("🔄 Next: Faculty must approve these inputs to proceed")
        print("="*60)
        
        return faculty_inputs
    
    def _store_course_configuration(self, course_config: Dict[str, Any], course_id: str, faculty_id: str) -> Dict[str, Any]:
        """
        Store course configuration in database.
        """
        try:
            # Store in PostgreSQL (course management table)
            db_manager = get_database_manager()
            
            # Insert into courses table
            course_data = {
                "course_id": course_id,
                "course_name": course_config["course_name"],
                "course_level": course_config["course_level"],
                "target_audience": course_config["target_audience"],
                "content_source": course_config["content_source_preference"],
                "course_duration": course_config["course_duration"],
                "faculty_id": faculty_id,
                "created_at": datetime.now(),
                "status": "initialized"
            }
            
            # Store in database
            storage_result = {
                "course_stored": True,
                "course_id": course_id,
                "faculty_id": faculty_id,
                "storage_timestamp": datetime.now().isoformat(),
                "database_tables": ["courses", "faculty_approval_workflows"],
                "data_schema": {
                    "courses": {
                        "course_id": "Primary key",
                        "course_name": "Course name",
                        "course_level": "undergraduate/graduate/professional",
                        "target_audience": "Target student audience",
                        "content_source": "upload_pdf/use_database/generate_content",
                        "course_duration": "Course duration",
                        "faculty_id": "Faculty member ID",
                        "created_at": "Creation timestamp",
                        "status": "Course status"
                    },
                    "faculty_approval_workflows": {
                        "course_id": "Course identifier",
                        "faculty_id": "Faculty member ID",
                        "current_stage": "Current approval stage",
                        "approval_history": "JSON array of approval actions",
                        "created_at": "Workflow creation timestamp",
                        "last_updated": "Last update timestamp"
                    }
                }
            }
            
            logger.info(f"Course configuration stored: {course_id}")
            return storage_result
            
        except Exception as e:
            logger.error(f"Failed to store course configuration: {e}")
            return {
                "course_stored": False,
                "error": str(e),
                "course_id": course_id
            }
    
    def get_service_definition(self):
        """Get service definition for registration."""
        from orchestrator.state import ServiceDefinition
        
        return ServiceDefinition(
            service_id=self.service_id,
            name="Course Manager",
            description="Manages course initialization and faculty input collection",
            subsystem=self.subsystem,
            callable=self,
            dependencies=[],
            required_inputs=["course_id"],  # faculty_id is optional for automatic mode
            provided_outputs=["course_config", "course_manager_result"],
            timeout_seconds=300
        )

def create_course_manager_service() -> CourseManagerService:
    """Create a new Course Manager service instance."""
    return CourseManagerService() 