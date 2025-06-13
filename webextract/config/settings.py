"""Enhanced configuration settings for WebExtract package."""

import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScrapingConfig:
    """Configuration for web scraping behavior."""

    request_timeout: int = 30
    max_content_length: int = 5000
    retry_attempts: int = 3
    retry_delay: float = 2.0
    request_delay: float = 1.0
    max_requests_per_minute: int = 30
    user_agents: List[str] = field(
        default_factory=lambda: [
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        ]
    )
    custom_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class LLMConfig:
    """Configuration for LLM processing."""

    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    model_name: str = "gemma3:27b"
    temperature: float = 0.1
    max_tokens: int = 2000
    retry_attempts: int = 2
    api_key: Optional[str] = None
    custom_prompt: Optional[str] = None


@dataclass
class FilterConfig:
    """Configuration for content filtering."""

    unwanted_elements: List[str] = field(
        default_factory=lambda: [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "noscript",
            "iframe",
        ]
    )
    unwanted_selectors: List[str] = field(
        default_factory=lambda: [
            ".advertisement",
            ".ad",
            ".ads",
            ".banner",
            ".popup",
            ".modal",
        ]
    )
    content_selectors: List[str] = field(
        default_factory=lambda: [
            "main",
            "article",
            '[role="main"]',
            ".main-content",
            ".content",
            "#content",
        ]
    )
    skip_link_patterns: List[str] = field(
        default_factory=lambda: [
            "javascript:",
            "mailto:",
            "tel:",
            "/admin",
            "/login",
            ".pdf",
            ".jpg",
            ".png",
        ]
    )
    min_content_length: int = 10
    max_url_length: int = 200


class WebExtractConfig:
    """Main configuration class for WebExtract package."""

    def __init__(
        self,
        scraping: Optional[ScrapingConfig] = None,
        llm: Optional[LLMConfig] = None,
        filtering: Optional[FilterConfig] = None,
    ):
        self.scraping = scraping or ScrapingConfig()
        self.llm = llm or LLMConfig()
        self.filtering = filtering or FilterConfig()

    @classmethod
    def from_env(cls) -> "WebExtractConfig":
        """Create config from environment variables."""
        scraping_config = ScrapingConfig(
            request_timeout=int(os.getenv("WEBEXTRACT_REQUEST_TIMEOUT", "30")),
            max_content_length=int(os.getenv("WEBEXTRACT_MAX_CONTENT", "5000")),
        )

        llm_config = LLMConfig(
            provider=os.getenv("WEBEXTRACT_LLM_PROVIDER", "ollama"),
            base_url=os.getenv("WEBEXTRACT_LLM_BASE_URL", "http://localhost:11434"),
            model_name=os.getenv("WEBEXTRACT_MODEL", "gemma3:27b"),
        )

        return cls(scraping=scraping_config, llm=llm_config, filtering=FilterConfig())


class ConfigBuilder:
    """Fluent configuration builder."""

    def __init__(self):
        self._config = WebExtractConfig()

    def with_model(self, model_name: str, provider: str = "ollama") -> "ConfigBuilder":
        """Configure LLM model."""
        self._config.llm.model_name = model_name
        self._config.llm.provider = provider
        return self

    def with_ollama(self, base_url: str = "http://localhost:11434") -> "ConfigBuilder":
        """Configure Ollama connection."""
        self._config.llm.provider = "ollama"
        self._config.llm.base_url = base_url
        return self

    def with_openai(self, api_key: str, model: str = "gpt-4") -> "ConfigBuilder":
        """Configure OpenAI connection."""
        self._config.llm.provider = "openai"
        self._config.llm.api_key = api_key
        self._config.llm.model_name = model
        return self

    def with_anthropic(
        self, api_key: str, model: str = "claude-3-sonnet-20240229"
    ) -> "ConfigBuilder":
        """Configure Anthropic connection."""
        self._config.llm.provider = "anthropic"
        self._config.llm.api_key = api_key
        self._config.llm.model_name = model
        return self

    def with_timeout(self, timeout: int) -> "ConfigBuilder":
        """Set request timeout."""
        self._config.scraping.request_timeout = timeout
        return self

    def with_content_limit(self, limit: int) -> "ConfigBuilder":
        """Set max content length."""
        self._config.scraping.max_content_length = limit
        return self

    def with_custom_prompt(self, prompt: str) -> "ConfigBuilder":
        """Set custom extraction prompt."""
        self._config.llm.custom_prompt = prompt
        return self

    def build(self) -> WebExtractConfig:
        """Build the final configuration."""
        return self._config


# Legacy compatibility class
class Settings:
    """Legacy settings class for backward compatibility."""

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemma3:27b")
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "5000"))
    RETRY_ATTEMPTS: int = int(os.getenv("RETRY_ATTEMPTS", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "2.0"))
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "1.0"))
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "30"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    LLM_RETRY_ATTEMPTS: int = int(os.getenv("LLM_RETRY_ATTEMPTS", "2"))
    DEFAULT_OUTPUT_FORMAT: str = os.getenv("DEFAULT_OUTPUT_FORMAT", "json")

    USER_AGENTS: List[str] = [
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    ]

    @classmethod
    def get_headers(cls, custom_user_agent: str = None) -> dict:
        """Get HTTP headers for requests with optional custom user agent."""
        user_agent = custom_user_agent or random.choice(cls.USER_AGENTS)

        return {
            "User-Agent": user_agent,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }


# Global settings instance for backward compatibility
settings = Settings()
