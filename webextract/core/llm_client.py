"""Base LLM client and Ollama implementation for processing extracted content."""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..config import get_default_config
from .exceptions import AuthenticationError, ErrorHandler, LLMError, ModelNotAvailableError
from .json_parser import JSONParser, JSONValidator, StructuredPromptBuilder

try:
    import ollama
except ImportError:
    ollama = None

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, model_name: str, config=None):
        """Initialize the base LLM client with model name."""
        self.model_name = model_name
        self.config = config or get_default_config()
        self.max_content_length = self.config.scraping.max_content_length
        self.json_parser = JSONParser()
        self.prompt_builder = StructuredPromptBuilder()

    @abstractmethod
    def is_model_available(self) -> bool:
        """Check if the specified model is available."""
        pass

    @abstractmethod
    def generate_structured_data(
        self,
        content: str,
        custom_prompt: str = None,
        schema: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Generate structured data from content."""
        pass

    @abstractmethod
    def summarize_content(self, content: str, max_length: int = 200) -> str:
        """Generate a brief summary of the content."""
        pass

    def extract_with_schema(self, content: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data according to a specific schema."""
        return self.generate_structured_data(content, schema=schema)

    def _get_improved_prompt(self, schema: Optional[Dict[str, Any]] = None) -> str:
        """Get improved prompt for reliable JSON generation."""
        return self.prompt_builder.create_extraction_prompt(schema=schema)

    def _create_schema_prompt(self, schema: Dict[str, Any]) -> str:
        """Create a prompt from a provided schema."""
        return self.prompt_builder.create_extraction_prompt(schema=schema)

    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response using robust parser."""
        return self.json_parser.parse_response(response_text)

    def _validate_extraction_result(
        self,
        result: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate extraction result using robust validator."""
        is_valid, fixed_result = JSONValidator.validate_and_fix(result, schema)

        # Update result in-place with fixes
        result.clear()
        result.update(fixed_result)

        return is_valid

    def _create_safe_fallback(self, content_preview: str) -> Dict[str, Any]:
        """Create a safe fallback response with proper structure."""
        return {
            "summary": f"Content extraction failed. Preview: {content_preview}...",
            "topics": [],
            "category": "unknown",
            "sentiment": "neutral",
            "entities": {"people": [], "organizations": [], "locations": []},
            "key_facts": [],
            "important_dates": [],
            "statistics": [],
            "extraction_error": True,
        }


class OllamaClient(BaseLLMClient):
    """Client for interacting with local Ollama LLM."""

    def __init__(self, model_name: str = None, base_url: str = None):
        """Initialize the Ollama client with model name and base URL."""
        config = get_default_config()
        super().__init__(model_name or config.llm.model_name, config)
        self.base_url = base_url or config.llm.base_url

        if ollama is None:
            raise LLMError(
                "Ollama package not installed",
                provider="ollama",
                suggestions=["Install with: pip install ollama"],
            )

        try:
            self.client = ollama.Client(host=self.base_url)
        except Exception as e:
            raise LLMError(
                "Failed to initialize Ollama client",
                provider="ollama",
                context={"base_url": self.base_url},
                original_error=e,
            )

    def is_model_available(self) -> bool:
        """Check if the specified model is available."""
        try:
            models = self.client.list()
            available_models = [model["name"] for model in models["models"]]
            logger.debug(f"Looking for model: '{self.model_name}'")
            logger.debug(f"Available models: {available_models}")

            # Check exact match first
            if self.model_name in available_models:
                return True

            # If no exact match, check if any available model starts with our model name
            # This handles cases like "llama3" matching "llama3:latest"
            for available_model in available_models:
                if available_model.startswith(self.model_name + ":"):
                    logger.debug(f"Found partial match: {available_model} for {self.model_name}")
                    return True

            return False
        except Exception as e:
            logger.error(f"Failed to check Ollama model availability: {e}")
            raise ModelNotAvailableError(
                "Cannot check model availability",
                requested_model=self.model_name,
                provider="ollama",
                context={"base_url": self.base_url},
                original_error=e,
            )

    def generate_structured_data(
        self,
        content: str,
        custom_prompt: str = None,
        schema: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Generate structured data from content using Ollama with improved JSON handling."""
        try:
            # Use schema if provided, otherwise use default
            if schema:
                prompt = self._create_schema_prompt(schema)
            else:
                prompt = custom_prompt or self._get_improved_prompt(schema)

            # Truncate content if needed
            truncated_content = content[: self.max_content_length]
            if len(content) > self.max_content_length:
                logger.info(
                    f"Content truncated from {len(content)} to "
                    f"{self.max_content_length} characters"
                )

            full_prompt = f"""Analyze the following content and return ONLY a valid JSON object.

CONTENT TO ANALYZE:
{truncated_content}

EXTRACTION INSTRUCTIONS:
{prompt}

CRITICAL RULES:
1. Return ONLY the JSON object - no explanatory text before or after
2. Start with {{ and end with }}
3. Use double quotes for ALL strings (no single quotes)
4. Ensure all required fields are present
5. Use empty arrays [] for missing list data
6. Use empty strings "" for missing text data
7. Escape any quotes inside string values with \\"""

            for attempt in range(self.config.llm.retry_attempts):
                try:
                    retry_count = self.config.llm.retry_attempts
                    logger.info(f"Ollama generation attempt {attempt + 1}/{retry_count}")
                    logger.debug(f"About to generate with model: '{self.model_name}'")

                    response = self.client.generate(
                        model=self.model_name,
                        prompt=full_prompt,
                        options={
                            "temperature": self.config.llm.temperature,
                            "num_predict": self.config.llm.max_tokens,
                            "format": "json",  # Request JSON format if model supports it
                        },
                    )

                    response_text = response.get("response", "").strip()
                    logger.debug(f"Ollama response length: {len(response_text)} characters")

                    # Try to parse the response
                    result = self._parse_json_response(response_text)

                    if result and self._validate_extraction_result(result, schema):
                        logger.info(
                            f"Successfully extracted valid structured data on "
                            f"attempt {attempt + 1}"
                        )
                        return result

                    # If validation failed, try once more with stricter prompt
                    if attempt == 0:
                        logger.warning(
                            "First attempt failed validation, trying with stricter prompt"
                        )
                        continue

                except Exception as e:
                    logger.error(f"Ollama generation failed (attempt {attempt + 1}): {e}")
                    if "connection" in str(e).lower():
                        raise LLMError(
                            "Cannot connect to Ollama server",
                            provider="ollama",
                            context={"base_url": self.base_url, "model_name": self.model_name},
                            original_error=e,
                        )
                    if attempt == self.config.llm.retry_attempts - 1:
                        retry_count = self.config.llm.retry_attempts
                        raise LLMError(
                            f"Ollama processing failed after {retry_count} attempts",
                            provider="ollama",
                            context={"model_name": self.model_name, "attempts": retry_count},
                            original_error=e,
                        )

            # Fallback if all attempts failed but no exception was raised
            logger.error("All LLM generation attempts failed, returning fallback")
            return self._create_safe_fallback(content[:200])

        except LLMError:
            raise
        except Exception as e:
            raise ErrorHandler.handle_with_context(
                "generate_structured_data",
                {"model_name": self.model_name, "provider": "ollama"},
                e,
                ["Check Ollama server status", "Verify model availability"],
            )

    def summarize_content(self, content: str, max_length: int = 200) -> str:
        """Generate a brief summary of the content using Ollama."""
        prompt = (
            f"Provide a clear, concise summary of this content in no more than "
            f"{max_length} characters. Focus on the main points and key takeaways.\n\n"
            f"Content: {content[:2000]}\n\nSummary (max {max_length} chars):"
        )

        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": 0.3,
                    "num_predict": max_length // 3,
                },
            )

            summary = response["response"].strip()

            # Ensure summary doesn't exceed max length
            if len(summary) > max_length:
                summary = summary[: max_length - 3].rsplit(" ", 1)[0] + "..."

            return summary

        except Exception as e:
            logger.error(f"Failed to generate Ollama summary: {e}")
            # For summarization, provide fallback instead of raising
            if len(content) > max_length:
                preview = content[: max_length - 3] + "..."
            else:
                preview = content
            return preview
