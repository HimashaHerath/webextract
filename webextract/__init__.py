"""LLM WebExtract - AI-powered web content extraction using LLMs.

This module provides clean, direct imports with excellent IDE support,
immediate error feedback, and proper type hints.
"""

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:  # pragma: no cover - for Python <3.10
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version("llm-webextract")
except PackageNotFoundError:
    # Package is not installed, read version from pyproject.toml
    from pathlib import Path
    import re

    root = Path(__file__).resolve().parents[1]
    pyproject = root / "pyproject.toml"
    version_pattern = re.compile(r"^version\s*=\s*['\"](.+?)['\"]", re.M)
    try:
        text = pyproject.read_text()
        match = version_pattern.search(text)
        __version__ = match.group(1) if match else "0.0.0"
    except Exception:  # pragma: no cover - failure fallback
        __version__ = "0.0.0"
__author__ = "Himasha Herath"
__description__ = "AI-powered web content extraction with Large Language Models"

# Direct imports for better IDE support and immediate error feedback
from .config.profiles import ConfigProfiles
from .config.settings import ConfigBuilder, LLMConfig, ScrapingConfig, WebExtractConfig
from .core.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ExtractionError,
    LLMError,
    ScrapingError,
    WebExtractError,
)
from .core.extractor import DataExtractor as WebExtractor
from .core.models import ExtractedContent, ExtractionConfig, StructuredData

# Public API
__all__ = [
    # Core classes
    "WebExtractor",
    "StructuredData",
    "ExtractedContent",
    "ExtractionConfig",
    # Configuration
    "WebExtractConfig",
    "ConfigBuilder",
    "ScrapingConfig",
    "LLMConfig",
    "ConfigProfiles",
    # Exceptions
    "WebExtractError",
    "ExtractionError",
    "ScrapingError",
    "LLMError",
    "ConfigurationError",
    "AuthenticationError",
    # Convenience functions
    "quick_extract",
    "extract_with_openai",
    "extract_with_anthropic",
    "extract_with_ollama",
]


def quick_extract(url: str, model: str = "llama3.2", **kwargs) -> StructuredData:
    """Quick extraction with minimal configuration.

    Args:
        url: URL to extract from
        model: LLM model name to use (default: llama3.2)
        **kwargs: Additional configuration options

    Returns:
        StructuredData: Extracted and processed data

    Raises:
        ExtractionError: If extraction fails
        ConfigurationError: If configuration is invalid
        LLMError: If LLM service is unavailable

    Example:
        >>> result = quick_extract("https://example.com")
        >>> print(result.content.title)
    """
    config = ConfigBuilder().with_model(model).build()

    # Apply additional configuration options
    if kwargs:
        for key, value in kwargs.items():
            if hasattr(config.llm, key):
                setattr(config.llm, key, value)
            elif hasattr(config.scraping, key):
                setattr(config.scraping, key, value)

    extractor = WebExtractor(config)
    return extractor.extract(url)


def extract_with_openai(
    url: str, api_key: str, model: str = "gpt-4o-mini", **kwargs
) -> StructuredData:
    """Quick extraction using OpenAI models.

    Args:
        url: URL to extract from
        api_key: OpenAI API key
        model: OpenAI model name (default: gpt-4o-mini)
        **kwargs: Additional configuration options

    Returns:
        StructuredData: Extracted and processed data

    Raises:
        AuthenticationError: If API key is invalid
        ExtractionError: If extraction fails
        LLMError: If OpenAI service is unavailable

    Example:
        >>> result = extract_with_openai("https://example.com", "sk-...")
        >>> print(result.structured_info.get("summary"))
    """
    config = ConfigBuilder().with_openai(api_key, model).build()
    extractor = WebExtractor(config)
    return extractor.extract(url)


def extract_with_anthropic(
    url: str, api_key: str, model: str = "claude-3-5-sonnet-20241022", **kwargs
) -> StructuredData:
    """Quick extraction using Anthropic Claude models.

    Args:
        url: URL to extract from
        api_key: Anthropic API key
        model: Claude model name (default: claude-3-5-sonnet-20241022)
        **kwargs: Additional configuration options

    Returns:
        StructuredData: Extracted and processed data

    Raises:
        AuthenticationError: If API key is invalid
        ExtractionError: If extraction fails
        LLMError: If Anthropic service is unavailable

    Example:
        >>> result = extract_with_anthropic("https://example.com", "sk-ant-...")
        >>> print(result.confidence)
    """
    config = ConfigBuilder().with_anthropic(api_key, model).build()
    extractor = WebExtractor(config)
    return extractor.extract(url)


def extract_with_ollama(
    url: str, model: str = "llama3.2", base_url: str = "http://localhost:11434", **kwargs
) -> StructuredData:
    """Quick extraction using Ollama models.

    Args:
        url: URL to extract from
        model: Ollama model name (default: llama3.2)
        base_url: Ollama server base URL (default: http://localhost:11434)
        **kwargs: Additional configuration options

    Returns:
        StructuredData: Extracted and processed data

    Raises:
        LLMError: If Ollama server is unavailable
        ExtractionError: If extraction fails
        ConfigurationError: If model is not available

    Example:
        >>> result = extract_with_ollama("https://example.com", "llama3.2")
        >>> print(result.content.main_content[:100])
    """
    config = ConfigBuilder().with_ollama(model, base_url).build()
    extractor = WebExtractor(config)
    return extractor.extract(url)
