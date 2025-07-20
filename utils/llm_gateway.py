"""
LLM Gateway - Adaptation Layer for LangGraph Knowledge Graph System

Provides a unified interface between LangGraph agents and backend LLMs:
- OpenAI, Claude, Ollama, and other LLM providers
- Dynamic model selection based on task type, cost, latency, privacy
- Prompt template management per task type
- Response post-processing and format enforcement
- Fallback strategies and caching

This is the "Adaptation Layer" that faculty was referring to.
"""

import os
import logging as log
import json
import hashlib
from typing import Dict, Any, List, Optional, Literal, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import time
from abc import ABC, abstractmethod

# LLM provider imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    log.warning("OpenAI client not available. Install with: pip install openai")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    log.warning("Anthropic client not available. Install with: pip install anthropic")

try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    log.warning("Ollama client not available. Install with: pip install langchain-ollama")

logger = log.getLogger(__name__)

# ===============================
# TASK TYPE DEFINITIONS
# ===============================

class TaskType(Enum):
    """Supported task types for LLM routing."""
    QUIZ_GENERATION = "quiz_generation"
    SUMMARY = "summary"
    DIALOGUE = "dialogue"
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"
    LEARNING_OBJECTIVE_GENERATION = "learning_objective_generation"
    INSTRUCTION_METHOD_SELECTION = "instruction_method_selection"
    PERSONALIZATION = "personalization"
    CONTENT_CHUNKING = "content_chunking"
    GRAPH_QUERY = "graph_query"
    PLT_GENERATION = "plt_generation"

# ===============================
# MODEL CONFIGURATIONS
# ===============================

@dataclass
class ModelConfig:
    """Configuration for an LLM model."""
    name: str
    provider: str
    max_tokens: int
    temperature: float
    cost_per_1k_tokens: float
    latency_ms: int
    privacy_level: Literal["local", "private", "public"]
    capabilities: List[str]
    fallback_to: Optional[str] = None

class ModelRegistry:
    """Registry of available LLM models."""
    
    def __init__(self):
        self.models = {
            # Ollama Models (Local) - ONLY Qwen3:4B
            "qwen3:4b": ModelConfig(
                name="qwen3:4b",
                provider="ollama",
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.0,  # Local = no cost
                latency_ms=3000,
                privacy_level="local",
                capabilities=["general", "local", "reasoning", "analysis", "creativity"],
                fallback_to=None
            ),
        }
    
    def get_model(self, name: str) -> Optional[ModelConfig]:
        """Get model configuration by name."""
        return self.models.get(name)
    
    def get_models_by_capability(self, capability: str) -> List[ModelConfig]:
        """Get models that support a specific capability."""
        return [model for model in self.models.values() if capability in model.capabilities]
    
    def get_models_by_privacy(self, privacy_level: str) -> List[ModelConfig]:
        """Get models by privacy level."""
        return [model for model in self.models.values() if model.privacy_level == privacy_level]

# ===============================
# TASK ROUTING CONFIGURATIONS
# ===============================

@dataclass
class TaskRoutingConfig:
    """Configuration for task-based model routing."""
    task_type: TaskType
    preferred_models: List[str]
    required_capabilities: List[str]
    max_cost_per_request: float
    max_latency_ms: int
    privacy_requirement: Literal["local", "private", "public"]
    prompt_template: str
    response_format: Dict[str, Any]

class TaskRouter:
    """Routes tasks to appropriate LLM models based on requirements."""
    
    def __init__(self):
        self.model_registry = ModelRegistry()
        self.task_configs = {
            TaskType.QUIZ_GENERATION: TaskRoutingConfig(
                task_type=TaskType.QUIZ_GENERATION,
                preferred_models=["qwen3:4b"],
                required_capabilities=["reasoning", "creativity"],
                max_cost_per_request=0.10,
                max_latency_ms=5000,
                privacy_requirement="local",
                prompt_template="Generate a quiz based on the following content: {content}",
                response_format={"type": "object", "properties": {"questions": {"type": "array"}}}
            ),
            TaskType.SUMMARY: TaskRoutingConfig(
                task_type=TaskType.SUMMARY,
                preferred_models=["qwen3:4b"],
                required_capabilities=["analysis"],
                max_cost_per_request=0.05,
                max_latency_ms=3000,
                privacy_requirement="local",
                prompt_template="Summarize the following content: {content}",
                response_format={"type": "string"}
            ),
            TaskType.DIALOGUE: TaskRoutingConfig(
                task_type=TaskType.DIALOGUE,
                preferred_models=["qwen3:4b"],
                required_capabilities=["general"],
                max_cost_per_request=0.08,
                max_latency_ms=4000,
                privacy_requirement="local",
                prompt_template="Engage in a dialogue about: {topic}",
                response_format={"type": "string"}
            ),
            TaskType.KNOWLEDGE_EXTRACTION: TaskRoutingConfig(
                task_type=TaskType.KNOWLEDGE_EXTRACTION,
                preferred_models=["qwen3:4b"],
                required_capabilities=["analysis", "reasoning"],
                max_cost_per_request=0.12,
                max_latency_ms=6000,
                privacy_requirement="local",
                prompt_template="Extract knowledge components from: {content}",
                response_format={"type": "object", "properties": {"concepts": {"type": "array"}}}
            ),
            TaskType.LEARNING_OBJECTIVE_GENERATION: TaskRoutingConfig(
                task_type=TaskType.LEARNING_OBJECTIVE_GENERATION,
                preferred_models=["qwen3:4b"],
                required_capabilities=["analysis", "creativity"],
                max_cost_per_request=0.15,
                max_latency_ms=7000,
                privacy_requirement="local",
                prompt_template="Generate learning objectives for: {content}",
                response_format={"type": "object", "properties": {"objectives": {"type": "array"}}}
            ),
            TaskType.INSTRUCTION_METHOD_SELECTION: TaskRoutingConfig(
                task_type=TaskType.INSTRUCTION_METHOD_SELECTION,
                preferred_models=["qwen3:4b"],
                required_capabilities=["analysis"],
                max_cost_per_request=0.08,
                max_latency_ms=4000,
                privacy_requirement="local",
                prompt_template="Select instruction methods for: {learning_objective}",
                response_format={"type": "object", "properties": {"methods": {"type": "array"}}}
            ),
            TaskType.PERSONALIZATION: TaskRoutingConfig(
                task_type=TaskType.PERSONALIZATION,
                preferred_models=["qwen3:4b"],
                required_capabilities=["analysis"],
                max_cost_per_request=0.06,
                max_latency_ms=3000,
                privacy_requirement="local",
                prompt_template="Personalize content for learner: {learner_profile}",
                response_format={"type": "object", "properties": {"personalization": {"type": "object"}}}
            ),
            TaskType.CONTENT_CHUNKING: TaskRoutingConfig(
                task_type=TaskType.CONTENT_CHUNKING,
                preferred_models=["qwen3:4b"],
                required_capabilities=["general"],
                max_cost_per_request=0.03,
                max_latency_ms=2000,
                privacy_requirement="local",
                prompt_template="Chunk content into sections: {content}",
                response_format={"type": "object", "properties": {"chunks": {"type": "array"}}}
            ),
            TaskType.GRAPH_QUERY: TaskRoutingConfig(
                task_type=TaskType.GRAPH_QUERY,
                preferred_models=["qwen3:4b"],
                required_capabilities=["reasoning"],
                max_cost_per_request=0.08,
                max_latency_ms=4000,
                privacy_requirement="local",
                prompt_template="Generate graph query for: {query_context}",
                response_format={"type": "object", "properties": {"cypher_query": {"type": "string"}}}
            ),
            TaskType.PLT_GENERATION: TaskRoutingConfig(
                task_type=TaskType.PLT_GENERATION,
                preferred_models=["qwen3:4b"],
                required_capabilities=["reasoning", "creativity"],
                max_cost_per_request=0.20,
                max_latency_ms=8000,
                privacy_requirement="local",
                prompt_template="Generate personalized learning tree for: {learner_context}",
                response_format={"type": "object", "properties": {"plt": {"type": "object"}}}
            ),
        }
    
    def select_model(self, task_type: TaskType, constraints: Dict[str, Any] = None) -> Optional[ModelConfig]:
        """Select the best model for a given task and constraints."""
        if task_type not in self.task_configs:
            logger.error(f"Unknown task type: {task_type}")
            return None
        
        config = self.task_configs[task_type]
        constraints = constraints or {}
        
        # Apply constraints
        max_cost = constraints.get('max_cost', config.max_cost_per_request)
        max_latency = constraints.get('max_latency_ms', config.max_latency_ms)
        privacy = constraints.get('privacy_requirement', config.privacy_requirement)
        
        # Filter models by constraints
        available_models = []
        for model_name in config.preferred_models:
            model = self.model_registry.get_model(model_name)
            if model and self._meets_constraints(model, max_cost, max_latency, privacy):
                available_models.append(model)
        
        if not available_models:
            logger.warning(f"No models available for task {task_type} with constraints {constraints}")
            return None
        
        # Select the first available model (could be enhanced with scoring)
        return available_models[0]
    
    def _meets_constraints(self, model: ModelConfig, max_cost: float, max_latency: int, privacy: str) -> bool:
        """Check if model meets the given constraints."""
        # Privacy level hierarchy: local > private > public
        privacy_levels = {"local": 3, "private": 2, "public": 1}
        required_level = privacy_levels.get(privacy, 1)
        model_level = privacy_levels.get(model.privacy_level, 1)
        
        return (
            model.cost_per_1k_tokens <= max_cost and
            model.latency_ms <= max_latency and
            model_level >= required_level
        )

# ===============================
# LLM PROVIDER ADAPTERS
# ===============================

class LLMProviderAdapter(ABC):
    """Abstract base class for LLM provider adapters."""
    
    @abstractmethod
    def generate(self, prompt: str, model_config: ModelConfig, **kwargs) -> Dict[str, Any]:
        """Generate response from LLM."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass

class OpenAIAdapter(LLMProviderAdapter):
    """Adapter for OpenAI models."""
    
    def __init__(self):
        self.client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def generate(self, prompt: str, model_config: ModelConfig, **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            raise RuntimeError("OpenAI client not available")
        
        try:
            response = self.client.chat.completions.create(
                model=model_config.name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                **kwargs
            )
            
            return {
                "content": response.choices[0].message.content,
                "model": model_config.name,
                "provider": "openai",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "cost": self._calculate_cost(response.usage, model_config)
            }
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

class AnthropicAdapter(LLMProviderAdapter):
    """Adapter for Anthropic models."""
    
    def __init__(self):
        self.client = None
        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def generate(self, prompt: str, model_config: ModelConfig, **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            raise RuntimeError("Anthropic client not available")
        
        try:
            response = self.client.messages.create(
                model=model_config.name,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            return {
                "content": response.content[0].text,
                "model": model_config.name,
                "provider": "anthropic",
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "cost": self._calculate_cost(response.usage, model_config)
            }
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise

class OllamaAdapter(LLMProviderAdapter):
    """Adapter for Ollama models."""
    
    def __init__(self):
        self.client = None
        if OLLAMA_AVAILABLE:
            try:
                self.client = ChatOllama(
                    model="qwen3:4b",
                    base_url="http://localhost:11434",  # default Ollama port
                    temperature=0.3
                )
                logger.info("Ollama client initialized successfully with qwen3:4b")
            except Exception as e:
                logger.warning(f"Ollama client initialization failed: {e}")
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def generate(self, prompt: str, model_config: ModelConfig, **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            raise RuntimeError("Ollama client not available")
        
        try:
            # Update model if different from current
            if self.client.model != model_config.name:
                self.client = ChatOllama(
                    model=model_config.name,
                    base_url="http://localhost:11434",
                    temperature=0.3
                )
            
            # Use invoke method for ChatOllama
            response = self.client.invoke(prompt)
            
            # Extract content from response
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            return {
                "content": content,
                "model": model_config.name,
                "provider": "ollama",
                "usage": {
                    "prompt_tokens": len(prompt.split()),  # Rough estimate
                    "completion_tokens": len(content.split()),
                    "total_tokens": len(prompt.split()) + len(content.split())
                },
                "cost": 0.0  # Local models have no cost
            }
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

# ===============================
# CACHE MANAGEMENT
# ===============================

class LLMCache:
    """Cache for LLM responses to avoid repeat queries."""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.cache = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if valid."""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() - entry['timestamp'] < self.ttl:
                return entry['response']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, response: Dict[str, Any]):
        """Cache a response."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'response': response,
            'timestamp': datetime.now()
        }
    
    def generate_key(self, prompt: str, model: str, task_type: str) -> str:
        """Generate cache key for a request."""
        content = f"{prompt}:{model}:{task_type}"
        return hashlib.md5(content.encode()).hexdigest()

# ===============================
# MAIN LLM GATEWAY
# ===============================

class LLMGateway:
    """Main LLM Gateway - unified interface for all LLM operations."""
    
    def __init__(self):
        self.task_router = TaskRouter()
        self.cache = LLMCache()
        
        # Initialize provider adapters
        self.providers = {
            "openai": OpenAIAdapter(),
            "anthropic": AnthropicAdapter(),
            "ollama": OllamaAdapter()
        }
    
    def generate(
        self,
        task_type: TaskType,
        prompt: str,
        constraints: Dict[str, Any] = None,
        use_cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using appropriate LLM for the task."""
        
        # Check cache first
        if use_cache:
            model_config = self.task_router.select_model(task_type, constraints)
            if model_config:
                cache_key = self.cache.generate_key(prompt, model_config.name, task_type.value)
                cached_response = self.cache.get(cache_key)
                if cached_response:
                    logger.info(f"Cache hit for task {task_type}")
                    return cached_response
        
        # Select appropriate model
        model_config = self.task_router.select_model(task_type, constraints)
        if not model_config:
            raise RuntimeError(f"No suitable model found for task {task_type}")
        
        # Get provider adapter
        provider = self.providers.get(model_config.provider)
        if not provider or not provider.is_available():
            # Try fallback model
            if model_config.fallback_to:
                fallback_config = self.task_router.model_registry.get_model(model_config.fallback_to)
                if fallback_config:
                    model_config = fallback_config
                    provider = self.providers.get(model_config.provider)
        
        if not provider or not provider.is_available():
            raise RuntimeError(f"No available provider for model {model_config.name}")
        
        # Generate response
        try:
            response = provider.generate(prompt, model_config, **kwargs)
            
            # Add metadata
            response.update({
                "task_type": task_type.value,
                "model_used": model_config.name,
                "provider_used": model_config.provider,
                "generated_at": datetime.now().isoformat(),
                "constraints_applied": constraints or {}
            })
            
            # Cache response
            if use_cache:
                cache_key = self.cache.generate_key(prompt, model_config.name, task_type.value)
                self.cache.set(cache_key, response)
            
            return response
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            
            # Try fallback if available
            if model_config.fallback_to:
                logger.info(f"Trying fallback model: {model_config.fallback_to}")
                fallback_config = self.task_router.model_registry.get_model(model_config.fallback_to)
                if fallback_config:
                    fallback_provider = self.providers.get(fallback_config.provider)
                    if fallback_provider and fallback_provider.is_available():
                        return fallback_provider.generate(prompt, fallback_config, **kwargs)
            
            raise
    
    def get_available_models(self) -> List[ModelConfig]:
        """Get list of available models."""
        available = []
        for model in self.task_router.model_registry.models.values():
            provider = self.providers.get(model.provider)
            if provider and provider.is_available():
                available.append(model)
        return available
    
    def get_task_config(self, task_type: TaskType) -> Optional[TaskRoutingConfig]:
        """Get configuration for a specific task type."""
        return self.task_router.task_configs.get(task_type)
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all providers."""
        health = {}
        for provider_name, provider in self.providers.items():
            health[provider_name] = provider.is_available()
        return health

# ===============================
# GLOBAL GATEWAY INSTANCE
# ===============================

_llm_gateway = None

def get_llm_gateway() -> LLMGateway:
    """Get the global LLM Gateway instance."""
    global _llm_gateway
    if _llm_gateway is None:
        _llm_gateway = LLMGateway()
    return _llm_gateway

# ===============================
# USAGE EXAMPLES
# ===============================

def test_ollama_connection():
    """Test Ollama connection directly."""
    try:
        from langchain_community.chat_models import ChatOllama
        
        llm = ChatOllama(
            model="qwen3:4b",
            base_url="http://localhost:11434",
            temperature=0.3
        )
        
        response = llm.invoke("Explain LangGraph to a student in one sentence.")
        print(f"✅ Ollama test successful: {response.content[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

def example_usage():
    """Example usage of the LLM Gateway."""
    gateway = get_llm_gateway()
    
    # Test Ollama connection first
    if not test_ollama_connection():
        print("Ollama connection failed, skipping examples")
        return
    
    # Generate a quiz
    quiz_response = gateway.generate(
        task_type=TaskType.QUIZ_GENERATION,
        prompt="Generate a quiz about operating systems memory management",
        constraints={"max_cost": 0.05, "privacy_requirement": "local"}
    )
    
    print(f"Quiz generated: {quiz_response['content'][:100]}...")
    
    # Generate a summary
    summary_response = gateway.generate(
        task_type=TaskType.SUMMARY,
        prompt="Summarize the key concepts of process scheduling",
        use_cache=True
    )
    
    print(f"Summary generated: {summary_response['content'][:100]}...")
    
    # Check health
    health = gateway.health_check()
    print(f"Provider health: {health}")

if __name__ == "__main__":
    test_ollama_connection()
    example_usage() 