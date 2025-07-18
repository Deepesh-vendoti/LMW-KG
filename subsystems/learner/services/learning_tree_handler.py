"""
Learning Tree Handler Service - Learner Subsystem

Handles personalized learning tree (PLT) generation and storage.
Integrates with existing PLT generation agents and Neo4j storage.
"""

from typing import Dict, Any, List, Optional
import logging
from orchestrator.state import UniversalState, ServiceStatus, SubsystemType

logger = logging.getLogger(__name__)

class LearningTreeHandlerService:
    """
    Learning Tree Handler microservice for the learner subsystem.
    
    Responsibilities:
    - Generate personalized learning trees (PLT)
    - Store PLT data in Neo4j and Redis
    - Manage learning path sequencing
    - Handle adaptive recommendations
    """
    
    def __init__(self):
        self.service_id = "learning_tree_handler"
        self.subsystem = SubsystemType.LEARNER
        
    def __call__(self, state: UniversalState) -> UniversalState:
        """
        Main entry point for learning tree handling.
        Compatible with LangGraph orchestrator.
        """
        print(f"🌳 [Learning Tree Handler] Generating personalized learning tree...")
        
        try:
            # Extract learner context
            learner_id = state.get("learner_id")
            course_id = state.get("course_id")
            learner_profile = state.get("learner_profile", {})
            
            if not learner_id or not course_id:
                raise ValueError("Learner ID and Course ID are required")
            
            # Generate PLT using existing PLT generator
            plt_result = self._generate_plt(learner_id, course_id, learner_profile)
            
            # Store PLT in databases
            storage_result = self._store_plt(plt_result, learner_id, course_id)
            
            # Update state with results
            state["personalized_learning_tree"] = plt_result
            state["adaptive_recommendations"] = self._generate_recommendations(plt_result)
            
            # Mark service as completed
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.COMPLETED
            
            # Store service result
            if "service_results" not in state:
                state["service_results"] = {}
            state["service_results"][self.service_id] = {
                "plt": plt_result,
                "storage": storage_result,
                "learner_id": learner_id,
                "course_id": course_id
            }
            
            print(f"✅ Learning tree generation completed for learner {learner_id}")
            return state
            
        except Exception as e:
            logger.error(f"Learning tree handling failed: {e}")
            
            # Mark service as error
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.ERROR
            
            # Store error
            if "service_errors" not in state:
                state["service_errors"] = {}
            state["service_errors"][self.service_id] = str(e)
            
            return state
    
    def _generate_plt(self, learner_id: str, course_id: str, learner_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized learning tree using existing PLT generator."""
        try:
            print("🔄 Using existing PLT generation pipeline...")
            
            # Import legacy PLT generator and agents
            from graph.plt_generator import run_plt_generator
            
            # Run PLT generation - this uses the existing 6 PLT agents
            plt_result = run_plt_generator()
            
            # Extract the final PLT
            final_plt = plt_result.get("final_plt", {})
            
            # Add learner-specific context
            enhanced_plt = {
                "learner_id": learner_id,
                "course_id": course_id,
                "learner_profile": learner_profile,
                "learning_path": final_plt.get("learning_path", []),
                "priority_weights": final_plt.get("priority_weights", {}),
                "sequencing_metadata": final_plt.get("sequencing_metadata", {}),
                "generated_at": plt_result.get("timestamp", "unknown")
            }
            
            return enhanced_plt
            
        except Exception as e:
            raise Exception(f"PLT generation failed: {e}")
    
    def _store_plt(self, plt_data: Dict[str, Any], learner_id: str, course_id: str) -> Dict[str, Any]:
        """Store PLT data in Neo4j and Redis."""
        try:
            storage_results = {}
            
            # Store in Neo4j using existing function
            try:
                from graph.db import insert_plt_to_neo4j
                insert_plt_to_neo4j(plt_data, clear_existing=False)
                storage_results["neo4j"] = "success"
            except Exception as e:
                storage_results["neo4j"] = f"error: {e}"
            
            # Store in Redis (if available)
            try:
                # This would be implemented when Redis integration is added
                storage_results["redis"] = "not_implemented"
            except Exception as e:
                storage_results["redis"] = f"error: {e}"
            
            # Store in PostgreSQL (if available)  
            try:
                # This would be implemented when PostgreSQL integration is added
                storage_results["postgresql"] = "not_implemented"
            except Exception as e:
                storage_results["postgresql"] = f"error: {e}"
            
            return storage_results
            
        except Exception as e:
            raise Exception(f"PLT storage failed: {e}")
    
    def _generate_recommendations(self, plt_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate adaptive recommendations based on PLT."""
        try:
            learning_path = plt_data.get("learning_path", [])
            recommendations = []
            
            # Generate recommendations for next steps
            for i, step in enumerate(learning_path[:3]):  # Next 3 steps
                recommendation = {
                    "step_id": i + 1,
                    "learning_objective": step.get("lo", "Unknown LO"),
                    "knowledge_component": step.get("kc", "Unknown KC"),
                    "instruction_method": step.get("instruction_method", "Unknown IM"),
                    "priority": step.get("priority", 1),
                    "sequence": step.get("sequence", i + 1),
                    "recommendation_type": "next_step" if i == 0 else "upcoming",
                    "confidence": 0.8 - (i * 0.1)  # Decreasing confidence for future steps
                }
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Failed to generate recommendations: {e}")
            return []
    
    def get_service_definition(self):
        """Get service definition for registration."""
        from orchestrator.state import ServiceDefinition
        
        return ServiceDefinition(
            service_id=self.service_id,
            subsystem=self.subsystem,
            name="Learning Tree Handler",
            description="Generates and stores personalized learning trees with adaptive recommendations",
            dependencies=["content_preprocessor"],  # Needs content to be processed first
            required_inputs=["learner_id", "course_id"],
            provided_outputs=["personalized_learning_tree", "adaptive_recommendations"],
            callable=self,
            timeout_seconds=600  # PLT generation can take longer
        )

# ===============================
# SERVICE FACTORY
# ===============================

def create_learning_tree_handler_service() -> LearningTreeHandlerService:
    """Factory function to create learning tree handler service."""
    return LearningTreeHandlerService()

# ===============================
# LEGACY COMPATIBILITY
# ===============================

def learning_tree_handler_service(state: UniversalState) -> UniversalState:
    """Legacy compatibility function."""
    service = create_learning_tree_handler_service()
    return service(state) 