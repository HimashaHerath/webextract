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

    def generate_structured_data(self, content: str, custom_prompt: str = None) -> Dict[str, Any]:
        """Generate structured data from content using LLM with retry logic."""

        prompt = custom_prompt or self._get_default_prompt()

        full_prompt = f"""
Content to analyze:
{content[:self.max_content_length]}

{prompt}

IMPORTANT: Respond with ONLY the JSON object. Do not include any explanatory text, markdown formatting, or code blocks. Start your response with {{ and end with }}.
"""

        if len(content) > self.max_content_length:
            logger.info(
                f"Content truncated from {len(content)} to {self.max_content_length} characters"
            )

        for attempt in range(settings.LLM_RETRY_ATTEMPTS):
            try:
                logger.info(f"LLM generation attempt {attempt + 1}/{settings.LLM_RETRY_ATTEMPTS}")

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
                logger.debug(f"LLM response preview: {response_text[:200]}...")

                structured_data = self._extract_json_from_response(response_text)
                if structured_data:
                    # Validate the structure has expected fields
                    if self._validate_structured_data(structured_data):
                        logger.info(f"Successfully extracted valid structured data on attempt {attempt + 1}")
                        return structured_data
                    else:
                        logger.warning(f"Invalid structured data format (attempt {attempt + 1})")
                        if attempt < settings.LLM_RETRY_ATTEMPTS - 1:
                            continue

                # If JSON extraction fails, try to fix common issues
                fixed_response = self._fix_json_response(response_text)
                if fixed_response and self._validate_structured_data(fixed_response):
                    logger.info(f"Successfully fixed and validated JSON on attempt {attempt + 1}")
                    return fixed_response

                # Last resort - return a structured error response
                if attempt == settings.LLM_RETRY_ATTEMPTS - 1:
                    logger.warning("All JSON parsing attempts failed, creating fallback response")
                    return self._create_fallback_response(response_text)

            except Exception as e:
                logger.error(f"LLM generation failed (attempt {attempt + 1}): {e}")
                if attempt == settings.LLM_RETRY_ATTEMPTS - 1:
                    return self._create_fallback_response(f"Error: {str(e)}")

        return self._create_fallback_response("All LLM attempts failed")

    def _create_fallback_response(self, error_info: str) -> Dict[str, Any]:
        """Create a fallback response when JSON parsing fails."""
        # Try to extract some basic information from the error_info if it looks like content
        summary = error_info
        if len(error_info) > 200 and not error_info.startswith("Error:"):
            # If it's actual content, use first 200 chars as summary
            summary = error_info[:200] + "..."
        elif error_info.startswith("Error:"):
            summary = "Failed to analyze content due to processing error"
        
        return {
            "summary": summary,
            "topics": [],
            "entities": {
                "people": [],
                "organizations": [],
                "locations": []
            },
            "category": "unknown",
            "sentiment": "neutral",
            "key_points": [],
            "important_dates": [],
            "numbers": [],
            "error": error_info if error_info.startswith("Error:") else None
        }

    def _get_default_prompt(self) -> str:
        """Get the default prompt for content analysis."""
        return """
You are a JSON extraction assistant. Analyze the web content and return ONLY valid JSON.

Extract these fields and return as JSON:
{
  "summary": "Brief summary of the content (required)",
  "topics": ["topic1", "topic2"],
  "category": "content category (e.g., technology, news, tutorial)",
  "sentiment": "positive, negative, or neutral",
  "entities": {
    "people": ["person1", "person2"],
    "organizations": ["org1", "org2"],
    "locations": ["place1", "place2"]
  },
  "important_dates": ["date1", "date2"],
  "numbers": ["stat1", "stat2"],
  "key_points": ["point1", "point2"]
}

Rules:
- Return ONLY the JSON object, no other text
- All fields must be present, use empty arrays/objects if no data
- Use double quotes for all strings
- Summary field is required and cannot be empty"""

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response with improved parsing."""
        try:
            # Clean the response
            cleaned_text = response_text.strip()

            # Remove markdown formatting if present
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            cleaned_text = cleaned_text.strip()

            # Remove any text before the first { and after the last }
            start_idx = cleaned_text.find("{")
            end_idx = cleaned_text.rfind("}") + 1

            if start_idx != -1 and end_idx != 0 and end_idx > start_idx:
                json_str = cleaned_text[start_idx:end_idx]
                
                # Try to parse the JSON
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Try fixing common issues first
                    fixed_json = self._fix_json_string(json_str)
                    if fixed_json:
                        return json.loads(fixed_json)
                    raise

            # If no JSON braces found, try to parse the entire response
            return json.loads(cleaned_text)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"Response text: {response_text[:300]}...")
            return None

    def _validate_structured_data(self, data: Dict[str, Any]) -> bool:
        """Validate that structured data has expected fields."""
        if not isinstance(data, dict):
            logger.warning("Structured data is not a dictionary")
            return False
            
        required_fields = ["summary"]
        recommended_fields = ["topics", "category", "sentiment"]

        # Check if it has at least a summary and it's not empty
        if not any(field in data and data[field] for field in required_fields):
            logger.warning("Structured data missing required fields or required fields are empty")
            return False

        # Check if it has some recommended fields
        if not any(field in data for field in recommended_fields):
            logger.warning("Structured data missing recommended fields")
            # Still valid, just warn

        # Ensure all expected fields exist with proper types
        self._ensure_field_types(data)

        return True

    def _ensure_field_types(self, data: Dict[str, Any]) -> None:
        """Ensure all fields have the correct types."""
        # Ensure lists exist and are actually lists
        list_fields = ["topics", "key_points", "important_dates", "numbers"]
        for field in list_fields:
            if field not in data:
                data[field] = []
            elif not isinstance(data[field], list):
                # Convert to list if it's a string or other type
                if isinstance(data[field], str):
                    data[field] = [data[field]] if data[field] else []
                else:
                    data[field] = []

        # Ensure entities is a dict
        if "entities" not in data:
            data["entities"] = {}
        elif not isinstance(data["entities"], dict):
            data["entities"] = {}

        # Ensure string fields are strings
        string_fields = ["summary", "category", "sentiment"]
        for field in string_fields:
            if field not in data:
                data[field] = ""
            elif not isinstance(data[field], str):
                data[field] = str(data[field]) if data[field] is not None else ""

    def _fix_json_string(self, json_str: str) -> Optional[str]:
        """Apply common JSON fixes to a JSON string."""
        try:
            import re
            
            fixed = json_str
            
            # Fix 1: Remove trailing commas before } and ]
            fixed = re.sub(r',(\s*[}\]])', r'\1', fixed)
            
            # Fix 2: Fix single quotes to double quotes (but be careful not to break contractions)
            # This is a simple approach - replace single quotes that are likely JSON delimiters
            fixed = re.sub(r"'(\w+)':", r'"\1":', fixed)  # Keys
            fixed = re.sub(r":\s*'([^']*)'", r': "\1"', fixed)  # String values
            fixed = re.sub(r'\[\s*\'([^\']*)\'\s*\]', r'["\1"]', fixed)  # Arrays with single quotes
            
            # Fix 3: Escape unescaped quotes in strings
            # This is tricky, so we'll do a simple fix for common cases
            fixed = re.sub(r'(?<!\\)"(?=[^,}\]:]*[,}\]:]*)', r'\\"', fixed)
            
            # Fix 4: Fix common control characters
            fixed = fixed.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            
            # Fix 5: Remove any non-printable characters except necessary whitespace
            fixed = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', fixed)
            
            return fixed
            
        except Exception as e:
            logger.debug(f"Error in _fix_json_string: {e}")
            return None

    def _fix_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Attempt to fix common JSON formatting issues."""
        try:
            # Apply fixes and try parsing again
            fixed_text = self._fix_json_string(response_text)
            if fixed_text:
                return self._extract_json_from_response(fixed_text)
            return None

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
