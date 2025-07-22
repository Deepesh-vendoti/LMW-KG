"""
Unified Database Manager

Consolidates all database operations across the system:
- Neo4j knowledge graph operations
- PostgreSQL structured data
- MongoDB document storage
- Redis caching
"""

from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase
from graph.config import NEO4J_URI, NEO4J_AUTH
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Unified database manager for all database operations.
    
    Consolidates scattered database functions into a single interface:
    - Knowledge graph operations (Neo4j)
    - Learning tree operations (Neo4j)
    - Course data operations (Neo4j)
    - Learner data operations (Neo4j)
    - Document storage (MongoDB)
    - Structured data (PostgreSQL)
    - Caching (Redis)
    """
    
    def __init__(self):
        """Initialize database connections."""
        # Use the database connection manager for proper authentication handling
        from utils.database_connections import get_database_manager as get_conn_manager
        conn_manager = get_conn_manager()
        self.neo4j_driver = conn_manager.get_neo4j_driver('course_mapper')
        
        logger.info("DatabaseManager initialized")
    
    # ===============================
    # KNOWLEDGE GRAPH OPERATIONS
    # ===============================
    
    def insert_knowledge_graph(self, nodes: List[Dict], relationships: List[Dict], course_id: str = None) -> Dict[str, Any]:
        """
        Insert complete knowledge graph structure into Neo4j.
        
        Args:
            nodes: List of node dictionaries with type and properties
            relationships: List of relationship dictionaries
            
        Returns:
            Result dictionary with operation status
        """
        try:
            with self.neo4j_driver.session() as session:
                # Create nodes
                for node in nodes:
                    node_type = node["type"]
                    properties = node["properties"]
                    
                    session.run(f"""
                        CREATE (n:{node_type} {{
                            {', '.join([f'{k}: ${k}' for k in properties.keys()])}
                        }})
                    """, **properties)
                
                # Create relationships
                for rel in relationships:
                    from_node = rel["from"]
                    to_node = rel["to"]
                    rel_type = rel["type"]
                    properties = rel.get("properties", {})
                    
                    # Handle different node identification patterns
                    if from_node == "Course":
                        # Course nodes are identified by course_id
                        session.run(f"""
                            MATCH (a:Course {{course_id: $course_id}}), (b {{id: $to_node}})
                            CREATE (a)-[r:{rel_type} {{
                                {', '.join([f'{k}: ${k}' for k in properties.keys()])}
                            }}]->(b)
                        """, course_id=course_id or "default_course", to_node=to_node, **properties)
                    else:
                        # Other nodes are identified by id
                        session.run(f"""
                            MATCH (a {{id: $from_node}}), (b {{id: $to_node}})
                            CREATE (a)-[r:{rel_type} {{
                                {', '.join([f'{k}: ${k}' for k in properties.keys()])}
                            }}]->(b)
                        """, from_node=from_node, to_node=to_node, **properties)
            
            return {
                "status": "success",
                "nodes_created": len(nodes),
                "relationships_created": len(relationships),
                "database": "neo4j"
            }
            
        except Exception as e:
            logger.error(f"Failed to insert knowledge graph: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database": "neo4j"
            }
    
    def insert_learning_tree(self, plt_data: Dict[str, Any], learner_id: str, course_id: str) -> Dict[str, Any]:
        """
        Insert personalized learning tree into Neo4j.
        
        Args:
            plt_data: Learning tree data structure
            learner_id: Learner identifier
            course_id: Course identifier
            
        Returns:
            Result dictionary with operation status
        """
        try:
            with self.neo4j_driver.session() as session:
                # Clear existing PLT for this learner/course
                session.run("""
                    MATCH (n:PersonalizedLearningStep)
                    WHERE n.learner_id = $learner_id AND n.course_id = $course_id
                    DETACH DELETE n
                """, learner_id=learner_id, course_id=course_id)
                
                # Insert new PLT steps
                steps = plt_data.get("steps", [])
                for step in steps:
                    session.run("""
                        CREATE (n:PersonalizedLearningStep {
                            learner_id: $learner_id,
                            course_id: $course_id,
                            step_id: $step_id,
                            lo: $lo,
                            kc: $kc,
                            instruction_method: $instruction_method,
                            sequence: $sequence
                        })
                    """, 
                    learner_id=learner_id,
                    course_id=course_id,
                    step_id=step.get("step_id"),
                    lo=step.get("lo"),
                    kc=step.get("kc"),
                    instruction_method=step.get("instruction_method"),
                    sequence=step.get("sequence"))
            
            return {
                "status": "success",
                "steps_inserted": len(steps),
                "learner_id": learner_id,
                "course_id": course_id,
                "database": "neo4j"
            }
            
        except Exception as e:
            logger.error(f"Failed to insert learning tree: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database": "neo4j"
            }
    
    def insert_course_data(self, course_id: str, course_name: str, **kwargs) -> Dict[str, Any]:
        """
        Insert course data into Neo4j.
        
        Args:
            course_id: Course identifier
            course_name: Course name
            **kwargs: Additional course properties
            
        Returns:
            Result dictionary with operation status
        """
        try:
            with self.neo4j_driver.session() as session:
                properties = {"course_id": course_id, "course_name": course_name, **kwargs}
                
                session.run("""
                    MERGE (:Course {
                        course_id: $course_id,
                        course_name: $course_name,
                        created_at: datetime(),
                        status: 'active'
                    })
                """, **properties)
            
            return {
                "status": "success",
                "course_id": course_id,
                "course_name": course_name,
                "database": "neo4j"
            }
            
        except Exception as e:
            logger.error(f"Failed to insert course data: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database": "neo4j"
            }
    
    def insert_learner_data(self, learner_id: str, name: str, **kwargs) -> Dict[str, Any]:
        """
        Insert learner data into Neo4j.
        
        Args:
            learner_id: Learner identifier
            name: Learner name
            **kwargs: Additional learner properties
            
        Returns:
            Result dictionary with operation status
        """
        try:
            with self.neo4j_driver.session() as session:
                properties = {"learner_id": learner_id, "name": name, **kwargs}
                
                session.run("""
                    MERGE (:Learner {
                        learner_id: $learner_id,
                        name: $name,
                        created_at: datetime(),
                        status: 'active'
                    })
                """, **properties)
            
            return {
                "status": "success",
                "learner_id": learner_id,
                "name": name,
                "database": "neo4j"
            }
            
        except Exception as e:
            logger.error(f"Failed to insert learner data: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database": "neo4j"
            }
    
    def link_course_to_learning_objectives(self, course_id: str, lo_names: List[str]) -> Dict[str, Any]:
        """
        Link course to its learning objectives.
        
        Args:
            course_id: Course identifier
            lo_names: List of learning objective names
            
        Returns:
            Result dictionary with operation status
        """
        try:
            with self.neo4j_driver.session() as session:
                for lo in lo_names:
                    session.run("""
                        MATCH (c:Course {course_id: $course_id}), (lo:LearningObjective {text: $lo})
                        MERGE (c)-[:HAS_LEARNING_OBJECTIVE]->(lo)
                    """, course_id=course_id, lo=lo)
            
            return {
                "status": "success",
                "course_id": course_id,
                "learning_objectives_linked": len(lo_names),
                "database": "neo4j"
            }
            
        except Exception as e:
            logger.error(f"Failed to link course to LOs: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database": "neo4j"
            }
    
    def link_learner_to_course(self, learner_id: str, course_id: str) -> Dict[str, Any]:
        """
        Link learner to course enrollment.
        
        Args:
            learner_id: Learner identifier
            course_id: Course identifier
            
        Returns:
            Result dictionary with operation status
        """
        try:
            with self.neo4j_driver.session() as session:
                session.run("""
                    MATCH (l:Learner {learner_id: $learner_id}), (c:Course {course_id: $course_id})
                    MERGE (l)-[:ENROLLED_IN]->(c)
                """, learner_id=learner_id, course_id=course_id)
            
            return {
                "status": "success",
                "learner_id": learner_id,
                "course_id": course_id,
                "database": "neo4j"
            }
            
        except Exception as e:
            logger.error(f"Failed to link learner to course: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database": "neo4j"
            }
    
    # ===============================
    # QUERY OPERATIONS
    # ===============================
    
    def get_knowledge_components_for_lo(self, lo_name: str) -> List[str]:
        """
        Get knowledge components for a learning objective.
        
        Args:
            lo_name: Learning objective name
            
        Returns:
            List of knowledge component names
        """
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (lo:LearningObjective {text: $lo_name})-[:HAS_KNOWLEDGE_COMPONENT]->(kc:KnowledgeComponent)
                    RETURN kc.text AS kc_name
                """, lo_name=lo_name)
                return [record["kc_name"] for record in result]
        except Exception as e:
            logger.error(f"Failed to get KCs for LO: {e}")
            return []
    
    def get_instruction_methods_for_kc(self, kc_name: str) -> List[str]:
        """
        Get instruction methods for a knowledge component.
        
        Args:
            kc_name: Knowledge component name
            
        Returns:
            List of instruction method descriptions
        """
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (kc:KnowledgeComponent {text: $kc_name})-[:ACHIEVES_OUTCOME]->(lo:LearningOutcome)
                    -[:BEST_SUPPORTED_BY]->(im:InstructionMethod)
                    RETURN im.text AS im_description
                """, kc_name=kc_name)
                return [record["im_description"] for record in result]
        except Exception as e:
            logger.error(f"Failed to get IMs for KC: {e}")
            return []
    
    def get_learning_tree_for_learner(self, learner_id: str, course_id: str) -> List[Dict[str, Any]]:
        """
        Get personalized learning tree for a learner.
        
        Args:
            learner_id: Learner identifier
            course_id: Course identifier
            
        Returns:
            List of learning tree steps
        """
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (n:PersonalizedLearningStep)
                    WHERE n.learner_id = $learner_id AND n.course_id = $course_id
                    RETURN n
                    ORDER BY n.sequence
                """, learner_id=learner_id, course_id=course_id)
                return [dict(record["n"]) for record in result]
        except Exception as e:
            logger.error(f"Failed to get learning tree: {e}")
            return []
    
    # ===============================
    # UTILITY OPERATIONS
    # ===============================
    
    def clear_database(self) -> Dict[str, Any]:
        """
        Clear all data from Neo4j database.
        
        Returns:
            Result dictionary with operation status
        """
        try:
            with self.neo4j_driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            
            return {
                "status": "success",
                "message": "All nodes and relationships cleared",
                "database": "neo4j"
            }
            
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database": "neo4j"
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            with self.neo4j_driver.session() as session:
                # Get node counts by type
                node_counts = session.run("""
                    MATCH (n)
                    RETURN labels(n) as NodeType, count(n) as Count
                """)
                
                # Get relationship counts by type
                rel_counts = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as RelType, count(r) as Count
                """)
                
                return {
                    "status": "success",
                    "node_counts": {record["NodeType"][0]: record["Count"] for record in node_counts},
                    "relationship_counts": {record["RelType"]: record["Count"] for record in rel_counts},
                    "database": "neo4j"
                }
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database": "neo4j"
            }
    
    def close(self):
        """Close database connections."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        logger.info("Database connections closed")

# Global database manager instance
database_manager = DatabaseManager()

# Convenience functions for backward compatibility
def insert_knowledge_graph(nodes: List[Dict], relationships: List[Dict], course_id: str = None) -> Dict[str, Any]:
    """Convenience function for inserting knowledge graph."""
    return database_manager.insert_knowledge_graph(nodes, relationships, course_id)

def insert_learning_tree(plt_data: Dict[str, Any], learner_id: str, course_id: str) -> Dict[str, Any]:
    """Convenience function for inserting learning tree."""
    return database_manager.insert_learning_tree(plt_data, learner_id, course_id)

def insert_course_data(course_id: str, course_name: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for inserting course data."""
    return database_manager.insert_course_data(course_id, course_name, **kwargs)

def insert_learner_data(learner_id: str, name: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for inserting learner data."""
    return database_manager.insert_learner_data(learner_id, name, **kwargs)

def clear_neo4j_database() -> Dict[str, Any]:
    """Convenience function for clearing database."""
    return database_manager.clear_database()

def get_knowledge_components_for_lo(lo_name: str) -> List[str]:
    """Convenience function for getting knowledge components for a learning objective."""
    return database_manager.get_knowledge_components_for_lo(lo_name)

def get_instruction_methods_for_kc(kc_name: str) -> List[str]:
    """Convenience function for getting instruction methods for a knowledge component."""
    return database_manager.get_instruction_methods_for_kc(kc_name)

def insert_plt_to_neo4j(plt_data: Dict[str, Any], clear_existing: bool = False) -> Dict[str, Any]:
    """Convenience function for inserting PLT to Neo4j."""
    if clear_existing:
        database_manager.clear_database()
    return database_manager.insert_learning_tree(plt_data, plt_data.get("learner_id", "unknown"), plt_data.get("course_id", "unknown"))

# Alias for consistency with class method naming
def insert_learning_tree_to_neo4j(plt_data: Dict[str, Any], clear_existing: bool = False) -> Dict[str, Any]:
    """Alias for insert_plt_to_neo4j for naming consistency."""
    return insert_plt_to_neo4j(plt_data, clear_existing)

def get_plt_for_learner(learner_id: str, course_id: str) -> List[Dict[str, Any]]:
    """Convenience function for getting PLT for a learner."""
    return database_manager.get_learning_tree_for_learner(learner_id, course_id)

def insert_course_kg_to_neo4j(course_graph: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for inserting course knowledge graph to Neo4j."""
    # Convert course_graph to nodes and relationships format
    nodes = []
    relationships = []
    
    # Add course node
    if "course_id" in course_graph:
        nodes.append({
            "type": "Course",
            "properties": {
                "id": course_graph["course_id"],
                "name": course_graph.get("course_name", course_graph["course_id"])
            }
        })
    
    # Add learning objectives
    for lo in course_graph.get("learning_objectives", []):
        nodes.append({
            "type": "LearningObjective",
            "properties": {
                "id": lo.get("id", lo.get("text", "")),
                "text": lo.get("text", "")
            }
        })
        
        # Add relationship from course to LO
        if "course_id" in course_graph:
            relationships.append({
                "from": course_graph["course_id"],
                "to": lo.get("id", lo.get("text", "")),
                "type": "HAS_LO"
            })
    
    return database_manager.insert_knowledge_graph(nodes, relationships)

# Alias for consistency with class method naming
def insert_knowledge_graph_to_neo4j(course_graph: Dict[str, Any]) -> Dict[str, Any]:
    """Alias for insert_course_kg_to_neo4j for naming consistency."""
    return insert_course_kg_to_neo4j(course_graph) 