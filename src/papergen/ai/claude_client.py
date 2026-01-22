"""Claude API client wrapper."""

from typing import Dict, Any, Optional, Iterator
import anthropic
import httpx
import requests
import json
import time

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
        self.model = model or config.get('api.model', 'claude-sonnet-4-5-20250929')
        self.base_url = base_url if base_url is not None else config.get_api_base_url()

        # For third-party APIs (like Claude Code proxies), use requests library
        # to avoid httpx connection pooling issues
        if self.base_url:
            self.use_direct_http = True
            self.logger.info(f"Claude client initialized: model={self.model}, base_url={self.base_url}, using requests library")
        else:
            self.use_direct_http = False
            # For official Anthropic API, use the SDK
            timeout = httpx.Timeout(600.0, connect=30.0)
            self.client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=timeout
            )
            self.logger.info(f"Claude client initialized: model={self.model}, using Anthropic SDK")

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

            if self.use_direct_http:
                # Use direct HTTP requests for third-party APIs
                result = self._direct_http_generate(messages, max_tokens, temperature, system)
            else:
                # Use Anthropic SDK for official API
                result = self._sdk_generate(messages, max_tokens, temperature, system)

            self.logger.info(f"API call successful: response_length={len(result)}")
            return result

        except Exception as e:
            log_error(e, "Claude API generate", model=self.model, max_tokens=max_tokens)
            raise RuntimeError(f"Claude API error: {str(e)}")

    def _sdk_generate(
        self,
        messages: list,
        max_tokens: int,
        temperature: float,
        system: Optional[str]
    ) -> str:
        """Generate using Anthropic SDK."""
        # Build API call parameters
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

        return result

    def _direct_http_generate(
        self,
        messages: list,
        max_tokens: int,
        temperature: float,
        system: Optional[str]
    ) -> str:
        """Generate using direct HTTP requests (for third-party APIs)."""
        # Build request payload
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        if system:
            payload["system"] = system

        # Retry logic for flaky proxies
        max_retries = 3
        retry_delay = 1.0  # Start with 1 second

        for attempt in range(max_retries):
            session = requests.Session()
            try:
                response = session.post(
                    f"{self.base_url}/v1/messages",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Connection": "close"  # Force connection close
                    },
                    json=payload,
                    timeout=120.0
                )

                response.raise_for_status()
                data = response.json()

                # Extract text from response
                result = data["content"][0]["text"]
                input_tokens = data["usage"]["input_tokens"]
                output_tokens = data["usage"]["output_tokens"]

                log_api_call(
                    endpoint="messages.create",
                    model=self.model,
                    tokens=input_tokens + output_tokens,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    max_tokens=max_tokens
                )

                return result

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                session.close()
                if attempt < max_retries - 1:
                    self.logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error(f"Request failed after {max_retries} attempts: {e}")
                    raise
            except requests.exceptions.HTTPError as e:
                session.close()
                # Don't retry on HTTP errors like 502, 4xx
                if e.response.status_code == 502 and attempt < max_retries - 1:
                    self.logger.warning(f"502 Bad Gateway (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
            except Exception as e:
                session.close()
                raise
            finally:
                session.close()

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
            if self.use_direct_http:
                # For third-party APIs, fall back to non-streaming
                # (streaming with direct HTTP is more complex)
                result = self._direct_http_generate(messages, max_tokens, temperature, system)
                yield result
            else:
                # Use SDK streaming for official API
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
            if self.use_direct_http:
                max_retries = 2
                retry_delay = 1.0

                for attempt in range(max_retries):
                    session = requests.Session()
                    try:
                        response = session.post(
                            f"{self.base_url}/v1/messages",
                            headers={
                                "Content-Type": "application/json",
                                "x-api-key": self.api_key,
                                "anthropic-version": "2023-06-01",
                                "Connection": "close"
                            },
                            json={
                                "model": self.model,
                                "max_tokens": 10,
                                "messages": [{"role": "user", "content": "Hi"}]
                            },
                            timeout=30.0
                        )
                        response.raise_for_status()
                        session.close()
                        return True
                    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                        session.close()
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            self.logger.error(f"API key validation failed: {type(e).__name__}: {str(e)}")
                            return False
                    except Exception as e:
                        session.close()
                        self.logger.error(f"API key validation failed: {type(e).__name__}: {str(e)}")
                        return False
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                return True
        except Exception as e:
            self.logger.error(f"API key validation failed: {type(e).__name__}: {str(e)}")
            return False
