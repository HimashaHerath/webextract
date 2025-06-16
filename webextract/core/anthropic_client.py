"""Anthropic Claude client for processing extracted content."""

import json
import logging
from typing import Any, Dict, Optional

from .exceptions import AuthenticationError, LLMError, ModelNotAvailableError
from .llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Client for interacting with Anthropic Claude models."""

    def __init__(
        self, api_key: str, model_name: str = "claude-3-5-sonnet-20241022"
    ):
        super().__init__(model_name)
        self.api_key = api_key
        self._client = None
        self._setup_client()

    def _setup_client(self):
        """Setup Anthropic client."""
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise LLMError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )
        except Exception as e:
            raise AuthenticationError(f"Failed to setup Anthropic client: {e}")

    def is_model_available(self) -> bool:
        """Check if the specified model is available."""
        try:
            # Anthropic doesn't have a public models endpoint, so we'll try a simple request
            response = self._client.messages.create(
                model=self.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception as e:
            error_str = str(e).lower()
            if "model" in error_str and (
                "not found" in error_str or "invalid" in error_str
            ):
                return False
            # If it's an auth error, the model might exist but we can't access it
            logger.error(f"Failed to check Anthropic model availability: {e}")
            return False

    def generate_structured_data(
        self,
        content: str,
        custom_prompt: str = None,
        schema: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Generate structured data from content using Anthropic Claude."""
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
                    f"Content truncated from {len(content)} to "
                    f"{self.max_content_length} characters"
                )

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

            for attempt in range(3):  # Claude is reliable, fewer retries needed
                try:
                    logger.info(f"Anthropic generation attempt {attempt + 1}/3")

                    system_msg = (
                        "You are an expert content analyzer. Extract structured "
                        "information from the provided content and return it as "
                        "valid JSON. Follow the instructions exactly and return "
                        "only the JSON object."
                    )
                    response = self._client.messages.create(
                        model=self.model_name,
                        max_tokens=2000,
                        temperature=0.1,
                        system=system_msg,
                        messages=[{"role": "user", "content": user_message}],
                    )

                    response_text = response.content[0].text.strip()
                    logger.debug(
                        f"Anthropic response length: {len(response_text)} characters"
                    )

                    # Parse the response
                    result = self._parse_json_response(response_text)

                    if result and self._validate_extraction_result(result, schema):
                        logger.info(
                            f"Successfully extracted valid structured data on "
                            f"attempt {attempt + 1}"
                        )
                        return result

                except Exception as e:
                    logger.error(
                        f"Anthropic generation failed (attempt {attempt + 1}): {e}"
                    )
                    error_str = str(e).lower()

                    if "rate" in error_str and "limit" in error_str:
                        raise LLMError(f"Anthropic rate limit exceeded: {e}")
                    elif "authentication" in error_str or "api_key" in error_str:
                        raise AuthenticationError(
                            f"Anthropic authentication failed: {e}"
                        )
                    elif "model" in error_str and (
                        "not found" in error_str or "invalid" in error_str
                    ):
                        raise ModelNotAvailableError(
                            f"Anthropic model {self.model_name} not available: {e}"
                        )

                    if attempt == 2:  # Last attempt
                        raise LLMError(
                            f"Anthropic processing failed after 3 attempts: {e}"
                        )

            return self._create_safe_fallback(content[:200])

        except (AuthenticationError, ModelNotAvailableError, LLMError):
            raise
        except Exception as e:
            raise LLMError(f"Unexpected error in Anthropic processing: {e}")

    def summarize_content(self, content: str, max_length: int = 200) -> str:
        """Generate a brief summary using Anthropic Claude."""
        try:
            response = self._client.messages.create(
                model=self.model_name,
                max_tokens=max_length // 3,
                temperature=0.3,
                system="You are a content summarizer. Provide clear, concise summaries.",
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Provide a clear, concise summary of this content in no "
                            f"more than {max_length} characters. Focus on the main "
                            f"points and key takeaways.\n\nContent: {content[:2000]}"
                        ),
                    }
                ],
            )

            summary = response.content[0].text.strip()

            # Ensure summary doesn't exceed max length
            if len(summary) > max_length:
                summary = summary[:max_length - 3].rsplit(" ", 1)[0] + "..."

            return summary

        except Exception as e:
            logger.error(f"Failed to generate Anthropic summary: {e}")
            if len(content) > max_length:
                preview = content[:max_length - 3] + "..."
            else:
                preview = content
            return preview