"""CLI-specific exceptions."""


class CLIError(Exception):
    """Base exception for CLI errors."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


class CLIValidationError(CLIError):
    """Raised when CLI input validation fails."""

    pass


class CLIConfigurationError(CLIError):
    """Raised when CLI configuration is invalid."""

    pass


class CLIConnectionError(CLIError):
    """Raised when connection tests fail."""

    pass


class CLIExtractionError(CLIError):
    """Raised when extraction fails."""

    pass


class CLIOutputError(CLIError):
    """Raised when output operations fail."""

    pass
