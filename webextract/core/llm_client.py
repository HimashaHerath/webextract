"""Ollama LLM client for processing extracted content."""

import json
import logging
from typing import Any, Dict, Optional

import ollama

from ..config.settings import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with local Ollama LLM."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.DEFAULT_MODEL
        self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        self.max_content_length = settings.MAX_CONTENT_LENGTH

    def is_model_available(self) -> bool:
        """Check if the specified model is available."""
        try:
            models = self.client.list()
            available_models = [model["name"] for model in models["models"]]
            return self.model_name in available_models
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False

    def generate_structured_data(
        self, content: str, custom_prompt: str = None
    ) -> Dict[str, Any]:
        """Generate structured data from content using LLM with retry logic."""

        prompt = custom_prompt or self._get_default_prompt()

        full_prompt = f"""
Content to analyze:
{content[:self.max_content_length]}

{prompt}

Please respond with valid JSON only.
"""

        if len(content) > self.max_content_length:
            logger.info(
                f"Content truncated from {len(content)} to {self.max_content_length} characters"
            )

        for attempt in range(settings.LLM_RETRY_ATTEMPTS):
            try:
                logger.info(
                    f"LLM generation attempt {attempt + 1}/{settings.LLM_RETRY_ATTEMPTS}"
                )

                response = self.client.generate(
                    model=self.model_name,
                    prompt=full_prompt,
                    options={
                        "temperature": settings.LLM_TEMPERATURE,
                        "num_predict": settings.MAX_TOKENS,
                    },
                )

                response_text = response.get("response", "").strip()
                logger.debug(f"LLM response length: {len(response_text)} characters")

                structured_data = self._extract_json_from_response(response_text)
                if structured_data:
                    # Validate the structure has expected fields
                    if self._validate_structured_data(structured_data):
                        return structured_data
                    else:
                        logger.warning(
                            f"Invalid structured data format (attempt {attempt + 1})"
                        )
                        if attempt < settings.LLM_RETRY_ATTEMPTS - 1:
                            continue

                # If JSON extraction fails, try to fix common issues
                fixed_response = self._fix_json_response(response_text)
                if fixed_response:
                    return fixed_response

                # Last resort - return a structured error response
                if attempt == settings.LLM_RETRY_ATTEMPTS - 1:
                    return {
                        "summary": (
                            response_text[:500] + "..."
                            if len(response_text) > 500
                            else response_text
                        ),
                        "raw_response": response_text,
                        "error": "Failed to parse JSON response",
                        "topics": [],
                        "entities": {},
                        "category": "unknown",
                        "sentiment": "neutral",
                        "key_points": [],
                    }

            except Exception as e:
                logger.error(f"LLM generation failed (attempt {attempt + 1}): {e}")
                if attempt == settings.LLM_RETRY_ATTEMPTS - 1:
                    return {
                        "error": str(e),
                        "summary": "Failed to analyze content",
                        "topics": [],
                        "entities": {},
                        "category": "error",
                        "sentiment": "neutral",
                        "key_points": [],
                    }

        return {"error": "All LLM attempts failed"}

    def _get_default_prompt(self) -> str:
        """Get the default prompt for content analysis."""
        return """
You are a helpful assistant that extracts structured information from web content.
Analyze the following content and extract key information in a structured format.

Please extract:
1. Main topics or themes
2. Key entities (people, organizations, locations, etc.)
3. Important dates or numbers
4. Summary of the content
5. Category or type of content
6. Sentiment (positive, negative, neutral)

Return the information as a JSON object with these fields:
- topics: list of main topics
- entities: dict with entity types as keys and lists of entities as values
- important_dates: list of important dates mentioned
- numbers: list of important numbers or statistics
- summary: brief summary of the content
- category: type/category of the content
- sentiment: overall sentiment
- key_points: list of key takeaways
"""

    def _extract_json_from_response(
        self, response_text: str
    ) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response with improved parsing."""
        try:
            # Clean the response
            cleaned_text = response_text.strip()

            # Remove markdown formatting if present
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            cleaned_text = cleaned_text.strip()

            # Try to find JSON in the response
            start_idx = cleaned_text.find("{")
            end_idx = cleaned_text.rfind("}") + 1

            if start_idx != -1 and end_idx != 0 and end_idx > start_idx:
                json_str = cleaned_text[start_idx:end_idx]
                return json.loads(json_str)

            # If no JSON braces found, try to parse the entire response
            return json.loads(cleaned_text)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"Response text: {response_text[:200]}...")
            return None

    def _validate_structured_data(self, data: Dict[str, Any]) -> bool:
        """Validate that structured data has expected fields."""
        required_fields = ["summary"]
        recommended_fields = ["topics", "category", "sentiment"]

        # Check if it has at least a summary
        if not any(field in data for field in required_fields):
            logger.warning("Structured data missing required fields")
            return False

        # Check if it has some recommended fields
        if not any(field in data for field in recommended_fields):
            logger.warning("Structured data missing recommended fields")
            # Still valid, just warn

        return True

    def _fix_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Attempt to fix common JSON formatting issues."""
        try:
            # Common fixes
            fixes = [
                # Remove trailing commas
                lambda x: x.replace(",}", "}").replace(",]", "]"),
                # Fix single quotes to double quotes
                lambda x: x.replace("'", '"'),
                # Remove newlines in strings
                lambda x: x.replace("\n", "\\n"),
            ]

            fixed_text = response_text
            for fix in fixes:
                fixed_text = fix(fixed_text)

            return self._extract_json_from_response(fixed_text)

        except Exception as e:
            logger.warning(f"Failed to fix JSON response: {e}")
            return None

    def summarize_content(self, content: str, max_length: int = 200) -> str:
        """Generate a brief summary of the content."""
        prompt = f"""
Please provide a concise summary of the following content in no more than {max_length} characters:

{content}

Summary:
"""

        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": 0.3,
                    "num_predict": max_length // 3,  # Rough token estimate
                },
            )

            summary = response["response"].strip()

            # Ensure summary doesn't exceed max length
            if len(summary) > max_length:
                summary = summary[: max_length - 3] + "..."

            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return f"Summary generation failed: {str(e)}"
