"""
Course Manager Microservice

Handles faculty upload/ES fetch/LLM fallback triggers.
Manages different content input types and faculty approval workflows.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging
from graph.config import CONFIG

logger = logging.getLogger(__name__)

class CourseManager:
    """
    Microservice responsible for managing course content input and faculty workflows.
    """
    
    def __init__(self):
        self.config = CONFIG['microservices']['course_manager']
        self.timeout = self.config.get('timeout', 300)
        
    def handle_faculty_upload(self, file_path: str, course_id: str) -> Dict[str, Any]:
        """
        Handle direct faculty file upload (PDF, documents, etc.)
        
        Args:
            file_path: Path to uploaded file
            course_id: Course identifier
            
        Returns:
            Dict containing upload status and metadata
        """
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
                
            return {
                "status": "success",
                "upload_type": "faculty_upload",
                "file_path": file_path,
                "course_id": course_id,
                "metadata": {
                    "file_size": Path(file_path).stat().st_size,
                    "file_type": Path(file_path).suffix
                }
            }
        except Exception as e:
            logger.error(f"Faculty upload failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "upload_type": "faculty_upload"
            }
    
    def handle_es_fetch(self, es_index: str, course_id: str) -> Dict[str, Any]:
        """
        Handle Elasticsearch content fetch for existing chunked data.
        
        Args:
            es_index: Elasticsearch index name
            course_id: Course identifier
            
        Returns:
            Dict containing ES fetch status and metadata
        """
        try:
            # Import here to avoid circular dependencies
            from graph.utils.es_to_kg import validate_es_connection, get_es_chunk_count
            
            if not validate_es_connection():
                raise ConnectionError("Elasticsearch connection failed")
                
            chunk_count = get_es_chunk_count()
            if chunk_count == 0:
                raise ValueError("No chunks found in Elasticsearch index")
                
            return {
                "status": "success",
                "upload_type": "elasticsearch",
                "es_index": es_index,
                "course_id": course_id,
                "metadata": {
                    "chunk_count": chunk_count,
                    "source": "elasticsearch"
                }
            }
        except Exception as e:
            logger.error(f"ES fetch failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "upload_type": "elasticsearch"
            }
    
    def handle_llm_fallback(self, topic: str, course_id: str) -> Dict[str, Any]:
        """
        Handle LLM-generated content fallback when no existing content is available.
        
        Args:
            topic: Course topic for content generation
            course_id: Course identifier
            
        Returns:
            Dict containing LLM generation status and content
        """
        try:
            # Generate basic course content using LLM
            from graph.config import get_llm
            llm = get_llm()
            
            prompt = f"""Generate educational content for the topic: {topic}
            
            Create a comprehensive overview covering:
            1. Key concepts and definitions
            2. Learning objectives
            3. Important relationships and dependencies
            4. Practical applications
            
            Topic: {topic}
            
            Provide structured, educational content suitable for knowledge graph generation."""
            
            generated_content = llm.invoke(prompt)
            
            return {
                "status": "success",
                "upload_type": "llm_generated",
                "course_id": course_id,
                "content": generated_content,
                "metadata": {
                    "topic": topic,
                    "source": "llm_generated",
                    "content_length": len(generated_content)
                }
            }
        except Exception as e:
            logger.error(f"LLM fallback failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "upload_type": "llm_generated"
            }
    
    def process_course_input(self, upload_type: str, **kwargs) -> Dict[str, Any]:
        """
        Main entry point for processing different types of course input.
        
        Args:
            upload_type: Type of upload ('pdf', 'elasticsearch', 'llm_generated')
            **kwargs: Additional arguments specific to upload type
            
        Returns:
            Dict containing processing results
        """
        if upload_type == "pdf":
            return self.handle_faculty_upload(
                kwargs.get('file_path'), 
                kwargs.get('course_id')
            )
        elif upload_type == "elasticsearch":
            return self.handle_es_fetch(
                kwargs.get('es_index'), 
                kwargs.get('course_id')
            )
        elif upload_type == "llm_generated":
            return self.handle_llm_fallback(
                kwargs.get('topic', 'General Course Content'), 
                kwargs.get('course_id')
            )
        else:
            return {
                "status": "error",
                "error": f"Unsupported upload type: {upload_type}"
            }

# Service instance
course_manager_service = CourseManager() 