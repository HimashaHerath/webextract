"""Configuration management for CLI."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..config.settings import ConfigBuilder, WebExtractConfig
from .constants import DEFAULT_CONFIG_FILE, DEFAULT_LOG_FILE, DEFAULT_MODELS
from .exceptions import CLIConfigurationError


class ConfigManager:
    """Manage CLI configuration and settings."""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or DEFAULT_CONFIG_FILE
        self.config_path = Path(self.config_file)

    def load_config(self) -> WebExtractConfig:
        """Load configuration from file or create default.

        Returns:
            WebExtractConfig instance

        Raises:
            CLIConfigurationError: If config loading fails
        """
        try:
            if self.config_path.exists():
                return self._load_from_file()
            else:
                return self._create_default_config()
        except Exception as e:
            raise CLIConfigurationError(f"Failed to load configuration: {e}")

    def save_config(self, config: WebExtractConfig) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save

        Raises:
            CLIConfigurationError: If saving fails
        """
        try:
            config_dict = self._config_to_dict(config)

            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise CLIConfigurationError(f"Failed to save configuration: {e}")

    def update_config_from_cli(
        self,
        config: WebExtractConfig,
        model: Optional[str] = None,
        max_content: Optional[int] = None,
        custom_prompt: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
    ) -> WebExtractConfig:
        """Update configuration with CLI parameters.

        Args:
            config: Base configuration
            model: Optional model override
            max_content: Optional max content override
            custom_prompt: Optional custom prompt
            base_url: Optional base URL override
            temperature: Optional temperature override
            timeout: Optional timeout override

        Returns:
            Updated configuration
        """
        import copy

        # Create a copy to avoid modifying the original
        builder = ConfigBuilder()
        builder._config = copy.deepcopy(config)

        # Apply CLI overrides
        if model is not None:
            builder._config.llm.model_name = model

        if max_content is not None:
            builder._config.scraping.max_content_length = max_content

        if custom_prompt is not None:
            builder._config.llm.custom_prompt = custom_prompt

        if base_url is not None:
            builder._config.llm.base_url = base_url

        if temperature is not None:
            builder._config.llm.temperature = temperature

        if timeout is not None:
            builder._config.llm.timeout = timeout

        return builder.build()

    def _load_from_file(self) -> WebExtractConfig:
        """Load configuration from JSON file."""
        with open(self.config_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)

        return self._dict_to_config(config_dict)

    def _create_default_config(self) -> WebExtractConfig:
        """Create default configuration."""
        from ..config import get_default_config

        return get_default_config()

    def _config_to_dict(self, config: WebExtractConfig) -> Dict[str, Any]:
        """Convert config to dictionary for JSON serialization."""
        return {
            "llm": {
                "provider": config.llm.provider,
                "model_name": config.llm.model_name,
                "api_key": config.llm.api_key,
                "base_url": config.llm.base_url,
                "temperature": config.llm.temperature,
                "max_tokens": config.llm.max_tokens,
                "timeout": config.llm.timeout,
                "retry_attempts": config.llm.retry_attempts,
                "custom_prompt": config.llm.custom_prompt,
            },
            "scraping": {
                "user_agents": config.scraping.user_agents,
                "request_timeout": config.scraping.request_timeout,
                "request_delay": config.scraping.request_delay,
                "retry_attempts": config.scraping.retry_attempts,
                "retry_delay": config.scraping.retry_delay,
                "max_content_length": config.scraping.max_content_length,
            },
        }

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> WebExtractConfig:
        """Convert dictionary to config object."""
        builder = ConfigBuilder()

        # Load LLM config
        if "llm" in config_dict:
            llm_dict = config_dict["llm"]
            for key, value in llm_dict.items():
                if hasattr(builder.llm_config, key) and value is not None:
                    setattr(builder.llm_config, key, value)

        # Load scraping config
        if "scraping" in config_dict:
            scraping_dict = config_dict["scraping"]
            for key, value in scraping_dict.items():
                if hasattr(builder.scraping_config, key) and value is not None:
                    setattr(builder.scraping_config, key, value)

        return builder.build()

    def get_log_file_path(self) -> str:
        """Get the log file path for the current configuration."""
        # Try to load from config file if it exists
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_dict = json.load(f)
                    return config_dict.get("log_file", DEFAULT_LOG_FILE)
            except Exception:
                pass

        return DEFAULT_LOG_FILE

    def set_log_file_path(self, log_file: str) -> None:
        """Set the log file path in configuration."""
        try:
            config_dict = {}
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_dict = json.load(f)

            config_dict["log_file"] = log_file

            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise CLIConfigurationError(f"Failed to set log file path: {e}")


class EnvironmentManager:
    """Manage environment variables and detection."""

    @staticmethod
    def detect_environment() -> Dict[str, Any]:
        """Detect the current environment and return relevant information."""
        env_info = {
            "platform": os.name,
            "home_dir": str(Path.home()),
            "cwd": str(Path.cwd()),
            "python_path": os.environ.get("PYTHONPATH", ""),
            "has_ollama": EnvironmentManager._check_command_available("ollama"),
            "has_docker": EnvironmentManager._check_command_available("docker"),
        }

        # Check for API keys
        env_info["api_keys"] = {
            "openai": bool(os.environ.get("OPENAI_API_KEY")),
            "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
        }

        return env_info

    @staticmethod
    def _check_command_available(command: str) -> bool:
        """Check if a command is available in the system."""
        import shutil

        return shutil.which(command) is not None

    @staticmethod
    def get_default_model_for_environment() -> str:
        """Get the best default model for the current environment."""
        env_info = EnvironmentManager.detect_environment()

        if env_info["has_ollama"]:
            return DEFAULT_MODELS["ollama"]
        elif env_info["api_keys"]["openai"]:
            return DEFAULT_MODELS["openai"]
        elif env_info["api_keys"]["anthropic"]:
            return DEFAULT_MODELS["anthropic"]
        else:
            # Default to Ollama even if not detected
            return DEFAULT_MODELS["ollama"]
