"""
Cheap LLM API Router
Routes requests to the cheapest available AI APIs
Supports: DeepSeek, OpenRouter, Alibaba Qwen, Together AI, etc.
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Available LLM providers ranked by cost (cheapest first)"""
    GROQ = "groq"  # FREE tier, ultra-fast! (500+ tokens/sec)
    OLLAMA = "ollama"  # FREE local inference, unlimited
    DEEPSEEK = "deepseek"  # $0.14/M tokens (cheapest paid)
    TOGETHER = "together"  # $0.20/M tokens
    OPENROUTER_QWEN = "openrouter_qwen"  # $0.20/M tokens (Alibaba)
    OPENROUTER_LLAMA = "openrouter_llama"  # $0.18/M tokens
    LOCAL = "local"  # Fallback placeholder

class LLMRouter:
    """Routes LLM requests to the cheapest available provider"""

    # API endpoints
    ENDPOINTS = {
        LLMProvider.GROQ: "https://api.groq.com/openai/v1/chat/completions",
        LLMProvider.OLLAMA: "http://localhost:11434/api/generate",  # Local
        LLMProvider.DEEPSEEK: "https://api.deepseek.com/v1/chat/completions",
        LLMProvider.TOGETHER: "https://api.together.xyz/v1/chat/completions",
        LLMProvider.OPENROUTER_QWEN: "https://openrouter.ai/api/v1/chat/completions",
        LLMProvider.OPENROUTER_LLAMA: "https://openrouter.ai/api/v1/chat/completions",
    }

    # Model names
    MODELS = {
        LLMProvider.GROQ: "llama-3.1-70b-versatile",
        LLMProvider.OLLAMA: "llama3:8b",
        LLMProvider.DEEPSEEK: "deepseek-chat",
        LLMProvider.TOGETHER: "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        LLMProvider.OPENROUTER_QWEN: "qwen/qwen-2.5-72b-instruct",
        LLMProvider.OPENROUTER_LLAMA: "meta-llama/llama-3.1-70b-instruct",
    }

    # Cost per million tokens (input/output)
    COSTS = {
        LLMProvider.GROQ: (0.0, 0.0),  # FREE tier!
        LLMProvider.OLLAMA: (0.0, 0.0),  # FREE local!
        LLMProvider.DEEPSEEK: (0.14, 0.28),
        LLMProvider.TOGETHER: (0.20, 0.20),
        LLMProvider.OPENROUTER_QWEN: (0.20, 0.20),
        LLMProvider.OPENROUTER_LLAMA: (0.18, 0.18),
        LLMProvider.LOCAL: (0.0, 0.0),  # Fallback
    }

    def __init__(self):
        """Initialize LLM router with API keys from environment"""
        self.api_keys = {
            LLMProvider.GROQ: os.getenv("GROQ_API_KEY"),
            LLMProvider.OLLAMA: self._check_ollama(),  # Check if Ollama is running
            LLMProvider.DEEPSEEK: os.getenv("DEEPSEEK_API_KEY"),
            LLMProvider.TOGETHER: os.getenv("TOGETHER_API_KEY"),
            LLMProvider.OPENROUTER_QWEN: os.getenv("OPENROUTER_API_KEY"),
            LLMProvider.OPENROUTER_LLAMA: os.getenv("OPENROUTER_API_KEY"),
        }

        self.total_cost = 0.0
        self.request_count = 0
        self.provider_stats = {provider: {"requests": 0, "cost": 0.0} for provider in LLMProvider}

    def _check_ollama(self) -> Optional[str]:
        """Check if Ollama is available"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=1)
            if response.status_code == 200:
                logger.info("Ollama detected and available")
                return "available"  # Use non-None value to indicate availability
        except:
            pass
        return None

    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available providers with API keys"""
        available = []

        # Always add local as fallback
        available.append(LLMProvider.LOCAL)

        # Check which providers have API keys
        for provider, key in self.api_keys.items():
            if key:
                available.append(provider)

        # Sort by cost (cheapest first)
        available.sort(key=lambda p: self.COSTS[p][0])

        return available

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        preferred_provider: Optional[LLMProvider] = None
    ) -> Dict[str, Any]:
        """Generate response using cheapest available provider"""

        providers = self.get_available_providers()

        # If preferred provider specified and available, try it first
        if preferred_provider and preferred_provider in providers:
            providers.remove(preferred_provider)
            providers.insert(0, preferred_provider)

        # Try providers in order until one works
        for provider in providers:
            try:
                if provider == LLMProvider.LOCAL:
                    result = await self._generate_local(prompt, system_prompt, max_tokens, temperature)
                else:
                    result = await self._generate_api(
                        provider, prompt, system_prompt, max_tokens, temperature
                    )

                # Track stats
                self.request_count += 1
                self.provider_stats[provider]["requests"] += 1

                if "cost" in result:
                    self.total_cost += result["cost"]
                    self.provider_stats[provider]["cost"] += result["cost"]

                return result

            except Exception as e:
                logger.warning(f"Provider {provider.value} failed: {e}, trying next...")
                continue

        raise Exception("All LLM providers failed")

    async def _generate_api(
        self,
        provider: LLMProvider,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Generate using external API provider"""

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_keys[provider]}"
        }

        payload = {
            "model": self.MODELS[provider],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # For OpenRouter, add routing preferences
        if "openrouter" in provider.value:
            headers["HTTP-Referer"] = "https://github.com/yourusername/discovery"
            headers["X-Title"] = "Politician Trading Analysis"

        # Make request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.ENDPOINTS[provider],
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:

                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")

                data = await response.json()

                # Extract response
                content = data["choices"][0]["message"]["content"]

                # Calculate cost
                input_tokens = data.get("usage", {}).get("prompt_tokens", 0)
                output_tokens = data.get("usage", {}).get("completion_tokens", 0)

                input_cost = (input_tokens / 1_000_000) * self.COSTS[provider][0]
                output_cost = (output_tokens / 1_000_000) * self.COSTS[provider][1]
                total_cost = input_cost + output_cost

                return {
                    "content": content,
                    "provider": provider.value,
                    "model": self.MODELS[provider],
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": total_cost,
                    "timestamp": datetime.now().isoformat()
                }

    async def _generate_local(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Generate using local model (fallback)"""

        # For now, return a placeholder
        # In production, integrate with Ollama or llama.cpp
        logger.warning("Using local fallback - returning simplified analysis")

        content = f"LOCAL ANALYSIS PLACEHOLDER:\nPrompt length: {len(prompt)} chars\nThis would use a local LLM like Ollama/llama.cpp"

        return {
            "content": content,
            "provider": "local",
            "model": "local-fallback",
            "input_tokens": len(prompt) // 4,
            "output_tokens": len(content) // 4,
            "cost": 0.0,
            "timestamp": datetime.now().isoformat()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_requests": self.request_count,
            "total_cost": round(self.total_cost, 4),
            "provider_stats": {
                provider.value: {
                    "requests": stats["requests"],
                    "cost": round(stats["cost"], 4)
                }
                for provider, stats in self.provider_stats.items()
                if stats["requests"] > 0
            },
            "average_cost_per_request": round(
                self.total_cost / max(self.request_count, 1), 4
            )
        }


# Singleton instance
_router = None

def get_llm_router() -> LLMRouter:
    """Get global LLM router instance"""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router


async def generate_with_retry(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    max_retries: int = 3
) -> str:
    """Generate with automatic retry and error handling"""
    router = get_llm_router()

    for attempt in range(max_retries):
        try:
            result = await router.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )

            logger.info(f"Generated response using {result['provider']} (cost: ${result['cost']:.4f})")
            return result["content"]

        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"All retry attempts failed: {e}")
                raise

            logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

    raise Exception("Should not reach here")


# Example usage
if __name__ == "__main__":
    async def test():
        router = get_llm_router()

        print("Available providers:", [p.value for p in router.get_available_providers()])

        result = await router.generate(
            prompt="Analyze this trading pattern: Large tech stock purchases before earnings. What does this suggest?",
            system_prompt="You are a financial analyst specializing in political trading patterns.",
            max_tokens=500
        )

        print(f"\nProvider: {result['provider']}")
        print(f"Cost: ${result['cost']:.4f}")
        print(f"\nResponse:\n{result['content']}")
        print(f"\nStats:\n{json.dumps(router.get_stats(), indent=2)}")

    asyncio.run(test())
