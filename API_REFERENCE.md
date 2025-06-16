# 🚀 LLM WebExtract - API Reference

## Installation & Setup

```bash
# Basic installation
pip install llm-webextract
playwright install chromium

# With providers
pip install llm-webextract[openai]     # OpenAI
pip install llm-webextract[anthropic]  # Anthropic  
pip install llm-webextract[all]        # All providers
```

## CLI Commands

```bash
# Extract from URL
llm-webextract extract "https://example.com"

# Pretty output
llm-webextract extract "https://example.com" --format pretty

# Custom prompt
llm-webextract extract "https://example.com" \
  --prompt "Focus on extracting pricing and contact information"

# Test setup
llm-webextract test
```

## Python API

### Basic Usage

```python
import webextract

# Quick extraction (Ollama)
result = webextract.quick_extract("https://example.com")

# With OpenAI
result = webextract.extract_with_openai(
    "https://example.com", 
    api_key="sk-...",
    model="gpt-4o-mini"
)

# With Anthropic
result = webextract.extract_with_anthropic(
    "https://example.com",
    api_key="sk-ant-...",
    model="claude-3-5-sonnet-20241022"
)
```

### Configuration

```python
from webextract import WebExtractor, ConfigBuilder

# Ollama (local)
config = ConfigBuilder().with_ollama("llama3.2").build()

# OpenAI
config = ConfigBuilder().with_openai("sk-...", "gpt-4o-mini").build()

# Anthropic
config = ConfigBuilder().with_anthropic("sk-ant-...", "claude-3-5-sonnet-20241022").build()

# Advanced config
config = (ConfigBuilder()
    .with_openai("sk-...", "gpt-4")
    .with_timeout(60)
    .with_content_limit(12000)
    .with_temperature(0.1)
    .with_custom_prompt("Extract financial data and metrics")
    .build())

extractor = WebExtractor(config)
```

### Pre-built Profiles

```python
from webextract import ConfigProfiles, WebExtractor

# Ready-to-use configurations
news_extractor = WebExtractor(ConfigProfiles.news_scraping())
research_extractor = WebExtractor(ConfigProfiles.research_papers())
ecommerce_extractor = WebExtractor(ConfigProfiles.ecommerce())
```

## Extraction Methods

### Single URL

```python
# Basic extraction
result = extractor.extract("https://example.com")

# With custom schema
schema = {
    "title": "Main article title",
    "author": "Article author name",
    "publish_date": "Publication date",
    "key_points": "List of main points discussed"
}
result = extractor.extract_with_custom_schema("https://example.com", schema)

# Force refresh (skip cache)
result = extractor.extract("https://example.com", force_refresh=True)
```

### Batch Processing

```python
urls = ["https://site1.com", "https://site2.com", "https://site3.com"]

# Process multiple URLs
results = extractor.extract_batch(urls, max_workers=3)

# With schema
results = extractor.extract_batch(urls, schema=custom_schema)

# Process results
for result in results:
    if result and result.is_successful:
        print(f"{result.url}: {result.get_summary()}")
```

## Error Handling

```python
from webextract import (
    ExtractionError,
    ScrapingError, 
    LLMError,
    AuthenticationError,
    ConfigurationError
)

try:
    result = extractor.extract("https://example.com")
except AuthenticationError:
    print("Invalid API key")
except ScrapingError as e:
    print(f"Website scraping failed: {e}")
except LLMError as e:
    print(f"AI processing failed: {e}")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except ExtractionError as e:
    print(f"General extraction error: {e}")
```

## Environment Variables

```bash
# LLM Configuration
export WEBEXTRACT_LLM_PROVIDER="openai"        # ollama|openai|anthropic
export WEBEXTRACT_MODEL="gpt-4o-mini"          # Model name
export WEBEXTRACT_API_KEY="sk-your-key"        # API key
export WEBEXTRACT_LLM_BASE_URL="https://..."   # Custom base URL
export WEBEXTRACT_TEMPERATURE="0.1"            # LLM temperature
export WEBEXTRACT_MAX_TOKENS="4000"            # Max output tokens
export WEBEXTRACT_LLM_TIMEOUT="60"             # LLM timeout (seconds)

# Scraping Configuration  
export WEBEXTRACT_REQUEST_TIMEOUT="30"         # Page load timeout
export WEBEXTRACT_MAX_CONTENT="10000"          # Max content length
export WEBEXTRACT_RETRY_ATTEMPTS="3"           # Retry attempts
export WEBEXTRACT_REQUEST_DELAY="1.0"          # Delay between requests
```

## Data Structure

### StructuredData Object

```python
result = extractor.extract("https://example.com")

# Properties
result.url                  # Source URL
result.extracted_at         # Timestamp
result.confidence           # Confidence score (0.0-1.0)
result.is_successful        # Boolean
result.has_high_confidence  # True if confidence >= 0.7

# Content access
result.content.title        # Page title
result.content.description  # Meta description
result.content.main_content # Main text content
result.content.links        # Important links
result.content.metadata     # Additional metadata

# Structured info
result.get_summary()        # Summary text
result.get_topics()         # Topics list
result.structured_info      # Full structured data

# Convert to simple dict
simple_data = result.to_simple_dict()
```

### Structured Info Fields

```python
{
    "summary": "Text summary of content",
    "topics": ["topic1", "topic2"],
    "category": "technology|business|news|education|entertainment|other",
    "sentiment": "positive|negative|neutral|mixed",
    "entities": {
        "people": ["Name1", "Name2"],
        "organizations": ["Org1", "Org2"], 
        "locations": ["Location1", "Location2"]
    },
    "key_facts": ["Fact1", "Fact2"],
    "important_dates": ["2024-01-15", "Q1 2024"],
    "statistics": ["50% increase", "$1M revenue"],
    "confidence": 0.85
}
```

## Utility Functions

### Provider Information

```python
from webextract.core.llm_factory import get_available_providers

providers = get_available_providers()
print(providers)
# {
#   "ollama": {"available": True, "requires": "Local Ollama installation"},
#   "openai": {"available": True, "requires": "openai package"},
#   "anthropic": {"available": False, "requires": "anthropic package"}
# }
```

### Testing Connection

```python
# Test if everything is working
success = extractor.test_connection()
if success:
    print("✅ Ready to extract!")
else:
    print("❌ Setup issues detected")
```

### Cache Management

```python
# Clear extraction cache
extractor.clear_cache()

# Check cache
cached_result = extractor._extraction_cache.get("https://example.com")
```

## Common Patterns

### News Article Extraction

```python
news_schema = {
    "headline": "Main headline",
    "author": "Article author",
    "publish_date": "Publication date",
    "summary": "Brief summary",
    "key_quotes": "Important quotes from the article",
    "tags": "Article tags or categories"
}

extractor = WebExtractor(ConfigProfiles.news_scraping())
result = extractor.extract_with_custom_schema(news_url, news_schema)
```

### Product Information

```python
product_schema = {
    "name": "Product name",
    "price": "Current price",
    "rating": "Average rating",
    "reviews_count": "Number of reviews",
    "features": "List of key features",
    "availability": "In stock status"
}

result = extractor.extract_with_custom_schema(product_url, product_schema)
```

### Research Paper Processing

```python
research_schema = {
    "title": "Paper title",
    "authors": "List of authors",
    "abstract": "Paper abstract",
    "keywords": "Keywords or tags",
    "methodology": "Research methodology",
    "conclusions": "Main conclusions"
}

extractor = WebExtractor(ConfigProfiles.research_papers())
result = extractor.extract_with_custom_schema(paper_url, research_schema)
```

## Tips & Best Practices

### Performance

- Use batch processing for multiple URLs
- Set appropriate `max_workers` based on your system
- Cache results when possible
- Use content limits to avoid processing huge pages

### Reliability

- Always use try-catch for error handling
- Check `result.is_successful` before processing
- Monitor confidence scores
- Set reasonable timeouts

### Cost Optimization (Cloud APIs)

- Use local Ollama for development/testing
- Set content limits to reduce token usage
- Use batch processing to minimize API calls
- Consider caching for repeated URLs

### Quality

- Use pre-built profiles for better results
- Customize prompts for your specific use case
- Validate extracted data in your application
- Monitor extraction confidence scores