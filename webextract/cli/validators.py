"""Input validation utilities for CLI."""

import os
from typing import Optional, Tuple
from urllib.parse import urlparse

from .constants import ERROR_TEMPLATES, OUTPUT_FORMATS, REQUIRED_URL_PARTS, URL_SCHEMES
from .exceptions import CLIValidationError


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        parsed = urlparse(url)

        # Check required parts
        for part in REQUIRED_URL_PARTS:
            if not getattr(parsed, part):
                return False, ERROR_TEMPLATES["invalid_url"]

        # Check scheme
        if parsed.scheme.lower() not in URL_SCHEMES:
            return False, f"URL scheme must be one of: {', '.join(URL_SCHEMES)}"

        return True, None

    except Exception as e:
        return False, f"URL parsing error: {str(e)}"


def validate_output_format(format_name: str) -> Tuple[bool, Optional[str]]:
    """Validate output format.

    Args:
        format_name: Output format to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if format_name.lower() not in OUTPUT_FORMATS:
        formats_str = ", ".join(OUTPUT_FORMATS)
        error_msg = ERROR_TEMPLATES["invalid_format"].format(formats=formats_str)
        return False, error_msg

    return True, None


def validate_output_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """Validate output file path.

    Args:
        file_path: Path to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check if directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            return False, f"Directory does not exist: {directory}"

        # Check write permissions
        test_dir = directory if directory else "."
        if not os.access(test_dir, os.W_OK):
            return False, f"No write permission for directory: {test_dir}"

        return True, None

    except Exception as e:
        return False, f"File path validation error: {str(e)}"


def validate_positive_int(value: Optional[int], name: str) -> Tuple[bool, Optional[str]]:
    """Validate positive integer value.

    Args:
        value: Value to validate
        name: Parameter name for error messages

    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        return True, None

    if not isinstance(value, int) or value <= 0:
        return False, f"{name} must be a positive integer"

    return True, None


def validate_confidence_threshold(value: Optional[float]) -> Tuple[bool, Optional[str]]:
    """Validate confidence threshold value.

    Args:
        value: Threshold to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        return True, None

    if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
        return False, "Confidence threshold must be between 0.0 and 1.0"

    return True, None


class InputValidator:
    """Centralized input validation for CLI commands."""

    @staticmethod
    def validate_extract_params(
        url: str,
        output_format: str,
        output_file: Optional[str] = None,
        max_content: Optional[int] = None,
    ) -> None:
        """Validate parameters for extract command.

        Args:
            url: URL to extract from
            output_format: Output format
            output_file: Optional output file path
            max_content: Optional max content length

        Raises:
            CLIValidationError: If validation fails
        """
        # Validate URL
        is_valid, error = validate_url(url)
        if not is_valid:
            raise CLIValidationError(error)

        # Validate output format
        is_valid, error = validate_output_format(output_format)
        if not is_valid:
            raise CLIValidationError(error)

        # Validate output file if provided
        if output_file:
            is_valid, error = validate_output_file(output_file)
            if not is_valid:
                raise CLIValidationError(error)

        # Validate max content
        is_valid, error = validate_positive_int(max_content, "max_content")
        if not is_valid:
            raise CLIValidationError(error)

    @staticmethod
    def validate_model_name(model_name: Optional[str]) -> None:
        """Validate model name format.

        Args:
            model_name: Model name to validate

        Raises:
            CLIValidationError: If validation fails
        """
        if model_name is None:
            return

        if not isinstance(model_name, str) or len(model_name.strip()) == 0:
            raise CLIValidationError("Model name cannot be empty")

        # Basic format validation
        if any(char in model_name for char in ['"', "'", "\n", "\r"]):
            raise CLIValidationError("Model name contains invalid characters")
