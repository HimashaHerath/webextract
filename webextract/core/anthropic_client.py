"""Anthropic Claude client for processing extracted content."""

import logging
from typing import Any, Dict

from .exceptions import (
    AuthenticationError,
    ErrorHandler,
    LLMError,
    ModelNotAvailableError,
    RateLimitError,
)
from .llm_client import BaseLLMClient

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Client for interacting with Anthropic Claude models."""

    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-20241022"):
        """Initialize the Anthropic client with API key and model name."""
        super().__init__(model_name)
        self.api_key = api_key
        self._client = None
        self._setup_client()

    def _setup_client(self):
        """Set up the Anthropic client."""
        try:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise LLMError(
                "Anthropic package not installed",
                provider="anthropic",
                suggestions=["Install with: pip install anthropic"],
            )
        except Exception as e:
            raise AuthenticationError(
                "Failed to setup Anthropic client", provider="anthropic", original_error=e
            )

    def is_model_available(self) -> bool:
        """Check if the specified model is available."""
        try:
            # Anthropic doesn't have a public models endpoint, so we'll try a simple request
            self._client.messages.create(
                model=self.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception as e:
            error_str = str(e).lower()
            if "model" in error_str and ("not found" in error_str or "invalid" in error_str):
                return False
            # If it's an auth error, the model might exist but we can't access it
            logger.error(f"Failed to check Anthropic model availability: {e}")
            raise ModelNotAvailableError(
                "Cannot check model availability",
                requested_model=self.model_name,
                provider="anthropic",
                original_error=e,
            )

    def generate_structured_data(
        self,
        content: str,
        custom_prompt: str = None,
        schema: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Generate structured data from content using Anthropic Claude."""
        try:
            # Try tool-based approach first for better reliability
            if schema or not custom_prompt:
                return self._generate_with_tools(content, schema, custom_prompt)

            # Fallback to prompt-based approach
            return self._generate_with_prompt(content, custom_prompt, schema)

        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            return self._create_safe_fallback(content[:100])

    def _generate_with_tools(
        self, content: str, schema: Dict[str, Any] = None, custom_prompt: str = None
    ) -> Dict[str, Any]:
        """Generate structured data using Claude's tool calling for better reliability."""
        try:
            # Truncate content if needed
            truncated_content = content[: self.max_content_length]
            if len(content) > self.max_content_length:
                logger.info(
                    f"Content truncated from {len(content)} to {self.max_content_length} characters"
                )

            # Define extraction tool
            extraction_tool = {
                "name": "extract_structured_data",
                "description": "Extract structured information from content and return as JSON",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Clear, concise summary (2-3 sentences)",
                        },
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Main topics discussed",
                        },
                        "category": {
                            "type": "string",
                            "description": "Primary category (technology/business/news/education/entertainment/other)",
                        },
                        "sentiment": {
                            "type": "string",
                            "description": "Overall tone (positive/negative/neutral)",
                        },
                        "entities": {
                            "type": "object",
                            "properties": {
                                "people": {"type": "array", "items": {"type": "string"}},
                                "organizations": {"type": "array", "items": {"type": "string"}},
                                "locations": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["people", "organizations", "locations"],
                        },
                        "key_facts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Important facts or claims",
                        },
                        "important_dates": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Dates mentioned with context",
                        },
                        "statistics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Numbers, percentages, or metrics",
                        },
                    },
                    "required": [
                        "summary",
                        "topics",
                        "category",
                        "sentiment",
                        "entities",
                        "key_facts",
                        "important_dates",
                        "statistics",
                    ],
                },
            }

            # Override schema if provided
            if schema:
                extraction_tool["input_schema"] = schema

            user_message = f"""Analyze the following content and extract structured information using the extract_structured_data tool.

CONTENT TO ANALYZE:
{truncated_content}

{custom_prompt or "Extract all relevant information and structure it according to the tool schema."}"""

            for attempt in range(3):
                try:
                    logger.info(f"Anthropic tool-based generation attempt {attempt + 1}/3")

                    response = self._client.messages.create(
                        model=self.model_name,
                        max_tokens=2000,
                        temperature=0.1,
                        tools=[extraction_tool],
                        tool_choice={"type": "tool", "name": "extract_structured_data"},
                        messages=[{"role": "user", "content": user_message}],
                    )

                    # Extract tool use result
                    if response.content and len(response.content) > 0:
                        for content_block in response.content:
                            if hasattr(content_block, "type") and content_block.type == "tool_use":
                                result = content_block.input
                                if result and self._validate_extraction_result(result, schema):
                                    logger.info("Anthropic tool-based generation successful")
                                    return result

                except Exception as e:
                    logger.warning(f"Anthropic tool attempt {attempt + 1} failed: {e}")
                    continue

            # If all tool attempts fail, fallback to prompt-based
            logger.warning("Tool-based approach failed, falling back to prompt-based")
            return self._generate_with_prompt(content, custom_prompt, schema)

        except Exception as e:
            logger.error(f"Tool-based generation failed: {e}")
            return self._generate_with_prompt(content, custom_prompt, schema)

    def _generate_with_prompt(
        self, content: str, custom_prompt: str = None, schema: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate structured data using prompt-based approach with response prefilling."""
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
                    f"Content truncated from {len(content)} to {self.max_content_length} characters"
                )

            user_message = f"""Analyze the following content and extract structured information.

CONTENT TO ANALYZE:
{truncated_content}

EXTRACTION INSTRUCTIONS:
{prompt}

Return the result as valid JSON starting immediately with {{ and ending with }}."""

            for attempt in range(3):
                try:
                    logger.info(f"Anthropic prompt-based generation attempt {attempt + 1}/3")

                    system_msg = "You are an expert content analyzer. Extract structured information and return valid JSON only."

                    # Use response prefilling to force JSON output
                    response = self._client.messages.create(
                        model=self.model_name,
                        max_tokens=2000,
                        temperature=0.1,
                        system=system_msg,
                        messages=[
                            {"role": "user", "content": user_message},
                            {"role": "assistant", "content": "{"},  # Prefill with opening brace
                        ],
                    )

                    # Since we prefilled with "{", we need to prepend it to the response
                    response_text = "{" + response.content[0].text.strip()
                    logger.debug(f"Anthropic response length: {len(response_text)} characters")

                    # Parse the response
                    result = self._parse_json_response(response_text)

                    if result and self._validate_extraction_result(result, schema):
                        logger.info(
                            f"Successfully extracted valid structured data on "
                            f"attempt {attempt + 1}"
                        )
                        return result

                except Exception as e:
                    logger.error(f"Anthropic generation failed (attempt {attempt + 1}): {e}")
                    error_str = str(e).lower()

                    if "rate" in error_str and "limit" in error_str:
                        raise RateLimitError(
                            "Anthropic rate limit exceeded",
                            limit_type="api_requests",
                            provider="anthropic",
                            original_error=e,
                        )
                    elif "authentication" in error_str or "api_key" in error_str:
                        raise AuthenticationError(
                            "Anthropic authentication failed",
                            provider="anthropic",
                            original_error=e,
                        )
                    elif "model" in error_str and (
                        "not found" in error_str or "invalid" in error_str
                    ):
                        raise ModelNotAvailableError(
                            "Anthropic model not available",
                            requested_model=self.model_name,
                            provider="anthropic",
                            original_error=e,
                        )

                    if attempt == 2:  # Last attempt
                        raise LLMError(
                            "Anthropic processing failed after 3 attempts",
                            provider="anthropic",
                            model_name=self.model_name,
                            original_error=e,
                        )

            return self._create_safe_fallback(content[:200])

        except (AuthenticationError, ModelNotAvailableError, LLMError):
            raise
        except Exception as e:
            raise ErrorHandler.handle_with_context(
                "generate_structured_data",
                {"model_name": self.model_name, "provider": "anthropic"},
                e,
                ["Check Anthropic API key", "Verify model availability", "Check account credits"],
            )

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
                summary = summary[: max_length - 3].rsplit(" ", 1)[0] + "..."

            return summary

        except Exception as e:
            logger.error(f"Failed to generate Anthropic summary: {e}")
            if len(content) > max_length:
                preview = content[: max_length - 3] + "..."
            else:
                preview = content
            return preview
