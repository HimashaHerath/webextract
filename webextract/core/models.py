"""Enhanced data models for structured output with validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class ExtractedContent(BaseModel):
    """Model for extracted webpage content."""

    model_config = {"protected_namespaces": ()}

    title: Optional[str] = Field(None, description="Page title")
    description: Optional[str] = Field(None, description="Page meta description")
    main_content: str = Field(..., description="Main textual content")
    links: List[str] = Field(default_factory=list, description="Important links")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("main_content")
    def validate_main_content(cls, v):
        """Ensure main content is not empty."""
        if not v or not v.strip():
            raise ValueError("Main content cannot be empty")
        return v.strip()

    @field_validator("links")
    def validate_links(cls, v):
        """Ensure links are valid URLs."""
        if v:
            from urllib.parse import urlparse

            valid_links = []
            for link in v:
                try:
                    parsed = urlparse(link)
                    if parsed.scheme and parsed.netloc:
                        valid_links.append(link)
                except:
                    pass
            return valid_links
        return v

    @property
    def content_length(self) -> int:
        """Get the length of main content."""
        return len(self.main_content)

    @property
    def has_metadata(self) -> bool:
        """Check if metadata is present."""
        return bool(self.metadata)


class EntityInfo(BaseModel):
    """Model for extracted entities."""

    people: List[str] = Field(default_factory=list, description="Person names")
    organizations: List[str] = Field(
        default_factory=list, description="Organization names"
    )
    locations: List[str] = Field(default_factory=list, description="Location names")

    @property
    def total_entities(self) -> int:
        """Get total number of entities."""
        return len(self.people) + len(self.organizations) + len(self.locations)

    @property
    def has_entities(self) -> bool:
        """Check if any entities were found."""
        return self.total_entities > 0


class StructuredInfo(BaseModel):
    """Model for LLM-extracted structured information."""

    summary: str = Field(..., description="Content summary")
    topics: List[str] = Field(default_factory=list, description="Main topics")
    category: str = Field(default="unknown", description="Content category")
    sentiment: str = Field(default="neutral", description="Overall sentiment")
    entities: EntityInfo = Field(
        default_factory=EntityInfo, description="Named entities"
    )
    key_facts: List[str] = Field(default_factory=list, description="Key facts")
    important_dates: List[str] = Field(
        default_factory=list, description="Important dates"
    )
    statistics: List[str] = Field(
        default_factory=list, description="Statistics and numbers"
    )
    extraction_error: bool = Field(
        default=False, description="Whether extraction had errors"
    )

    @field_validator("sentiment")
    def validate_sentiment(cls, v):
        """Ensure sentiment is valid."""
        valid_sentiments = {"positive", "negative", "neutral", "mixed"}
        if v.lower() not in valid_sentiments:
            return "neutral"
        return v.lower()

    @field_validator("summary")
    def validate_summary(cls, v):
        """Ensure summary is not empty."""
        if not v or not v.strip():
            raise ValueError("Summary cannot be empty")
        return v.strip()

    @model_validator(mode="before")
    def handle_entities(cls, values):
        """Handle different entity formats."""
        if "entities" in values:
            entities = values["entities"]
            if isinstance(entities, dict):
                # Ensure it has the right structure
                values["entities"] = EntityInfo(
                    people=entities.get("people", []),
                    organizations=entities.get("organizations", []),
                    locations=entities.get("locations", []),
                )
            elif not isinstance(entities, EntityInfo):
                # If it's not the right type, create empty
                values["entities"] = EntityInfo()
        return values


class StructuredData(BaseModel):
    """Complete extraction result with all data."""

    url: str = Field(..., description="Source URL")
    extracted_at: str = Field(..., description="Extraction timestamp")
    content: ExtractedContent = Field(..., description="Raw extracted content")
    structured_info: Union[StructuredInfo, Dict[str, Any]] = Field(
        ..., description="LLM-processed information"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Extraction confidence"
    )

    @field_validator("extracted_at")
    def validate_timestamp(cls, v):
        """Ensure timestamp is valid."""
        try:
            # Try to parse it to ensure it's valid
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except:
            # If invalid, use current time
            return datetime.now().isoformat()

    @field_validator("url")
    def validate_url(cls, v):
        """Ensure URL is valid."""
        from urllib.parse import urlparse

        try:
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
            return v
        except:
            raise ValueError(f"Invalid URL: {v}")

    @property
    def is_successful(self) -> bool:
        """Check if extraction was successful."""
        if isinstance(self.structured_info, dict):
            return not self.structured_info.get("extraction_error", False)
        return not self.structured_info.extraction_error

    @property
    def has_high_confidence(self) -> bool:
        """Check if extraction has high confidence."""
        return self.confidence >= 0.7

    def get_summary(self) -> Optional[str]:
        """Get summary from structured info."""
        if isinstance(self.structured_info, dict):
            return self.structured_info.get("summary")
        return self.structured_info.summary

    def get_topics(self) -> List[str]:
        """Get topics from structured info."""
        if isinstance(self.structured_info, dict):
            return self.structured_info.get("topics", [])
        return self.structured_info.topics

    def to_simple_dict(self) -> Dict[str, Any]:
        """Convert to a simplified dictionary."""
        return {
            "url": self.url,
            "title": self.content.title,
            "summary": self.get_summary(),
            "topics": self.get_topics(),
            "confidence": self.confidence,
            "extracted_at": self.extracted_at,
        }


class ExtractionConfig(BaseModel):
    """Configuration for data extraction."""

    model_config = {"protected_namespaces": ()}

    model_name: str = Field(default="llama3.2", description="LLM model name")
    max_content_length: int = Field(
        default=10000, ge=100, le=50000, description="Maximum content length"
    )
    extract_links: bool = Field(default=True, description="Whether to extract links")
    custom_prompt: Optional[str] = Field(None, description="Custom extraction prompt")
    extraction_schema: Optional[Dict[str, str]] = Field(
        None, description="Custom schema for extraction"
    )

    @field_validator("model_name")
    def validate_model_name(cls, v):
        """Ensure model name is not empty."""
        if not v or not v.strip():
            raise ValueError("Model name cannot be empty")
        return v.strip()


class ExtractionError(BaseModel):
    """Model for extraction errors."""

    url: str = Field(..., description="URL that failed")
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Error message")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    traceback: Optional[str] = Field(None, description="Error traceback")

    @classmethod
    def from_exception(cls, url: str, exception: Exception) -> "ExtractionError":
        """Create from an exception."""
        import traceback

        return cls(
            url=url,
            error_type=type(exception).__name__,
            error_message=str(exception),
            traceback=traceback.format_exc(),
        )
