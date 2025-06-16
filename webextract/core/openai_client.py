"""OpenAI LLM client for processing extracted content."""

import json
import logging
from typing import Any, Dict, Optional

from .exceptions import AuthenticationError, LLMError, ModelNotAvailableError
from .llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """Client for interacting with OpenAI GPT models."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", base_url: str = None):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self._client = None
        self._setup_client()

    def _setup_client(self):
        """Setup OpenAI client."""
        try:
            import openai
            self._client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            raise LLMError(
                "OpenAI package not installed. Install with: pip install openai"
            )
        except Exception as e:
            raise AuthenticationError(f"Failed to setup OpenAI client: {e}")

    def is_model_available(self) -> bool:
        """Check if the specified model is available."""
        try:
            # Try to list models to verify API key and model availability
            models = self._client.models.list()
            available_models = [model.id for model in models.data]
            return self.model_name in available_models
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False

    def generate_structured_data(
        self, content: str, custom_prompt: str = None, schema: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate structured data from content using OpenAI."""
        try:
            # Use schema if provided, otherwise use default
            if schema:
                prompt = self._create_schema_prompt(schema)
            else:
                prompt = custom_prompt or self._get_improved_prompt()

            # Truncate content if needed
            truncated_content = content[:self.max_content_length]
            if len(content) > self.max_content_length:
                logger.info(
                    f"Content truncated from {len(content)} to {self.max_content_length} characters"
                )

            system_message = """You are an expert content analyzer. Extract structured information from the provided content and return it as valid JSON. Follow the instructions exactly and return only the JSON object."""

            user_message = f"""Analyze the following content and return ONLY a valid JSON object.

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

            for attempt in range(3):  # OpenAI is more reliable, fewer retries needed
                try:
                    logger.info(f"OpenAI generation attempt {attempt + 1}/3")
                    
                    response = self._client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_message}
                        ],
                        temperature=0.1,
                        max_tokens=2000,
                        response_format={"type": "json_object"}  # Force JSON output
                    )

                    response_text = response.choices[0].message.content.strip()
                    logger.debug(f"OpenAI response length: {len(response_text)} characters")

                    # Parse the response
                    result = self._parse_json_response(response_text)

                    if result and self._validate_extraction_result(result, schema):
                        logger.info(f"Successfully extracted valid structured data on attempt {attempt + 1}")
                        return result

                except Exception as e:
                    logger.error(f"OpenAI generation failed (attempt {attempt + 1}): {e}")
                    if "rate_limit" in str(e).lower():
                        raise LLMError(f"OpenAI rate limit exceeded: {e}")
                    elif "authentication" in str(e).lower():
                        raise AuthenticationError(f"OpenAI authentication failed: {e}")
                    elif "model" in str(e).lower() and "not found" in str(e).lower():
                        raise ModelNotAvailableError(f"OpenAI model {self.model_name} not available: {e}")
                    
                    if attempt == 2:  # Last attempt
                        raise LLMError(f"OpenAI processing failed after 3 attempts: {e}")

            return self._create_safe_fallback(content[:200])

        except (AuthenticationError, ModelNotAvailableError, LLMError):
            raise
        except Exception as e:
            raise LLMError(f"Unexpected error in OpenAI processing: {e}")

    def summarize_content(self, content: str, max_length: int = 200) -> str:
        """Generate a brief summary using OpenAI."""
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a content summarizer. Provide clear, concise summaries."
                    },
                    {
                        "role": "user", 
                        "content": f"Provide a clear, concise summary of this content in no more than {max_length} characters. Focus on the main points and key takeaways.\n\nContent: {content[:2000]}"
                    }
                ],
                temperature=0.3,
                max_tokens=max_length // 3,
            )

            summary = response.choices[0].message.content.strip()

            # Ensure summary doesn't exceed max length
            if len(summary) > max_length:
                summary = summary[:max_length - 3].rsplit(" ", 1)[0] + "..."

            return summary

        except Exception as e:
            logger.error(f"Failed to generate OpenAI summary: {e}")
            preview = content[:max_length - 3] + "..." if len(content) > max_length else content
            return preview