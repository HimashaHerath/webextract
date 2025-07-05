"""Output formatting for different formats."""

import csv
import json
from io import StringIO
from typing import Any, Dict, List, Optional

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .constants import CONFIDENCE_COLORS, CONFIDENCE_THRESHOLDS, DISPLAY_LIMITS
from .exceptions import CLIOutputError


class OutputFormatter:
    """Handle different output formats for extraction results."""

    def __init__(self, console: Console):
        self.console = console

    def format_output(
        self, result: Any, format_type: str, output_file: Optional[str] = None
    ) -> None:
        """Format and display/save extraction results.

        Args:
            result: Extraction result object
            format_type: Output format ('json', 'pretty', 'yaml', 'csv')
            output_file: Optional file path to save output

        Raises:
            CLIOutputError: If formatting or saving fails
        """
        try:
            if format_type.lower() == "pretty":
                self._display_pretty_output(result)
            else:
                output_data = self._format_structured_output(result, format_type)

                if output_file:
                    self._save_to_file(output_data, output_file, format_type)
                    self.console.print(f"✅ Results saved to {output_file}", style="bold green")
                else:
                    self._display_structured_output(output_data, format_type)

            # Always show confidence score
            self._display_confidence_score(result)

        except Exception as e:
            raise CLIOutputError(f"Output formatting failed: {e}")

    def _format_structured_output(self, result: Any, format_type: str) -> str:
        """Format result as structured data.

        Args:
            result: Extraction result
            format_type: Output format

        Returns:
            Formatted string
        """
        # Convert to dictionary
        if hasattr(result, "model_dump"):
            data = result.model_dump()
        elif hasattr(result, "dict"):
            data = result.dict()
        else:
            data = dict(result)

        if format_type.lower() == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format_type.lower() == "yaml":
            if not YAML_AVAILABLE:
                raise CLIOutputError(
                    "YAML format requires 'pyyaml' package. Install with: pip install pyyaml"
                )
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        elif format_type.lower() == "csv":
            return self._convert_to_csv(data)
        else:
            raise CLIOutputError(f"Unsupported format: {format_type}")

    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert data to CSV format.

        Args:
            data: Data dictionary

        Returns:
            CSV formatted string
        """
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Field", "Value"])

        # Flatten nested data
        flattened = self._flatten_dict(data)

        # Write data rows
        for key, value in flattened.items():
            # Convert lists/dicts to JSON strings for CSV
            if isinstance(value, (list, dict)):
                value = json.dumps(value)
            writer.writerow([key, str(value)])

        return output.getvalue()

    def _flatten_dict(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested dictionary.

        Args:
            data: Dictionary to flatten
            prefix: Key prefix

        Returns:
            Flattened dictionary
        """
        flattened = {}

        for key, value in data.items():
            new_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                flattened.update(self._flatten_dict(value, new_key))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Handle list of dictionaries
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        flattened.update(self._flatten_dict(item, f"{new_key}[{i}]"))
                    else:
                        flattened[f"{new_key}[{i}]"] = item
            else:
                flattened[new_key] = value

        return flattened

    def _save_to_file(self, data: str, file_path: str, format_type: str) -> None:
        """Save formatted data to file.

        Args:
            data: Formatted data string
            file_path: File path to save to
            format_type: Format type for encoding selection
        """
        try:
            encoding = "utf-8"
            with open(file_path, "w", encoding=encoding) as f:
                f.write(data)
        except Exception as e:
            raise CLIOutputError(f"Failed to save file {file_path}: {e}")

    def _display_structured_output(self, data: str, format_type: str) -> None:
        """Display structured output to console.

        Args:
            data: Formatted data string
            format_type: Format type
        """
        if format_type.lower() == "json":
            # Use rich's JSON formatting for better display
            try:
                parsed_json = json.loads(data)
                self.console.print_json(data=parsed_json)
            except json.JSONDecodeError:
                self.console.print(data)
        else:
            self.console.print(data)

    def _display_pretty_output(self, result: Any) -> None:
        """Display results in pretty format.

        Args:
            result: Extraction result object
        """
        # Main info panel
        info_table = Table(show_header=False, box=None)
        info_table.add_row("URL:", getattr(result, "url", "N/A"))
        info_table.add_row("Extracted:", getattr(result, "extracted_at", "N/A"))

        confidence = getattr(result, "confidence", 0.0)
        confidence_color = self._get_confidence_color(confidence)
        info_table.add_row(
            "Confidence:", f"[{confidence_color}]{confidence:.2f}[/{confidence_color}]"
        )

        # Get title from content if available
        title = "N/A"
        if hasattr(result, "content") and result.content:
            title = getattr(result.content, "title", "N/A") or "N/A"

        info_table.add_row("Title:", title)

        self.console.print(Panel(info_table, title="📄 Extraction Info", border_style="blue"))

        # Content summary
        if hasattr(result, "content") and result.content:
            description = getattr(result.content, "description", None)
            if description:
                # Truncate long descriptions
                if len(description) > DISPLAY_LIMITS["description_truncate"]:
                    description = description[: DISPLAY_LIMITS["description_truncate"]] + "..."

                self.console.print(
                    Panel(
                        description,
                        title="📝 Description",
                        border_style="green",
                    )
                )

        # Structured data
        if hasattr(result, "structured_info") and result.structured_info:
            self._display_structured_info(result.structured_info)

        # Links
        if hasattr(result, "content") and result.content:
            links = getattr(result.content, "links", [])
            if links:
                self._display_links(links)

    def _display_structured_info(self, structured_info: Any) -> None:
        """Display structured information in a table.

        Args:
            structured_info: Structured information object or dict
        """
        structured_table = Table(show_header=True, header_style="bold magenta")
        structured_table.add_column("Field", style="cyan")
        structured_table.add_column("Value", style="white")

        # Convert to dictionary format
        if hasattr(structured_info, "model_dump"):
            structured_dict = structured_info.model_dump()
        elif hasattr(structured_info, "dict"):
            structured_dict = structured_info.dict()
        elif isinstance(structured_info, dict):
            structured_dict = structured_info
        else:
            try:
                structured_dict = dict(structured_info)
            except (TypeError, ValueError):
                structured_dict = {"data": str(structured_info)}

        # Display each field
        for key, value in structured_dict.items():
            value_str = self._format_value_for_display(value)
            structured_table.add_row(key, value_str)

        self.console.print(
            Panel(
                structured_table,
                title="🧠 LLM Analysis",
                border_style="yellow",
            )
        )

    def _display_links(self, links: List[str]) -> None:
        """Display links section.

        Args:
            links: List of links
        """
        display_links = links[: DISPLAY_LIMITS["links"]]
        links_text = "\n".join(display_links)

        if len(links) > DISPLAY_LIMITS["links"]:
            remaining = len(links) - DISPLAY_LIMITS["links"]
            links_text += f"\n... and {remaining} more links"

        self.console.print(Panel(links_text, title="🔗 Important Links", border_style="cyan"))

    def _format_value_for_display(self, value: Any) -> str:
        """Format a value for pretty display.

        Args:
            value: Value to format

        Returns:
            Formatted string
        """
        if isinstance(value, (list, dict)):
            json_str = json.dumps(value, indent=2, ensure_ascii=False)
            if len(json_str) > DISPLAY_LIMITS["value_truncate"]:
                return json_str[: DISPLAY_LIMITS["value_truncate"]] + "..."
            return json_str
        else:
            str_value = str(value)
            if len(str_value) > DISPLAY_LIMITS["value_truncate"]:
                return str_value[: DISPLAY_LIMITS["value_truncate"]] + "..."
            return str_value

    def _get_confidence_color(self, confidence: float) -> str:
        """Get color for confidence score.

        Args:
            confidence: Confidence value

        Returns:
            Color name
        """
        if confidence >= CONFIDENCE_THRESHOLDS["high"]:
            return CONFIDENCE_COLORS["high"]
        elif confidence >= CONFIDENCE_THRESHOLDS["medium"]:
            return CONFIDENCE_COLORS["medium"]
        else:
            return CONFIDENCE_COLORS["low"]

    def _display_confidence_score(self, result: Any) -> None:
        """Display confidence score.

        Args:
            result: Extraction result
        """
        confidence = getattr(result, "confidence", 0.0)
        confidence_color = self._get_confidence_color(confidence)

        message = f"✅ Extraction completed successfully! (Confidence: {confidence:.2f})"
        self.console.print(message, style=f"bold {confidence_color}")


class ProgressTracker:
    """Track and display progress for long-running operations."""

    def __init__(self, console: Console):
        self.console = console
        self._current_progress = None

    def start_progress(self, description: str):
        """Start a progress indicator.

        Args:
            description: Description of the operation
        """
        from rich.progress import Progress, SpinnerColumn, TextColumn

        self._current_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )

        self._current_progress.start()
        self._current_task = self._current_progress.add_task(description, total=None)

    def update_progress(self, description: str):
        """Update progress description.

        Args:
            description: New description
        """
        if self._current_progress and self._current_task:
            self._current_progress.update(self._current_task, description=description)

    def stop_progress(self):
        """Stop the progress indicator."""
        if self._current_progress:
            self._current_progress.stop()
            self._current_progress = None
            self._current_task = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_progress()
