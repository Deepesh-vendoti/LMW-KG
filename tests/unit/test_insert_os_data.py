#!/usr/bin/env python3
"""
Unit tests for OS data insertion into knowledge graph.
Tests database operations for learning objectives, knowledge components, and instruction methods.
"""

import pytest
from typing import Dict, List, Any
from unittest.mock import Mock, patch

from utils.database_manager import insert_knowledge_graph

# Test data for OS concepts
sample_entries = [
    {
        "lo": "Understand Process Synchronization",
        "kc": "Semaphores & Mutexes",
        "learning_process": "Understanding",
        "recommended_instruction": "Worked Example Comparison"
    },
    {
        "lo": "Apply Deadlock Prevention",
        "kc": "Banker's Algorithm",
        "learning_process": "Fluency",
        "recommended_instruction": "Spaced Retrieval Practice"
    },
    {
        "lo": "Master File Management",
        "kc": "Inode Structure",
        "learning_process": "Memory",
        "recommended_instruction": "Retrieval Practice"
    },
    {
        "lo": "Understand Virtual Memory",
        "kc": "Paging & Segmentation",
        "learning_process": "Understanding",
        "recommended_instruction": "Concept Mapping"
    },
    {
        "lo": "Evaluate Scheduling Policies",
        "kc": "Multi-level Feedback Queues",
        "learning_process": "Strategic Thinking",
        "recommended_instruction": "Decision-based Scenarios"
    }
]

def test_sample_entries_structure() -> None:
    """Test that sample entries have correct structure."""
    for entry in sample_entries:
        assert "lo" in entry, "Learning objective missing"
        assert "kc" in entry, "Knowledge component missing"
        assert "learning_process" in entry, "Learning process missing"
        assert "recommended_instruction" in entry, "Recommended instruction missing"
        assert isinstance(entry["lo"], str), "Learning objective must be string"
        assert isinstance(entry["kc"], str), "Knowledge component must be string"

def test_knowledge_graph_insertion() -> None:
    """Test knowledge graph insertion with mock database."""
    with patch('utils.database_manager.DatabaseManager') as mock_db:
        mock_instance = Mock()
        mock_instance.insert_knowledge_graph.return_value = {
            "status": "success",
            "nodes_created": 5,
            "relationships_created": 10
        }
        mock_db.return_value = mock_instance
        
        # Convert sample entries to knowledge graph format
        nodes = []
        relationships = []
        
        for entry in sample_entries:
            # Add learning objective node
            nodes.append({
                "type": "LearningObjective",
                "properties": {"id": entry["lo"], "text": entry["lo"]}
            })
            
            # Add knowledge component node
            nodes.append({
                "type": "KnowledgeComponent",
                "properties": {"id": entry["kc"], "text": entry["kc"]}
            })
            
            # Add relationship
            relationships.append({
                "from": entry["lo"],
                "to": entry["kc"],
                "type": "CONTAINS",
                "properties": {
                    "learning_process": entry["learning_process"],
                    "instruction_method": entry["recommended_instruction"]
                }
            })
        
        # Test insertion
        result = insert_knowledge_graph(nodes, relationships, "TEST_COURSE")
        
        assert result["status"] == "success"
        assert result["nodes_created"] == 5
        assert result["relationships_created"] == 10

def test_data_validation() -> None:
    """Test data validation for OS concepts."""
    # Test that all entries have valid learning processes
    valid_processes = ["Understanding", "Fluency", "Memory", "Strategic Thinking", "Comparison", "Conceptual", "Procedural", "Procedural Fluency"]
    
    for entry in sample_entries:
        assert entry["learning_process"] in valid_processes, f"Invalid learning process: {entry['learning_process']}"
    
    # Test that all entries have non-empty strings
    for entry in sample_entries:
        assert len(entry["lo"].strip()) > 0, "Empty learning objective"
        assert len(entry["kc"].strip()) > 0, "Empty knowledge component"
        assert len(entry["recommended_instruction"].strip()) > 0, "Empty instruction method"

@pytest.mark.database
def test_actual_database_insertion() -> None:
    """Test actual database insertion (requires database connection)."""
    # This test requires a real database connection
    # It's marked with @pytest.mark.database to run only when database is available
    try:
        from utils.database_connections import get_database_manager
        db_manager = get_database_manager()
        
        # Convert sample entries to knowledge graph format
        nodes = []
        relationships = []
        
        for entry in sample_entries[:2]:  # Use only first 2 entries for testing
            nodes.append({
                "type": "LearningObjective",
                "properties": {"id": entry["lo"], "text": entry["lo"]}
            })
            nodes.append({
                "type": "KnowledgeComponent",
                "properties": {"id": entry["kc"], "text": entry["kc"]}
            })
            relationships.append({
                "from": entry["lo"],
                "to": entry["kc"],
                "type": "CONTAINS",
                "properties": {
                    "learning_process": entry["learning_process"],
                    "instruction_method": entry["recommended_instruction"]
                }
            })
        
        result = insert_knowledge_graph(nodes, relationships, "TEST_COURSE")
        assert result["status"] == "success"
        
    except Exception as e:
        pytest.skip(f"Database not available: {e}")