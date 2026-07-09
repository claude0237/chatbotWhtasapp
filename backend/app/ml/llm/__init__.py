"""LLM Providers for text generation"""
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from app.config import settings


class LLMProvider(ABC):
    """Base interface for LLM providers"""
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    async def generate_response_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response with conversation history"""
        pass


class OpenAILLMProvider(LLMProvider):
    """OpenAI LLM provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response using OpenAI API"""
        try:
            import openai
            openai.api_key = self.api_key
            
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": prompt})
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except ImportError:
            raise ImportError("OpenAI library not installed")
        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {str(e)}")
    
    async def generate_response_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response with conversation history using OpenAI API"""
        try:
            import openai
            openai.api_key = self.api_key
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except ImportError:
            raise ImportError("OpenAI library not installed")
        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {str(e)}")


class AnthropicLLMProvider(LLMProvider):
    """Anthropic LLM provider"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response using Anthropic API"""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            system_prompt = context if context else ""
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except ImportError:
            raise ImportError("Anthropic library not installed")
        except Exception as e:
            raise RuntimeError(f"Anthropic generation failed: {str(e)}")
    
    async def generate_response_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response with conversation history using Anthropic API"""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            # Convert messages to Anthropic format
            anthropic_messages = []
            system_prompt = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                else:
                    anthropic_messages.append({"role": msg["role"], "content": msg["content"]})
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=anthropic_messages
            )
            
            return response.content[0].text
        except ImportError:
            raise ImportError("Anthropic library not installed")
        except Exception as e:
            raise RuntimeError(f"Anthropic generation failed: {str(e)}")


class OllamaLLMProvider(LLMProvider):
    """Ollama LLM provider (local)"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response using Ollama API"""
        try:
            import httpx
            
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                else:
                    raise RuntimeError(f"Ollama API error: {response.status_code}")
        except ImportError:
            raise ImportError("httpx library not installed")
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {str(e)}")
    
    async def generate_response_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response with conversation history using Ollama API"""
        try:
            import httpx
            
            # Convert messages to a single prompt for Ollama
            prompt_parts = []
            for msg in messages:
                role = msg["role"].upper()
                prompt_parts.append(f"{role}: {msg['content']}")
            
            prompt = "\n".join(prompt_parts)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                else:
                    raise RuntimeError(f"Ollama API error: {response.status_code}")
        except ImportError:
            raise ImportError("httpx library not installed")
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {str(e)}")


# Factory function to get LLM provider
def get_llm_provider(provider_type: str) -> LLMProvider:
    """Get LLM provider by type"""
    if provider_type == "openai":
        return OpenAILLMProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model or "gpt-3.5-turbo"
        )
    elif provider_type == "anthropic":
        return AnthropicLLMProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model or "claude-3-sonnet-20240229"
        )
    elif provider_type == "ollama":
        return OllamaLLMProvider(
            base_url=settings.ollama_base_url or "http://localhost:11434",
            model=settings.ollama_model or "llama2"
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_type}")
