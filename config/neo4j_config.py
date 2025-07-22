"""
Neo4j Configuration

Centralized configuration for Neo4j connections across all services.
This ensures consistent connection settings and proper authentication handling.
"""

# Neo4j connection configuration for different services
NEO4J_CONFIG = {
    "course_mapper": {
        "uri": "bolt://localhost:7687",
        "auth": None  # Explicitly set to None, not "none" string
    },
    "kli_app": {
        "uri": "bolt://localhost:7688",
        "auth": None
    },
    "kg_generator": {
        "uri": "bolt://localhost:7689",
        "auth": None
    }
}

# Function to get Neo4j configuration for a specific service
def get_neo4j_config(service_name="course_mapper"):
    """
    Get Neo4j configuration for a specific service.
    
    Args:
        service_name: Name of the service (course_mapper, kli_app, kg_generator)
        
    Returns:
        Dictionary with uri and auth configuration
    """
    return NEO4J_CONFIG.get(service_name, NEO4J_CONFIG["course_mapper"]) 