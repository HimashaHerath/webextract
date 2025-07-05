"""Enhanced exception hierarchy for WebExtract with actionable error messages."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WebExtractError(Exception):
    """
    Base exception for WebExtract package with enhanced error context.

    Provides structured error information, logging capabilities, and actionable guidance.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        recoverable: bool = True,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize enhanced WebExtract exception.

        Args:
            message: Human-readable error description
            error_code: Unique error identifier for programmatic handling
            context: Additional context information (URL, config, etc.)
            suggestions: List of actionable suggestions for fixing the error
            recoverable: Whether this error can potentially be recovered from
            original_error: Original exception that caused this error (for chaining)
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.suggestions = suggestions or []
        self.recoverable = recoverable
        self.original_error = original_error
        self.timestamp = datetime.now().isoformat()

        # Create comprehensive error message
        full_message = self._build_full_message()
        super().__init__(full_message)

        # Log error with appropriate level
        self._log_error()

    def _build_full_message(self) -> str:
        """Build comprehensive error message with context and suggestions."""
        parts = [self.message]

        # Add context information
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")

        # Add suggestions
        if self.suggestions:
            suggestions_str = "; ".join(self.suggestions)
            parts.append(f"Suggestions: {suggestions_str}")

        # Add error code
        if self.error_code:
            parts.append(f"Error Code: {self.error_code}")

        return " | ".join(parts)

    def _log_error(self):
        """Log error with appropriate level based on recoverability."""
        log_level = logging.WARNING if self.recoverable else logging.ERROR

        log_data = {
            "error_code": self.error_code,
            "error_message": self.message,
            "recoverable": self.recoverable,
            "context": self.context,
            "timestamp": self.timestamp,
        }

        if self.original_error:
            log_data["original_error"] = str(self.original_error)

        # Log without extra to avoid conflicts
        logger.log(
            log_level,
            f"WebExtract Error: {self.message} | Context: {self.context} | Code: {self.error_code}",
        )

    def add_context(self, key: str, value: Any) -> "WebExtractError":
        """Add context information to the error."""
        self.context[key] = value
        return self

    def add_suggestion(self, suggestion: str) -> "WebExtractError":
        """Add actionable suggestion to the error."""
        self.suggestions.append(suggestion)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "suggestions": self.suggestions,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp,
            "original_error": str(self.original_error) if self.original_error else None,
        }


class ExtractionError(WebExtractError):
    """Raised when content extraction fails."""

    def __init__(
        self,
        message: str,
        *,
        url: Optional[str] = None,
        extraction_stage: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if url:
            context["url"] = url
        if extraction_stage:
            context["stage"] = extraction_stage

        # Add common suggestions
        suggestions = kwargs.pop("suggestions", [])
        if not suggestions:
            suggestions = [
                "Verify the URL is accessible",
                "Check if the website has anti-bot protection",
                "Try adjusting content extraction settings",
                "Consider using a different user agent",
            ]

        super().__init__(message, context=context, suggestions=suggestions, **kwargs)


class ScrapingError(WebExtractError):
    """Raised when web scraping fails."""

    def __init__(
        self,
        message: str,
        *,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        timeout_duration: Optional[float] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if url:
            context["url"] = url
        if status_code:
            context["status_code"] = status_code
        if timeout_duration:
            context["timeout_duration"] = timeout_duration

        # Add specific suggestions based on error type
        suggestions = kwargs.pop("suggestions", [])
        if not suggestions:
            suggestions = self._get_scraping_suggestions(status_code, timeout_duration)

        super().__init__(message, context=context, suggestions=suggestions, **kwargs)

    def _get_scraping_suggestions(
        self, status_code: Optional[int], timeout_duration: Optional[float]
    ) -> List[str]:
        """Get specific suggestions based on error details."""
        suggestions = []

        if status_code:
            if status_code == 404:
                suggestions.extend(
                    [
                        "Verify the URL is correct",
                        "Check if the page still exists",
                        "Look for redirects or moved content",
                    ]
                )
            elif status_code == 403:
                suggestions.extend(
                    [
                        "Website may be blocking automated access",
                        "Try using a different user agent",
                        "Check if authentication is required",
                    ]
                )
            elif status_code >= 500:
                suggestions.extend(
                    [
                        "Website server error - try again later",
                        "Check website status on social media",
                        "Consider using a cached version",
                    ]
                )

        if timeout_duration:
            suggestions.extend(
                [
                    f"Increase timeout beyond {timeout_duration}s",
                    "Check your internet connection",
                    "Try scraping during off-peak hours",
                ]
            )

        # Default suggestions
        if not suggestions:
            suggestions = [
                "Check network connectivity",
                "Verify the URL is accessible in a browser",
                "Increase timeout settings",
                "Check for website blocking",
            ]

        return suggestions


class LLMError(WebExtractError):
    """Raised when LLM processing fails."""

    def __init__(
        self,
        message: str,
        *,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        api_call: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if model_name:
            context["model_name"] = model_name
        if provider:
            context["provider"] = provider
        if api_call:
            context["api_call"] = api_call

        suggestions = kwargs.pop("suggestions", [])
        if not suggestions:
            suggestions = self._get_llm_suggestions(provider, model_name)

        super().__init__(message, context=context, suggestions=suggestions, **kwargs)

    def _get_llm_suggestions(self, provider: Optional[str], model_name: Optional[str]) -> List[str]:
        """Get specific suggestions based on LLM provider and model."""
        suggestions = []

        if provider == "ollama":
            suggestions.extend(
                [
                    "Ensure Ollama is running (ollama serve)",
                    f"Check if model '{model_name}' is installed (ollama list)",
                    f"Pull the model if missing (ollama pull {model_name})",
                    "Verify Ollama is accessible at the configured URL",
                ]
            )
        elif provider == "openai":
            suggestions.extend(
                [
                    "Verify your OpenAI API key is valid",
                    "Check your OpenAI account billing status",
                    "Ensure the model is available in your region",
                    "Check OpenAI service status",
                ]
            )
        elif provider == "anthropic":
            suggestions.extend(
                [
                    "Verify your Anthropic API key is valid",
                    "Check your Anthropic account credits",
                    "Ensure you have access to the requested model",
                    "Check Anthropic service status",
                ]
            )
        else:
            suggestions.extend(
                [
                    "Verify LLM service is running and accessible",
                    "Check API credentials and permissions",
                    "Ensure the model is available",
                    "Check service status and rate limits",
                ]
            )

        return suggestions


class ConfigurationError(WebExtractError):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        *,
        config_field: Optional[str] = None,
        expected_type: Optional[str] = None,
        provided_value: Optional[Any] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if config_field:
            context["config_field"] = config_field
        if expected_type:
            context["expected_type"] = expected_type
        if provided_value is not None:
            context["provided_value"] = str(provided_value)

        suggestions = kwargs.pop("suggestions", [])
        if not suggestions:
            suggestions = self._get_config_suggestions(config_field, expected_type)

        super().__init__(
            message,
            context=context,
            suggestions=suggestions,
            recoverable=True,  # Config errors are usually recoverable
            **kwargs,
        )

    def _get_config_suggestions(
        self, config_field: Optional[str], expected_type: Optional[str]
    ) -> List[str]:
        """Get specific suggestions for configuration errors."""
        suggestions = []

        if config_field:
            suggestions.append(f"Check the '{config_field}' configuration field")

        if expected_type:
            suggestions.append(f"Ensure the value is of type {expected_type}")

        suggestions.extend(
            [
                "Refer to the configuration documentation",
                "Use ConfigBuilder for guided configuration",
                "Check environment variables if using env-based config",
                "Validate configuration before initializing components",
            ]
        )

        return suggestions


class ModelNotAvailableError(LLMError):
    """Raised when requested LLM model is not available."""

    def __init__(
        self,
        message: str,
        *,
        requested_model: Optional[str] = None,
        available_models: Optional[List[str]] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if requested_model:
            context["requested_model"] = requested_model
        if available_models:
            context["available_models"] = available_models

        suggestions = kwargs.pop("suggestions", [])
        if not suggestions:
            suggestions = self._get_model_suggestions(requested_model, available_models)

        super().__init__(message, context=context, suggestions=suggestions, **kwargs)

    def _get_model_suggestions(
        self, requested_model: Optional[str], available_models: Optional[List[str]]
    ) -> List[str]:
        """Get specific suggestions for model availability errors."""
        suggestions = []

        if requested_model:
            suggestions.append(f"Install the model: ollama pull {requested_model}")

        if available_models:
            suggestions.append(f"Use one of the available models: {', '.join(available_models)}")
        else:
            suggestions.append("Check available models with: ollama list")

        suggestions.extend(
            [
                "Ensure Ollama service is running",
                "Check internet connection for model downloads",
                "Verify sufficient disk space for model installation",
            ]
        )

        return suggestions


class RateLimitError(WebExtractError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if retry_after:
            context["retry_after"] = retry_after
        if limit_type:
            context["limit_type"] = limit_type

        suggestions = kwargs.pop("suggestions", [])
        if not suggestions:
            suggestions = self._get_rate_limit_suggestions(retry_after)

        super().__init__(
            message,
            context=context,
            suggestions=suggestions,
            recoverable=True,  # Rate limits are recoverable with delay
            **kwargs,
        )

    def _get_rate_limit_suggestions(self, retry_after: Optional[int]) -> List[str]:
        """Get suggestions for handling rate limits."""
        suggestions = []

        if retry_after:
            suggestions.append(f"Wait {retry_after} seconds before retrying")

        suggestions.extend(
            [
                "Implement exponential backoff for retries",
                "Reduce request frequency",
                "Consider upgrading your API plan",
                "Batch multiple requests if possible",
                "Check API usage dashboard",
            ]
        )

        return suggestions


class AuthenticationError(WebExtractError):
    """Raised when API authentication fails."""

    def __init__(
        self,
        message: str,
        *,
        auth_type: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if auth_type:
            context["auth_type"] = auth_type
        if provider:
            context["provider"] = provider

        suggestions = kwargs.pop("suggestions", [])
        if not suggestions:
            suggestions = self._get_auth_suggestions(provider)

        super().__init__(
            message,
            context=context,
            suggestions=suggestions,
            recoverable=True,  # Auth errors are usually recoverable
            **kwargs,
        )

    def _get_auth_suggestions(self, provider: Optional[str]) -> List[str]:
        """Get authentication-specific suggestions."""
        suggestions = []

        if provider:
            suggestions.append(f"Verify your {provider} API key is correct")
            suggestions.append(f"Check {provider} account status and permissions")

        suggestions.extend(
            [
                "Ensure API key environment variable is set",
                "Check for API key expiration",
                "Verify account billing and credits",
                "Test authentication with a simple API call",
            ]
        )

        return suggestions


class ContentTooLargeError(ExtractionError):
    """Raised when content exceeds size limits."""

    def __init__(
        self,
        message: str,
        *,
        content_size: Optional[int] = None,
        size_limit: Optional[int] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if content_size:
            context["content_size"] = content_size
        if size_limit:
            context["size_limit"] = size_limit

        suggestions = kwargs.pop("suggestions", [])
        if not suggestions:
            suggestions = self._get_size_suggestions(content_size, size_limit)

        super().__init__(message, context=context, suggestions=suggestions, **kwargs)

    def _get_size_suggestions(
        self, content_size: Optional[int], size_limit: Optional[int]
    ) -> List[str]:
        """Get suggestions for content size issues."""
        suggestions = []

        if content_size and size_limit:
            reduction_needed = content_size - size_limit
            suggestions.append(f"Reduce content by {reduction_needed} characters")

        suggestions.extend(
            [
                "Increase max_content_length in configuration",
                "Use content filtering to extract only relevant sections",
                "Process content in smaller chunks",
                "Consider summarizing long content before processing",
            ]
        )

        return suggestions


class InvalidURLError(ScrapingError):
    """Raised when URL is invalid or inaccessible."""

    def __init__(
        self,
        message: str,
        *,
        url: Optional[str] = None,
        validation_error: Optional[str] = None,
        **kwargs,
    ):
        context = kwargs.pop("context", {})
        if url:
            context["url"] = url
        if validation_error:
            context["validation_error"] = validation_error

        suggestions = kwargs.pop("suggestions", [])
        if not suggestions:
            suggestions = self._get_url_suggestions(url)

        super().__init__(message, context=context, suggestions=suggestions, **kwargs)

    def _get_url_suggestions(self, url: Optional[str]) -> List[str]:
        """Get URL-specific suggestions."""
        suggestions = [
            "Ensure URL includes protocol (http:// or https://)",
            "Check for typos in the URL",
            "Verify the domain exists and is accessible",
            "Test the URL in a web browser first",
        ]

        if url:
            if not url.startswith(("http://", "https://")):
                suggestions.insert(0, f"Add protocol to URL: https://{url}")

        return suggestions


# Error handler utilities
class ErrorHandler:
    """Utility class for consistent error handling patterns."""

    @staticmethod
    def handle_with_context(
        func_name: str,
        context: Dict[str, Any],
        error: Exception,
        suggestions: Optional[List[str]] = None,
    ) -> WebExtractError:
        """Convert generic exception to WebExtractError with context."""
        if isinstance(error, WebExtractError):
            # Already a WebExtract error, just add context
            for key, value in context.items():
                error.add_context(key, value)
            return error

        # Convert to appropriate WebExtract error
        error_message = f"Error in {func_name}: {str(error)}"

        return WebExtractError(
            error_message,
            context=context,
            suggestions=suggestions
            or [
                f"Check the {func_name} implementation",
                "Review input parameters",
                "Check logs for more details",
            ],
            original_error=error,
        )

    @staticmethod
    def chain_error(
        new_message: str, original_error: Exception, error_class: type = WebExtractError, **kwargs
    ) -> WebExtractError:
        """Create new error chained from original error."""
        return error_class(new_message, original_error=original_error, **kwargs)


# Backward compatibility
# Keep original exception names for existing code
pass  # The original exceptions are still available with their improved versions
