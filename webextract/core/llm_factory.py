"""Factory for creating LLM clients based on configuration."""

import logging

from ..config.settings import WebExtractConfig
from .exceptions import ConfigurationError, LLMError
from .llm_client import BaseLLMClient, OllamaClient

logger = logging.getLogger(__name__)


def create_llm_client(config: WebExtractConfig) -> BaseLLMClient:
    """Create an LLM client based on the configuration.

    Args:
        config: WebExtract configuration

    Returns:
        BaseLLMClient: Appropriate LLM client instance

    Raises:
        ConfigurationError: If configuration is invalid
        LLMError: If client creation fails
    """
    provider = config.llm.provider.lower()

    try:
        if provider == "ollama":
            return OllamaClient(model_name=config.llm.model_name, base_url=config.llm.base_url)

        elif provider == "openai":
            if not config.llm.api_key:
                raise ConfigurationError(
                    "OpenAI API key is required but not provided",
                    config_field="llm.api_key",
                    expected_type="string",
                    suggestions=[
                        "Set OPENAI_API_KEY environment variable",
                        "Provide api_key in configuration",
                        "Check your OpenAI account for API key",
                    ],
                )

            try:
                from .openai_client import OpenAIClient

                return OpenAIClient(
                    api_key=config.llm.api_key,
                    model_name=config.llm.model_name,
                    base_url=config.llm.base_url,
                )
            except ImportError as e:
                raise LLMError(
                    "OpenAI dependencies not installed",
                    provider="openai",
                    suggestions=["Install with: pip install openai"],
                    original_error=e,
                )

        elif provider == "anthropic":
            if not config.llm.api_key:
                raise ConfigurationError(
                    "Anthropic API key is required but not provided",
                    config_field="llm.api_key",
                    expected_type="string",
                    suggestions=[
                        "Set ANTHROPIC_API_KEY environment variable",
                        "Provide api_key in configuration",
                        "Check your Anthropic account for API key",
                    ],
                )

            try:
                from .anthropic_client import AnthropicClient

                return AnthropicClient(api_key=config.llm.api_key, model_name=config.llm.model_name)
            except ImportError as e:
                raise LLMError(
                    "Anthropic dependencies not installed",
                    provider="anthropic",
                    suggestions=["Install with: pip install anthropic"],
                    original_error=e,
                )

        else:
            raise ConfigurationError(
                f"Unsupported LLM provider: {provider}",
                config_field="llm.provider",
                provided_value=provider,
                suggestions=[
                    "Use 'ollama' for local models",
                    "Use 'openai' for OpenAI GPT models",
                    "Use 'anthropic' for Claude models",
                    "Check configuration documentation",
                ],
            )

    except (ConfigurationError, LLMError):
        raise
    except Exception as e:
        raise LLMError(
            f"Failed to create {provider} client",
            provider=provider,
            context={"model_name": config.llm.model_name},
            suggestions=[
                f"Check {provider} service status",
                "Verify configuration parameters",
                "Check network connectivity",
            ],
            original_error=e,
        )


def get_available_providers() -> dict:
    """Get information about available LLM providers.

    Returns:
        dict: Information about each provider's availability
    """
    providers = {
        "ollama": {"available": True, "requires": "Local Ollama installation"},
        "openai": {"available": False, "requires": "openai package"},
        "anthropic": {"available": False, "requires": "anthropic package"},
    }

    # Check OpenAI availability
    try:
        import openai  # noqa: F401

        providers["openai"]["available"] = True
    except ImportError:
        pass

    # Check Anthropic availability
    try:
        import anthropic  # noqa: F401

        providers["anthropic"]["available"] = True
    except ImportError:
        pass

    return providers
