"""Core functionality for WebExtract."""

from .extractor import DataExtractor
from .scraper import WebScraper  
from .llm_client import OllamaClient
from .models import StructuredData, ExtractedContent, ExtractionConfig

__all__ = [
    "DataExtractor",
    "WebScraper", 
    "OllamaClient",
    "StructuredData",
    "ExtractedContent", 
    "ExtractionConfig"
] 