"""Custom exceptions for WebExtract package."""


class WebExtractError(Exception):
    """Base exception for WebExtract package."""
    pass


class ExtractionError(WebExtractError):
    """Raised when content extraction fails."""
    pass


class ScrapingError(WebExtractError):
    """Raised when web scraping fails."""
    pass


class LLMError(WebExtractError):
    """Raised when LLM processing fails."""
    pass


class ConfigurationError(WebExtractError):
    """Raised when configuration is invalid."""
    pass


class ModelNotAvailableError(LLMError):
    """Raised when requested LLM model is not available."""
    pass


class RateLimitError(WebExtractError):
    """Raised when rate limit is exceeded."""
    pass


class AuthenticationError(WebExtractError):
    """Raised when API authentication fails."""
    pass


class ContentTooLargeError(ExtractionError):
    """Raised when content exceeds size limits."""
    pass


class InvalidURLError(ScrapingError):
    """Raised when URL is invalid or inaccessible."""
    pass