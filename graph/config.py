"""
Configuration settings for the LangGraph Knowledge Graph system
"""

import yaml
import os
from pathlib import Path
from langchain_ollama import OllamaLLM

# Load configuration from YAML
def load_config():
    """Load configuration from YAML file"""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Global configuration
CONFIG = load_config()

# LLM Configuration
DEFAULT_LLM_MODEL = CONFIG['llm']['default_model']
ALTERNATIVE_LLM_MODEL = CONFIG['llm']['alternative_model']

# Shared LLM instance
def get_llm(model: str = None) -> OllamaLLM:
    """Get a configured LLM instance"""
    if model is None:
        model = DEFAULT_LLM_MODEL
    return OllamaLLM(model=model)

# LLM Gateway integration
def get_llm_gateway():
    """Get the LLM Gateway for advanced LLM operations"""
    try:
        from utils.llm_gateway import get_llm_gateway as get_gateway
        return get_gateway()
    except ImportError:
        # Fallback to basic Ollama if LLM Gateway not available
        return get_llm()

# Neo4j Configuration - Updated for dual Neo4j setup
NEO4J_COURSE_MAPPER_URI = CONFIG['databases']['neo4j']['course_mapper']['uri']
NEO4J_COURSE_MAPPER_AUTH = CONFIG['databases']['neo4j']['course_mapper']['auth']
NEO4J_KLI_APP_URI = CONFIG['databases']['neo4j']['kli_app']['uri']
NEO4J_KLI_APP_AUTH = CONFIG['databases']['neo4j']['kli_app']['auth']

# Backward compatibility - use course_mapper as default
NEO4J_URI = NEO4J_COURSE_MAPPER_URI
NEO4J_AUTH = NEO4J_COURSE_MAPPER_AUTH

# Elasticsearch Configuration  
ES_ENDPOINT = CONFIG['databases']['elasticsearch']['endpoint']
ES_INDEX = CONFIG['databases']['elasticsearch']['index']
ES_VECTOR_STORE_DIR = CONFIG['databases']['elasticsearch']['vector_store_dir']

# Course Configuration
DEFAULT_COURSE_ID = CONFIG['courses']['default_course_id']
DEFAULT_LEARNER_ID = CONFIG['courses']['default_learner_id']

# Paths
PROMPTS_PATH = CONFIG['paths']['prompts'] 