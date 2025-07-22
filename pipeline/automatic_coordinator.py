#!/usr/bin/env python3
"""
Automatic Pipeline Coordinator for LangGraph Knowledge Graph System

This module provides automatic coordination of microservices across subsystems
for knowledge graph generation and personalized learning tree creation.

Microservices Architecture:
- Content Subsystem: course_manager, content_preprocessor, course_mapper, kli_application, knowledge_graph_generator
- Learner Subsystem: query_strategy_manager, learning_tree_handler, graph_query_engine
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from orchestrator.state import UniversalState, SubsystemType, ServiceStatus
from orchestrator.service_registry import get_service_registry, register_all_services
from orchestrator.universal_orchestrator import UniversalOrchestrator
from utils.logging import get_orchestrator_logger

# Enhanced logger
logger = get_orchestrator_logger("automatic_coordinator")

@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    status: str
    pipeline_type: str
    course_id: str
    learner_id: Optional[str] = None
    content_pipeline: Optional[Dict[str, Any]] = None
    learner_pipeline: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: int = 0

class MicroservicesAutomaticCoordinator:
    """
    Automatic coordinator that uses actual microservices instead of stage-based approach.
    
    Two separate pipelines:
    1. Knowledge Graph Generation Pipeline (Content Subsystem)
    2. Personalized Learning Tree Pipeline (Learner Subsystem)
    """
    
    def __init__(self):
        """Initialize the automatic coordinator."""
        self.orchestrator = UniversalOrchestrator()
        self.registry = get_service_registry()
        self.logger = logger
        
        # Register all services
        register_all_services()
        
        self.logger.info("Microservices Automatic Coordinator initialized")
    
    def run_knowledge_graph_pipeline(self, 
                                   course_id: str,
                                   content_source: str = "elasticsearch",
                                   file_path: Optional[str] = None,
                                   es_index: Optional[str] = None,
                                   raw_content: Optional[str] = None) -> PipelineResult:
        """
        Run the Knowledge Graph Generation Pipeline using Content Subsystem microservices.
        
        Pipeline Flow:
        1. course_manager -> 2. content_preprocessor -> 3. course_mapper -> 
        4. kli_application -> 5. knowledge_graph_generator
        """
        start_time = time.time()
        operation_id = self.logger.start_operation("knowledge_graph_pipeline")
        
        try:
            self.logger.info("Starting Knowledge Graph Generation Pipeline",
                           course_id=course_id,
                           content_source=content_source)
            
            print("🚀 [CONTENT] Knowledge Graph Generation Pipeline")
            print("=" * 60)
            print(f"📚 Course: {course_id}")
            print(f"📖 Source: {content_source}")
            print("=" * 60)
            
            # Build initial state for content pipeline
            initial_state: UniversalState = {
                "course_id": course_id,
                "content_source": content_source,
                "subsystem": SubsystemType.CONTENT,
                "service_statuses": {},
                "execution_history": []
            }
            
            # Add source-specific inputs
            if content_source == "pdf" and file_path:
                initial_state["file_path"] = file_path
            elif content_source == "elasticsearch" and es_index:
                initial_state["es_index"] = es_index
            elif content_source == "llm_generated" and raw_content:
                initial_state["raw_content"] = raw_content
            
            # Execute content pipeline using orchestrator
            result = self.orchestrator.run(initial_state)
            
            # Extract pipeline results
            content_pipeline = {
                "status": "completed" if result.get("status") == "completed" else "failed",
                "services_executed": list(result.get("service_statuses", {}).keys()),
                "stages": self._extract_content_stages(result),
                "knowledge_graph_generated": "knowledge_graph" in result,
                "ffcs_generated": "ffcs" in result
            }
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Display results
            if content_pipeline["status"] == "completed":
                print("\n✅ [SUCCESS] Knowledge Graph Generation Pipeline Completed!")
                print(f"📊 Services Executed: {', '.join(content_pipeline['services_executed'])}")
                print(f"📈 Stages: {' -> '.join(content_pipeline['stages'])}")
                print(f"🕒 Execution Time: {execution_time}ms")
                
                if content_pipeline["knowledge_graph_generated"]:
                    print("🗺️ Knowledge Graph: Generated and stored")
                if content_pipeline["ffcs_generated"]:
                    print("📋 FFCS: Faculty Finalized Course Structure ready")
            else:
                print(f"\n❌ [ERROR] Knowledge Graph Pipeline failed: {result.get('error', 'Unknown error')}")
            
            self.logger.end_operation(operation_id, success=content_pipeline["status"] == "completed")
            
            return PipelineResult(
                status="completed" if content_pipeline["status"] == "completed" else "failed",
                pipeline_type="knowledge_graph_generation",
                course_id=course_id,
                content_pipeline=content_pipeline,
                error=result.get("error"),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="knowledge_graph_pipeline")
            
            return PipelineResult(
                status="failed",
                pipeline_type="knowledge_graph_generation",
                course_id=course_id,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def run_learning_tree_pipeline(self,
                                 course_id: str,
                                 learner_id: str,
                                 learner_context: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """
        Run the Personalized Learning Tree Pipeline using Learner Subsystem microservices.
        
        Pipeline Flow:
        1. query_strategy_manager -> 2. learning_tree_handler -> 3. graph_query_engine
        """
        start_time = time.time()
        operation_id = self.logger.start_operation("learning_tree_pipeline")
        
        try:
            self.logger.info("Starting Learning Tree Pipeline",
                           course_id=course_id,
                           learner_id=learner_id)
            
            print("🌳 [LEARNER] Personalized Learning Tree Pipeline")
            print("=" * 60)
            print(f"📚 Course: {course_id}")
            print(f"👤 Learner: {learner_id}")
            if learner_context:
                print(f"🎯 Context: {list(learner_context.keys())}")
            print("=" * 60)
            
            # Build initial state for learner pipeline
            initial_state: UniversalState = {
                "course_id": course_id,
                "learner_id": learner_id,
                "subsystem": SubsystemType.LEARNER,
                "service_statuses": {},
                "execution_history": []
            }
            
            # Add learner context if provided
            if learner_context:
                initial_state["learner_context"] = learner_context
            
            # Execute learner pipeline using orchestrator
            result = self.orchestrator.run(initial_state)
            
            # Extract pipeline results
            learner_pipeline = {
                "status": "completed" if result.get("status") == "completed" else "failed",
                "services_executed": list(result.get("service_statuses", {}).keys()),
                "stages": self._extract_learner_stages(result),
                "plt_generated": "personalized_learning_tree" in result,
                "query_strategy": "query_strategy" in result
            }
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Display results
            if learner_pipeline["status"] == "completed":
                print("\n✅ [SUCCESS] Learning Tree Pipeline Completed!")
                print(f"📊 Services Executed: {', '.join(learner_pipeline['services_executed'])}")
                print(f"📈 Stages: {' -> '.join(learner_pipeline['stages'])}")
                print(f"🕒 Execution Time: {execution_time}ms")
                
                if learner_pipeline["plt_generated"]:
                    plt = result.get("personalized_learning_tree", {})
                    steps = len(plt.get("learning_path", []))
                    print(f"🌳 Personalized Learning Tree: {steps} learning steps generated")
                if learner_pipeline["query_strategy"]:
                    print("🎯 Query Strategy: Personalized strategy created")
            else:
                print(f"\n❌ [ERROR] Learning Tree Pipeline failed: {result.get('error', 'Unknown error')}")
            
            self.logger.end_operation(operation_id, success=learner_pipeline["status"] == "completed")
            
            return PipelineResult(
                status="completed" if learner_pipeline["status"] == "completed" else "failed",
                pipeline_type="personalized_learning_tree",
                course_id=course_id,
                learner_id=learner_id,
                learner_pipeline=learner_pipeline,
                error=result.get("error"),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="learning_tree_pipeline")
            
            return PipelineResult(
                status="failed",
                pipeline_type="personalized_learning_tree",
                course_id=course_id,
                learner_id=learner_id,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def run_complete_pipeline(self,
                            content_source: str = "elasticsearch",
                            course_id: Optional[str] = None,
                            learner_id: Optional[str] = None,
                            file_path: Optional[str] = None,
                            generate_plt: bool = True,
                            **kwargs) -> Dict[str, Any]:
        """
        Run both pipelines in sequence: Knowledge Graph Generation -> Learning Tree (if requested).
        
        This is the main entry point for automatic pipeline execution.
        """
        operation_id = self.logger.start_operation("complete_pipeline")
        
        try:
            # Use default course ID if not provided
            course_id = course_id or "OSN"
            
            print("🚀 [AUTOMATIC] Complete Microservices Pipeline")
            print("=" * 80)
            print(f"📚 Course: {course_id}")
            print(f"📖 Content Source: {content_source}")
            if learner_id and generate_plt:
                print(f"👤 Learner: {learner_id}")
            print(f"🌳 Generate PLT: {generate_plt}")
            print("=" * 80)
            
            # Step 1: Run Knowledge Graph Generation Pipeline
            print("\n📋 [STEP 1] Knowledge Graph Generation Pipeline")
            kg_result = self.run_knowledge_graph_pipeline(
                course_id=course_id,
                content_source=content_source,
                file_path=file_path,
                es_index=kwargs.get("es_index"),
                raw_content=kwargs.get("raw_content")
            )
            
            # Step 2: Run Learning Tree Pipeline (if requested and KG was successful)
            learner_result = None
            if generate_plt and kg_result.status == "completed" and learner_id:
                print("\n🌳 [STEP 2] Personalized Learning Tree Pipeline")
                learner_result = self.run_learning_tree_pipeline(
                    course_id=course_id,
                    learner_id=learner_id,
                    learner_context=kwargs.get("learner_context")
                )
            
            # Compile final results
            final_status = "completed"
            if kg_result.status == "failed":
                final_status = "failed"
            elif learner_result and learner_result.status == "failed":
                final_status = "partial"  # KG succeeded but PLT failed
            
            total_time = kg_result.execution_time_ms
            if learner_result:
                total_time += learner_result.execution_time_ms
            
            # Display final summary
            print("\n" + "=" * 80)
            print("📊 [FINAL] Pipeline Execution Summary")
            print("=" * 80)
            print(f"🎯 Overall Status: {final_status.upper()}")
            print(f"📚 Course: {course_id}")
            print(f"🗺️ Knowledge Graph: {'✅ Generated' if kg_result.status == 'completed' else '❌ Failed'}")
            if generate_plt and learner_id:
                print(f"🌳 Learning Tree: {'✅ Generated' if learner_result and learner_result.status == 'completed' else '❌ Failed'}")
            print(f"🕒 Total Time: {total_time}ms")
            print("=" * 80)
            
            self.logger.end_operation(operation_id, success=final_status == "completed")
            
            return {
                "status": final_status,
                "pipeline_type": "complete_microservices",
                "course_id": course_id,
                "learner_id": learner_id,
                "content_pipeline": kg_result.content_pipeline,
                "learner_pipeline": learner_result.learner_pipeline if learner_result else None,
                "total_execution_time_ms": total_time
            }
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="complete_pipeline")
            
            return {
                "status": "failed",
                "error": str(e),
                "pipeline_type": "complete_microservices"
            }
    
    def _extract_content_stages(self, result: Dict[str, Any]) -> List[str]:
        """Extract content pipeline stages from orchestrator result."""
        stages = []
        service_statuses = result.get("service_statuses", {})
        
        # Map service IDs to readable stage names
        stage_mapping = {
            "course_manager": "Course Management",
            "content_preprocessor": "Content Preprocessing", 
            "course_mapper": "Course Mapping",
            "kli_application": "KLI Application",
            "knowledge_graph_generator": "Knowledge Graph Generation"
        }
        
        for service_id, status in service_statuses.items():
            if status == ServiceStatus.COMPLETED:
                stage_name = stage_mapping.get(service_id, service_id)
                stages.append(stage_name)
        
        return stages
    
    def _extract_learner_stages(self, result: Dict[str, Any]) -> List[str]:
        """Extract learner pipeline stages from orchestrator result."""
        stages = []
        service_statuses = result.get("service_statuses", {})
        
        # Map service IDs to readable stage names
        stage_mapping = {
            "query_strategy_manager": "Query Strategy Management",
            "learning_tree_handler": "Learning Tree Handling",
            "graph_query_engine": "Graph Query Execution"
        }
        
        for service_id, status in service_statuses.items():
            if status == ServiceStatus.COMPLETED:
                stage_name = stage_mapping.get(service_id, service_id)
                stages.append(stage_name)
        
        return stages

# Global coordinator instance
microservices_coordinator = MicroservicesAutomaticCoordinator()

# Convenience functions for backward compatibility
def run_automatic_pipeline(**kwargs) -> Dict[str, Any]:
    """Run the complete automatic pipeline with microservices."""
    return microservices_coordinator.run_complete_pipeline(**kwargs)

def process_course_content(course_id: str = None, 
                         content_source: str = "elasticsearch",
                         **kwargs) -> Dict[str, Any]:
    """Run knowledge graph generation pipeline only."""
    result = microservices_coordinator.run_knowledge_graph_pipeline(
        course_id=course_id,
        content_source=content_source,
        **kwargs
    )
    return {
        "status": result.status,
        "course_id": result.course_id,
        "content_pipeline": result.content_pipeline,
        "error": result.error
    }

def generate_learner_plt(course_id: str = None,
                        learner_id: str = None,
                        **kwargs) -> Dict[str, Any]:
    """Run learning tree pipeline only."""
    result = microservices_coordinator.run_learning_tree_pipeline(
        course_id=course_id,
        learner_id=learner_id,
        **kwargs
    )
    return {
        "status": result.status,
        "course_id": result.course_id,
        "learner_id": result.learner_id,
        "learner_pipeline": result.learner_pipeline,
        "error": result.error
    } 