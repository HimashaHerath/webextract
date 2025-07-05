"""Error handling and recovery for CLI operations."""

import traceback
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel

from .constants import ERROR_RECOVERY_SUGGESTIONS, ERROR_TEMPLATES
from .exceptions import (
    CLIConnectionError,
    CLIError,
    CLIExtractionError,
    CLIOutputError,
    CLIValidationError,
)


class ErrorHandler:
    """Centralized error handling and recovery suggestions."""

    def __init__(self, console: Console, verbose: bool = False):
        self.console = console
        self.verbose = verbose

    def handle_error(self, error: Exception, context: Optional[str] = None) -> int:
        """Handle an error and provide recovery suggestions.

        Args:
            error: The exception that occurred
            context: Optional context information

        Returns:
            Exit code for the CLI
        """
        if isinstance(error, CLIError):
            return self._handle_cli_error(error, context)
        elif isinstance(error, KeyboardInterrupt):
            return self._handle_keyboard_interrupt()
        else:
            return self._handle_unexpected_error(error, context)

    def _handle_cli_error(self, error: CLIError, context: Optional[str] = None) -> int:
        """Handle CLI-specific errors."""
        self.console.print(f"\n{error.message}", style="bold red")

        # Determine error type and provide specific suggestions
        error_type = self._classify_error(error)
        suggestions = self._get_recovery_suggestions(error_type, error)

        if suggestions:
            self._show_recovery_suggestions(suggestions, context)

        if self.verbose and hasattr(error, "__traceback__"):
            self._show_traceback(error)

        return error.exit_code

    def _handle_keyboard_interrupt(self) -> int:
        """Handle user cancellation."""
        self.console.print("\n⚠️ Operation cancelled by user", style="yellow")
        return 1

    def _handle_unexpected_error(self, error: Exception, context: Optional[str] = None) -> int:
        """Handle unexpected errors."""
        error_msg = ERROR_TEMPLATES["unexpected_error"].format(error=str(error))
        self.console.print(f"\n{error_msg}", style="bold red")

        # Always show traceback for unexpected errors when verbose
        if self.verbose:
            self._show_traceback(error)
        else:
            self.console.print("💡 Run with --verbose for detailed error information", style="dim")

        # Provide general recovery suggestions
        general_suggestions = [
            "Check your internet connection",
            "Verify the URL is accessible",
            "Try running with --verbose for more details",
            "Check the logs for more information",
        ]
        self._show_recovery_suggestions(general_suggestions, context)

        return 1

    def _classify_error(self, error: CLIError) -> str:
        """Classify the error type for targeted suggestions."""
        error_msg = str(error).lower()

        if isinstance(error, CLIValidationError):
            if "url" in error_msg:
                return "invalid_url"
            return "validation_error"
        elif isinstance(error, CLIConnectionError):
            if "model" in error_msg:
                return "model_not_found"
            return "connection_failed"
        elif isinstance(error, CLIExtractionError):
            return "extraction_failed"
        elif isinstance(error, CLIOutputError):
            return "output_error"
        else:
            return "general_error"

    def _get_recovery_suggestions(self, error_type: str, error: CLIError) -> List[str]:
        """Get recovery suggestions for the error type."""
        suggestions = ERROR_RECOVERY_SUGGESTIONS.get(error_type, [])

        # Format suggestions with error-specific information
        formatted_suggestions = []
        for suggestion in suggestions:
            try:
                # Try to format with error information
                if hasattr(error, "message") and "{" in suggestion:
                    suggestion = suggestion.format(error=error.message)
                formatted_suggestions.append(suggestion)
            except (KeyError, ValueError):
                # If formatting fails, use the suggestion as-is
                formatted_suggestions.append(suggestion)

        return formatted_suggestions

    def _show_recovery_suggestions(self, suggestions: List[str], context: Optional[str] = None):
        """Display recovery suggestions to the user."""
        if not suggestions:
            return

        title = "💡 Suggested Solutions"
        if context:
            title += f" ({context})"

        suggestion_text = "\n".join(f"  • {suggestion}" for suggestion in suggestions)

        panel = Panel(suggestion_text, title=title, border_style="yellow", padding=(1, 2))

        self.console.print(panel)

    def _show_traceback(self, error: Exception):
        """Display detailed traceback information."""
        traceback_text = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

        panel = Panel(
            traceback_text,
            title="🔍 Detailed Error Information",
            border_style="red",
            padding=(1, 2),
        )

        self.console.print(panel)

    def show_warning(self, message: str, suggestions: Optional[List[str]] = None):
        """Show a warning message with optional suggestions."""
        self.console.print(f"⚠️ {message}", style="yellow")

        if suggestions:
            self._show_recovery_suggestions(suggestions, "Warning")

    def show_info(self, message: str):
        """Show an informational message."""
        self.console.print(f"ℹ️ {message}", style="blue")


class RetryHandler:
    """Handle retry logic for failed operations."""

    def __init__(self, console: Console, max_retries: int = 3):
        self.console = console
        self.max_retries = max_retries

    def retry_with_backoff(self, operation, *args, **kwargs):
        """Retry an operation with exponential backoff.

        Args:
            operation: Function to retry
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Result of the operation

        Raises:
            Last exception if all retries fail
        """
        import time

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = 2 ** (attempt - 1)  # Exponential backoff
                    self.console.print(
                        f"⏳ Retrying in {delay} seconds... (attempt {attempt}/{self.max_retries})"
                    )
                    time.sleep(delay)

                return operation(*args, **kwargs)

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    self.console.print(f"⚠️ Attempt {attempt + 1} failed: {str(e)}", style="yellow")
                else:
                    self.console.print(
                        f"❌ All {self.max_retries + 1} attempts failed", style="red"
                    )

        # If we get here, all retries failed
        raise last_error
