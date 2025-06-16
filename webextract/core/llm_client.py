"""Base LLM client and Ollama implementation for processing extracted content."""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..config.settings import settings
from .exceptions import LLMError

try:
    import ollama
except ImportError:
    ollama = None

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, model_name: str):
        """Initialize the base LLM client with model name."""
        self.model_name = model_name
        self.max_content_length = settings.MAX_CONTENT_LENGTH

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

    def _get_improved_prompt(self) -> str:
        """Get improved default prompt for better JSON generation."""
        return """Extract the following information from the content:

{
  "summary": "A clear, concise summary of the main points (required, 2-3 sentences)",
  "topics": ["array of main topics or themes discussed"],
  "category": "primary category (technology/business/news/education/"
              "entertainment/other)",
  "sentiment": "overall tone (positive/negative/neutral)",
  "entities": {
    "people": ["array of person names mentioned"],
    "organizations": ["array of organization/company names"],
    "locations": ["array of locations/places mentioned"]
  },
  "key_facts": ["array of important facts or claims"],
  "important_dates": ["array of dates mentioned with context"],
  "statistics": ["array of numbers, percentages, or metrics mentioned"]
}

Return this EXACT structure with these EXACT field names.
ALL fields must be present. Use empty arrays [] if no data found."""

    def _create_schema_prompt(self, schema: Dict[str, Any]) -> str:
        """Create a prompt from a provided schema."""
        return f"""Extract information according to this schema:

{json.dumps(schema, indent=2)}

Return data matching this EXACT structure with ALL fields present.
Use appropriate empty values (empty strings, empty arrays) for missing data."""

    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response with multiple strategies."""
        if not response_text:
            return None

        # Strategy 1: Direct parsing
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract JSON from text
        json_pattern = r"\{[^{}]*\{[^{}]*\}[^{}]*\}|\{[^{}]*\}"
        json_match = re.search(json_pattern, response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Strategy 3: Clean and parse
        cleaned = self._clean_json_text(response_text)
        if cleaned:
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error after cleaning: {e}")

        return None

    def _clean_json_text(self, text: str) -> Optional[str]:
        """Clean potential JSON text with safer approach."""
        # Remove markdown code blocks
        text = re.sub(r"```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```", "", text)
        text = text.strip()

        # Find JSON boundaries
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            return None

        json_text = text[start : end + 1]

        # Safe replacements
        # Fix common LLM mistakes
        json_text = re.sub(r",\s*}", "}", json_text)  # Remove trailing commas
        json_text = re.sub(r",\s*]", "]", json_text)  # Remove trailing commas in arrays

        # Fix newlines and tabs in strings (but not between JSON elements)
        def fix_string_newlines(match):
            string_content = match.group(1)
            string_content = (
                string_content.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            )
            return f'"{string_content}"'

        # This regex matches strings but avoids the complexities of escaped quotes
        string_pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
        json_text = re.sub(string_pattern, fix_string_newlines, json_text)

        return json_text

    def _validate_extraction_result(
        self,
        result: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate extraction result against schema or default requirements."""
        if not isinstance(result, dict):
            return False

        if schema:
            return self._validate_against_schema(result, schema)

        # Default validation
        required_fields = ["summary"]
        if not all(field in result and result[field] for field in required_fields):
            return False

        # Check for expected structure
        expected_structure = {
            "summary": str,
            "topics": list,
            "category": str,
            "sentiment": str,
            "entities": dict,
            "key_facts": list,
            "important_dates": list,
            "statistics": list,
        }

        for field, expected_type in expected_structure.items():
            if field in result:
                if not isinstance(result[field], expected_type):
                    # Try to fix common type mismatches
                    if expected_type == list and isinstance(result[field], str):
                        result[field] = [result[field]] if result[field] else []
                    elif expected_type == str and result[field] is None:
                        result[field] = ""
                    else:
                        logger.warning(f"Field {field} has wrong type: {type(result[field])}")

        return True

    def _validate_against_schema(self, result: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate result against provided schema."""
        for key, value in schema.items():
            if key not in result:
                logger.warning(f"Missing required field: {key}")
                return False

            # Basic type checking based on schema value
            if isinstance(value, str):
                if not isinstance(result[key], str):
                    result[key] = str(result[key]) if result[key] is not None else ""
            elif isinstance(value, list):
                if not isinstance(result[key], list):
                    result[key] = [result[key]] if result[key] else []
            elif isinstance(value, dict):
                if not isinstance(result[key], dict):
                    result[key] = {}

        return True

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
        super().__init__(model_name or settings.DEFAULT_MODEL)
        self.base_url = base_url or settings.OLLAMA_BASE_URL

        if ollama is None:
            raise LLMError("Ollama package not installed. Install with: pip install ollama")

        try:
            self.client = ollama.Client(host=self.base_url)
        except Exception as e:
            raise LLMError(f"Failed to initialize Ollama client: {e}")

    def is_model_available(self) -> bool:
        """Check if the specified model is available."""
        try:
            models = self.client.list()
            available_models = [model["name"] for model in models["models"]]
            return self.model_name in available_models
        except Exception as e:
            logger.error(f"Failed to check Ollama model availability: {e}")
            return False

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
                prompt = custom_prompt or self._get_improved_prompt()

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

            for attempt in range(settings.LLM_RETRY_ATTEMPTS):
                try:
                    retry_count = settings.LLM_RETRY_ATTEMPTS
                    logger.info(f"Ollama generation attempt {attempt + 1}/{retry_count}")

                    response = self.client.generate(
                        model=self.model_name,
                        prompt=full_prompt,
                        options={
                            "temperature": settings.LLM_TEMPERATURE,
                            "num_predict": settings.MAX_TOKENS,
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
                        raise LLMError(f"Cannot connect to Ollama server at {self.base_url}: {e}")
                    if attempt == settings.LLM_RETRY_ATTEMPTS - 1:
                        retry_count = settings.LLM_RETRY_ATTEMPTS
                        raise LLMError(
                            f"Ollama processing failed after {retry_count} attempts: {e}"
                        )

            # Fallback if all attempts failed but no exception was raised
            return self._create_safe_fallback(content[:200])

        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Unexpected error in Ollama processing: {e}")

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
            if len(content) > max_length:
                preview = content[: max_length - 3] + "..."
            else:
                preview = content
            return preview
