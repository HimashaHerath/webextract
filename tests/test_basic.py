"""Basic tests for LLM WebExtract package."""

import asyncio
from unittest.mock import Mock, patch

import webextract
from webextract import WebExtractor


def test_package_imports():
    """Test that main package components can be imported."""
    assert hasattr(webextract, "WebExtractor")
    assert hasattr(webextract, "ConfigBuilder")
    assert hasattr(webextract, "ConfigProfiles")
    assert hasattr(webextract, "quick_extract")


def test_config_builder():
    """Test ConfigBuilder functionality."""
    config = webextract.ConfigBuilder().with_model("test-model").build()
    assert config.llm.model_name == "test-model"


def test_config_profiles():
    """Test that config profiles are available."""
    profiles = webextract.ConfigProfiles
    assert hasattr(profiles, "news_scraping")
    assert hasattr(profiles, "research_papers")
    assert hasattr(profiles, "ecommerce")


@patch("webextract.core.extractor.DataExtractor.extract")
def test_quick_extract(mock_extract):
    """Test quick_extract convenience function."""
    mock_result = Mock()
    mock_result.summary = "Test summary"
    mock_extract.return_value = mock_result

    result = webextract.quick_extract("https://example.com")

    mock_extract.assert_called_once()
    assert result.summary == "Test summary"


def test_version():
    """Test package version is available."""
    assert hasattr(webextract, "__version__")
    assert webextract.__version__ == "1.0.2"


def test_author():
    """Test author information."""
    assert hasattr(webextract, "__author__")
    assert webextract.__author__ == "Himasha Herath"


def test_extractor_initialization():
    """Test that WebExtractor can be initialized."""
    extractor = WebExtractor()
    assert extractor is not None


def test_extractor_has_required_methods():
    """Test that WebExtractor has the required methods."""
    extractor = WebExtractor()
    assert hasattr(extractor, "extract")
    assert hasattr(extractor, "test_connection")


async def async_test_basic_functionality():
    """Basic async test - placeholder for future async tests."""
    extractor = WebExtractor()
    # This is a placeholder - actual web scraping tests would require
    # either mocked responses or actual test URLs
    assert extractor is not None


def test_basic_functionality():
    """Test basic functionality using asyncio."""
    asyncio.run(async_test_basic_functionality())


def test_import_structure():
    """Test that key classes can be imported."""
    from webextract import WebExtractor
    from webextract.core.models import ExtractedContent

    assert WebExtractor is not None
    assert ExtractedContent is not None
