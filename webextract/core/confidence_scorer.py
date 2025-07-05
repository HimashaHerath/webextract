"""Configurable confidence scoring system for extraction quality assessment."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .models import ExtractedContent

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceConfig:
    """Configuration for confidence scoring algorithm."""

    # Base scoring weights
    base_extraction_score: float = 0.1
    title_weight: float = 0.1
    description_weight: float = 0.05

    # Content length scoring
    content_length_thresholds: Dict[int, float] = field(
        default_factory=lambda: {
            1000: 0.2,  # High quality: substantial content
            500: 0.15,  # Good quality: decent content
            200: 0.1,  # Fair quality: minimal content
            100: 0.05,  # Low quality: very short content
        }
    )

    # Structured data scoring
    structured_data_weight: float = 0.2
    summary_weight: float = 0.1
    summary_min_length: int = 20
    topics_weight: float = 0.05
    entities_weight: float = 0.05
    rich_data_weight: float = 0.1
    rich_data_threshold: int = 4

    # Quality penalties
    error_penalty: float = -0.5
    empty_content_penalty: float = -0.3

    # Maximum confidence score
    max_score: float = 1.0
    min_score: float = 0.0


class ConfidenceScorer:
    """Configurable confidence scorer with evidence-based scoring."""

    def __init__(self, config: Optional[ConfidenceConfig] = None):
        self.config = config or ConfidenceConfig()

    def calculate_confidence(
        self, content: ExtractedContent, structured_info: Dict[str, Any]
    ) -> float:
        """
        Calculate extraction confidence score with detailed breakdown.

        Args:
            content: Extracted webpage content
            structured_info: LLM-generated structured data

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            # Initialize scoring breakdown for transparency
            breakdown = {
                "base_score": 0.0,
                "content_quality": 0.0,
                "structured_quality": 0.0,
                "penalties": 0.0,
            }

            # Base score for successful extraction
            breakdown["base_score"] = self.config.base_extraction_score

            # Content quality scoring
            breakdown["content_quality"] = self._score_content_quality(content)

            # Structured data quality scoring
            breakdown["structured_quality"] = self._score_structured_data(structured_info)

            # Apply penalties for errors or poor quality
            breakdown["penalties"] = self._calculate_penalties(content, structured_info)

            # Calculate final score
            total_score = sum(breakdown.values())
            final_score = max(self.config.min_score, min(self.config.max_score, total_score))

            # Log scoring breakdown for transparency
            logger.debug(f"Confidence breakdown: {breakdown}, final: {final_score:.3f}")

            return final_score

        except Exception as e:
            logger.warning(f"Error calculating confidence: {e}")
            return self.config.min_score

    def _score_content_quality(self, content: ExtractedContent) -> float:
        """Score content quality based on title, description, and content length."""
        score = 0.0

        # Title presence
        if content.title and content.title.strip():
            score += self.config.title_weight

        # Description presence
        if content.description and content.description.strip():
            score += self.config.description_weight

        # Content length scoring with configurable thresholds
        content_length = len(content.main_content) if content.main_content else 0
        length_score = self._score_content_length(content_length)
        score += length_score

        return score

    def _score_content_length(self, length: int) -> float:
        """Score content based on length with configurable thresholds."""
        # Sort thresholds in descending order
        sorted_thresholds = sorted(
            self.config.content_length_thresholds.items(), key=lambda x: x[0], reverse=True
        )

        # Find the first threshold that the content length meets
        for threshold, score in sorted_thresholds:
            if length >= threshold:
                return score

        return 0.0  # Below all thresholds

    def _score_structured_data(self, structured_info: Dict[str, Any]) -> float:
        """Score structured data quality."""
        if not structured_info:
            return 0.0

        score = 0.0

        # Check for extraction errors first
        if structured_info.get("error") or structured_info.get("extraction_error"):
            return 0.0  # No score for failed extractions

        # Base score for successful structured extraction
        score += self.config.structured_data_weight

        # Summary quality
        summary = structured_info.get("summary", "")
        if summary and len(summary) >= self.config.summary_min_length:
            score += self.config.summary_weight

        # Topics presence
        topics = structured_info.get("topics", [])
        if topics and len(topics) > 0:
            score += self.config.topics_weight

        # Entities scoring
        entities = structured_info.get("entities", {})
        if self._has_meaningful_entities(entities):
            score += self.config.entities_weight

        # Rich data bonus (multiple fields populated)
        populated_fields = self._count_populated_fields(structured_info)
        if populated_fields >= self.config.rich_data_threshold:
            score += self.config.rich_data_weight

        return score

    def _has_meaningful_entities(self, entities: Any) -> bool:
        """Check if entities contain meaningful data."""
        if not isinstance(entities, dict):
            return False

        total_entities = 0
        for value in entities.values():
            if isinstance(value, list):
                total_entities += len(value)
            elif value:  # Non-empty value
                total_entities += 1

        return total_entities > 0

    def _count_populated_fields(self, structured_info: Dict[str, Any]) -> int:
        """Count populated fields in structured data."""
        excluded_fields = {"error", "extraction_error"}
        count = 0

        for key, value in structured_info.items():
            if key in excluded_fields:
                continue

            # Check if field has meaningful content
            if self._is_field_populated(value):
                count += 1

        return count

    def _is_field_populated(self, value: Any) -> bool:
        """Check if a field has meaningful content."""
        if value is None:
            return False

        if isinstance(value, str):
            return bool(value.strip())

        if isinstance(value, (list, dict)):
            return len(value) > 0

        return bool(value)

    def _calculate_penalties(
        self, content: ExtractedContent, structured_info: Dict[str, Any]
    ) -> float:
        """Calculate penalties for poor quality indicators."""
        penalties = 0.0

        # Error penalties
        if structured_info.get("error") or structured_info.get("extraction_error"):
            penalties += self.config.error_penalty

        # Empty or very short content penalty
        if not content.main_content or len(content.main_content.strip()) < 50:
            penalties += self.config.empty_content_penalty

        return penalties


class AdaptiveConfidenceScorer(ConfidenceScorer):
    """Adaptive confidence scorer that learns from feedback."""

    def __init__(self, config: Optional[ConfidenceConfig] = None):
        super().__init__(config)
        self.feedback_history = []

    def add_feedback(self, predicted_confidence: float, actual_quality: float):
        """Add feedback to improve scoring accuracy."""
        self.feedback_history.append(
            {
                "predicted": predicted_confidence,
                "actual": actual_quality,
                "error": abs(predicted_confidence - actual_quality),
            }
        )

        # Keep only recent feedback (last 100 entries)
        if len(self.feedback_history) > 100:
            self.feedback_history = self.feedback_history[-100:]

    def get_average_error(self) -> float:
        """Get average prediction error from feedback."""
        if not self.feedback_history:
            return 0.0

        total_error = sum(item["error"] for item in self.feedback_history)
        return total_error / len(self.feedback_history)

    def get_calibration_stats(self) -> Dict[str, float]:
        """Get calibration statistics."""
        if not self.feedback_history:
            return {}

        predictions = [item["predicted"] for item in self.feedback_history]
        actuals = [item["actual"] for item in self.feedback_history]

        return {
            "mean_predicted": sum(predictions) / len(predictions),
            "mean_actual": sum(actuals) / len(actuals),
            "mean_error": self.get_average_error(),
            "correlation": self._calculate_correlation(predictions, actuals),
        }

    def _calculate_correlation(self, x: list, y: list) -> float:
        """Calculate correlation between predicted and actual scores."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))

        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2)) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator
