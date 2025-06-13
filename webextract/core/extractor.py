"""Main data extraction logic combining scraping and LLM processing."""

import logging
from datetime import datetime
from typing import Optional

from .llm_client import OllamaClient
from .models import ExtractedContent, ExtractionConfig, StructuredData
from .scraper import WebScraper

logger = logging.getLogger(__name__)


class DataExtractor:
    """Main class for extracting structured data from web pages."""

    def __init__(self, config: ExtractionConfig = None):
        self.config = config or ExtractionConfig()
        self.llm_client = OllamaClient(model_name=self.config.model_name)

    def extract(self, url: str) -> Optional[StructuredData]:
        """Extract structured data from a web page with comprehensive error handling."""
        import time

        start_time = time.time()

        logger.info(f"Starting extraction for: {url}")

        try:
            from urllib.parse import urlparse

            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.error(f"Invalid URL format: {url}")
                return None

            if not self.llm_client.is_model_available():
                logger.error(f"Model {self.config.model_name} is not available")
                return None

            scrape_start = time.time()
            with WebScraper() as scraper:
                extracted_content = scraper.scrape(url)
            scrape_time = time.time() - scrape_start

            if not extracted_content:
                logger.error(f"Failed to scrape content from: {url}")
                return None

            logger.info(
                f"Successfully scraped content: {len(extracted_content.main_content)} characters in {scrape_time:.2f}s"
            )

            if len(extracted_content.main_content.strip()) < 50:
                logger.warning(f"Very short content ({len(extracted_content.main_content)} chars) from {url}")

            llm_start = time.time()
            try:
                structured_info = self.llm_client.generate_structured_data(
                    content=extracted_content.main_content, custom_prompt=self.config.custom_prompt
                )
                llm_time = time.time() - llm_start
                logger.info(f"LLM processing completed in {llm_time:.2f}s")

            except Exception as e:
                logger.error(f"LLM processing failed: {e}")
                structured_info = {
                    "error": f"LLM processing failed: {str(e)}",
                    "summary": (
                        extracted_content.main_content[:200] + "..."
                        if len(extracted_content.main_content) > 200
                        else extracted_content.main_content
                    ),
                    "topics": [],
                    "entities": {},
                    "category": "unknown",
                    "sentiment": "neutral",
                    "key_points": [],
                }

            confidence = self._calculate_confidence(extracted_content, structured_info)

            total_time = time.time() - start_time
            result = StructuredData(
                url=url,
                extracted_at=datetime.now().isoformat(),
                content=extracted_content,
                structured_info=structured_info,
                confidence=confidence,
            )

            logger.info(f"Extraction completed in {total_time:.2f}s with confidence: {confidence:.2f}")
            return result

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Critical error during extraction of {url} after {total_time:.2f}s: {e}")

            try:
                if "extracted_content" in locals() and extracted_content:
                    return StructuredData(
                        url=url,
                        extracted_at=datetime.now().isoformat(),
                        content=extracted_content,
                        structured_info={
                            "error": f"Partial extraction due to error: {str(e)}",
                            "summary": "Extraction failed during processing",
                            "topics": [],
                            "entities": {},
                            "category": "error",
                            "sentiment": "neutral",
                            "key_points": [],
                        },
                        confidence=0.1,
                    )
            except Exception as nested_e:
                logger.error(f"Failed to create partial result: {nested_e}")

            return None

    def extract_with_summary(self, url: str, summary_length: int = 200) -> Optional[StructuredData]:
        """Extract data and add a brief summary."""
        result = self.extract(url)

        if result:
            try:
                summary = self.llm_client.summarize_content(result.content.main_content, max_length=summary_length)
                result.structured_info["brief_summary"] = summary
            except Exception as e:
                logger.warning(f"Failed to generate summary: {e}")

        return result

    def _calculate_confidence(self, content: ExtractedContent, structured_info: dict) -> float:
        """Calculate a confidence score for the extraction."""
        score = 0.0

        score += 0.3

        if content.title:
            score += 0.1

        if content.description:
            score += 0.1

        if len(content.main_content) > 100:
            score += 0.2

        if content.links:
            score += 0.1

        if isinstance(structured_info, dict) and not structured_info.get("error"):
            score += 0.2

            expected_fields = ["summary", "topics", "entities", "category"]
            found_fields = sum(1 for field in expected_fields if field in structured_info)
            score += (found_fields / len(expected_fields)) * 0.1

        return min(score, 1.0)

    def test_connection(self) -> bool:
        """Test connection to Ollama and model availability."""
        try:
            if not self.llm_client.is_model_available():
                logger.error(f"Model {self.config.model_name} is not available")
                print(f"Model '{self.config.model_name}' is not available")
                print("Available models:")
                try:
                    models = self.llm_client.client.list()
                    for model in models["models"]:
                        print(f"  - {model['name']}")
                except:
                    print("  Could not list available models")
                return False

            print(f"Model '{self.config.model_name}' is available")
            return True

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            print(f"Failed to connect to Ollama: {e}")
            return False
