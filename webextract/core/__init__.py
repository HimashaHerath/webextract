"""Core functionality for WebExtract."""

from .extractor import DataExtractor
from .llm_client import OllamaClient
from .models import ExtractedContent, ExtractionConfig, StructuredData
from .scraper import WebScraper

__all__ = [
    "DataExtractor",
    "WebScraper",
    "OllamaClient",
    "StructuredData",
    "ExtractedContent",
    "ExtractionConfig",
]
