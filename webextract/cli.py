"""LLM WebExtract CLI interface.

This module provides the main CLI entry point while delegating
to the modular CLI implementation in the cli package.
"""

# For backwards compatibility, also expose the console
# Import the main CLI app from the modular implementation
from .cli.main import app, console, main

# Expose all public interfaces
__all__ = ["app", "main", "console"]


# Backwards compatibility: if this module is run directly
if __name__ == "__main__":
    main()
