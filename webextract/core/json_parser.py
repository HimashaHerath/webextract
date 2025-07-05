"""Robust JSON parsing utilities for LLM responses."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class JSONParser:
    """Robust JSON parser with advanced extraction capabilities."""

    def __init__(self):
        self.json_start_patterns = [
            r"```json\s*\n",
            r"```\s*\n",
            r"JSON:\s*\n",
            r"Response:\s*\n",
            r"Output:\s*\n",
            r"Result:\s*\n",
        ]

    def parse_response(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response using multiple robust strategies.

        Args:
            text: Raw response text from LLM

        Returns:
            Parsed JSON dict or None if parsing fails
        """
        if not text or not text.strip():
            return None

        # Strategy 1: Direct JSON parsing (fastest)
        result = self._try_direct_parse(text.strip())
        if result is not None:
            return result

        # Strategy 2: Extract from markdown code blocks
        result = self._extract_from_markdown(text)
        if result is not None:
            return result

        # Strategy 3: Find JSON boundaries with bracket matching
        result = self._extract_with_bracket_matching(text)
        if result is not None:
            return result

        # Strategy 4: Progressive cleaning and repair
        result = self._extract_with_repair(text)
        if result is not None:
            return result

        logger.warning("All JSON parsing strategies failed")
        return None

    def _try_direct_parse(self, text: str) -> Optional[Dict[str, Any]]:
        """Try direct JSON parsing."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _extract_from_markdown(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from markdown code blocks."""
        # Remove markdown code block markers
        patterns = [
            r"```json\s*\n(.*?)\n```",
            r"```\s*\n(.*?)\n```",
            r"```json(.*?)```",
            r"```(.*?)```",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                json_content = match.group(1).strip()
                result = self._try_direct_parse(json_content)
                if result is not None:
                    return result

        return None

    def _extract_with_bracket_matching(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON using proper bracket matching."""
        # Find all potential JSON start positions
        start_positions = []
        for i, char in enumerate(text):
            if char == "{":
                start_positions.append(i)

        # Try each start position and find matching closing brace
        for start in start_positions:
            json_text = self._extract_balanced_json(text, start)
            if json_text:
                result = self._try_direct_parse(json_text)
                if result is not None:
                    return result

        return None

    def _extract_balanced_json(self, text: str, start: int) -> Optional[str]:
        """Extract balanced JSON starting from given position."""
        if start >= len(text) or text[start] != "{":
            return None

        bracket_count = 0
        in_string = False
        escape_next = False

        for i in range(start, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == "\\" and in_string:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == "{":
                    bracket_count += 1
                elif char == "}":
                    bracket_count -= 1

                if bracket_count == 0:
                    return text[start : i + 1]

        return None

    def _extract_with_repair(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract and repair malformed JSON."""
        # Find potential JSON content
        json_candidates = self._find_json_candidates(text)

        for candidate in json_candidates:
            # Apply repair strategies
            repaired = self._repair_json(candidate)
            if repaired:
                result = self._try_direct_parse(repaired)
                if result is not None:
                    return result

        return None

    def _find_json_candidates(self, text: str) -> List[str]:
        """Find potential JSON strings in text."""
        candidates = []

        # Look for content between { and }
        start_idx = 0
        while True:
            start = text.find("{", start_idx)
            if start == -1:
                break

            # Find corresponding closing brace (simple heuristic)
            end = text.rfind("}")
            if end > start:
                candidates.append(text[start : end + 1])

            start_idx = start + 1

        return candidates

    def _repair_json(self, json_text: str) -> Optional[str]:
        """Apply common JSON repair strategies."""
        # Remove common prefixes/suffixes
        prefixes_to_remove = [
            "JSON:",
            "Response:",
            "Output:",
            "Result:",
            "Here is the JSON:",
            "The extracted information is:",
            "Based on the content:",
        ]

        for prefix in prefixes_to_remove:
            if json_text.lower().startswith(prefix.lower()):
                json_text = json_text[len(prefix) :].strip()

        # Remove trailing text after JSON
        if json_text.count("}") > 0:
            last_brace = json_text.rfind("}")
            json_text = json_text[: last_brace + 1]

        # Fix common formatting issues
        repairs = [
            # Remove trailing commas
            (r",(\s*[}\]])", r"\1"),
            # Fix unescaped quotes in strings (basic cases)
            (r':\s*"([^"]*)"([^",\]}]*)"', r': "\1\2"'),
            # Fix missing quotes around keys
            (r"(\w+):", r'"\1":'),
            # Fix single quotes to double quotes
            (r"'([^']*)'", r'"\1"'),
            # Remove extra whitespace
            (r"\s+", " "),
        ]

        for pattern, replacement in repairs:
            json_text = re.sub(pattern, replacement, json_text)

        return json_text.strip()


class StructuredPromptBuilder:
    """Build prompts optimized for reliable JSON output."""

    @staticmethod
    def create_extraction_prompt(
        schema: Optional[Dict[str, Any]] = None, custom_fields: Optional[List[str]] = None
    ) -> str:
        """
        Create a prompt optimized for JSON extraction.

        Args:
            schema: JSON schema for validation
            custom_fields: Custom fields to extract

        Returns:
            Optimized prompt string
        """
        if schema:
            return StructuredPromptBuilder._create_schema_prompt(schema)

        return StructuredPromptBuilder._create_default_prompt(custom_fields)

    @staticmethod
    def _create_default_prompt(custom_fields: Optional[List[str]] = None) -> str:
        """Create default extraction prompt."""
        base_fields = {
            "summary": "string - A clear, concise summary (2-3 sentences, required)",
            "topics": "array - Main topics discussed",
            "category": "string - Primary category (technology/business/news/education/entertainment/other)",
            "sentiment": "string - Overall tone (positive/negative/neutral)",
            "entities": {
                "people": "array - Person names mentioned",
                "organizations": "array - Organization/company names",
                "locations": "array - Locations/places mentioned",
            },
            "key_facts": "array - Important facts or claims",
            "important_dates": "array - Dates mentioned with context",
            "statistics": "array - Numbers, percentages, or metrics",
        }

        if custom_fields:
            for field in custom_fields:
                base_fields[field] = "string - Custom field"

        prompt = """Extract structured information from the content and return it as valid JSON.

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON - no explanations, no markdown, no extra text
2. Use double quotes for all strings and keys
3. All fields are required - use empty arrays [] or empty strings "" if no data
4. Do not include trailing commas
5. Ensure proper JSON formatting

Required JSON structure:
"""

        # Add formatted schema
        prompt += json.dumps(base_fields, indent=2, ensure_ascii=False)

        prompt += """

Example valid response:
{
  "summary": "This is a clear summary of the content.",
  "topics": ["topic1", "topic2"],
  "category": "technology",
  "sentiment": "positive",
  "entities": {
    "people": ["John Smith"],
    "organizations": ["Company ABC"],
    "locations": ["New York"]
  },
  "key_facts": ["Important fact 1", "Important fact 2"],
  "important_dates": ["2024-01-15: Product launch"],
  "statistics": ["50% increase", "1000 users"]
}

Extract information from the content and return JSON in exactly this format."""

        return prompt

    @staticmethod
    def _create_schema_prompt(schema: Dict[str, Any]) -> str:
        """Create prompt based on provided schema."""
        prompt = """Extract information from the content and return valid JSON matching this exact schema:

"""
        prompt += json.dumps(schema, indent=2, ensure_ascii=False)

        prompt += """

CRITICAL REQUIREMENTS:
- Return ONLY valid JSON matching the schema above
- No explanations, comments, or extra text
- Use double quotes for strings and keys
- Include all required fields from schema
- Use appropriate data types (string, number, boolean, array, object)

Extract the information and return properly formatted JSON."""

        return prompt


class JSONValidator:
    """Validate and fix JSON extraction results."""

    @staticmethod
    def validate_and_fix(
        data: Dict[str, Any], schema: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate JSON data and apply fixes.

        Args:
            data: JSON data to validate
            schema: Optional schema for validation

        Returns:
            Tuple of (is_valid, fixed_data)
        """
        if not isinstance(data, dict):
            return False, {}

        if schema:
            return JSONValidator._validate_against_schema(data, schema)

        return JSONValidator._validate_default_structure(data)

    @staticmethod
    def _validate_default_structure(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Validate against default extraction structure."""
        required_fields = {
            "summary": str,
            "topics": list,
            "category": str,
            "sentiment": str,
            "entities": dict,
            "key_facts": list,
            "important_dates": list,
            "statistics": list,
        }

        fixed_data = data.copy()
        is_valid = True

        for field, expected_type in required_fields.items():
            if field not in fixed_data:
                # Add missing field with default value
                if expected_type == str:
                    fixed_data[field] = ""
                elif expected_type == list:
                    fixed_data[field] = []
                elif expected_type == dict:
                    fixed_data[field] = {}
                is_valid = False
            else:
                # Fix type mismatches
                if not isinstance(fixed_data[field], expected_type):
                    if expected_type == list and isinstance(fixed_data[field], str):
                        fixed_data[field] = [fixed_data[field]] if fixed_data[field] else []
                    elif expected_type == str and fixed_data[field] is None:
                        fixed_data[field] = ""
                    elif expected_type == dict and not isinstance(fixed_data[field], dict):
                        fixed_data[field] = {}
                    else:
                        logger.warning(f"Cannot fix type mismatch for field {field}")
                        is_valid = False

        # Validate entities structure
        if "entities" in fixed_data and isinstance(fixed_data["entities"], dict):
            required_entity_fields = ["people", "organizations", "locations"]
            for field in required_entity_fields:
                if field not in fixed_data["entities"]:
                    fixed_data["entities"][field] = []
                elif not isinstance(fixed_data["entities"][field], list):
                    fixed_data["entities"][field] = []

        return is_valid, fixed_data

    @staticmethod
    def _validate_against_schema(
        data: Dict[str, Any], schema: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Validate against provided schema."""
        # Basic schema validation - can be enhanced with jsonschema library
        fixed_data = data.copy()
        is_valid = True

        # Check required fields if specified in schema
        if "required" in schema:
            for field in schema["required"]:
                if field not in fixed_data:
                    fixed_data[field] = None
                    is_valid = False

        return is_valid, fixed_data
