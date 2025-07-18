"""
Graph Query Engine Service - Learner Subsystem

Wrapper for existing Neo4j query functionality in graph/db.py.
Provides Cypher query generation and execution for learner queries.
"""

from typing import Dict, Any, List, Optional
import logging
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
        
    def __call__(self, state: UniversalState) -> UniversalState:
        """
        Main entry point for graph query execution.
        Compatible with LangGraph orchestrator.
        """
        print(f"🔍 [Graph Query Engine] Executing queries...")
        
        try:
            # Extract query context
            learner_id = state.get("learner_id")
            course_id = state.get("course_id") 
            learner_query = state.get("learner_query", "")
            
            if not learner_id or not course_id:
                raise ValueError("Learner ID and Course ID are required")
            
            # Execute various query types using existing functions
            query_results = self._execute_queries(learner_id, course_id, learner_query)
            
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
    
    def _execute_queries(self, learner_id: str, course_id: str, learner_query: str) -> List[Dict[str, Any]]:
        """Execute various query types using existing database functions."""
        try:
            print("🔄 Using existing Neo4j query functions...")
            
            query_results = []
            
            # Query 1: Get PLT for learner (existing function)
            try:
                from graph.db import get_plt_for_learner
                plt_steps = get_plt_for_learner(learner_id, course_id)
                
                query_results.append({
                    "query_type": "plt_for_learner",
                    "query": f"PLT steps for learner {learner_id} in course {course_id}",
                    "results": plt_steps,
                    "count": len(plt_steps) if plt_steps else 0,
                    "status": "success"
                })
                
            except Exception as e:
                query_results.append({
                    "query_type": "plt_for_learner",
                    "query": f"PLT steps for learner {learner_id} in course {course_id}",
                    "results": [],
                    "count": 0,
                    "status": "error",
                    "error": str(e)
                })
            
            # Query 2: Get knowledge components under learning objectives (existing function)
            try:
                from graph.db import get_kcs_under_lo
                
                # Get a sample LO to query KCs (in practice, this would be more sophisticated)
                sample_lo = "Understand Memory Management"
                kcs = get_kcs_under_lo(sample_lo)
                
                query_results.append({
                    "query_type": "kcs_under_lo",
                    "query": f"Knowledge components under LO: {sample_lo}",
                    "results": kcs,
                    "count": len(kcs) if kcs else 0,
                    "status": "success"
                })
                
            except Exception as e:
                query_results.append({
                    "query_type": "kcs_under_lo",
                    "query": f"Knowledge components under LO: {sample_lo}",
                    "results": [],
                    "count": 0,
                    "status": "error",
                    "error": str(e)
                })
            
            # Query 3: Get best instruction method for KC and learning process (existing function)
            try:
                from graph.db import get_best_im_for_kc_lp
                
                # Sample query (in practice, this would be driven by learner context)
                sample_kc = "Virtual Memory Concepts"
                sample_lp = "Understanding"
                best_im = get_best_im_for_kc_lp(sample_kc, sample_lp)
                
                query_results.append({
                    "query_type": "best_im_for_kc_lp",
                    "query": f"Best IM for KC: {sample_kc}, LP: {sample_lp}",
                    "results": best_im,
                    "count": len(best_im) if best_im else 0,
                    "status": "success"
                })
                
            except Exception as e:
                query_results.append({
                    "query_type": "best_im_for_kc_lp",
                    "query": f"Best IM for KC: {sample_kc}, LP: {sample_lp}",
                    "results": [],
                    "count": 0,
                    "status": "error",
                    "error": str(e)
                })
            
            # Query 4: Custom learner query (if provided)
            if learner_query:
                try:
                    # For now, we'll provide a mock response
                    # In practice, this would parse the query and execute appropriate Cypher
                    custom_result = {
                        "query_type": "custom_learner_query",
                        "query": learner_query,
                        "results": [{"message": f"Processed query: {learner_query}"}],
                        "count": 1,
                        "status": "mock_response"
                    }
                    query_results.append(custom_result)
                    
                except Exception as e:
                    query_results.append({
                        "query_type": "custom_learner_query",
                        "query": learner_query,
                        "results": [],
                        "count": 0,
                        "status": "error",
                        "error": str(e)
                    })
            
            return query_results
            
        except Exception as e:
            raise Exception(f"Query execution failed: {e}")
    
    def get_service_definition(self):
        """Get service definition for registration."""
        from orchestrator.state import ServiceDefinition
        
        return ServiceDefinition(
            service_id=self.service_id,
            subsystem=self.subsystem,
            name="Graph Query Engine",
            description="Executes Cypher queries against Neo4j using existing database functions",
            dependencies=["learning_tree_handler"],  # Typically runs after PLT generation
            required_inputs=["learner_id", "course_id"],
            provided_outputs=["query_results"],
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