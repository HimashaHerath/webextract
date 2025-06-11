"""LLM Web Scraper package."""

from .extractor import DataExtractor
from .models import StructuredData, ExtractedContent, ExtractionConfig
from .scraper import WebScraper
from .llm_client import OllamaClient

__version__ = "1.0.0"
__all__ = [
    "DataExtractor",
    "StructuredData", 
    "ExtractedContent",
    "ExtractionConfig",
    "WebScraper",
    "OllamaClient"
] 