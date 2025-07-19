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
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute learning tree generation with personalized recommendations."""
        try:
            # Extract required inputs
            learner_id = state.get("learner_id")
            course_id = state.get("course_id")
            learner_profile = state.get("learner_profile", {})
            query_strategy = state.get("query_strategy", {})  # From Query Strategy Manager
            query_results = state.get("query_results", {})   # From Graph Query Engine
            
            if not learner_id or not course_id:
                raise ValueError("Learner ID and Course ID are required")
            
            # Generate PLT using strategy and query results
            plt_result = self._generate_plt_with_strategy(
                learner_id, course_id, learner_profile, query_strategy, query_results
            )
            
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
    
    def _generate_plt_with_strategy(self, learner_id: str, course_id: str, 
                                   learner_profile: Dict[str, Any], 
                                   query_strategy: Dict[str, Any], 
                                   query_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized learning tree using query strategy and results."""
        try:
            print("🔄 Generating PLT with adaptive strategy...")
            
            # Import legacy PLT generator and agents
            from graph.plt_generator import run_plt_generator
            
            # Run PLT generation - this uses the existing 6 PLT agents
            plt_result = run_plt_generator()
            
            # Extract the final PLT
            final_plt = plt_result.get("final_plt", {})
            
            # Apply query strategy for personalization
            personalization_strategy = query_strategy.get('personalization_strategy', {})
            learner_type = personalization_strategy.get('learner_type', 'visual')
            intervention_strategy = personalization_strategy.get('intervention_strategy', 'scaffolding')
            delivery_strategy = personalization_strategy.get('delivery_strategy', 'interactive')
            
            # Enhance PLT with query results and strategy
            enhanced_plt = {
                "learner_id": learner_id,
                "course_id": course_id,
                "learner_profile": learner_profile,
                "query_strategy": query_strategy,
                "query_results": query_results,
                "learning_path": final_plt.get("learning_path", []),
                "priority_weights": final_plt.get("priority_weights", {}),
                "sequencing_metadata": final_plt.get("sequencing_metadata", {}),
                "personalization": {
                    "learner_type": learner_type,
                    "intervention_strategy": intervention_strategy,
                    "delivery_strategy": delivery_strategy,
                    "adaptive_features": self._extract_adaptive_features(query_results)
                },
                "generated_at": plt_result.get("timestamp", "unknown")
            }
            
            return enhanced_plt
            
        except Exception as e:
            raise Exception(f"PLT generation with strategy failed: {e}")
    
    def _extract_adaptive_features(self, query_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract adaptive features from query results."""
        features = {
            "content_adaptation": [],
            "difficulty_progression": [],
            "interaction_patterns": []
        }
        
        # Extract features from query results
        if "knowledge_graph_data" in query_results:
            kg_data = query_results["knowledge_graph_data"]
            features["content_adaptation"] = kg_data.get("concepts", [])
            features["difficulty_progression"] = kg_data.get("difficulty_levels", [])
        
        if "interaction_data" in query_results:
            features["interaction_patterns"] = query_results["interaction_data"]
        
        return features
    
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
            dependencies=["query_strategy_manager", "graph_query_engine"],  # Depends on strategy and query results
            required_inputs=["learner_id", "course_id", "query_strategy", "query_results"],
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