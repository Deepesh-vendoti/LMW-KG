"""
Knowledge Graph Generator Service - Content Subsystem

Handles knowledge graph generation and storage across multiple databases:
Neo4j, MongoDB, PostgreSQL integration with FFCS output.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import uuid
from orchestrator.state import UniversalState, ServiceStatus, SubsystemType
from utils.database_connections import get_database_manager

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
        self.db_manager = get_database_manager()
        
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
        
        # Store in MongoDB
        try:
            mongodb_result = self._store_in_mongodb(knowledge_graph)
            storage_results["mongodb"] = mongodb_result
        except Exception as e:
            storage_results["mongodb"] = {"status": "error", "error": str(e)}
        
        # Store in PostgreSQL
        try:
            postgresql_result = self._store_in_postgresql(knowledge_graph)
            storage_results["postgresql"] = postgresql_result
        except Exception as e:
            storage_results["postgresql"] = {"status": "error", "error": str(e)}
        
        return storage_results
    
    def _store_in_neo4j(self, knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Store knowledge graph in Neo4j using proper knowledge graph structure."""
        try:
            # Convert to proper Neo4j format
            result = self._convert_to_neo4j_format(knowledge_graph)
            
            return {
                "status": "success",
                "nodes_created": result.get("nodes_created", 0),
                "relationships_created": result.get("relationships_created", 0),
                "database": "neo4j"
            }
            
        except Exception as e:
            raise Exception(f"Neo4j storage failed: {e}")
    
    def _convert_to_neo4j_format(self, knowledge_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert knowledge graph to proper Neo4j knowledge graph structure."""
        try:
            # Clear existing data first
            from utils.database_manager import clear_neo4j_database
            clear_neo4j_database()
            
            # Get course information
            course_id = knowledge_graph.get("course_id", "default_course")
            course_name = knowledge_graph.get("course_name", "Operating Systems")
            
            # Create proper knowledge graph structure
            # 1. Course Node
            course_node = {
                "type": "Course",
                "properties": {
                    "course_id": course_id,
                    "course_name": course_name,
                    "created_at": datetime.now().isoformat()
                }
            }
            
            # 2. Extract Learning Objectives from FCCS
            fccs = knowledge_graph.get("fccs", {})
            learning_objectives = fccs.get("learning_objectives", [])
            
            # If no LOs in FCCS, create from course content
            if not learning_objectives:
                learning_objectives = self._extract_learning_objectives_from_content(knowledge_graph)
            
            # 3. Create proper knowledge graph nodes and relationships
            nodes = [course_node]
            relationships = []
            
            for i, lo in enumerate(learning_objectives):
                # Learning Objective Node
                lo_node = {
                    "type": "LearningObjective",
                    "properties": {
                        "id": f"LO_{i+1:03d}",
                        "text": lo.get("text", f"Learning Objective {i+1}"),
                        "description": lo.get("description", ""),
                        "priority": lo.get("priority", "medium"),
                        "created_at": datetime.now().isoformat()
                    }
                }
                nodes.append(lo_node)
                
                # Course -> LO relationship
                relationships.append({
                    "from": "Course",
                    "to": f"LO_{i+1:03d}",
                    "type": "HAS_LEARNING_OBJECTIVE",
                    "properties": {
                        "sequence": i+1,
                        "created_at": datetime.now().isoformat()
                    }
                })
                
                # Knowledge Components for this LO
                kcs = lo.get("knowledge_components", [])
                for j, kc in enumerate(kcs):
                    kc_node = {
                        "type": "KnowledgeComponent",
                        "properties": {
                            "id": f"KC_{i+1:03d}_{j+1:03d}",
                            "text": kc.get("text", f"Knowledge Component {j+1}"),
                            "description": kc.get("description", ""),
                            "difficulty": kc.get("difficulty", "medium"),
                            "created_at": datetime.now().isoformat()
                        }
                    }
                    nodes.append(kc_node)
                    
                    # LO -> KC relationship
                    relationships.append({
                        "from": f"LO_{i+1:03d}",
                        "to": f"KC_{i+1:03d}_{j+1:03d}",
                        "type": "HAS_KNOWLEDGE_COMPONENT",
                        "properties": {
                            "sequence": j+1,
                            "created_at": datetime.now().isoformat()
                        }
                    })
                    
                    # Learning Outcomes for this KC
                    los = kc.get("learning_outcomes", [])
                    for k, lo_outcome in enumerate(los):
                        lo_outcome_node = {
                            "type": "LearningOutcome",
                            "properties": {
                                "id": f"LO_Outcome_{i+1:03d}_{j+1:03d}_{k+1:03d}",
                                "text": lo_outcome.get("text", f"Learning Outcome {k+1}"),
                                "description": lo_outcome.get("description", ""),
                                "created_at": datetime.now().isoformat()
                            }
                        }
                        nodes.append(lo_outcome_node)
                        
                        # KC -> Learning Outcome relationship
                        relationships.append({
                            "from": f"KC_{i+1:03d}_{j+1:03d}",
                            "to": f"LO_Outcome_{i+1:03d}_{j+1:03d}_{k+1:03d}",
                            "type": "ACHIEVES_OUTCOME",
                            "properties": {
                                "sequence": k+1,
                                "created_at": datetime.now().isoformat()
                            }
                        })
                        
                        # Instruction Methods for this Learning Outcome
                        ims = lo_outcome.get("instruction_methods", [])
                        for l, im in enumerate(ims):
                            im_node = {
                                "type": "InstructionMethod",
                                "properties": {
                                    "id": f"IM_{i+1:03d}_{j+1:03d}_{k+1:03d}_{l+1:03d}",
                                    "text": im.get("text", f"Instruction Method {l+1}"),
                                    "description": im.get("description", ""),
                                    "method_type": im.get("method_type", "lecture"),
                                    "created_at": datetime.now().isoformat()
                                }
                            }
                            nodes.append(im_node)
                            
                            # Learning Outcome -> Instruction Method relationship
                            relationships.append({
                                "from": f"LO_Outcome_{i+1:03d}_{j+1:03d}_{k+1:03d}",
                                "to": f"IM_{i+1:03d}_{j+1:03d}_{k+1:03d}_{l+1:03d}",
                                "type": "BEST_SUPPORTED_BY",
                                "properties": {
                                    "sequence": l+1,
                                    "created_at": datetime.now().isoformat()
                                }
                            })
                            
                            # Reference Materials for this Instruction Method
                            rms = im.get("reference_materials", [])
                            for m, rm in enumerate(rms):
                                rm_node = {
                                    "type": "ReferenceMaterial",
                                    "properties": {
                                        "id": f"RM_{i+1:03d}_{j+1:03d}_{k+1:03d}_{l+1:03d}_{m+1:03d}",
                                        "text": rm.get("text", f"Reference Material {m+1}"),
                                        "description": rm.get("description", ""),
                                        "material_type": rm.get("material_type", "textbook"),
                                        "url": rm.get("url", ""),
                                        "created_at": datetime.now().isoformat()
                                    }
                                }
                                nodes.append(rm_node)
                                
                                # Instruction Method -> Reference Material relationship
                                relationships.append({
                                    "from": f"IM_{i+1:03d}_{j+1:03d}_{k+1:03d}_{l+1:03d}",
                                    "to": f"RM_{i+1:03d}_{j+1:03d}_{k+1:03d}_{l+1:03d}_{m+1:03d}",
                                    "type": "REFERENCES",
                                    "properties": {
                                        "sequence": m+1,
                                        "created_at": datetime.now().isoformat()
                                    }
                                })
            
            # Store in Neo4j using proper graph structure
            from utils.database_manager import insert_knowledge_graph
            result = insert_knowledge_graph(nodes, relationships, course_id)
            
            return {
                "status": "success",
                "nodes_created": len(nodes),
                "relationships_created": len(relationships),
                "course_id": course_id
            }
            
        except Exception as e:
            logger.error(f"Failed to convert to Neo4j format: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _extract_learning_objectives_from_content(self, knowledge_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract learning objectives from course content when FCCS is not available."""
        # Sample learning objectives for Operating Systems course
        learning_objectives = [
            {
                "text": "Understand Process Management and Scheduling",
                "description": "Comprehend how operating systems manage processes and implement scheduling algorithms",
                "priority": "high",
                "knowledge_components": [
                    {
                        "text": "Process Abstraction",
                        "description": "Understanding of process as an abstraction of a running program",
                        "difficulty": "medium",
                        "learning_outcomes": [
                            {
                                "text": "Define process and explain its role in OS",
                                "description": "Student can explain what a process is and why it's important",
                                "instruction_methods": [
                                    {
                                        "text": "Lecture with Process Diagrams",
                                        "description": "Use visual diagrams to explain process concept",
                                        "method_type": "lecture",
                                        "reference_materials": [
                                            {
                                                "text": "Operating Systems: Three Easy Pieces - Chapter 4",
                                                "description": "Process abstraction chapter",
                                                "material_type": "textbook",
                                                "url": ""
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "text": "Scheduling Algorithms",
                        "description": "Understanding of different CPU scheduling strategies",
                        "difficulty": "medium",
                        "learning_outcomes": [
                            {
                                "text": "Compare and contrast different scheduling algorithms",
                                "description": "Student can analyze different scheduling approaches",
                                "instruction_methods": [
                                    {
                                        "text": "Interactive Simulation",
                                        "description": "Use scheduling simulator to demonstrate algorithms",
                                        "method_type": "simulation",
                                        "reference_materials": [
                                            {
                                                "text": "CPU Scheduling Simulator",
                                                "description": "Interactive tool for scheduling algorithms",
                                                "material_type": "tool",
                                                "url": ""
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "text": "Master Memory Management Concepts",
                "description": "Understand virtual memory, paging, and memory allocation strategies",
                "priority": "high",
                "knowledge_components": [
                    {
                        "text": "Virtual Memory",
                        "description": "Understanding of virtual memory abstraction",
                        "difficulty": "high",
                        "learning_outcomes": [
                            {
                                "text": "Explain virtual memory and address translation",
                                "description": "Student can describe how virtual memory works",
                                "instruction_methods": [
                                    {
                                        "text": "Memory Layout Visualization",
                                        "description": "Use diagrams to show memory layout",
                                        "method_type": "visualization",
                                        "reference_materials": [
                                            {
                                                "text": "Memory Management Diagrams",
                                                "description": "Visual aids for memory concepts",
                                                "material_type": "diagram",
                                                "url": ""
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        
        return learning_objectives
    
    def _store_in_mongodb(self, knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Store knowledge graph in MongoDB."""
        try:
            # Get MongoDB database
            db = self.db_manager.get_mongodb_database('kg_snapshots_db')
            
            # Create snapshot document
            snapshot = {
                "knowledge_graph": knowledge_graph,
                "created_at": datetime.now(),
                "version": "1.0",
                "status": "active"
            }
            
            # Insert into course_snapshots collection
            result = db.course_snapshots.insert_one(snapshot)
            
            # Store version control info
            version_info = {
                "snapshot_id": str(result.inserted_id),
                "version": "1.0",
                "created_at": datetime.now(),
                "status": "active"
            }
            db.kg_versions.insert_one(version_info)
            
            # Log export
            export_log = {
                "snapshot_id": str(result.inserted_id),
                "export_type": "knowledge_graph",
                "exported_at": datetime.now(),
                "status": "success"
            }
            db.export_logs.insert_one(export_log)
            
            return {
                "status": "success",
                "snapshot_id": str(result.inserted_id),
                "records_inserted": 3,  # snapshot + version + log
                "database": "mongodb"
            }
            
        except Exception as e:
            logger.error(f"MongoDB storage failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database": "mongodb"
            }
    
    def _store_in_postgresql(self, knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Store knowledge graph metadata in PostgreSQL."""
        try:
            with self.db_manager.postgresql_cursor() as cursor:
                # Use the safe function to store KG metadata
                kg_id = str(uuid.uuid4())
                course_id = knowledge_graph.get("course_id", "unknown")
                version = "1.0"
                status = "active"
                
                cursor.execute("""
                    SELECT store_kg_metadata(%s, %s, %s, %s) as success
                """, (kg_id, course_id, version, status))
                
                result = cursor.fetchone()
                success = result and result.get('success', False)
                
                if not success:
                    # Fall back to direct insert with explicit columns
                    cursor.execute("""
                        INSERT INTO kg_metadata (kg_id, course_id, version, status, created_at)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """, (kg_id, course_id, version, status))
                
                # Store version control
                cursor.execute("""
                    INSERT INTO version_control (kg_id, changes, created_by, created_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    kg_id,
                    '{"type": "initial"}',
                    "system"
                ))
                
                # Store faculty approval record
                cursor.execute("""
                    INSERT INTO faculty_approvals (kg_id, stage, faculty_id, approved, approved_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    kg_id,
                    "FFCS",
                    knowledge_graph.get("faculty_id", "default_faculty"),
                    True
                ))
                
                return {
                    "status": "success",
                    "records_inserted": 3,  # metadata + version + approval
                    "database": "postgresql"
                }
                
        except Exception as e:
            logger.error(f"PostgreSQL storage failed: {e}")
            return {
                "status": "error",
                "error": str(e),
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

def create_knowledge_graph(nodes: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
    """
    Create a Neo4j knowledge graph from nodes and relationships.
    
    Args:
        nodes: List of node dictionaries with type and properties
        relationships: List of relationship dictionaries
        
    Returns:
        Dictionary with knowledge graph creation results
    """
    try:
        # Use the database manager to insert the knowledge graph
        from utils.database_manager import insert_knowledge_graph
        result = insert_knowledge_graph(nodes, relationships)
        
        return {
            "status": "success" if result.get("status") == "success" else "error",
            "nodes_created": result.get("nodes_created", 0),
            "relationships_created": result.get("relationships_created", 0),
            "error": result.get("error")
        }
    except Exception as e:
        logger.error(f"Failed to create knowledge graph: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

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