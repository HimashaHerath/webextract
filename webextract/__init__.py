"""LLM WebExtract - AI-powered web content extraction using LLMs."""

__version__ = "1.0.0"
__author__ = "Himasha Herath"
__description__ = "AI-powered web content extraction with Large Language Models"

from .config.profiles import ConfigProfiles

# Configuration imports
from .config.settings import ConfigBuilder, FilterConfig, LLMConfig, ScrapingConfig, WebExtractConfig

# Core imports
from .core.extractor import DataExtractor as WebExtractor
from .core.models import ExtractedContent, ExtractionConfig, StructuredData

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
    "FilterConfig",
    "ConfigProfiles",
]


# Convenience functions for quick usage
def quick_extract(url: str, model: str = "gemma3:27b", **kwargs):
    """Quick extraction with minimal configuration.

    Args:
        url: URL to extract from
        model: LLM model name to use
        **kwargs: Additional configuration options

    Returns:
        StructuredData: Extracted and processed data
    """
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
    config = ConfigBuilder().with_openai(api_key, model).build()
    extractor = WebExtractor(config)
    return extractor.extract(url)


def extract_with_anthropic(url: str, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs):
    """Quick extraction using Anthropic models.

    Args:
        url: URL to extract from
        api_key: Anthropic API key
        model: Claude model name
        **kwargs: Additional configuration options

    Returns:
        StructuredData: Extracted and processed data
    """
    config = ConfigBuilder().with_anthropic(api_key, model).build()
    extractor = WebExtractor(config)
    return extractor.extract(url)
