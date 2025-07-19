"""
Course Manager Service - Content Subsystem

Handles course lifecycle management and faculty bootstrap with real PostgreSQL storage.
Manages course metadata, upload tracking, and faculty approval workflows.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import uuid

from orchestrator.state import UniversalState, ServiceStatus, SubsystemType
from utils.database_connections import get_database_manager

logger = logging.getLogger(__name__)

class CourseManagerService:
    """
    Course Manager microservice for the content subsystem.
    
    Responsibilities:
    - Course lifecycle management
    - Faculty upload bootstrapping
    - Course metadata storage
    - Upload tracking and status management
    - Faculty approval workflow initialization
    """
    
    def __init__(self):
        self.service_id = "course_manager"
        self.subsystem = SubsystemType.CONTENT
        self.db_manager = get_database_manager()
    
    def __call__(self, state: UniversalState) -> UniversalState:
        """
        Main entry point for course management.
        Compatible with LangGraph orchestrator.
        """
        print(f"📋 [Course Manager] Managing course lifecycle...")
        
        try:
            # Extract required inputs
            course_id = state.get("course_id", "default_course")
            upload_type = state.get("upload_type", "elasticsearch")
            faculty_id = state.get("faculty_id", "default_faculty")
            
            # Initialize course in database
            course_result = self._initialize_course(course_id, upload_type, faculty_id)
            
            # Create upload record
            upload_result = self._create_upload_record(course_id, upload_type, state)
            
            # Initialize faculty approval workflow
            workflow_result = self._initialize_approval_workflow(course_id, faculty_id)
            
            # Update state with results
            state.update({
                "course_manager_result": {
                    "course_initialized": course_result,
                    "upload_recorded": upload_result,
                    "workflow_initialized": workflow_result
                }
            })
            
            # Mark service as completed
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.COMPLETED
            
            print(f"✅ Course management completed: {course_id}")
            return state
            
        except Exception as e:
            logger.error(f"Course management failed: {e}")
            
            # Mark service as error
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.ERROR
            
            # Store error
            if "service_errors" not in state:
                state["service_errors"] = {}
            state["service_errors"][self.service_id] = str(e)
            
            return state
    
    def _initialize_course(self, course_id: str, upload_type: str, faculty_id: str) -> Dict[str, Any]:
        """Initialize course in PostgreSQL database."""
        try:
            with self.db_manager.postgresql_cursor() as cursor:
                # Check if course already exists
                cursor.execute(
                    "SELECT course_id FROM courses WHERE course_id = %s",
                    (course_id,)
                )
                existing_course = cursor.fetchone()
                
                if existing_course:
                    # Update existing course
                    cursor.execute("""
                        UPDATE courses 
                        SET upload_type = %s, faculty_id = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE course_id = %s
                    """, (upload_type, faculty_id, course_id))
                    
                    return {
                        "status": "updated",
                        "course_id": course_id,
                        "action": "course_updated"
                    }
                else:
                    # Create new course
                    cursor.execute("""
                        INSERT INTO courses (course_id, name, faculty_id, upload_type, status, created_at)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """, (course_id, f"Course {course_id}", faculty_id, upload_type, "initialized"))
                    
                    return {
                        "status": "created",
                        "course_id": course_id,
                        "action": "course_created"
                    }
                    
        except Exception as e:
            logger.error(f"Course initialization failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "course_id": course_id
            }
    
    def _create_upload_record(self, course_id: str, upload_type: str, state: UniversalState) -> Dict[str, Any]:
        """Create upload record in PostgreSQL database."""
        try:
            upload_id = str(uuid.uuid4())
            
            # Extract upload metadata
            metadata = {
                "upload_type": upload_type,
                "file_path": state.get("file_path"),
                "es_index": state.get("es_index"),
                "raw_content_length": len(state.get("raw_content", "")),
                "chunks_count": len(state.get("chunks", [])),
                "processing_timestamp": datetime.now().isoformat()
            }
            
            with self.db_manager.postgresql_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO uploads (upload_id, course_id, file_path, upload_type, status, metadata, uploaded_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    upload_id,
                    course_id,
                    state.get("file_path"),
                    upload_type,
                    "processing",
                    metadata
                ))
                
                return {
                    "status": "created",
                    "upload_id": upload_id,
                    "course_id": course_id,
                    "upload_type": upload_type
                }
                
        except Exception as e:
            logger.error(f"Upload record creation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "course_id": course_id
            }
    
    def _initialize_approval_workflow(self, course_id: str, faculty_id: str) -> Dict[str, Any]:
        """Initialize faculty approval workflow in PostgreSQL database."""
        try:
            workflow_id = str(uuid.uuid4())
            
            with self.db_manager.postgresql_cursor() as cursor:
                # Create approval workflow record
                cursor.execute("""
                    INSERT INTO approval_workflows (workflow_id, course_id, stage, status, faculty_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (workflow_id, course_id, "FACD", "pending", faculty_id))
                
                return {
                    "status": "initialized",
                    "workflow_id": workflow_id,
                    "course_id": course_id,
                    "stage": "FACD",
                    "faculty_id": faculty_id
                }
                
        except Exception as e:
            logger.error(f"Approval workflow initialization failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "course_id": course_id
            }
    
    def get_course_info(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get course information from database."""
        try:
            with self.db_manager.postgresql_cursor() as cursor:
                cursor.execute("""
                    SELECT c.*, 
                           COUNT(u.upload_id) as upload_count,
                           MAX(u.uploaded_at) as last_upload
                    FROM courses c
                    LEFT JOIN uploads u ON c.course_id = u.course_id
                    WHERE c.course_id = %s
                    GROUP BY c.course_id, c.name, c.faculty_id, c.upload_type, c.status, c.created_at
                """, (course_id,))
                
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get course info: {e}")
            return None
    
    def get_upload_history(self, course_id: str) -> List[Dict[str, Any]]:
        """Get upload history for a course."""
        try:
            with self.db_manager.postgresql_cursor() as cursor:
                cursor.execute("""
                    SELECT upload_id, file_path, upload_type, status, metadata, uploaded_at
                    FROM uploads
                    WHERE course_id = %s
                    ORDER BY uploaded_at DESC
                """, (course_id,))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to get upload history: {e}")
            return []
    
    def update_course_status(self, course_id: str, status: str) -> bool:
        """Update course status."""
        try:
            with self.db_manager.postgresql_cursor() as cursor:
                cursor.execute("""
                    UPDATE courses 
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE course_id = %s
                """, (status, course_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update course status: {e}")
            return False
    
    def get_service_definition(self):
        """Get service definition for registration."""
        from orchestrator.state import ServiceDefinition
        
        return ServiceDefinition(
            service_id=self.service_id,
            subsystem=self.subsystem,
            name="Course Manager",
            description="Manages course lifecycle, uploads, and faculty approval workflows",
            dependencies=[],
            required_inputs=["course_id", "upload_type"],
            provided_outputs=["course_manager_result"],
            callable=self,
            timeout_seconds=60
        )

def create_course_manager_service():
    """Factory function to create Course Manager service."""
    return CourseManagerService() 