"""
Configuration Loader for LangGraph Knowledge Graph System

Loads configuration from config/config.yaml and provides easy access to settings.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """Singleton configuration manager for the LangGraph KG system."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """Load configuration from config.yaml"""
        config_path = Path(__file__).parent / "config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as file:
            self._config = yaml.safe_load(file)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., 'databases.neo4j.uri')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self.get('llm', {})
    
    def get_database_config(self, db_name: str) -> Dict[str, Any]:
        """Get database configuration for specific database"""
        return self.get(f'databases.{db_name}', {})
    
    def get_default_course_id(self) -> str:
        """Get default course ID"""
        return self.get('courses.default_course_id', 'OSN')
    
    def get_default_learner_id(self) -> str:
        """Get default learner ID"""
        return self.get('courses.default_learner_id', 'R000')
    
    def get_microservice_config(self, service_name: str) -> Dict[str, Any]:
        """Get microservice configuration"""
        return self.get(f'microservices.{service_name}', {})
    
    def get_chunk_config(self) -> Dict[str, int]:
        """Get chunking configuration"""
        return {
            'chunk_size': self.get('microservices.content_preprocessor.chunk_size', 1000),
            'chunk_overlap': self.get('microservices.content_preprocessor.chunk_overlap', 100)
        }
    
    def get_paths_config(self) -> Dict[str, str]:
        """Get paths configuration"""
        return self.get('paths', {})
    
    def get_faculty_approval_config(self) -> Dict[str, Any]:
        """Get faculty approval workflow configuration"""
        return self.get('faculty_approval', {})

# Global configuration instance
config = ConfigManager()

# Convenience functions for common configurations
def get_default_course_id() -> str:
    """Get default course ID from configuration"""
    return config.get_default_course_id()

def get_default_learner_id() -> str:
    """Get default learner ID from configuration"""
    return config.get_default_learner_id()

def get_neo4j_config() -> Dict[str, Any]:
    """Get Neo4j database configuration"""
    return config.get_database_config('neo4j')

def get_elasticsearch_config() -> Dict[str, Any]:
    """Get Elasticsearch configuration"""
    return config.get_database_config('elasticsearch')

def get_llm_model() -> str:
    """Get default LLM model"""
    return config.get('llm.default_model', 'qwen3:4b')

def get_chunk_settings() -> Dict[str, int]:
    """Get chunk size and overlap settings"""
    return config.get_chunk_config() 