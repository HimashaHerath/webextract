"""Main CLI application with modular structure."""

from typing import Optional

import typer
from rich.console import Console

from .commands import ConfigCommand, ExtractCommand, TestCommand, VersionCommand
from .constants import DEFAULT_OUTPUT_FORMAT

# Create the main app
app = typer.Typer(
    name="llm-webextract",
    help="Turn any webpage into structured data using LLMs",
    add_completion=False,
    rich_markup_mode="rich",
)

# Create console instance
console = Console()


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to extract from"),
    output_format: str = typer.Option(
        DEFAULT_OUTPUT_FORMAT, "--format", "-f", help="Output format (json, pretty, yaml, csv)"
    ),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM model to use"),
    max_content: Optional[int] = typer.Option(
        None, "--max-content", help="Maximum content length to process"
    ),
    custom_prompt: Optional[str] = typer.Option(
        None, "--prompt", "-p", help="Custom extraction prompt"
    ),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for LLM service"),
    temperature: Optional[float] = typer.Option(
        None, "--temperature", help="Temperature for LLM generation (0.0-1.0)"
    ),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Request timeout in seconds"),
    summary: bool = typer.Option(False, "--summary", "-s", help="Include brief summary"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    retry_attempts: int = typer.Option(
        3, "--retry", help="Number of retry attempts for failed extractions"
    ),
):
    """Extract structured data from a webpage.

    This command fetches content from the specified URL and uses an LLM
    to extract structured information based on the content type.

    Examples:
        Extract from URL with default settings:
        $ llm-webextract extract https://example.com

        Save results to file in pretty format:
        $ llm-webextract extract https://example.com --format pretty --output results.txt

        Use specific model with custom prompt:
        $ llm-webextract extract https://example.com --model gpt-4 --prompt "Extract key facts"
    """
    command = ExtractCommand(console)
    exit_code = command.execute(
        url=url,
        output_format=output_format,
        output_file=output_file,
        model=model,
        max_content=max_content,
        custom_prompt=custom_prompt,
        base_url=base_url,
        temperature=temperature,
        timeout=timeout,
        summary=summary,
        verbose=verbose,
        retry_attempts=retry_attempts,
    )
    raise typer.Exit(exit_code)


@app.command()
def test(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM model to test"),
):
    """Test connection and model availability.

    This command verifies that the LLM service is accessible and the
    specified model is available for use.

    Examples:
        Test default configuration:
        $ llm-webextract test

        Test specific model:
        $ llm-webextract test --model llama3.2
    """
    command = TestCommand(console)
    exit_code = command.execute(model=model)
    raise typer.Exit(exit_code)


@app.command()
def version():
    """Show version information.

    Displays the current version of LLM WebExtract along with
    author information and platform details.
    """
    command = VersionCommand(console)
    exit_code = command.execute()
    raise typer.Exit(exit_code)


# Create config subcommand group
config_app = typer.Typer(
    name="config", help="Manage configuration settings", rich_markup_mode="rich"
)

app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show():
    """Show current configuration settings.

    Displays all current configuration values including LLM provider
    settings, model parameters, and scraping options.
    """
    command = ConfigCommand(console)
    exit_code = command.show_config()
    raise typer.Exit(exit_code)


@config_app.command("init")
def config_init():
    """Initialize configuration interactively.

    Sets up initial configuration by detecting the environment
    and suggesting appropriate defaults.
    """
    command = ConfigCommand(console)
    exit_code = command.init_config()
    raise typer.Exit(exit_code)


def main():
    """Run the main CLI application."""
    app()


if __name__ == "__main__":
    main()
