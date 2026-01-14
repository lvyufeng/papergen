"""Multi-LLM manager for parallel generation."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from ..core.logging_config import get_logger


@dataclass
class LLMConfig:
    """Configuration for a single LLM."""
    provider: str  # anthropic, openai, gemini, deepseek, qwen
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    enabled: bool = True


@dataclass
class LLMResponse:
    """Response from a single LLM."""
    provider: str
    model: str
    content: str
    success: bool
    error: Optional[str] = None


class MultiLLMManager:
    """Manages multiple LLMs for parallel generation."""

    def __init__(self):
        """Initialize multi-LLM manager."""
        self.logger = get_logger()
        self.llm_configs: List[LLMConfig] = []
        self._clients: Dict[str, Any] = {}

    def add_llm(self, config: LLMConfig):
        """Add an LLM configuration."""
        if config.enabled:
            self.llm_configs.append(config)
            self.logger.info(f"Added LLM: {config.provider}/{config.model}")

    def _get_client(self, config: LLMConfig):
        """Get or create a client for the given config."""
        key = f"{config.provider}_{config.model}"
        if key not in self._clients:
            if config.provider == "anthropic":
                from .claude_client import ClaudeClient
                self._clients[key] = ClaudeClient(
                    api_key=config.api_key,
                    model=config.model,
                    base_url=config.base_url
                )
            else:
                from .openai_client import OpenAIClient
                self._clients[key] = OpenAIClient(
                    api_key=config.api_key,
                    model=config.model,
                    base_url=config.base_url,
                    provider=config.provider
                )
        return self._clients[key]

    def _generate_single(
        self,
        config: LLMConfig,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.8
    ) -> LLMResponse:
        """Generate from a single LLM."""
        try:
            client = self._get_client(config)
            content = client.generate(
                prompt=prompt,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return LLMResponse(
                provider=config.provider,
                model=config.model,
                content=content,
                success=True
            )
        except Exception as e:
            self.logger.error(f"Error from {config.provider}: {e}")
            return LLMResponse(
                provider=config.provider,
                model=config.model,
                content="",
                success=False,
                error=str(e)
            )

    def generate_parallel(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.8,
        max_workers: int = 5
    ) -> List[LLMResponse]:
        """Generate from all LLMs in parallel."""
        if not self.llm_configs:
            raise ValueError("No LLMs configured")

        self.logger.info(f"Generating from {len(self.llm_configs)} LLMs")
        responses = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._generate_single,
                    config, prompt, system, max_tokens, temperature
                ): config
                for config in self.llm_configs
            }

            for future in as_completed(futures):
                response = future.result()
                responses.append(response)
                if response.success:
                    self.logger.info(f"Got response from {response.provider}")
                else:
                    self.logger.warning(f"Failed: {response.provider}")

        return responses

    @classmethod
    def from_env(cls) -> "MultiLLMManager":
        """Create manager with LLMs configured from environment."""
        manager = cls()

        # Check for Anthropic/Claude
        if os.environ.get("ANTHROPIC_API_KEY"):
            manager.add_llm(LLMConfig(
                provider="anthropic",
                model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
                base_url=os.environ.get("ANTHROPIC_BASE_URL")
            ))

        # Check for OpenAI
        if os.environ.get("OPENAI_API_KEY"):
            manager.add_llm(LLMConfig(
                provider="openai",
                model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
                api_key=os.environ.get("OPENAI_API_KEY")
            ))

        # Check for Gemini
        if os.environ.get("GEMINI_API_KEY"):
            manager.add_llm(LLMConfig(
                provider="gemini",
                model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
                api_key=os.environ.get("GEMINI_API_KEY")
            ))

        return manager
