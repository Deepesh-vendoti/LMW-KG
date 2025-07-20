#!/usr/bin/env python3
"""
Simple test script to verify Ollama connection
"""

def test_ollama_connection():
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
        return True
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Ollama Connection...")
    test_ollama_connection() 