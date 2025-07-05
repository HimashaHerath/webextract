"""Configuration settings for WebExtract package."""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ScrapingConfig:
    """Configuration for web scraping behavior."""

    request_timeout: int = 30
    max_content_length: int = 10000  # Increased default
    retry_attempts: int = 3
    retry_delay: float = 2.0
    request_delay: float = 1.0
    user_agents: List[str] = field(
        default_factory=lambda: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
    )


@dataclass
class LLMConfig:
    """Configuration for LLM processing."""

    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    model_name: str = "llama3.2"  # Updated default
    temperature: float = 0.1
    max_tokens: int = 4000  # Increased for better responses
    retry_attempts: int = 3
    api_key: Optional[str] = None
    custom_prompt: Optional[str] = None
    timeout: int = 60


@dataclass
class WebExtractConfig:
    """Main configuration class."""

    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)

    @classmethod
    def from_env(cls) -> "WebExtractConfig":
        """Create configuration from environment variables."""
        scraping = ScrapingConfig(
            request_timeout=int(os.getenv("WEBEXTRACT_REQUEST_TIMEOUT", "30")),
            max_content_length=int(os.getenv("WEBEXTRACT_MAX_CONTENT", "10000")),
            retry_attempts=int(os.getenv("WEBEXTRACT_RETRY_ATTEMPTS", "3")),
            request_delay=float(os.getenv("WEBEXTRACT_REQUEST_DELAY", "1.0")),
        )

        llm = LLMConfig(
            provider=os.getenv("WEBEXTRACT_LLM_PROVIDER", "ollama"),
            base_url=os.getenv("WEBEXTRACT_LLM_BASE_URL", "http://localhost:11434"),
            model_name=os.getenv("WEBEXTRACT_MODEL", "llama3.2"),
            temperature=float(os.getenv("WEBEXTRACT_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("WEBEXTRACT_MAX_TOKENS", "4000")),
            api_key=os.getenv("WEBEXTRACT_API_KEY"),
            timeout=int(os.getenv("WEBEXTRACT_LLM_TIMEOUT", "60")),
        )

        return cls(scraping=scraping, llm=llm)


class ConfigBuilder:
    """Fluent API for building configurations."""

    def __init__(self):
        self._config = WebExtractConfig()

    def with_model(self, model_name: str, provider: str = "ollama") -> "ConfigBuilder":
        """Set the LLM model."""
        self._config.llm.model_name = model_name
        self._config.llm.provider = provider
        return self

    def with_ollama(
        self, model: str = "llama3.2", base_url: str = "http://localhost:11434"
    ) -> "ConfigBuilder":
        """Configure for Ollama."""
        self._config.llm.provider = "ollama"
        self._config.llm.model_name = model
        self._config.llm.base_url = base_url
        return self

    def with_openai(self, api_key: str, model: str = "gpt-4o-mini") -> "ConfigBuilder":
        """Configure for OpenAI."""
        self._config.llm.provider = "openai"
        self._config.llm.api_key = api_key
        self._config.llm.model_name = model
        self._config.llm.base_url = "https://api.openai.com/v1"
        return self

    def with_anthropic(
        self, api_key: str, model: str = "claude-3-5-sonnet-20241022"
    ) -> "ConfigBuilder":
        """Configure for Anthropic."""
        self._config.llm.provider = "anthropic"
        self._config.llm.api_key = api_key
        self._config.llm.model_name = model
        return self

    def with_timeout(self, timeout: int) -> "ConfigBuilder":
        """Set request timeout."""
        self._config.scraping.request_timeout = timeout
        self._config.llm.timeout = timeout
        return self

    def with_content_limit(self, limit: int) -> "ConfigBuilder":
        """Set content length limit."""
        self._config.scraping.max_content_length = limit
        return self

    def with_custom_prompt(self, prompt: str) -> "ConfigBuilder":
        """Set custom extraction prompt."""
        self._config.llm.custom_prompt = prompt
        return self

    def with_temperature(self, temperature: float) -> "ConfigBuilder":
        """Set LLM temperature."""
        self._config.llm.temperature = max(0.0, min(1.0, temperature))
        return self

    def build(self) -> WebExtractConfig:
        """Build the configuration."""
        return self._config


# Default global configuration instance
_default_config = None


def get_default_config() -> WebExtractConfig:
    """Get the default configuration instance."""
    global _default_config
    if _default_config is None:
        _default_config = WebExtractConfig.from_env()
    return _default_config


def set_default_config(config: WebExtractConfig):
    """Set the default configuration instance."""
    global _default_config
    _default_config = config


def get_http_headers(custom_user_agent: str = None) -> dict:
    """Get HTTP headers with rotating user agents."""
    import random

    config = get_default_config()
    user_agent = custom_user_agent or random.choice(config.scraping.user_agents)

    return {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


# Legacy compatibility layer - will be removed in future versions
class _LegacySettings:
    """Legacy settings wrapper for backward compatibility."""

    def __init__(self):
        import warnings

        warnings.warn(
            "The Settings class is deprecated. Use WebExtractConfig instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    @property
    def OLLAMA_BASE_URL(self):
        return get_default_config().llm.base_url

    @property
    def DEFAULT_MODEL(self):
        return get_default_config().llm.model_name

    @property
    def REQUEST_TIMEOUT(self):
        return get_default_config().scraping.request_timeout

    @property
    def MAX_CONTENT_LENGTH(self):
        return get_default_config().scraping.max_content_length

    @property
    def RETRY_ATTEMPTS(self):
        return get_default_config().scraping.retry_attempts

    @property
    def RETRY_DELAY(self):
        return get_default_config().scraping.retry_delay

    @property
    def REQUEST_DELAY(self):
        return get_default_config().scraping.request_delay

    @property
    def LLM_TEMPERATURE(self):
        return get_default_config().llm.temperature

    @property
    def MAX_TOKENS(self):
        return get_default_config().llm.max_tokens

    @property
    def LLM_RETRY_ATTEMPTS(self):
        return get_default_config().llm.retry_attempts

    @property
    def USER_AGENTS(self):
        return get_default_config().scraping.user_agents

    @staticmethod
    def get_headers(custom_user_agent: str = None) -> dict:
        """Get HTTP headers."""
        return get_http_headers(custom_user_agent)


# Deprecated global settings instance
settings = _LegacySettings()
