"""Configuration system for WebExtract."""

from .profiles import ConfigProfiles
from .settings import settings  # Deprecated
from .settings import (
    ConfigBuilder,
    LLMConfig,
    ScrapingConfig,
    WebExtractConfig,
    get_default_config,
    get_http_headers,
    set_default_config,
)

__all__ = [
    "WebExtractConfig",
    "ConfigBuilder",
    "ScrapingConfig",
    "LLMConfig",
    "ConfigProfiles",
    "get_default_config",
    "set_default_config",
    "get_http_headers",
    "settings",  # Deprecated - use get_default_config() instead
]
