"""
Knowledge Graph Generator Service - Content Subsystem

Handles knowledge graph generation and storage across multiple databases:
Neo4j, MongoDB, PostgreSQL integration with FFCS output.
"""

from typing import Dict, Any, List, Optional
import logging
from orchestrator.state import UniversalState, ServiceStatus, SubsystemType

logger = logging.getLogger(__name__)

class KnowledgeGraphGeneratorService:
    """
    Knowledge Graph Generator microservice for the content subsystem.
    
    Responsibilities:
    - Generate complete knowledge graph from FCCS
    - Store in Neo4j for graph relationships
    - Store in MongoDB for document storage
    - Store in PostgreSQL for structured data
    - Produce Faculty Finalized Course Structure (FFCS)
    """
    
    def __init__(self):
        self.service_id = "knowledge_graph_generator"
        self.subsystem = SubsystemType.CONTENT
        
    def __call__(self, state: UniversalState) -> UniversalState:
        """
        Main entry point for knowledge graph generation.
        Compatible with LangGraph orchestrator.
        """
        print(f"📊 [Knowledge Graph Generator] Generating and storing knowledge graph...")
        
        try:
            # Check for required inputs (FCCS from KLI Application)
            fccs = state.get("fccs")
            if not fccs:
                raise ValueError("FCCS (Faculty Confirmed Course Structure) required for knowledge graph generation")
            
            if not state.get("fccs_approved", False):
                print("⚠️ FCCS not yet confirmed by faculty, proceeding with draft data")
            
            # Generate complete knowledge graph
            knowledge_graph = self._generate_knowledge_graph(fccs)
            
            # Store in multiple databases
            storage_results = self._store_knowledge_graph(knowledge_graph)
            
            # Generate FFCS (Faculty Finalized Course Structure)
            ffcs = self._generate_ffcs(fccs, knowledge_graph, storage_results)
            
            # Update state with results
            state["knowledge_graph"] = knowledge_graph
            state["ffcs"] = ffcs
            state["ffcs_approved"] = False  # Requires final faculty approval
            
            # Mark service as completed
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.COMPLETED
            
            # Store service result
            if "service_results" not in state:
                state["service_results"] = {}
            state["service_results"][self.service_id] = {
                "knowledge_graph": knowledge_graph,
                "storage_results": storage_results,
                "ffcs": ffcs,
                "total_nodes": len(knowledge_graph.get("nodes", [])),
                "total_relationships": len(knowledge_graph.get("relationships", []))
            }
            
            print(f"✅ Knowledge graph generation completed: {len(knowledge_graph.get('nodes', []))} nodes, {len(knowledge_graph.get('relationships', []))} relationships")
            return state
            
        except Exception as e:
            logger.error(f"Knowledge graph generation failed: {e}")
            
            # Mark service as error
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.ERROR
            
            # Store error
            if "service_errors" not in state:
                state["service_errors"] = {}
            state["service_errors"][self.service_id] = str(e)
            
            return state
    
    def _generate_knowledge_graph(self, fccs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete knowledge graph from FCCS."""
        try:
            nodes = []
            relationships = []
            
            # Extract components from FCCS
            learning_objectives = fccs.get("learning_objectives", [])
            knowledge_components = fccs.get("knowledge_components", [])
            learning_processes = fccs.get("learning_processes", [])
            instruction_methods = fccs.get("instruction_methods", [])
            
            # Create course node
            course_node = {
                "id": fccs.get("course_id", "default_course"),
                "type": "Course",
                "properties": {
                    "name": fccs.get("course_name", "Default Course"),
                    "version": fccs.get("version", "1.0")
                }
            }
            nodes.append(course_node)
            
            # Create learning objective nodes
            for lo in learning_objectives:
                lo_node = {
                    "id": lo.get("lo_id", ""),
                    "type": "LearningObjective",
                    "properties": {
                        "text": lo.get("text", ""),
                        "difficulty": lo.get("difficulty", "medium")
                    }
                }
                nodes.append(lo_node)
                
                # Course -> LO relationship
                relationships.append({
                    "from": course_node["id"],
                    "to": lo["lo_id"],
                    "type": "HAS_LO"
                })
            
            # Create knowledge component nodes
            for kc in knowledge_components:
                kc_node = {
                    "id": kc.get("kc_id", ""),
                    "type": "KnowledgeComponent",
                    "properties": {
                        "text": kc.get("text", ""),
                        "complexity": kc.get("complexity", "medium")
                    }
                }
                nodes.append(kc_node)
                
                # LO -> KC relationship
                if kc.get("lo_id"):
                    relationships.append({
                        "from": kc["lo_id"],
                        "to": kc["kc_id"],
                        "type": "HAS_KC"
                    })
            
            # Create learning process nodes
            for lp in learning_processes:
                lp_node = {
                    "id": lp.get("lp_id", ""),
                    "type": "LearningProcess",
                    "properties": {
                        "type": lp.get("type", ""),
                        "description": lp.get("description", ""),
                        "complexity": lp.get("complexity", "medium")
                    }
                }
                nodes.append(lp_node)
                
                # KC -> LP relationship
                if lp.get("kc_id"):
                    relationships.append({
                        "from": lp["kc_id"],
                        "to": lp["lp_id"],
                        "type": "REQUIRES"
                    })
            
            # Create instruction method nodes
            for im in instruction_methods:
                im_node = {
                    "id": im.get("im_id", ""),
                    "type": "InstructionMethod",
                    "properties": {
                        "type": im.get("type", ""),
                        "description": im.get("description", ""),
                        "duration": im.get("duration", "")
                    }
                }
                nodes.append(im_node)
                
                # LP -> IM relationship
                if im.get("lp_id"):
                    relationships.append({
                        "from": im["lp_id"],
                        "to": im["im_id"],
                        "type": "BEST_SUPPORTED_BY"
                    })
            
            knowledge_graph = {
                "nodes": nodes,
                "relationships": relationships,
                "metadata": {
                    "total_nodes": len(nodes),
                    "total_relationships": len(relationships),
                    "node_types": list(set([node["type"] for node in nodes])),
                    "relationship_types": list(set([rel["type"] for rel in relationships]))
                }
            }
            
            return knowledge_graph
            
        except Exception as e:
            raise Exception(f"Knowledge graph generation failed: {e}")
    
    def _store_knowledge_graph(self, knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Store knowledge graph in multiple databases."""
        storage_results = {}
        
        # Store in Neo4j
        try:
            neo4j_result = self._store_in_neo4j(knowledge_graph)
            storage_results["neo4j"] = neo4j_result
        except Exception as e:
            storage_results["neo4j"] = {"status": "error", "error": str(e)}
        
        # Store in MongoDB (placeholder for future implementation)
        try:
            mongodb_result = self._store_in_mongodb(knowledge_graph)
            storage_results["mongodb"] = mongodb_result
        except Exception as e:
            storage_results["mongodb"] = {"status": "error", "error": str(e)}
        
        # Store in PostgreSQL (placeholder for future implementation)
        try:
            postgresql_result = self._store_in_postgresql(knowledge_graph)
            storage_results["postgresql"] = postgresql_result
        except Exception as e:
            storage_results["postgresql"] = {"status": "error", "error": str(e)}
        
        return storage_results
    
    def _store_in_neo4j(self, knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Store knowledge graph in Neo4j using existing database functions."""
        try:
            # Convert to format expected by existing Neo4j functions
            data_list = self._convert_to_neo4j_format(knowledge_graph)
            
            # Use existing database function
            from graph.db import insert_lo_kc_lp_im
            insert_lo_kc_lp_im(data_list)
            
            return {
                "status": "success",
                "records_inserted": len(data_list),
                "database": "neo4j"
            }
            
        except Exception as e:
            raise Exception(f"Neo4j storage failed: {e}")
    
    def _convert_to_neo4j_format(self, knowledge_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert knowledge graph to format expected by existing Neo4j functions."""
        data_list = []
        
        nodes = knowledge_graph.get("nodes", [])
        relationships = knowledge_graph.get("relationships", [])
        
        # Group nodes by type for easier processing
        nodes_by_id = {node["id"]: node for node in nodes}
        
        # Find LO nodes and build records
        lo_nodes = [node for node in nodes if node["type"] == "LearningObjective"]
        
        for lo_node in lo_nodes:
            lo_id = lo_node["id"]
            lo_text = lo_node["properties"]["text"]
            
            # Find associated KC, LP, and IM
            kc_ids = [rel["to"] for rel in relationships if rel["from"] == lo_id and rel["type"] == "HAS_KC"]
            
            for kc_id in kc_ids:
                kc_node = nodes_by_id.get(kc_id)
                if not kc_node:
                    continue
                
                kc_text = kc_node["properties"]["text"]
                
                # Find associated LP
                lp_ids = [rel["to"] for rel in relationships if rel["from"] == kc_id and rel["type"] == "REQUIRES"]
                
                for lp_id in lp_ids:
                    lp_node = nodes_by_id.get(lp_id)
                    if not lp_node:
                        continue
                    
                    lp_type = lp_node["properties"]["type"]
                    
                    # Find associated IM
                    im_ids = [rel["to"] for rel in relationships if rel["from"] == lp_id and rel["type"] == "BEST_SUPPORTED_BY"]
                    
                    for im_id in im_ids:
                        im_node = nodes_by_id.get(im_id)
                        if not im_node:
                            continue
                        
                        im_description = im_node["properties"]["description"]
                        
                        # Create record in expected format
                        record = {
                            "lo": lo_text,
                            "kc": kc_text,
                            "learning_process": lp_type,
                            "recommended_instruction": im_description
                        }
                        data_list.append(record)
        
        # Ensure at least one record for testing
        if not data_list:
            data_list.append({
                "lo": "Default Learning Objective",
                "kc": "Default Knowledge Component",
                "learning_process": "Understanding",
                "recommended_instruction": "Lecture"
            })
        
        return data_list
    
    def _store_in_mongodb(self, knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Store knowledge graph in MongoDB (placeholder)."""
        # Placeholder for MongoDB implementation
        return {
            "status": "not_implemented",
            "message": "MongoDB storage not yet implemented",
            "database": "mongodb"
        }
    
    def _store_in_postgresql(self, knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Store knowledge graph in PostgreSQL (placeholder)."""
        # Placeholder for PostgreSQL implementation
        return {
            "status": "not_implemented", 
            "message": "PostgreSQL storage not yet implemented",
            "database": "postgresql"
        }
    
    def _generate_ffcs(self, fccs: Dict[str, Any], knowledge_graph: Dict[str, Any], storage_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Faculty Finalized Course Structure (FFCS)."""
        try:
            ffcs = {
                "version": "1.0",
                "generated_at": "auto",
                "status": "ready_for_production",
                "learning_objectives": fccs.get("learning_objectives", []),
                "knowledge_components": fccs.get("knowledge_components", []),
                "learning_processes": fccs.get("learning_processes", []),
                "instruction_methods": fccs.get("instruction_methods", []),
                "knowledge_graph": knowledge_graph,
                "storage_status": storage_results,
                "metadata": {
                    "total_los": len(fccs.get("learning_objectives", [])),
                    "total_kcs": len(fccs.get("knowledge_components", [])),
                    "total_lps": len(fccs.get("learning_processes", [])),
                    "total_ims": len(fccs.get("instruction_methods", [])),
                    "graph_nodes": len(knowledge_graph.get("nodes", [])),
                    "graph_relationships": len(knowledge_graph.get("relationships", [])),
                    "databases_targeted": list(storage_results.keys()),
                    "successful_storage": [db for db, result in storage_results.items() if result.get("status") == "success"],
                    "requires_final_approval": True
                }
            }
            
            return ffcs
            
        except Exception as e:
            raise Exception(f"FFCS generation failed: {e}")
    
    def get_service_definition(self):
        """Get service definition for registration."""
        from orchestrator.state import ServiceDefinition
        
        return ServiceDefinition(
            service_id=self.service_id,
            subsystem=self.subsystem,
            name="Knowledge Graph Generator",
            description="Generates and stores complete knowledge graph across Neo4j, MongoDB, and PostgreSQL",
            dependencies=["kli_application"],  # Needs FCCS
            required_inputs=["fccs"],
            provided_outputs=["knowledge_graph", "ffcs"],
            callable=self,
            timeout_seconds=900  # KG generation can take longer
        )

# ===============================
# SERVICE FACTORY
# ===============================

def create_knowledge_graph_generator_service() -> KnowledgeGraphGeneratorService:
    """Factory function to create knowledge graph generator service."""
    return KnowledgeGraphGeneratorService()

# ===============================
# LEGACY COMPATIBILITY
# ===============================

def knowledge_graph_generator_service(state: UniversalState) -> UniversalState:
    """Legacy compatibility function."""
    service = create_knowledge_graph_generator_service()
    return service(state) 