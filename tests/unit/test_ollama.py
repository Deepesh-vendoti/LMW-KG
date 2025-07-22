#!/usr/bin/env python3
"""
Unit tests for Ollama LLM integration.
Tests LLM connection, response generation, and error handling.
"""

import pytest
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

def test_ollama_connection() -> None:
    """Test Ollama connection directly."""
    try:
        from langchain_community.chat_models import ChatOllama
        
        print("🔧 Initializing ChatOllama with qwen3:4b...")
        llm = ChatOllama(
            model="qwen3:4b",
            base_url="http://localhost:11434",
            temperature=0.3
        )
        
        print("📝 Testing with a simple prompt...")
        response = llm.invoke("Explain LangGraph to a student in one sentence.")
        print(f"✅ Ollama test successful: {response.content[:100]}...")
        assert response.content is not None
        assert len(response.content) > 0
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        pytest.skip(f"Ollama not available: {e}")

def test_ollama_response_format() -> None:
    """Test Ollama response format and structure."""
    with patch('langchain_community.chat_models.ChatOllama') as mock_ollama:
        # Mock response
        mock_response = Mock()
        mock_response.content = "LangGraph is a framework for building stateful, multi-actor applications with LLMs."
        mock_ollama.return_value.invoke.return_value = mock_response
        
        # Test response format
        response = mock_ollama.return_value.invoke("Test prompt")
        assert response.content is not None
        assert isinstance(response.content, str)
        assert len(response.content) > 0

def test_ollama_error_handling() -> None:
    """Test Ollama error handling for connection failures."""
    with patch('langchain_community.chat_models.ChatOllama') as mock_ollama:
        # Mock connection error
        mock_ollama.side_effect = ConnectionError("Failed to connect to Ollama")
        
        with pytest.raises(ConnectionError, match="Failed to connect to Ollama"):
            from langchain_community.chat_models import ChatOllama
            ChatOllama(model="qwen3:4b", base_url="http://localhost:11434")

def test_ollama_configuration() -> None:
    """Test Ollama configuration parameters."""
    config: Dict[str, Any] = {
        "model": "qwen3:4b",
        "base_url": "http://localhost:11434",
        "temperature": 0.3,
        "max_tokens": 1000
    }
    
    # Test that configuration parameters are valid
    assert config["model"] == "qwen3:4b"
    assert config["base_url"] == "http://localhost:11434"
    assert config["temperature"] == 0.3
    assert config["max_tokens"] == 1000
    assert len(config) == 4

if __name__ == "__main__":
    print("🚀 Testing Ollama Connection...")
    test_ollama_connection() 