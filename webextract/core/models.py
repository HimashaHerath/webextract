"""Data models for structured output."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExtractedContent(BaseModel):
    """Model for extracted webpage content."""

    model_config = {"protected_namespaces": ()}

    title: Optional[str] = Field(None, description="Page title")
    description: Optional[str] = Field(None, description="Page description or summary")
    main_content: str = Field(..., description="Main textual content of the page")
    links: List[str] = Field(default_factory=list, description="Important links found on the page")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class StructuredData(BaseModel):
    """Model for LLM-processed structured data."""

    url: str = Field(..., description="Source URL")
    extracted_at: str = Field(..., description="Extraction timestamp")
    content: ExtractedContent = Field(..., description="Extracted content")
    structured_info: Dict[str, Any] = Field(
        default_factory=dict, description="LLM-structured information"
    )
    confidence: Optional[float] = Field(None, description="Confidence score of extraction")


class ExtractionConfig(BaseModel):
    """Configuration for data extraction."""

    model_config = {"protected_namespaces": ()}

    model_name: str = Field(default="gemma3:27b", description="Ollama model to use")
    max_content_length: int = Field(default=5000, description="Maximum content length to process")
    extract_links: bool = Field(default=True, description="Whether to extract links")
    custom_prompt: Optional[str] = Field(None, description="Custom extraction prompt")
