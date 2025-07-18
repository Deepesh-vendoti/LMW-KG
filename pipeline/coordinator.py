"""
Automatic Pipeline Coordinator for LangGraph Knowledge Graph System

Provides automatic orchestration of the complete pipeline:
1. Content Preprocessing → 2. Stage 1 Mapping → 3. Stage 2 KLI → 4. KG Generation → 5. PLT Generation

Eliminates manual CLI invocation by providing smart pipeline coordination.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.loader import get_default_course_id, get_default_learner_id, config
from utils.logging import get_orchestrator_logger, performance_tracker
from orchestrator.universal_orchestrator import run_cross_subsystem_workflow
from orchestrator.service_registry import get_service_registry

class PipelineCoordinator:
    """
    Automatic pipeline coordinator that orchestrates complete workflows.
    
    Supports:
    - Content-only pipelines (content preprocessing → mapping → KG generation)
    - Learner-focused pipelines (PLT generation → recommendations)
    - Full cross-subsystem pipelines (content → learner integration)
    """
    
    def __init__(self):
        self.logger = get_orchestrator_logger("pipeline_coordinator")
        self.registry = get_service_registry()
        
        # Default configurations
        self.default_course_id = get_default_course_id()
        self.default_learner_id = get_default_learner_id()
        
        self.logger.info("Initialized Pipeline Coordinator", 
                        default_course=self.default_course_id,
                        default_learner=self.default_learner_id)
    
    def run_complete_pipeline(self, 
                            content_source: str = "elasticsearch",
                            course_id: Optional[str] = None,
                            learner_id: Optional[str] = None,
                            file_path: Optional[str] = None,
                            generate_plt: bool = True,
                            **kwargs) -> Dict[str, Any]:
        """
        Run the complete automated pipeline from content to personalized learning.
        
        This is the main entry point that replaces manual CLI invocation.
        
        Args:
            content_source: Source type ("pdf", "elasticsearch", "llm_generated")
            course_id: Course identifier (uses default if None)
            learner_id: Learner identifier (uses default if None) 
            file_path: PDF file path (required for PDF source)
            generate_plt: Whether to generate personalized learning tree
            **kwargs: Additional configuration
            
        Returns:
            Complete pipeline results including all stages
        """
        operation_id = self.logger.start_operation("complete_pipeline")
        
        course_id = course_id or self.default_course_id
        learner_id = learner_id or self.default_learner_id
        
        try:
            self.logger.info("Starting complete automated pipeline",
                           source=content_source,
                           course_id=course_id,
                           learner_id=learner_id,
                           generate_plt=generate_plt)
            
            # Stage 1: Content Processing Pipeline
            content_results = self._run_content_pipeline(
                content_source=content_source,
                course_id=course_id,
                file_path=file_path,
                **kwargs
            )
            
            # Stage 2: Learner Pipeline (if requested)
            learner_results = {}
            if generate_plt:
                learner_results = self._run_learner_pipeline(
                    course_id=course_id,
                    learner_id=learner_id,
                    **kwargs
                )
            
            # Compile final results
            pipeline_results = {
                "pipeline_type": "complete",
                "course_id": course_id,
                "learner_id": learner_id if generate_plt else None,
                "content_pipeline": content_results,
                "learner_pipeline": learner_results,
                "status": "completed",
                "timestamp": performance_tracker.metrics
            }
            
            self.logger.end_operation(operation_id, success=True,
                                    stages_completed=["content", "learner"] if generate_plt else ["content"],
                                    course_id=course_id)
            
            return pipeline_results
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="complete_pipeline",
                                             course_id=course_id,
                                             source=content_source)
            return {
                "pipeline_type": "complete",
                "status": "failed", 
                "error": str(e),
                "course_id": course_id
            }
    
    def _run_content_pipeline(self, 
                            content_source: str,
                            course_id: str,
                            file_path: Optional[str] = None,
                            **kwargs) -> Dict[str, Any]:
        """
        Run the content processing pipeline automatically.
        
        Pipeline: Content Preprocessor → Course Mapper → KLI Application → KG Generator
        """
        operation_id = self.logger.start_operation("content_pipeline")
        
        try:
            self.logger.info("Starting content pipeline",
                           source=content_source,
                           course_id=course_id)
            
            # Prepare initial state for content subsystem
            workflow_kwargs = {
                "course_id": course_id,
                "source": content_source,
                "workflow_type": "content_processing"
            }
            
            # Add source-specific parameters
            if content_source == "pdf" and file_path:
                workflow_kwargs["file_path"] = file_path
            elif content_source == "elasticsearch":
                workflow_kwargs["es_index"] = kwargs.get("es_index", "advanced_docs_elasticsearch_v2")
            elif content_source == "llm_generated":
                workflow_kwargs["raw_content"] = kwargs.get("raw_content", "")
            
            # Execute content workflow via universal orchestrator
            from orchestrator.state import SubsystemType
            result = run_cross_subsystem_workflow(
                subsystem=SubsystemType.CONTENT,
                **workflow_kwargs
            )
            
            self.logger.end_operation(operation_id, success=True,
                                    content_source=content_source,
                                    course_id=course_id)
            
            return {
                "status": "completed",
                "source": content_source,
                "course_id": course_id,
                "results": result,
                "stages": ["content_preprocessor", "course_mapper", "kli_application", "knowledge_graph_generator"]
            }
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="content_pipeline",
                                             source=content_source,
                                             course_id=course_id)
            return {
                "status": "failed",
                "error": str(e),
                "source": content_source,
                "course_id": course_id
            }
    
    def _run_learner_pipeline(self,
                            course_id: str,
                            learner_id: str,
                            **kwargs) -> Dict[str, Any]:
        """
        Run the learner-focused pipeline automatically.
        
        Pipeline: Learning Tree Handler → Graph Query Engine
        """
        operation_id = self.logger.start_operation("learner_pipeline")
        
        try:
            self.logger.info("Starting learner pipeline",
                           course_id=course_id,
                           learner_id=learner_id)
            
            # Prepare learner workflow kwargs
            workflow_kwargs = {
                "course_id": course_id,
                "learner_id": learner_id,
                "workflow_type": "personalized_learning"
            }
            
            # Add learner context if provided
            if "learner_context" in kwargs:
                workflow_kwargs["learner_context"] = kwargs["learner_context"]
            
            # Execute learner workflow via universal orchestrator
            from orchestrator.state import SubsystemType
            result = run_cross_subsystem_workflow(
                subsystem=SubsystemType.LEARNER,
                **workflow_kwargs
            )
            
            self.logger.end_operation(operation_id, success=True,
                                    course_id=course_id,
                                    learner_id=learner_id)
            
            return {
                "status": "completed",
                "course_id": course_id,
                "learner_id": learner_id,
                "results": result,
                "stages": ["learning_tree_handler", "graph_query_engine"]
            }
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="learner_pipeline",
                                             course_id=course_id,
                                             learner_id=learner_id)
            return {
                "status": "failed",
                "error": str(e),
                "course_id": course_id,
                "learner_id": learner_id
            }
    
    def run_content_only_pipeline(self, 
                                content_source: str = "elasticsearch",
                                course_id: Optional[str] = None,
                                **kwargs) -> Dict[str, Any]:
        """
        Run only the content processing pipeline.
        
        Useful for content preparation without learner personalization.
        """
        course_id = course_id or self.default_course_id
        
        return self._run_content_pipeline(
            content_source=content_source,
            course_id=course_id,
            **kwargs
        )
    
    def run_learner_only_pipeline(self,
                                course_id: Optional[str] = None,
                                learner_id: Optional[str] = None,
                                **kwargs) -> Dict[str, Any]:
        """
        Run only the learner pipeline (assumes content already processed).
        
        Useful for generating PLT when course content already exists.
        """
        course_id = course_id or self.default_course_id
        learner_id = learner_id or self.default_learner_id
        
        return self._run_learner_pipeline(
            course_id=course_id,
            learner_id=learner_id,
            **kwargs
        )
    
    def run_batch_processing(self, 
                           courses: List[str],
                           learners: List[str] = None,
                           content_source: str = "elasticsearch") -> Dict[str, Any]:
        """
        Run batch processing for multiple courses/learners.
        
        Automatically coordinates parallel processing pipelines.
        """
        operation_id = self.logger.start_operation("batch_processing")
        
        try:
            batch_results = {}
            total_courses = len(courses)
            
            self.logger.info("Starting batch processing",
                           total_courses=total_courses,
                           content_source=content_source)
            
            for i, course_id in enumerate(courses, 1):
                self.logger.info(f"Processing course {i}/{total_courses}",
                               course_id=course_id)
                
                # Process content for this course
                course_result = self.run_content_only_pipeline(
                    content_source=content_source,
                    course_id=course_id
                )
                
                # If learners specified, generate PLTs for each
                if learners:
                    course_result["learner_results"] = {}
                    for learner_id in learners:
                        learner_result = self.run_learner_only_pipeline(
                            course_id=course_id,
                            learner_id=learner_id
                        )
                        course_result["learner_results"][learner_id] = learner_result
                
                batch_results[course_id] = course_result
            
            self.logger.end_operation(operation_id, success=True,
                                    courses_processed=len(courses),
                                    learners_processed=len(learners) if learners else 0)
            
            return {
                "status": "completed",
                "total_courses": len(courses),
                "total_learners": len(learners) if learners else 0,
                "results": batch_results
            }
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="batch_processing")
            return {
                "status": "failed",
                "error": str(e)
            }

# Global coordinator instance
pipeline_coordinator = PipelineCoordinator()

# Convenience functions for common use cases
def run_automatic_pipeline(**kwargs) -> Dict[str, Any]:
    """
    Run the complete automatic pipeline with sensible defaults.
    
    This replaces manual CLI invocation.
    """
    return pipeline_coordinator.run_complete_pipeline(**kwargs)

def process_course_content(course_id: str = None, 
                         content_source: str = "elasticsearch",
                         **kwargs) -> Dict[str, Any]:
    """Quick content processing for a course."""
    return pipeline_coordinator.run_content_only_pipeline(
        content_source=content_source,
        course_id=course_id,
        **kwargs
    )

def generate_learner_plt(course_id: str = None,
                        learner_id: str = None,
                        **kwargs) -> Dict[str, Any]:
    """Quick PLT generation for a learner."""
    return pipeline_coordinator.run_learner_only_pipeline(
        course_id=course_id,
        learner_id=learner_id,
        **kwargs
    ) 