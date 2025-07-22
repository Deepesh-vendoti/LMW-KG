"""
Shared test fixtures and configuration for LangGraph Knowledge Graph System.
"""

import pytest
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch
from orchestrator.state import UniversalState, SubsystemType

@pytest.fixture
def mock_llm() -> Mock:
    """Mock LLM for testing without actual LLM connection."""
    mock = Mock()
    mock.generate.return_value = {"text": "Mock LLM response"}
    mock.invoke.return_value.content = "Mock LLM response"
    return mock

@pytest.fixture
def sample_state() -> UniversalState:
    """Sample state for testing services."""
    return {
        "course_id": "TEST_COURSE",
        "learner_id": "TEST_LEARNER",
        "learner_context": {"learning_style": "visual", "experience_level": "intermediate"},
        "subsystem": SubsystemType.LEARNER,
        "service_statuses": {},
        "service_results": {},
        "service_errors": {}
    }

@pytest.fixture
def mock_database_manager() -> Mock:
    """Mock database manager for testing."""
    mock = Mock()
    mock.insert_learning_tree.return_value = {"status": "success"}
    mock.get_learning_tree.return_value = {"learning_path": []}
    mock.clear_database.return_value = {"status": "success"}
    return mock

@pytest.fixture
def mock_elasticsearch_client() -> Mock:
    """Mock Elasticsearch client for testing."""
    mock = Mock()
    mock.ping.return_value = True
    mock.search.return_value = {
        "hits": {
            "total": {"value": 10},
            "hits": [{"_source": {"content": "test content"}} for _ in range(10)]
        }
    }
    return mock

@pytest.fixture
def mock_neo4j_driver() -> Mock:
    """Mock Neo4j driver for testing."""
    mock = Mock()
    mock.run.return_value.single.return_value = {"test": 1}
    return mock

@pytest.fixture
def faculty_workflow_state() -> UniversalState:
    """State for faculty workflow testing."""
    return {
        "course_id": "FACULTY_TEST_COURSE",
        "faculty_id": "TEST_FACULTY",
        "content_source": "elasticsearch",
        "subsystem": SubsystemType.CONTENT,
        "workflow_stage": "course_initialization_approval",
        "service_statuses": {},
        "service_results": {},
        "service_errors": {}
    }

@pytest.fixture
def learner_workflow_state() -> UniversalState:
    """State for learner workflow testing."""
    return {
        "course_id": "LEARNER_TEST_COURSE",
        "learner_id": "TEST_LEARNER",
        "learner_context": {
            "learning_style": "visual",
            "experience_level": "intermediate",
            "preferences": ["interactive", "examples"]
        },
        "subsystem": SubsystemType.LEARNER,
        "query_strategy": {
            "strategy": "adaptive_queries",
            "complexity": "medium",
            "personalization_strategy": {
                "learner_type": "visual",
                "intervention_strategy": "examples",
                "delivery_strategy": "interactive"
            }
        },
        "service_statuses": {},
        "service_results": {},
        "service_errors": {}
    }

@pytest.fixture
def mock_service_registry() -> Mock:
    """Mock service registry for testing."""
    mock = Mock()
    mock.services = {}
    mock.subsystems = {}
    mock.register_service.return_value = None
    mock.get_service.return_value = None
    mock.list_services.return_value = {}
    return mock

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration for all tests."""
    return {
        "llm": {
            "provider": "ollama",
            "model": "qwen2.5:4b",
            "base_url": "http://localhost:11434",
            "temperature": 0.7
        },
        "databases": {
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "username": "neo4j",
                "password": "test_password"
            },
            "elasticsearch": {
                "host": "localhost",
                "port": 9200,
                "scheme": "http"
            }
        },
        "test": {
            "timeout": 30,
            "retries": 3,
            "mock_llm": True
        }
    }

# Test markers for categorization
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (database, external services)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (complete workflows)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "llm: Tests requiring LLM connection"
    )
    config.addinivalue_line(
        "markers", "database: Tests requiring database connection"
    )
    config.addinivalue_line(
        "markers", "faculty: Faculty workflow tests"
    )
    config.addinivalue_line(
        "markers", "microservices: Microservices architecture tests"
    ) 