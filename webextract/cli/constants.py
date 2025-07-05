"""CLI constants and configuration values."""

from typing import Dict, List, Tuple

# Output formats
OUTPUT_FORMATS = ["json", "pretty", "yaml", "csv"]
DEFAULT_OUTPUT_FORMAT = "json"

# File and logging
DEFAULT_LOG_FILE = "webextract.log"
DEFAULT_CONFIG_FILE = "webextract.config.json"

# Display limits and thresholds
CONFIDENCE_THRESHOLDS = {"high": 0.7, "medium": 0.3, "low": 0.0}

DISPLAY_LIMITS = {"links": 5, "value_truncate": 200, "description_truncate": 500}

# Colors for different confidence levels
CONFIDENCE_COLORS = {"high": "green", "medium": "yellow", "low": "red"}

# Default model configurations
DEFAULT_MODELS = {
    "ollama": "llama3.2",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-20241022",
}

# Error recovery suggestions
ERROR_RECOVERY_SUGGESTIONS = {
    "connection_failed": [
        "Check if Ollama is running: ollama serve",
        "Verify the model is available: ollama list",
        "Check the base URL configuration",
        "Try using a different model with --model",
    ],
    "model_not_found": [
        "Pull the model: ollama pull {model}",
        "Check available models: ollama list",
        "Try a different model with --model",
    ],
    "extraction_failed": [
        "Try with a smaller content limit: --max-content 5000",
        "Use a different model: --model llama3.2",
        "Check if the URL is accessible",
        "Add --verbose for more details",
    ],
    "invalid_url": [
        "Ensure URL includes http:// or https://",
        "Check for typos in the URL",
        "Verify the website is accessible",
    ],
    "output_error": [
        "Check write permissions for output file",
        "Ensure output directory exists",
        "Try a different output path",
    ],
}

# Validation patterns
URL_SCHEMES = ["http", "https"]
REQUIRED_URL_PARTS = ["scheme", "netloc"]

# Progress messages
PROGRESS_MESSAGES = {
    "connection_test": "Testing connection...",
    "extracting": "Extracting data...",
    "processing": "Processing content...",
    "saving": "Saving results...",
}

# Success messages
SUCCESS_MESSAGES = {
    "extraction_complete": "✅ Extraction completed successfully!",
    "file_saved": "✅ Results saved to {file}",
    "connection_ok": "✅ All tests passed! You're ready to extract.",
    "setup_complete": "✅ Setup completed successfully!",
}

# Error message templates
ERROR_TEMPLATES = {
    "invalid_url": "❌ Invalid URL format. Please include http:// or https://",
    "invalid_format": "❌ Invalid output format. Use one of: {formats}",
    "connection_failed": "❌ Connection test failed",
    "extraction_failed": "❌ Failed to extract data",
    "file_error": "❌ Error with file operation: {error}",
    "unexpected_error": "❌ Unexpected error: {error}",
}
