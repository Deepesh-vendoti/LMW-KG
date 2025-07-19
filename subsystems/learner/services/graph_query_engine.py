"""
Graph Query Engine Service - Learner Subsystem

Wrapper for existing Neo4j query functionality in graph/db.py.
Provides Cypher query generation and execution for learner queries.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from orchestrator.state import UniversalState, ServiceStatus, SubsystemType

logger = logging.getLogger(__name__)

class GraphQueryEngineService:
    """
    Graph Query Engine microservice for the learner subsystem.
    
    Responsibilities:
    - Execute Cypher queries against Neo4j
    - Generate personalized query strategies
    - Query learning objectives and knowledge components
    - Support PLT data retrieval
    """
    
    def __init__(self):
        self.service_id = "graph_query_engine"
        self.subsystem = SubsystemType.LEARNER
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge graph queries with adaptive strategy."""
        try:
            # Extract required inputs
            learner_id = state.get("learner_id")
            course_id = state.get("course_id")
            learner_query = state.get("learner_query", "")
            query_strategy = state.get("query_strategy", {})  # From Query Strategy Manager
            
            if not learner_id or not course_id:
                raise ValueError("Learner ID and Course ID are required")
            
            # Execute queries using strategy guidance
            query_results = self._execute_queries_with_strategy(
                learner_id, course_id, learner_query, query_strategy
            )
            
            # Update state with results
            state["query_results"] = query_results
            
            # Mark service as completed
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.COMPLETED
            
            # Store service result
            if "service_results" not in state:
                state["service_results"] = {}
            state["service_results"][self.service_id] = {
                "query_results": query_results,
                "total_queries": len(query_results),
                "learner_id": learner_id,
                "course_id": course_id
            }
            
            print(f"✅ Graph query execution completed: {len(query_results)} queries executed")
            return state
            
        except Exception as e:
            logger.error(f"Graph query execution failed: {e}")
            
            # Mark service as error
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.ERROR
            
            # Store error
            if "service_errors" not in state:
                state["service_errors"] = {}
            state["service_errors"][self.service_id] = str(e)
            
            return state
    
    def _execute_queries_with_strategy(self, learner_id: str, course_id: str, 
                                      learner_query: str, query_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge graph queries using adaptive strategy."""
        try:
            print("🔄 Executing queries with adaptive strategy...")
            
            # Extract strategy parameters
            personalization_strategy = query_strategy.get('personalization_strategy', {})
            learner_type = personalization_strategy.get('learner_type', 'visual')
            intervention_strategy = personalization_strategy.get('intervention_strategy', 'scaffolding')
            delivery_strategy = personalization_strategy.get('delivery_strategy', 'interactive')
            
            # Execute base queries
            base_results = self._execute_queries(learner_id, course_id, learner_query)
            
            # Apply strategy-specific enhancements
            enhanced_results = {
                "base_queries": base_results,
                "strategy_enhanced": {
                    "learner_type_queries": self._get_learner_type_queries(learner_type),
                    "intervention_queries": self._get_intervention_queries(intervention_strategy),
                    "delivery_queries": self._get_delivery_queries(delivery_strategy),
                },
                "knowledge_graph_data": self._extract_knowledge_graph_data(base_results),
                "strategy_metadata": {
                    "learner_type": learner_type,
                    "intervention_strategy": intervention_strategy,
                    "delivery_strategy": delivery_strategy,
                    "query_timestamp": datetime.now().isoformat()
                }
            }
            
            return enhanced_results
            
        except Exception as e:
            raise Exception(f"Strategy-based query execution failed: {e}")
    
    def _get_learner_type_queries(self, learner_type: str) -> List[Dict]:
        """Get queries specific to learner type."""
        queries = []
        
        if learner_type == "visual":
            queries.extend([
                {"type": "visual_concepts", "query": "MATCH (n:Concept)-[:HAS_VISUAL_REPRESENTATION]->(v) RETURN n, v"},
                {"type": "diagrams", "query": "MATCH (n:Concept)-[:HAS_DIAGRAM]->(d) RETURN n, d"}
            ])
        elif learner_type == "auditory":
            queries.extend([
                {"type": "audio_content", "query": "MATCH (n:Concept)-[:HAS_AUDIO]->(a) RETURN n, a"},
                {"type": "verbal_explanations", "query": "MATCH (n:Concept)-[:HAS_EXPLANATION]->(e) RETURN n, e"}
            ])
        elif learner_type == "kinesthetic":
            queries.extend([
                {"type": "hands_on_activities", "query": "MATCH (n:Concept)-[:HAS_ACTIVITY]->(a) RETURN n, a"},
                {"type": "simulations", "query": "MATCH (n:Concept)-[:HAS_SIMULATION]->(s) RETURN n, s"}
            ])
        
        return queries
    
    def _get_intervention_queries(self, intervention_strategy: str) -> List[Dict]:
        """Get queries for intervention strategy."""
        queries = []
        
        if intervention_strategy == "scaffolding":
            queries.extend([
                {"type": "prerequisites", "query": "MATCH (n:Concept)-[:PREREQUISITE]->(p) RETURN n, p"},
                {"type": "step_by_step", "query": "MATCH (n:Concept)-[:HAS_STEPS]->(s) RETURN n, s"}
            ])
        elif intervention_strategy == "inquiry":
            queries.extend([
                {"type": "questions", "query": "MATCH (n:Concept)-[:HAS_QUESTION]->(q) RETURN n, q"},
                {"type": "explorations", "query": "MATCH (n:Concept)-[:ENABLES_EXPLORATION]->(e) RETURN n, e"}
            ])
        elif intervention_strategy == "collaborative":
            queries.extend([
                {"type": "group_activities", "query": "MATCH (n:Concept)-[:HAS_GROUP_ACTIVITY]->(g) RETURN n, g"},
                {"type": "peer_discussions", "query": "MATCH (n:Concept)-[:HAS_DISCUSSION]->(d) RETURN n, d"}
            ])
        
        return queries
    
    def _get_delivery_queries(self, delivery_strategy: str) -> List[Dict]:
        """Get queries for delivery strategy."""
        queries = []
        
        if delivery_strategy == "interactive":
            queries.extend([
                {"type": "interactive_elements", "query": "MATCH (n:Concept)-[:HAS_INTERACTIVE]->(i) RETURN n, i"},
                {"type": "simulations", "query": "MATCH (n:Concept)-[:HAS_SIMULATION]->(s) RETURN n, s"}
            ])
        elif delivery_strategy == "multimedia":
            queries.extend([
                {"type": "multimedia_content", "query": "MATCH (n:Concept)-[:HAS_MULTIMEDIA]->(m) RETURN n, m"},
                {"type": "rich_media", "query": "MATCH (n:Concept)-[:HAS_MEDIA]->(m) RETURN n, m"}
            ])
        elif delivery_strategy == "gamified":
            queries.extend([
                {"type": "game_elements", "query": "MATCH (n:Concept)-[:HAS_GAME_ELEMENT]->(g) RETURN n, g"},
                {"type": "challenges", "query": "MATCH (n:Concept)-[:HAS_CHALLENGE]->(c) RETURN n, c"}
            ])
        
        return queries
    
    def _extract_knowledge_graph_data(self, base_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured knowledge graph data from base results."""
        return {
            "concepts": base_results.get("concepts", []),
            "relationships": base_results.get("relationships", []),
            "difficulty_levels": base_results.get("difficulty_levels", []),
            "learning_objectives": base_results.get("learning_objectives", [])
        }
    
    def _execute_queries(self, learner_id: str, course_id: str, learner_query: str) -> Dict[str, Any]:
        """Execute various knowledge graph queries."""
        try:
            print("🔄 Executing knowledge graph queries...")
            
            # Import existing query functions - use correct function name
            from graph.query_strategy import determine_query_strategy
            
            # Execute different types of queries
            results = {
                "concepts": self._query_concepts(course_id),
                "relationships": self._query_relationships(course_id),
                "learning_objectives": self._query_learning_objectives(course_id),
                "difficulty_levels": self._query_difficulty_levels(course_id),
                "prerequisites": self._query_prerequisites(course_id),
                "assessments": self._query_assessments(course_id),
                "learner_progress": self._query_learner_progress(learner_id, course_id),
                "personalization_data": self._query_personalization_data(learner_id)
            }
            
            # Filter results based on learner query if provided
            if learner_query:
                results = self._filter_results_by_query(results, learner_query)
            
            print(f"✅ Executed {len(results)} different query types")
            return results
            
        except Exception as e:
            raise Exception(f"Query execution failed: {e}")
    
    def _query_concepts(self, course_id: str) -> List[Dict[str, Any]]:
        """Query concepts for a course."""
        # Stub implementation - would connect to Neo4j in production
        return [
            {"concept_id": "concept_1", "name": "Operating Systems", "difficulty": "intermediate"},
            {"concept_id": "concept_2", "name": "Memory Management", "difficulty": "advanced"}
        ]
    
    def _query_relationships(self, course_id: str) -> List[Dict[str, Any]]:
        """Query relationships between concepts."""
        # Stub implementation
        return [
            {"from_concept": "Operating Systems", "to_concept": "Memory Management", "relationship": "includes"}
        ]
    
    def _query_learning_objectives(self, course_id: str) -> List[Dict[str, Any]]:
        """Query learning objectives for a course."""
        # Stub implementation
        return [
            {"lo_id": "lo_1", "text": "Understand OS fundamentals", "priority": "high"},
            {"lo_id": "lo_2", "text": "Master memory management", "priority": "medium"}
        ]
    
    def _query_difficulty_levels(self, course_id: str) -> List[Dict[str, Any]]:
        """Query difficulty levels for course content."""
        # Stub implementation
        return [
            {"level": "beginner", "concepts": ["OS basics"]},
            {"level": "intermediate", "concepts": ["Process management"]},
            {"level": "advanced", "concepts": ["Memory optimization"]}
        ]
    
    def _query_prerequisites(self, course_id: str) -> List[Dict[str, Any]]:
        """Query prerequisites for course content."""
        # Stub implementation
        return [
            {"concept": "Memory Management", "prerequisites": ["Computer Architecture", "Data Structures"]}
        ]
    
    def _query_assessments(self, course_id: str) -> List[Dict[str, Any]]:
        """Query assessments for a course."""
        # Stub implementation
        return [
            {"assessment_id": "quiz_1", "type": "MCQ", "difficulty": "medium"},
            {"assessment_id": "project_1", "type": "hands_on", "difficulty": "high"}
        ]
    
    def _query_learner_progress(self, learner_id: str, course_id: str) -> Dict[str, Any]:
        """Query learner progress for a specific course."""
        # Stub implementation
        return {
            "learner_id": learner_id,
            "course_id": course_id,
            "completed_lessons": 3,
            "total_lessons": 10,
            "current_score": 75,
            "time_spent_minutes": 120
        }
    
    def _query_personalization_data(self, learner_id: str) -> Dict[str, Any]:
        """Query personalization data for a learner."""
        # Stub implementation
        return {
            "learner_id": learner_id,
            "learning_style": "visual",
            "preferred_difficulty": "medium",
            "interaction_pattern": "active"
        }
    
    def _filter_results_by_query(self, results: Dict[str, Any], learner_query: str) -> Dict[str, Any]:
        """Filter results based on learner query."""
        # Simple filtering - in production would use semantic search
        filtered_results = {}
        query_lower = learner_query.lower()
        
        for key, value in results.items():
            if isinstance(value, list):
                # Filter list items that might match the query
                filtered_results[key] = value  # For now, return all
            else:
                filtered_results[key] = value
        
        return filtered_results
    
    def get_service_definition(self):
        """Get service definition for registration."""
        from orchestrator.state import ServiceDefinition
        
        return ServiceDefinition(
            service_id=self.service_id,
            subsystem=self.subsystem,
            name="Graph Query Engine",
            description="Executes knowledge graph queries with adaptive strategy",
            dependencies=["query_strategy_manager"],  # Needs strategy to determine query approach
            required_inputs=["course_id", "query_strategy"],
            provided_outputs=["query_results", "knowledge_graph_data"],
            callable=self,
            timeout_seconds=300
        )

# ===============================
# SERVICE FACTORY
# ===============================

def create_graph_query_engine_service() -> GraphQueryEngineService:
    """Factory function to create graph query engine service."""
    return GraphQueryEngineService()

# ===============================
# LEGACY COMPATIBILITY
# ===============================

def graph_query_engine_service(state: UniversalState) -> UniversalState:
    """Legacy compatibility function."""
    service = create_graph_query_engine_service()
    return service(state) 