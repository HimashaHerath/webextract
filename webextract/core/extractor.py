"""Main data extraction logic combining scraping and LLM processing."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

from ..config import WebExtractConfig, get_default_config
from .confidence_scorer import ConfidenceConfig, ConfidenceScorer
from .exceptions import ConfigurationError, ExtractionError, LLMError, ScrapingError
from .llm_factory import create_llm_client
from .models import ExtractedContent, ExtractionConfig, StructuredData
from .scraper import WebScraper

logger = logging.getLogger(__name__)


class DataExtractor:
    """Main class for extracting structured data from web pages."""

    def __init__(
        self,
        config: Union[WebExtractConfig, ExtractionConfig, None] = None,
        confidence_config: Optional[ConfidenceConfig] = None,
    ):
        """
        Initialize the data extractor with unified configuration.

        Args:
            config: WebExtractConfig (preferred) or ExtractionConfig (deprecated)
            confidence_config: Optional confidence scoring configuration
        """
        # Handle legacy ExtractionConfig for backward compatibility
        if isinstance(config, ExtractionConfig):
            logger.warning("ExtractionConfig is deprecated. Please use WebExtractConfig instead.")
            config = self._convert_legacy_config(config)

        # Use provided config or get default
        self.config = config or get_default_config()

        # Initialize confidence scorer
        self.confidence_scorer = ConfidenceScorer(confidence_config)

        # Create LLM client based on unified configuration
        try:
            self.llm_client = create_llm_client(self.config)
        except (ConfigurationError, LLMError) as e:
            logger.error(f"Failed to create LLM client: {e}")
            raise e

        self._extraction_cache = {}  # Simple cache for repeated URLs

    def _convert_legacy_config(self, legacy_config: ExtractionConfig) -> WebExtractConfig:
        """Convert legacy ExtractionConfig to WebExtractConfig."""
        # Get default config and update with legacy values
        config = get_default_config()

        # Map legacy fields to new config structure
        if hasattr(legacy_config, "model_name") and legacy_config.model_name:
            config.llm.model_name = legacy_config.model_name

        if hasattr(legacy_config, "max_content_length") and legacy_config.max_content_length:
            config.scraping.max_content_length = legacy_config.max_content_length

        if hasattr(legacy_config, "custom_prompt") and legacy_config.custom_prompt:
            config.llm.custom_prompt = legacy_config.custom_prompt

        return config

    def extract(
        self,
        url: str,
        schema: Optional[Dict[str, str]] = None,
        force_refresh: bool = False,
    ) -> Optional[StructuredData]:
        """
        Extract structured data from a web page.

        Args:
            url: The URL to extract from
            schema: Optional schema defining what to extract
            force_refresh: Skip cache and force new extraction

        Returns:
            StructuredData object or None if extraction fails
        """
        try:
            # Validate URL
            if not self._validate_url(url):
                logger.error(f"Invalid URL format: {url}")
                raise ExtractionError(f"Invalid URL format: {url}")

            # Check cache unless force refresh
            if not force_refresh and url in self._extraction_cache:
                logger.info(f"Returning cached result for: {url}")
                return self._extraction_cache[url]

            # Check model availability
            try:
                if not self.llm_client.is_model_available():
                    logger.error(f"Model {self.config.llm.model_name} is not available")
                    raise LLMError(f"Model {self.config.llm.model_name} is not available")
            except LLMError:
                raise  # Re-raise LLMError as-is
            except Exception as e:
                logger.error(f"Failed to check model availability: {e}")
                raise LLMError(f"Cannot verify model availability: {e}")

            # Extract content
            extracted_content = self._scrape_content(url)
            if not extracted_content:
                raise ScrapingError(f"Failed to scrape content from {url}")

            # Process with LLM
            try:
                structured_info = self._process_with_llm(extracted_content, schema)
            except LLMError:
                raise
            except Exception as e:
                raise LLMError(f"LLM processing failed: {e}")

            # Calculate confidence using improved scorer
            confidence = self.confidence_scorer.calculate_confidence(
                extracted_content, structured_info
            )

            # Create result
            result = StructuredData(
                url=url,
                extracted_at=datetime.now().isoformat(),
                content=extracted_content,
                structured_info=structured_info,
                confidence=confidence,
            )

            # Cache successful results
            if confidence > 0.3:  # Only cache decent results
                self._extraction_cache[url] = result

            logger.info(f"Extraction completed for {url} with confidence: {confidence:.2f}")
            return result

        except (ExtractionError, ScrapingError, LLMError, ConfigurationError) as e:
            logger.error(f"Extraction failed for {url}: {e}")
            return self._create_error_result(url, str(e))
        except Exception as e:
            logger.error(f"Unexpected error during extraction for {url}: {e}")
            return self._create_error_result(url, f"Unexpected error: {e}")

    def extract_batch(
        self,
        urls: List[str],
        schema: Optional[Dict[str, str]] = None,
        max_workers: int = 3,
    ) -> List[Optional[StructuredData]]:
        """
        Extract data from multiple URLs.

        Args:
            urls: List of URLs to extract from
            schema: Optional schema for extraction
            max_workers: Maximum concurrent extractions

        Returns:
            List of StructuredData objects (None for failed extractions)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = [None] * len(urls)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(self.extract, url, schema): i for i, url in enumerate(urls)
            }

            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    logger.error(f"Batch extraction error for index {index}: {e}")
                    results[index] = None

        return results

    def extract_with_custom_schema(
        self, url: str, extraction_schema: Dict[str, str]
    ) -> Optional[StructuredData]:
        """
        Extract data using a custom schema.

        Args:
            url: URL to extract from
            extraction_schema: Dictionary mapping field names to extraction instructions

        Example:
            schema = {
                "price": "Extract the product price",
                "rating": "Extract the average rating",
                "reviews": "Extract number of reviews"
            }
        """
        return self.extract(url, schema=extraction_schema)

    def extract_with_summary(
        self, url: str, max_length: int = 200, force_refresh: bool = False
    ) -> Optional[StructuredData]:
        """Extract content and update summary only.

        This helper delegates to :meth:`extract` and then generates a short
        summary of the main content using the configured LLM client. The
        resulting :class:`StructuredData` object is returned with the summary
        inserted into ``structured_info``.
        """

        result = self.extract(url, force_refresh=force_refresh)

        if result and getattr(result, "content", None):
            try:
                summary = self.llm_client.summarize_content(
                    result.content.main_content, max_length=max_length
                )

                if isinstance(result.structured_info, dict):
                    result.structured_info["summary"] = summary
                elif hasattr(result.structured_info, "summary"):
                    result.structured_info.summary = summary
            except Exception as e:  # pragma: no cover - summary failure shouldn't crash
                logger.error(f"Summary generation failed for {url}: {e}")

        return result

    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception as e:
            logger.error(f"URL validation failed for {url}: {e}")
            return False

    def _scrape_content(self, url: str) -> Optional[ExtractedContent]:
        """Scrape content from URL with error handling."""
        try:
            with WebScraper(self.config) as scraper:
                content = scraper.scrape(url)

                if content and len(content.main_content.strip()) < 50:
                    logger.warning(
                        f"Very short content from {url}: {len(content.main_content)} chars"
                    )

                return content

        except ScrapingError:
            raise
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            raise ScrapingError(f"Web scraping failed for {url}: {e}")

    def _process_with_llm(
        self, content: ExtractedContent, schema: Optional[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """Process content with LLM."""
        try:
            # Prepare content for LLM
            llm_content = self._prepare_content_for_llm(content)

            if schema:
                # Use custom schema
                return self.llm_client.extract_with_schema(llm_content, schema)
            else:
                # Use default extraction
                return self.llm_client.generate_structured_data(
                    content=llm_content, custom_prompt=self.config.llm.custom_prompt
                )

        except LLMError:
            raise
        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            raise LLMError(f"LLM processing failed: {e}")

    def _prepare_content_for_llm(self, content: ExtractedContent) -> str:
        """Prepare content for LLM processing."""
        # Combine different content parts intelligently
        parts = []

        if content.title:
            parts.append(f"TITLE: {content.title}")

        if content.description:
            parts.append(f"DESCRIPTION: {content.description}")

        # Add main content
        parts.append(f"CONTENT: {content.main_content}")

        # Add some metadata if relevant
        if content.metadata.get("og_title"):
            parts.append(f"OG_TITLE: {content.metadata['og_title']}")

        return "\n\n".join(parts)

    def _create_error_result(self, url: str, error_message: str) -> StructuredData:
        """Create an error result for failed extractions."""
        return StructuredData(
            url=url,
            extracted_at=datetime.now().isoformat(),
            content=ExtractedContent(
                title=None,
                description=None,
                main_content=f"Extraction failed: {error_message}",
                links=[],
                metadata={"error": error_message},
            ),
            structured_info={
                "error": error_message,
                "summary": f"Failed to extract content: {error_message}",
                "extraction_error": True,
            },
            confidence=0.0,
        )

    def test_connection(self) -> bool:
        """Test connection to LLM service."""
        try:
            if not self.llm_client.is_model_available():
                model_name = self.config.llm.model_name
                logger.error(f"Model {model_name} is not available")
                print(f"❌ Model '{model_name}' is not available")

                # Try to list available models
                try:
                    models = self.llm_client.client.list()
                    available = [m["name"] for m in models.get("models", [])]
                    if available:
                        print("📋 Available models:")
                        for model in available:
                            print(f"   - {model}")
                    else:
                        print("❌ No models found. Please pull a model first:")
                        print("   ollama pull llama3.2")
                except Exception:
                    print("❌ Could not connect to Ollama. Is it running?")
                    print("   Start with: ollama serve")

                return False

            model_name = self.config.llm.model_name
            print(f"✅ Model '{model_name}' is available")

            # Test with a simple extraction
            test_result = self.llm_client.generate_structured_data(
                "This is a test.", custom_prompt="Extract a summary"
            )

            if test_result:
                print("✅ LLM extraction test successful")
                return True
            else:
                print("❌ LLM extraction test failed")
                return False

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            print(f"❌ Connection test failed: {e}")
            return False

    def clear_cache(self):
        """Clear the extraction cache."""
        self._extraction_cache.clear()
        logger.info("Extraction cache cleared")
