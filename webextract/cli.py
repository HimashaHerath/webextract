#!/usr/bin/env python3
"""LLM WebExtract CLI interface."""

import json
import logging
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config.settings import settings
from .core.extractor import DataExtractor
from .core.models import ExtractionConfig

app = typer.Typer(
    name="llm-webextract",
    help="Turn any webpage into structured data using LLMs",
    add_completion=False,
)
console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("webextract.log"), logging.StreamHandler()],
)


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to extract from"),
    output_format: str = typer.Option(
        "json", "--format", "-f", help="Output format (json, pretty)"
    ),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    model: str = typer.Option(settings.DEFAULT_MODEL, "--model", "-m", help="LLM model to use"),
    max_content: int = typer.Option(
        settings.MAX_CONTENT_LENGTH, "--max-content", help="Max content length"
    ),
    summary: bool = typer.Option(False, "--summary", "-s", help="Include brief summary"),
    custom_prompt: Optional[str] = typer.Option(
        None, "--prompt", "-p", help="Custom extraction prompt"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Extract structured data from a webpage."""
    # Validate URL format
    from urllib.parse import urlparse

    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            console.print(
                "❌ Invalid URL format. Please include http:// or https://",
                style="bold red",
            )
            raise typer.Exit(1)
    except Exception:
        console.print("❌ Invalid URL format", style="bold red")
        raise typer.Exit(1)

    # Validate output format
    if output_format.lower() not in ["json", "pretty"]:
        console.print(
            "❌ Invalid output format. Use 'json' or 'pretty'",
            style="bold red",
        )
        raise typer.Exit(1)

    console.print("🤖 LLM WebExtract v1.0.0", style="bold green")
    console.print(f"📄 URL: {url}")
    console.print(f"🤖 Model: {model}")
    if verbose:
        console.print(f"📊 Max content: {max_content} chars")
        console.print(f"📝 Summary: {'Yes' if summary else 'No'}")
        console.print(f"💬 Custom prompt: {'Yes' if custom_prompt else 'No'}")

    # Create extraction config
    config = ExtractionConfig(
        model_name=model,
        max_content_length=max_content,
        custom_prompt=custom_prompt,
    )

    # Initialize extractor
    extractor = DataExtractor(config)

    # Test connection first
    console.print("🔍 Testing connection...")
    if not extractor.test_connection():
        console.print("❌ Connection test failed. Please check:", style="bold red")
        console.print("  • Ollama is running (ollama serve)")
        console.print(f"  • Model '{model}' is available (ollama list)")
        console.print("  • Ollama is accessible at http://localhost:11434")
        raise typer.Exit(1)

    # Extract data with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Extracting data...", total=None)

        try:
            if summary:
                result = extractor.extract_with_summary(url)
            else:
                result = extractor.extract(url)
        except KeyboardInterrupt:
            console.print("\n⚠️ Extraction cancelled by user", style="yellow")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"\n❌ Unexpected error: {e}", style="bold red")
            if verbose:
                import traceback

                console.print(traceback.format_exc())
            raise typer.Exit(1)

        progress.update(task, completed=100)

    if not result:
        console.print("❌ Failed to extract data", style="bold red")
        raise typer.Exit(1)

    # Output results
    try:
        if output_format.lower() == "pretty":
            display_pretty_output(result)
        else:
            json_output = result.model_dump()

            if output_file:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(json_output, f, indent=2, ensure_ascii=False)
                console.print(f"✅ Results saved to {output_file}", style="bold green")
            else:
                console.print_json(data=json_output)

        console.print("✅ Extraction completed successfully!", style="bold green")

    except Exception as e:
        console.print(f"❌ Error saving results: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def test():
    """Test connection and model availability."""
    console.print("🔧 Testing LLM WebExtract setup...", style="bold blue")

    extractor = DataExtractor()

    if extractor.test_connection():
        console.print("✅ All tests passed! You're ready to extract.", style="bold green")
    else:
        console.print(
            "❌ Setup test failed. Please check your configuration.",
            style="bold red",
        )
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    from . import __author__, __version__

    console.print(f"LLM WebExtract v{__version__}")
    console.print(f"Author: {__author__}")


def display_pretty_output(result):
    """Display extraction results in a pretty format."""
    # Main info panel
    info_table = Table(show_header=False, box=None)
    info_table.add_row("URL:", result.url)
    info_table.add_row("Extracted:", result.extracted_at)
    info_table.add_row("Confidence:", f"{result.confidence:.2f}")
    info_table.add_row("Title:", result.content.title or "N/A")

    console.print(Panel(info_table, title="📄 Extraction Info", border_style="blue"))

    # Content summary
    if result.content.description:
        console.print(
            Panel(
                result.content.description,
                title="📝 Description",
                border_style="green",
            )
        )

    # Structured data
    if result.structured_info:
        structured_table = Table(show_header=True, header_style="bold magenta")
        structured_table.add_column("Field", style="cyan")
        structured_table.add_column("Value", style="white")

        # Handle both dictionary and Pydantic model formats
        if hasattr(result.structured_info, "model_dump"):
            # It's a Pydantic model
            structured_dict = result.structured_info.model_dump()
        elif isinstance(result.structured_info, dict):
            # It's already a dictionary
            structured_dict = result.structured_info
        else:
            # Fallback: try to convert to dict
            structured_dict = dict(result.structured_info)

        for key, value in structured_dict.items():
            if isinstance(value, (list, dict)):
                value_str = (
                    json.dumps(value, indent=2)[:200] + "..."
                    if len(str(value)) > 200
                    else json.dumps(value, indent=2)
                )
            else:
                value_str = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)

            structured_table.add_row(key, value_str)

        console.print(
            Panel(
                structured_table,
                title="🧠 LLM Analysis",
                border_style="yellow",
            )
        )

    # Links
    if result.content.links:
        links_text = "\n".join(result.content.links[:5])
        if len(result.content.links) > 5:
            links_text += f"\n... and {len(result.content.links) - 5} more links"

        console.print(Panel(links_text, title="🔗 Important Links", border_style="cyan"))


def main():
    """Run the main CLI application."""
    app()


if __name__ == "__main__":
    main()
