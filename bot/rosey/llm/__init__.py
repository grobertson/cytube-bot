"""
LLM integration for Rosey.

Supports multiple providers:
- Ollama (local inference)
- OpenRouter (remote API with multiple models)
"""

from .client import LLMClient
from .providers import OllamaProvider, OpenRouterProvider

__all__ = ['LLMClient', 'OllamaProvider', 'OpenRouterProvider']
