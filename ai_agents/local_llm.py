"""
Local LLM Provider using Ollama
Provides unlimited, free AI inference for ULTRATHINK
"""

import requests
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Local LLM inference using Ollama"""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3:8b"):
        self.base_url = base_url
        self.default_model = default_model
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> list:
        """List available Ollama models"""
        if not self.available:
            return []

        try:
            response = requests.get(f"{self.base_url}/api/tags")
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []

    def generate(self, prompt: str, model: Optional[str] = None,
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 2000) -> Dict[str, Any]:
        """Generate response using Ollama"""

        if not self.available:
            raise Exception("Ollama is not available. Install: curl -fsSL https://ollama.com/install.sh | sh")

        model = model or self.default_model

        # Construct full prompt with system message
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=60
            )

            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.text}")

            data = response.json()

            return {
                "content": data.get("response", ""),
                "model": model,
                "provider": "ollama",
                "cost": 0.0,  # Free!
                "tokens": {
                    "prompt": data.get("prompt_eval_count", 0),
                    "completion": data.get("eval_count", 0)
                }
            }

        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise

    async def generate_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Async wrapper for generate (for compatibility)"""
        # Note: Ollama doesn't have native async, but we can wrap it
        return self.generate(prompt, **kwargs)

    def pull_model(self, model: str) -> bool:
        """Download an Ollama model"""
        try:
            logger.info(f"Pulling Ollama model: {model}")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
                stream=True
            )

            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get("status", "")
                    logger.info(f"  {status}")

            logger.info(f"Model {model} pulled successfully")
            return True

        except Exception as e:
            logger.error(f"Error pulling model {model}: {e}")
            return False


class GroqProvider:
    """Groq API provider - FREE and ultra-fast"""

    def __init__(self, api_key: Optional[str] = None):
        import os
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.base_url = "https://api.groq.com/openai/v1"
        self.available = bool(self.api_key)

    def generate(self, prompt: str, model: str = "llama3-70b-8192",
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 2000) -> Dict[str, Any]:
        """Generate response using Groq"""

        if not self.available:
            raise Exception("GROQ_API_KEY not set. Get free key at: https://console.groq.com")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"Groq error: {response.text}")

            data = response.json()
            usage = data.get("usage", {})

            return {
                "content": data["choices"][0]["message"]["content"],
                "model": model,
                "provider": "groq",
                "cost": 0.0,  # FREE tier!
                "tokens": {
                    "prompt": usage.get("prompt_tokens", 0),
                    "completion": usage.get("completion_tokens", 0)
                }
            }

        except Exception as e:
            logger.error(f"Groq generation error: {e}")
            raise

    async def generate_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Async wrapper"""
        return self.generate(prompt, **kwargs)


# Convenience functions
def get_ollama() -> OllamaProvider:
    """Get Ollama provider instance"""
    return OllamaProvider()


def get_groq() -> GroqProvider:
    """Get Groq provider instance"""
    return GroqProvider()


# Setup instructions
SETUP_INSTRUCTIONS = """
=== FREE AI SETUP ===

1. GROQ (FREE + FAST):
   - Visit: https://console.groq.com
   - Sign up for free account
   - Get API key
   - export GROQ_API_KEY="gsk_..."

2. OLLAMA (LOCAL + UNLIMITED):
   - Install: curl -fsSL https://ollama.com/install.sh | sh
   - Download model: ollama pull llama3:8b
   - Start: ollama serve (runs automatically)

3. Verify:
   - python3 -c "from ai_agents.local_llm import get_ollama, get_groq; print('Ollama:', get_ollama().available); print('Groq:', get_groq().available)"

=== MODELS AVAILABLE ===

Ollama (Local):
  - llama3:8b (4.7GB) - Fast, good quality
  - llama3:70b (40GB) - Best quality, slower
  - mixtral:8x7b (26GB) - Excellent reasoning
  - deepseek-coder:6.7b (3.8GB) - Code analysis

Groq (Cloud, FREE):
  - llama3-70b-8192 - Best quality
  - llama3-8b-8192 - Fast
  - mixtral-8x7b-32768 - Long context
  - gemma-7b-it - Google model

=== COST ===
- Ollama: $0/month (unlimited)
- Groq: $0/month (free tier, 30 req/min)
- Together: $0.20/M tokens
- DeepSeek: $0.14/M tokens

Total: $0-2/month for unlimited AI! 🚀
"""


if __name__ == "__main__":
    print(SETUP_INSTRUCTIONS)

    # Test Ollama
    print("\n=== Testing Ollama ===")
    ollama = get_ollama()
    print(f"Ollama available: {ollama.available}")
    if ollama.available:
        print(f"Models: {ollama.list_models()}")

        # Test generation
        result = ollama.generate("What is 2+2? Answer in one word.")
        print(f"Response: {result['content']}")
        print(f"Tokens: {result['tokens']}")

    # Test Groq
    print("\n=== Testing Groq ===")
    groq = get_groq()
    print(f"Groq available: {groq.available}")
    if groq.available:
        result = groq.generate("What is 2+2? Answer in one word.")
        print(f"Response: {result['content']}")
        print(f"Tokens: {result['tokens']}")
