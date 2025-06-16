"""Core functionality for WebExtract."""

from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    ExtractionError,
    LLMError,
    ScrapingError,
    WebExtractError,
)
from .extractor import DataExtractor
from .llm_client import BaseLLMClient, OllamaClient
from .llm_factory import create_llm_client, get_available_providers
from .models import ExtractedContent, ExtractionConfig, StructuredData
from .scraper import WebScraper

__all__ = [
    "DataExtractor",
    "WebScraper",
    "BaseLLMClient",
    "OllamaClient",
    "StructuredData",
    "ExtractedContent",
    "ExtractionConfig",
    "create_llm_client",
    "get_available_providers",
    # Exceptions
    "WebExtractError",
    "ExtractionError",
    "ScrapingError",
    "LLMError",
    "ConfigurationError",
    "AuthenticationError",
]
