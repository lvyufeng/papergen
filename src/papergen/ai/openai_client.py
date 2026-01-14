"""OpenAI API client wrapper."""

from typing import Dict, Any, Optional, Iterator
import os

from ..core.logging_config import get_logger, log_api_call, log_error


class OpenAIClient:
    """Wrapper for OpenAI-compatible APIs (OpenAI, Gemini, DeepSeek, etc.)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: str = "openai"
    ):
        """
        Initialize OpenAI-compatible client.

        Args:
            api_key: API key (uses env var if not provided)
            model: Model to use
            base_url: Custom API base URL
            provider: Provider name (openai, gemini, deepseek, etc.)
        """
        self.logger = get_logger()
        self.provider = provider

        # Set defaults based on provider
        self.api_key = api_key or self._get_default_api_key()
        self.model = model or self._get_default_model()
        self.base_url = base_url or self._get_default_base_url()

        # Import openai lazily
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            self.logger.info(f"OpenAI client initialized: provider={provider}, model={self.model}")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def _get_default_api_key(self) -> str:
        """Get default API key based on provider."""
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "qwen": "DASHSCOPE_API_KEY",
        }
        env_var = env_vars.get(self.provider, f"{self.provider.upper()}_API_KEY")
        return os.environ.get(env_var, "")

    def _get_default_model(self) -> str:
        """Get default model based on provider."""
        models = {
            "openai": "gpt-4o",
            "gemini": "gemini-2.0-flash",
            "deepseek": "deepseek-chat",
            "qwen": "qwen-plus",
        }
        return models.get(self.provider, "gpt-4o")

    def _get_default_base_url(self) -> Optional[str]:
        """Get default base URL based on provider."""
        urls = {
            "openai": None,  # Use default
            "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "deepseek": "https://api.deepseek.com",
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        }
        return urls.get(self.provider)

    def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
    ) -> str:
        """
        Generate text using OpenAI-compatible API.

        Args:
            prompt: The prompt to send
            context: Optional context dictionary
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            system: Optional system prompt

        Returns:
            Generated text
        """
        messages = []

        # Add system message if provided
        if system:
            messages.append({"role": "system", "content": system})

        # Add context if provided
        if context:
            context_text = self._format_context(context)
            messages.append({
                "role": "user",
                "content": f"Context:\n{context_text}\n\n{prompt}"
            })
        else:
            messages.append({"role": "user", "content": prompt})

        try:
            self.logger.debug(f"API call: provider={self.provider}, model={self.model}")

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )

            result = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0

            log_api_call(
                endpoint="chat.completions",
                model=self.model,
                tokens=input_tokens + output_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                max_tokens=max_tokens
            )

            return result

        except Exception as e:
            log_error(e, f"{self.provider} API generate", model=self.model)
            raise RuntimeError(f"{self.provider} API error: {str(e)}")

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary as text."""
        formatted = []
        for key, value in context.items():
            if isinstance(value, dict):
                formatted.append(f"## {key}")
                for sub_key, sub_value in value.items():
                    formatted.append(f"**{sub_key}:** {sub_value}")
            elif isinstance(value, list):
                formatted.append(f"## {key}")
                for item in value:
                    formatted.append(f"- {item}")
            else:
                formatted.append(f"**{key}:** {value}")
        return "\n".join(formatted)

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return self.provider

    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model
