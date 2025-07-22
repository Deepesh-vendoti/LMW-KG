# 🧪 Testing Guide - LangGraph Knowledge Graph System

## 📋 **Test Structure**

```
tests/
├── unit/                    # Unit tests (fast, isolated)
├── integration/             # Integration tests (database, external services)
├── e2e/                    # End-to-end tests (complete workflows)
└── fixtures/               # Test data and fixtures
```

## 🚀 **Running Tests**

```bash
# Run all tests
python -m pytest tests/

# Run specific categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/e2e/

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run specific test
python -m pytest tests/unit/test_ollama.py -v
```

## 📝 **Test Patterns**

### **Unit Test Pattern**
```python
import pytest
from unittest.mock import Mock, patch
from orchestrator.state import ServiceStatus

class TestMyService:
    def setup_method(self):
        self.service = MyService()
        self.mock_state = {"test_data": "value"}
    
    def test_service_success(self):
        result = self.service(self.mock_state)
        assert result["service_status"] == ServiceStatus.COMPLETED
    
    def test_service_failure(self):
        with patch.object(self.service, '_process_data', side_effect=Exception("Test error")):
            result = self.service(self.mock_state)
            assert result["service_status"] == ServiceStatus.FAILED
```

### **Integration Test Pattern**
```python
import pytest
from utils.database_connections import get_database_manager

class TestDatabaseIntegration:
    def test_neo4j_connection(self):
        db_manager = get_database_manager()
        assert db_manager.neo4j_driver is not None
        
        result = db_manager.neo4j_driver.run("RETURN 1 as test")
        assert result.single()["test"] == 1
```

### **E2E Test Pattern**
```python
import pytest
from orchestrator.service_registry import register_all_services

class TestFacultyWorkflowE2E:
    def test_complete_faculty_workflow(self):
        registry = register_all_services()
        
        from pipeline.manual_coordinator import start_faculty_workflow
        result = start_faculty_workflow(
            course_id="TEST_COURSE",
            faculty_id="TEST_FACULTY",
            content_source="elasticsearch"
        )
        
        assert result["status"] == "awaiting_faculty_approval"
```

## ⚙️ **Test Configuration**

### **pytest.ini**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

### **conftest.py**
```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_llm():
    mock = Mock()
    mock.generate.return_value = {"text": "Mock response"}
    return mock

@pytest.fixture
def sample_state():
    return {
        "course_id": "TEST_COURSE",
        "learner_id": "TEST_LEARNER",
        "learner_context": {"learning_style": "visual"}
    }
```

## 🔧 **Test Standards**

### **Naming Conventions**
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<description>`

### **Type Hints**
```python
from typing import Dict, Any
from orchestrator.state import UniversalState

def test_service_execution(state: UniversalState) -> None:
    result: Dict[str, Any] = service(state)
    assert result["status"] == "completed"
```

### **Error Handling**
```python
def test_error_handling():
    with pytest.raises(ValueError, match="Required field missing"):
        service.process_invalid_data()
```

### **Mocking Best Practices**
```python
@patch('utils.database_manager.DatabaseManager')
def test_database_operation(mock_db):
    mock_db.return_value.insert_data.return_value = {"success": True}
    result = service.store_data(test_data)
    assert result["success"] is True
```

## 📊 **Test Coverage**

### **Coverage Targets**
- **Unit Tests**: 90%+ coverage
- **Integration Tests**: 80%+ coverage
- **E2E Tests**: Critical path coverage

### **Coverage Report**
```bash
# Generate coverage report
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## 🐛 **Troubleshooting Tests**

### **Common Issues**
```bash
# Import errors
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Database connection issues
docker-compose -f deployment/docker-compose-databases.yml up -d

# LLM connection issues
ollama serve
```

### **Test Debugging**
```python
# Add debug prints
def test_debug():
    print(f"Debug: {variable}")
    assert condition

# Use pytest -s for output
python -m pytest tests/ -s -v
```

## 📈 **Performance Testing**

### **Load Testing**
```python
import time
import pytest

def test_service_performance():
    start_time = time.time()
    result = service.process_large_dataset()
    end_time = time.time()
    
    assert end_time - start_time < 5.0  # 5 second timeout
    assert result["status"] == "completed"
```

### **Memory Testing**
```python
import psutil
import os

def test_memory_usage():
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    service.process_data()
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    assert memory_increase < 100 * 1024 * 1024  # 100MB limit
```

## 🔄 **Continuous Integration**

### **GitHub Actions**
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest tests/ --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## 📚 **Test Documentation**

### **Test Documentation Standards**
- Document test purpose in docstring
- Explain test data setup
- Document expected outcomes
- Include edge cases

```python
def test_faculty_approval_workflow():
    """
    Test complete faculty approval workflow from start to finish.
    
    Setup:
    - Mock faculty user
    - Mock course content
    - Mock database connections
    
    Expected:
    - Workflow progresses through all stages
    - Final state is 'course_ready'
    - All services execute successfully
    """
    # Test implementation
```

## 🎯 **Test Priorities**

### **High Priority**
- Service registration and discovery
- Database connections and operations
- LLM integration and responses
- Faculty workflow state transitions

### **Medium Priority**
- Error handling and recovery
- Performance under load
- Data validation and sanitization
- Configuration management

### **Low Priority**
- Edge cases and error conditions
- Performance optimization
- UI/UX testing (when implemented)
- Documentation accuracy

---

*Last updated: July 2024* 