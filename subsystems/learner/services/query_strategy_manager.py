"""
Query Strategy Manager Service - Learner Subsystem

🥇 ENTRY POINT: This is the FIRST service in the Learner Subsystem flow.
Handles learner decision routing and query strategy optimization.
Follows wrapper pattern: delegates to core logic in graph/

Flow: Query Strategy Manager → Graph Query Engine → Learning Tree Handler
"""

from typing import Dict, Any, Optional
import logging
from orchestrator.state import UniversalState, ServiceStatus, SubsystemType

logger = logging.getLogger(__name__)

class QueryStrategyManagerService:
    """
    🥇 ENTRY POINT: First service in Learner Subsystem flow.
    Microservice for managing learner query strategies and decision routing.
    
    Responsibilities:
    - Route learner queries based on context and decision trees
    - Optimize query strategies for different learner types
    - Handle adaptive query routing based on learner performance
    - Manage query complexity and difficulty adaptation
    
    Architecture: Thin wrapper around graph/query_strategy.py
    
    Flow: Query Strategy Manager → Graph Query Engine → Learning Tree Handler
    """
    
    def __init__(self):
        self.service_id = "query_strategy_manager"
        self.subsystem = SubsystemType.LEARNER
        
    def __call__(self, state: UniversalState) -> UniversalState:
        """
        Main entry point for query strategy management.
        Compatible with LangGraph orchestrator.
        """
        print(f"🎯 [Query Strategy Manager] Processing query strategy...")
        
        try:
            # Extract context for strategy decision
            learner_id = state.get("learner_id")
            learner_context = state.get("learner_context", {})
            query_type = state.get("query_type", "standard")
            
            if not learner_id:
                raise ValueError("Learner ID is required for query strategy management")
            
            # Delegate to core business logic in graph/
            strategy_result = self._determine_query_strategy(
                learner_id=learner_id,
                learner_context=learner_context,
                query_type=query_type
            )
            
            # Update state with strategy results
            state.update({
                "query_strategy_manager_result": strategy_result,
                "query_strategy": {
                    "strategy": strategy_result.get("strategy", "standard"),
                    "complexity": strategy_result.get("complexity", "medium"),
                    "personalization_strategy": {
                        "learner_type": learner_context.get("learning_style", "visual"),
                        "intervention_strategy": "scaffolding" if "Beginner" in learner_context.get("decision_label", "") else "examples",
                        "delivery_strategy": "interactive"
                    },
                    "decision_factors": strategy_result.get("decision_factors", {}),
                    "recommended_actions": strategy_result.get("recommended_actions", [])
                },
                "query_complexity": strategy_result.get("complexity", "medium"),
                "service_status": ServiceStatus.COMPLETED,
                "last_service": self.service_id
            })
            
            print(f"✅ Query strategy '{strategy_result.get('strategy')}' determined for {learner_id}")
            
            return state
            
        except Exception as e:
            logger.error(f"Query Strategy Manager error: {e}")
            state.update({
                "service_status": ServiceStatus.FAILED,
                "error": str(e),
                "last_service": self.service_id
            })
            return state
    
    def _determine_query_strategy(self, learner_id: str, learner_context: Dict[str, Any], 
                                query_type: str) -> Dict[str, Any]:
        """Determine optimal query strategy using core logic."""
        try:
            # Import core query strategy logic from graph/
            from graph.query_strategy import determine_query_strategy
            
            print("🔄 Delegating to core query strategy logic...")
            return determine_query_strategy(learner_id, learner_context, query_type)
            
        except ImportError:
            # Fallback implementation until graph/query_strategy.py is created
            print("⚠️ Using fallback query strategy logic (core logic not yet implemented)")
            
            # Simple strategy based on learner context
            decision_label = learner_context.get("decision_label", "Standard Learner")
            experience_level = learner_context.get("experience_level", "intermediate")
            
            # Basic strategy mapping
            if "Advanced" in decision_label or experience_level == "advanced":
                strategy = "complex_queries"
                complexity = "high"
            elif "Beginner" in decision_label or experience_level == "beginner":
                strategy = "guided_queries"
                complexity = "low"
            else:
                strategy = "adaptive_queries"
                complexity = "medium"
            
            return {
                "learner_id": learner_id,
                "strategy": strategy,
                "complexity": complexity,
                "query_type": query_type,
                "decision_factors": {
                    "decision_label": decision_label,
                    "experience_level": experience_level
                },
                "recommended_actions": [
                    f"Use {strategy} approach",
                    f"Set complexity to {complexity}",
                    "Monitor learner performance"
                ]
            }

    def get_service_definition(self):
        """Get service definition for registration."""
        from orchestrator.state import ServiceDefinition
        
        return ServiceDefinition(
            service_id=self.service_id,
            subsystem=self.subsystem,
            name="Query Strategy Manager",
            description="Manages learner query strategies and decision routing based on learner context",
            dependencies=[],  # No dependencies - can be entry point
            required_inputs=["learner_id", "learner_context"],
            provided_outputs=["query_strategy", "query_complexity", "query_strategy_manager_result"],
            callable=self,
            timeout_seconds=60  # Quick strategy decisions
        )


def create_query_strategy_manager_service() -> QueryStrategyManagerService:
    """Factory function to create QueryStrategyManagerService instance."""
    return QueryStrategyManagerService()


# Service instance for orchestrator registration
query_strategy_manager_service = create_query_strategy_manager_service() 