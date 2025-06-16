"""LLM WebExtract - AI-powered web content extraction using LLMs."""

__version__ = "1.2.0"
__author__ = "Himasha Herath"
__description__ = "AI-powered web content extraction with Large Language Models"

# Lazy imports - only import when needed to allow version checking
import sys

_imports_loaded = False


def _load_imports():
    """Load all imports when needed."""
    global _imports_loaded
    if _imports_loaded:
        return

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

    # Add to module globals
    current_module = sys.modules[__name__]
    setattr(current_module, "ConfigProfiles", ConfigProfiles)
    setattr(current_module, "ConfigBuilder", ConfigBuilder)
    setattr(current_module, "LLMConfig", LLMConfig)
    setattr(current_module, "ScrapingConfig", ScrapingConfig)
    setattr(current_module, "WebExtractConfig", WebExtractConfig)
    setattr(current_module, "AuthenticationError", AuthenticationError)
    setattr(current_module, "ConfigurationError", ConfigurationError)
    setattr(current_module, "ExtractionError", ExtractionError)
    setattr(current_module, "LLMError", LLMError)
    setattr(current_module, "ScrapingError", ScrapingError)
    setattr(current_module, "WebExtractError", WebExtractError)
    setattr(current_module, "WebExtractor", WebExtractor)
    setattr(current_module, "ExtractedContent", ExtractedContent)
    setattr(current_module, "ExtractionConfig", ExtractionConfig)
    setattr(current_module, "StructuredData", StructuredData)

    _imports_loaded = True


def __getattr__(name):
    """Load imports on first access."""
    _load_imports()
    return getattr(sys.modules[__name__], name)


# Public API
__all__ = [
    "WebExtractor",
    "StructuredData",
    "ExtractedContent",
    "ExtractionConfig",
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
]


# Convenience functions for quick usage
def quick_extract(url: str, model: str = "llama3.2", **kwargs):
    """Quick extraction with minimal configuration.

    Args:
        url: URL to extract from
        model: LLM model name to use
        **kwargs: Additional configuration options

    Returns:
        StructuredData: Extracted and processed data
    """
    _load_imports()
    current_module = sys.modules[__name__]
    ConfigBuilder = getattr(current_module, "ConfigBuilder")  # noqa: F821
    WebExtractor = getattr(current_module, "WebExtractor")  # noqa: F821

    config = ConfigBuilder().with_model(model).build()
    if kwargs:
        # Apply any additional config options
        for key, value in kwargs.items():
            if hasattr(config.llm, key):
                setattr(config.llm, key, value)
            elif hasattr(config.scraping, key):
                setattr(config.scraping, key, value)

    extractor = WebExtractor(config)
    return extractor.extract(url)


def extract_with_openai(url: str, api_key: str, model: str = "gpt-4", **kwargs):
    """Quick extraction using OpenAI models.

    Args:
        url: URL to extract from
        api_key: OpenAI API key
        model: OpenAI model name
        **kwargs: Additional configuration options

    Returns:
        StructuredData: Extracted and processed data
    """
    _load_imports()
    current_module = sys.modules[__name__]
    ConfigBuilder = getattr(current_module, "ConfigBuilder")  # noqa: F821
    WebExtractor = getattr(current_module, "WebExtractor")  # noqa: F821

    config = ConfigBuilder().with_openai(api_key, model).build()
    extractor = WebExtractor(config)
    return extractor.extract(url)


def extract_with_anthropic(
    url: str, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs
):
    """Quick extraction using Anthropic models.

    Args:
        url: URL to extract from
        api_key: Anthropic API key
        model: Claude model name
        **kwargs: Additional configuration options

    Returns:
        StructuredData: Extracted and processed data
    """
    _load_imports()
    current_module = sys.modules[__name__]
    ConfigBuilder = getattr(current_module, "ConfigBuilder")  # noqa: F821
    WebExtractor = getattr(current_module, "WebExtractor")  # noqa: F821

    config = ConfigBuilder().with_anthropic(api_key, model).build()
    extractor = WebExtractor(config)
    return extractor.extract(url)
