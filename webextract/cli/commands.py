"""CLI command implementations."""

import logging
from typing import Optional

import typer
from rich.console import Console

from ..core.extractor import DataExtractor
from .config_manager import ConfigManager, EnvironmentManager
from .constants import PROGRESS_MESSAGES, SUCCESS_MESSAGES
from .error_handler import ErrorHandler, RetryHandler
from .exceptions import CLIConnectionError, CLIExtractionError, CLIValidationError
from .output_formatter import OutputFormatter, ProgressTracker
from .validators import InputValidator


class ExtractCommand:
    """Handle the extract command."""

    def __init__(self, console: Console):
        self.console = console
        self.config_manager = ConfigManager()
        self.error_handler = ErrorHandler(console)
        self.output_formatter = OutputFormatter(console)
        self.validator = InputValidator()

    def execute(
        self,
        url: str,
        output_format: str = "json",
        output_file: Optional[str] = None,
        model: Optional[str] = None,
        max_content: Optional[int] = None,
        custom_prompt: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        summary: bool = False,
        verbose: bool = False,
        retry_attempts: int = 3,
    ) -> int:
        """Execute the extract command.

        Returns:
            Exit code
        """
        try:
            # Setup logging
            self._setup_logging(verbose)

            # Validate inputs
            self._validate_inputs(url, output_format, output_file, max_content)

            # Load and configure
            config = self._prepare_config(
                model, max_content, custom_prompt, base_url, temperature, timeout
            )

            # Display info
            self._display_extraction_info(url, config, summary, verbose)

            # Test connection
            self._test_connection(config)

            # Perform extraction
            result = self._perform_extraction(url, config, summary, retry_attempts)

            # Output results
            self.output_formatter.format_output(result, output_format, output_file)

            return 0

        except Exception as e:
            return self.error_handler.handle_error(e, "extract")

    def _setup_logging(self, verbose: bool) -> None:
        """Setup logging configuration."""
        level = logging.DEBUG if verbose else logging.INFO
        log_file = self.config_manager.get_log_file_path()

        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

    def _validate_inputs(
        self, url: str, output_format: str, output_file: Optional[str], max_content: Optional[int]
    ) -> None:
        """Validate command inputs."""
        try:
            self.validator.validate_extract_params(url, output_format, output_file, max_content)
        except Exception as e:
            raise CLIValidationError(str(e))

    def _prepare_config(
        self,
        model: Optional[str],
        max_content: Optional[int],
        custom_prompt: Optional[str],
        base_url: Optional[str],
        temperature: Optional[float],
        timeout: Optional[int],
    ) -> "WebExtractConfig":
        """Prepare configuration with CLI overrides."""
        # Load base config
        config = self.config_manager.load_config()

        # Apply CLI overrides
        updated_config = self.config_manager.update_config_from_cli(
            config=config,
            model=model,
            max_content=max_content,
            custom_prompt=custom_prompt,
            base_url=base_url,
            temperature=temperature,
            timeout=timeout,
        )

        return updated_config

    def _display_extraction_info(
        self, url: str, config: "WebExtractConfig", summary: bool, verbose: bool
    ) -> None:
        """Display extraction information."""
        from .. import __version__

        self.console.print(f"🤖 LLM WebExtract v{__version__}", style="bold green")
        self.console.print(f"📄 URL: {url}")
        self.console.print(f"🤖 Model: {config.llm.model_name}")

        if verbose:
            self.console.print(f"📊 Max content: {config.scraping.max_content_length} chars")
            self.console.print(f"📝 Summary: {'Yes' if summary else 'No'}")
            self.console.print(f"💬 Custom prompt: {'Yes' if config.llm.custom_prompt else 'No'}")
            self.console.print(f"🌐 Base URL: {config.llm.base_url}")

    def _test_connection(self, config: "WebExtractConfig") -> None:
        """Test connection to LLM service."""
        self.console.print(PROGRESS_MESSAGES["connection_test"])

        extractor = DataExtractor(config)

        if not extractor.test_connection():
            suggestions = [
                "Check if Ollama is running (ollama serve)",
                f"Verify model '{config.llm.model_name}' is available (ollama list)",
                f"Check if Ollama is accessible at {config.llm.base_url}",
                "Try using a different model with --model",
            ]

            self.error_handler.show_warning("Connection test failed", suggestions)

            raise CLIConnectionError("LLM service connection failed")

    def _perform_extraction(
        self, url: str, config: "WebExtractConfig", summary: bool, retry_attempts: int
    ) -> "StructuredData":
        """Perform the extraction with retry logic."""
        extractor = DataExtractor(config)
        retry_handler = RetryHandler(self.console, max_retries=retry_attempts - 1)

        with ProgressTracker(self.console) as progress:
            progress.start_progress(PROGRESS_MESSAGES["extracting"])

            try:
                # Use retry logic for extraction
                if summary:
                    result = retry_handler.retry_with_backoff(extractor.extract_with_summary, url)
                else:
                    result = retry_handler.retry_with_backoff(extractor.extract, url)

                if not result:
                    raise CLIExtractionError("Extraction returned no result")

                if not result.is_successful:
                    error_msg = "Extraction failed"
                    if hasattr(result, "structured_info") and result.structured_info:
                        if hasattr(result.structured_info, "get"):
                            error_detail = result.structured_info.get("error", "Unknown error")
                        else:
                            error_detail = getattr(result.structured_info, "error", "Unknown error")
                        error_msg += f": {error_detail}"

                    raise CLIExtractionError(error_msg)

                return result

            except KeyboardInterrupt:
                raise  # Re-raise to be handled by error handler
            except Exception as e:
                if isinstance(e, CLIExtractionError):
                    raise
                else:
                    raise CLIExtractionError(f"Extraction failed: {str(e)}")


class TestCommand:
    """Handle the test command."""

    def __init__(self, console: Console):
        self.console = console
        self.config_manager = ConfigManager()
        self.error_handler = ErrorHandler(console, verbose=True)

    def execute(self, model: Optional[str] = None) -> int:
        """Execute the test command.

        Returns:
            Exit code
        """
        try:
            # Setup verbose logging for test
            self._setup_logging()

            # Prepare config
            config = self._prepare_config(model)

            # Display test info
            self._display_test_info(config)

            # Run tests
            self._run_connection_test(config)

            # Display success
            self.console.print(SUCCESS_MESSAGES["connection_ok"], style="bold green")

            return 0

        except Exception as e:
            return self.error_handler.handle_error(e, "test")

    def _setup_logging(self) -> None:
        """Setup verbose logging for test command."""
        log_file = self.config_manager.get_log_file_path()

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

    def _prepare_config(self, model: Optional[str]) -> "WebExtractConfig":
        """Prepare configuration for testing."""
        config = self.config_manager.load_config()

        if model:
            config = self.config_manager.update_config_from_cli(config, model=model)

        return config

    def _display_test_info(self, config: "WebExtractConfig") -> None:
        """Display test information."""
        self.console.print("🔧 Testing LLM WebExtract setup...", style="bold blue")
        self.console.print(f"🤖 Testing model: {config.llm.model_name}")
        self.console.print(f"🌐 Base URL: {config.llm.base_url}")

        # Show environment info
        env_info = EnvironmentManager.detect_environment()
        self.console.print(f"💻 Platform: {env_info['platform']}")
        self.console.print(f"🏠 Ollama available: {'Yes' if env_info['has_ollama'] else 'No'}")

        if env_info["api_keys"]["openai"]:
            self.console.print("🔑 OpenAI API key: Found")
        if env_info["api_keys"]["anthropic"]:
            self.console.print("🔑 Anthropic API key: Found")

    def _run_connection_test(self, config: "WebExtractConfig") -> None:
        """Run connection test."""
        extractor = DataExtractor(config)

        if not extractor.test_connection():
            raise CLIConnectionError("Connection test failed")


class VersionCommand:
    """Handle the version command."""

    def __init__(self, console: Console):
        self.console = console

    def execute(self) -> int:
        """Execute the version command.

        Returns:
            Exit code
        """
        try:
            from .. import __author__, __version__

            self.console.print(f"LLM WebExtract v{__version__}")
            self.console.print(f"Author: {__author__}")

            # Show additional version info
            env_info = EnvironmentManager.detect_environment()
            self.console.print(f"Platform: {env_info['platform']}")

            return 0

        except Exception as e:
            self.console.print(f"❌ Error getting version info: {e}", style="red")
            return 1


class ConfigCommand:
    """Handle configuration management commands."""

    def __init__(self, console: Console):
        self.console = console
        self.config_manager = ConfigManager()
        self.error_handler = ErrorHandler(console)

    def show_config(self) -> int:
        """Show current configuration."""
        try:
            config = self.config_manager.load_config()

            # Display config in a nice format
            from rich.table import Table

            table = Table(title="Current Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="white")

            # LLM settings
            table.add_row("LLM Provider", config.llm.provider)
            table.add_row("Model Name", config.llm.model_name)
            table.add_row("Base URL", config.llm.base_url)
            table.add_row("Temperature", str(config.llm.temperature))
            table.add_row("Max Tokens", str(config.llm.max_tokens))
            table.add_row("Timeout", f"{config.llm.timeout}s")

            # Scraping settings
            table.add_row("Max Content Length", str(config.scraping.max_content_length))
            table.add_row("Request Timeout", f"{config.scraping.request_timeout}s")
            table.add_row("Retry Attempts", str(config.scraping.retry_attempts))

            self.console.print(table)

            return 0

        except Exception as e:
            return self.error_handler.handle_error(e, "config show")

    def init_config(self) -> int:
        """Initialize configuration interactively."""
        try:
            self.console.print("🔧 Initializing WebExtract configuration...", style="bold blue")

            # Detect environment and suggest defaults
            env_info = EnvironmentManager.detect_environment()
            default_model = EnvironmentManager.get_default_model_for_environment()

            self.console.print(f"💻 Detected platform: {env_info['platform']}")
            self.console.print(f"🤖 Suggested model: {default_model}")

            # For now, create a default config
            # In the future, this could be interactive
            config = self.config_manager.load_config()
            self.config_manager.save_config(config)

            self.console.print(SUCCESS_MESSAGES["setup_complete"], style="bold green")

            return 0

        except Exception as e:
            return self.error_handler.handle_error(e, "config init")
