"""
Nano Banana Studio Pro - Enhanced LLM Provider Service
======================================================
Multi-provider LLM service with intelligent fallback, health checks,
and task-specific routing per GAP-011 specification.

Features:
- LM Studio integration (local, priority 1)
- Ollama integration (local, priority 2)
- OpenRouter integration (cloud, priority 3)
- OpenAI integration (cloud, priority 4)
- Automatic fallback chain
- Health monitoring
- Task-specific model selection
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import httpx
import yaml

logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "llm_providers.yaml"


class ProviderStatus(Enum):
    """Provider health status."""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class ProviderHealth:
    """Track provider health metrics."""
    status: ProviderStatus = ProviderStatus.UNKNOWN
    last_check: Optional[datetime] = None
    last_success: Optional[datetime] = None
    consecutive_failures: int = 0
    avg_latency_ms: float = 0.0
    error_message: Optional[str] = None


@dataclass
class LLMResponse:
    """Structured LLM response."""
    content: str
    provider: str
    model: str
    latency_ms: float
    tokens_used: Optional[int] = None
    cached: bool = False


@dataclass
class ProviderConfig:
    """Provider configuration."""
    name: str
    enabled: bool
    base_url: str
    priority: int
    timeout: int
    models: List[str]
    default_model: str
    capabilities: List[str]
    requires_key: Optional[str] = None
    api_key: Optional[str] = None


class LLMProviderService:
    """
    Enhanced LLM provider service with fallback chain and health monitoring.
    
    Usage:
        service = LLMProviderService()
        await service.initialize()
        
        response = await service.complete(
            messages=[{"role": "user", "content": "Hello!"}],
            task="prompt_enhancement"
        )
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_PATH
        self.config: Dict[str, Any] = {}
        self.providers: Dict[str, ProviderConfig] = {}
        self.health: Dict[str, ProviderHealth] = {}
        self.http_client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize the service and load configuration."""
        if self._initialized:
            return
        
        self._load_config()
        self.http_client = httpx.AsyncClient(timeout=120.0)
        
        # Initialize health tracking
        for name in self.providers:
            self.health[name] = ProviderHealth()
        
        # Start health check loop
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Initial health check
        await self._check_all_providers()
        
        self._initialized = True
        logger.info(f"LLMProviderService initialized with {len(self.providers)} providers")
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                self.config = yaml.safe_load(f)
        else:
            logger.warning(f"Config not found: {self.config_path}, using defaults")
            self.config = self._default_config()
        
        # Parse provider configurations
        for name, cfg in self.config.get("providers", {}).items():
            if not cfg.get("enabled", True):
                continue
            
            api_key = None
            if cfg.get("requires_key"):
                api_key = os.getenv(cfg["requires_key"])
                if not api_key:
                    logger.warning(f"Provider {name} requires {cfg['requires_key']} but not set")
                    continue
            
            self.providers[name] = ProviderConfig(
                name=name,
                enabled=cfg.get("enabled", True),
                base_url=cfg.get("base_url", ""),
                priority=cfg.get("priority", 99),
                timeout=cfg.get("timeout", 60),
                models=cfg.get("models", []),
                default_model=cfg.get("default_model", ""),
                capabilities=cfg.get("capabilities", []),
                requires_key=cfg.get("requires_key"),
                api_key=api_key
            )
    
    def _default_config(self) -> Dict:
        """Return default configuration."""
        return {
            "providers": {
                "lm_studio": {
                    "enabled": True,
                    "base_url": "http://localhost:1234/v1",
                    "priority": 1,
                    "timeout": 120,
                    "models": ["local-model"],
                    "default_model": "local-model",
                    "capabilities": ["chat", "completion"]
                },
                "ollama": {
                    "enabled": True,
                    "base_url": "http://localhost:11434",
                    "priority": 2,
                    "timeout": 120,
                    "models": ["llama3.1:8b"],
                    "default_model": "llama3.1:8b",
                    "capabilities": ["chat", "completion"]
                }
            },
            "fallback": {
                "enabled": True,
                "max_retries": 3,
                "chain": ["lm_studio", "ollama"]
            }
        }
    
    async def _health_check_loop(self):
        """Background health check loop."""
        interval = self.config.get("health_check", {}).get("interval_seconds", 60)
        
        while True:
            await asyncio.sleep(interval)
            await self._check_all_providers()
    
    async def _check_all_providers(self):
        """Check health of all providers."""
        tasks = [self._check_provider(name) for name in self.providers]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_provider(self, name: str):
        """Check health of a specific provider."""
        provider = self.providers.get(name)
        if not provider:
            return
        
        health = self.health[name]
        start_time = datetime.now()
        
        try:
            test_prompt = self.config.get("health_check", {}).get(
                "test_prompt", "Say 'OK' if you're working."
            )
            timeout = self.config.get("health_check", {}).get("timeout_seconds", 5)
            
            response = await self._call_provider(
                provider,
                messages=[{"role": "user", "content": test_prompt}],
                max_tokens=10,
                timeout=timeout
            )
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            health.status = ProviderStatus.HEALTHY
            health.last_success = datetime.now()
            health.consecutive_failures = 0
            health.avg_latency_ms = (health.avg_latency_ms + latency) / 2
            health.error_message = None
            
            logger.debug(f"Provider {name} healthy (latency: {latency:.0f}ms)")
            
        except Exception as e:
            health.consecutive_failures += 1
            health.error_message = str(e)
            
            if health.consecutive_failures >= 3:
                health.status = ProviderStatus.UNAVAILABLE
            else:
                health.status = ProviderStatus.DEGRADED
            
            logger.warning(f"Provider {name} health check failed: {e}")
        
        health.last_check = datetime.now()
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers sorted by priority."""
        available = []
        
        for name, provider in sorted(self.providers.items(), key=lambda x: x[1].priority):
            health = self.health.get(name)
            if health and health.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED, ProviderStatus.UNKNOWN]:
                available.append(name)
        
        return available
    
    def get_model_for_task(self, task: str) -> tuple[str, str]:
        """Get recommended model and provider for a task."""
        task_config = self.config.get("task_models", {}).get(task, {})
        preferred_models = task_config.get("preferred", [])
        
        for provider_name in self.get_available_providers():
            provider = self.providers[provider_name]
            for model in preferred_models:
                if model in provider.models:
                    return provider_name, model
        
        # Fall back to first available provider's default model
        available = self.get_available_providers()
        if available:
            provider = self.providers[available[0]]
            return available[0], provider.default_model
        
        raise RuntimeError("No LLM providers available")
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        task: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        """
        Get completion from LLM with automatic fallback.
        
        Args:
            messages: Chat messages
            model: Specific model to use (optional)
            provider: Specific provider to use (optional)
            task: Task type for model selection (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLMResponse with content and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Determine provider and model
        if provider and provider in self.providers:
            providers_to_try = [provider]
            if not model:
                model = self.providers[provider].default_model
        elif task:
            prov, mdl = self.get_model_for_task(task)
            providers_to_try = [prov] + [p for p in self.get_available_providers() if p != prov]
            model = model or mdl
        else:
            providers_to_try = self.get_available_providers()
        
        # Get task-specific settings
        task_config = self.config.get("task_models", {}).get(task, {})
        temperature = task_config.get("temperature", temperature)
        max_tokens = task_config.get("max_tokens", max_tokens)
        
        # Try providers in order
        last_error = None
        
        for prov_name in providers_to_try:
            prov = self.providers.get(prov_name)
            if not prov:
                continue
            
            try:
                start_time = datetime.now()
                
                content = await self._call_provider(
                    prov,
                    messages=messages,
                    model=model or prov.default_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                latency = (datetime.now() - start_time).total_seconds() * 1000
                
                # Update health on success
                self.health[prov_name].status = ProviderStatus.HEALTHY
                self.health[prov_name].last_success = datetime.now()
                self.health[prov_name].consecutive_failures = 0
                
                return LLMResponse(
                    content=content,
                    provider=prov_name,
                    model=model or prov.default_model,
                    latency_ms=latency
                )
                
            except Exception as e:
                logger.warning(f"Provider {prov_name} failed: {e}")
                last_error = e
                
                # Update health on failure
                self.health[prov_name].consecutive_failures += 1
                if self.health[prov_name].consecutive_failures >= 3:
                    self.health[prov_name].status = ProviderStatus.UNAVAILABLE
                
                continue
        
        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")
    
    async def _call_provider(
        self,
        provider: ProviderConfig,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: Optional[int] = None,
        **kwargs
    ) -> str:
        """Make API call to a specific provider."""
        
        headers = {"Content-Type": "application/json"}
        
        # Handle different provider authentication
        if provider.api_key:
            if provider.name == "openrouter":
                headers["Authorization"] = f"Bearer {provider.api_key}"
                headers["HTTP-Referer"] = "https://nano-banana-studio.local"
            else:
                headers["Authorization"] = f"Bearer {provider.api_key}"
        
        # Build request based on provider type
        if provider.name == "ollama":
            # Ollama has different API format
            url = f"{provider.base_url}/api/chat"
            payload = {
                "model": model or provider.default_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
        else:
            # OpenAI-compatible API
            url = f"{provider.base_url}/chat/completions"
            payload = {
                "model": model or provider.default_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        
        response = await self.http_client.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout or provider.timeout
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"API error {response.status_code}: {response.text}")
        
        data = response.json()
        
        # Parse response based on provider
        if provider.name == "ollama":
            return data.get("message", {}).get("content", "")
        else:
            return data["choices"][0]["message"]["content"]
    
    async def list_models(self, provider: Optional[str] = None) -> Dict[str, List[str]]:
        """List available models per provider."""
        result = {}
        
        for name, prov in self.providers.items():
            if provider and name != provider:
                continue
            result[name] = prov.models
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status and health information."""
        return {
            "initialized": self._initialized,
            "providers": {
                name: {
                    "status": self.health[name].status.value,
                    "last_check": self.health[name].last_check.isoformat() if self.health[name].last_check else None,
                    "avg_latency_ms": round(self.health[name].avg_latency_ms, 2),
                    "consecutive_failures": self.health[name].consecutive_failures,
                    "error": self.health[name].error_message
                }
                for name in self.providers
            },
            "available_providers": self.get_available_providers()
        }
    
    async def close(self):
        """Cleanup resources."""
        if self._health_check_task:
            self._health_check_task.cancel()
        
        if self.http_client:
            await self.http_client.aclose()


# Singleton instance
_llm_service: Optional[LLMProviderService] = None


async def get_llm_service() -> LLMProviderService:
    """Get or create LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMProviderService()
        await _llm_service.initialize()
    return _llm_service
