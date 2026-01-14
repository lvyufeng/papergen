"""Claude API client wrapper."""

from typing import Dict, Any, Optional, Iterator
import anthropic

from ..core.config import config
from ..core.logging_config import get_logger, log_api_call, log_error


class ClaudeClient:
    """Wrapper for Anthropic Claude API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (uses env var if not provided)
            model: Model to use (uses config default if not provided)
            base_url: Custom API base URL (uses config if not provided, supports self-hosted/third-party APIs)
        """
        self.logger = get_logger()
        self.api_key = api_key or config.get_api_key()
        self.model = model or config.get('api.model', 'claude-opus-4-5')
        self.base_url = base_url if base_url is not None else config.get_api_base_url()

        # Initialize Anthropic client with optional custom base URL
        if self.base_url:
            self.client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
            self.logger.info(f"Claude client initialized: model={self.model}, base_url={self.base_url}")
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.logger.info(f"Claude client initialized: model={self.model}")

    def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
    ) -> str:
        """
        Generate text using Claude.

        Args:
            prompt: The prompt to send
            context: Optional context dictionary
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            system: Optional system prompt

        Returns:
            Generated text
        """
        # Build messages
        messages = []

        # Add context if provided
        if context:
            context_text = self._format_context(context)
            messages.append({
                "role": "user",
                "content": f"Context:\n{context_text}\n\n{prompt}"
            })
        else:
            messages.append({
                "role": "user",
                "content": prompt
            })

        # Call Claude API
        try:
            self.logger.debug(f"API call: model={self.model}, max_tokens={max_tokens}, temp={temperature}, prompt_length={len(prompt)}")

            # Build API call parameters (only include system if provided)
            api_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            if system:
                api_params["system"] = system

            response = self.client.messages.create(**api_params)

            # Extract text from response
            result = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            log_api_call(
                endpoint="messages.create",
                model=self.model,
                tokens=input_tokens + output_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                max_tokens=max_tokens
            )

            self.logger.info(f"API call successful: input_tokens={input_tokens}, output_tokens={output_tokens}, response_length={len(result)}")

            return result

        except Exception as e:
            log_error(e, "Claude API generate", model=self.model, max_tokens=max_tokens)
            raise RuntimeError(f"Claude API error: {str(e)}")

    def stream_generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Generate text using Claude with streaming.

        Args:
            prompt: The prompt to send
            context: Optional context dictionary
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            system: Optional system prompt

        Yields:
            Chunks of generated text
        """
        # Build messages
        messages = []

        if context:
            context_text = self._format_context(context)
            messages.append({
                "role": "user",
                "content": f"Context:\n{context_text}\n\n{prompt}"
            })
        else:
            messages.append({
                "role": "user",
                "content": prompt
            })

        # Call Claude API with streaming
        try:
            # Build API call parameters (only include system if provided)
            api_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            if system:
                api_params["system"] = system

            with self.client.messages.stream(**api_params) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            raise RuntimeError(f"Claude API error: {str(e)}")

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count
        """
        # Simple estimation: ~4 characters per token
        # This is a rough approximation
        # Claude's tokenizer may differ slightly
        return len(text) // 4

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

    def validate_api_key(self) -> bool:
        """
        Validate that API key works.

        Returns:
            True if API key is valid
        """
        try:
            # Make a minimal API call to test
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception:
            return False
