# 🤖 LLM WebExtract

> Turn any website into structured data using the power of AI

Ever wanted to extract meaningful information from websites but got tired of parsing HTML and dealing with messy data? That's exactly why I built this tool. It combines modern web scraping with Large Language Models to intelligently extract structured information from any webpage.

## 🎯 What does this actually do?

Instead of writing complex parsing rules for every website, this tool:

1. **Scrapes the webpage** using Playwright (handles modern JavaScript sites)
2. **Feeds the content to an LLM** (local via Ollama, or cloud via OpenAI/Anthropic)
3. **Gets back structured data** - topics, entities, summaries, key facts, and more

Think of it as having an AI assistant that reads web pages and summarizes them for you.

## 🚀 Getting Started

### Installation

```bash
pip install llm-webextract
playwright install chromium
```

Want to use OpenAI or Anthropic instead of local models?
```bash
pip install llm-webextract[openai]     # For GPT models
pip install llm-webextract[anthropic]  # For Claude models
pip install llm-webextract[all]        # Everything
```

### Quick Examples

**Command Line (easiest way to start):**
```bash
# Extract content from any URL
llm-webextract extract "https://news.ycombinator.com"

# Pretty formatted output
llm-webextract extract "https://example.com" --format pretty

# Test your setup
llm-webextract test
```

**Python Code:**
```python
import webextract

# Simple one-liner (requires Ollama running locally)
result = webextract.quick_extract("https://news.bbc.co.uk")
print(f"Summary: {result.summary}")
print(f"Key topics: {result.topics}")

# Or use cloud providers
result = webextract.extract_with_openai(
    "https://techcrunch.com", 
    api_key="sk-your-key-here"
)
```

## 🛠 Configuration Options

### Using Different LLM Providers

**Local with Ollama (default):**
```python
from webextract import WebExtractor, ConfigBuilder

extractor = WebExtractor(
    ConfigBuilder()
    .with_model("llama3:8b")  # or any model you have
    .build()
)
```

**OpenAI GPT:**
```python
extractor = WebExtractor(
    ConfigBuilder()
    .with_openai(api_key="sk-...", model="gpt-4")
    .build()
)
```

**Anthropic Claude:**
```python
extractor = WebExtractor(
    ConfigBuilder()
    .with_anthropic(api_key="sk-ant-...", model="claude-3-sonnet-20240229")
    .build()
)
```

### Pre-built Profiles

I've included some ready-to-use configurations for common scenarios:

```python
from webextract import ConfigProfiles

# For news articles
news_extractor = WebExtractor(ConfigProfiles.news_scraping())

# For research papers  
research_extractor = WebExtractor(ConfigProfiles.research_papers())

# For e-commerce sites
shop_extractor = WebExtractor(ConfigProfiles.ecommerce())
```

## 📊 What You Get Back

The LLM analyzes the content and returns structured data like:

- **Summary** - Clean, concise overview
- **Topics** - Main themes and subjects
- **Entities** - People, companies, locations mentioned
- **Key Facts** - Important information and takeaways
- **Sentiment** - Overall tone (positive/negative/neutral)
- **Category** - Content classification
- **Important Dates** - Key dates found in the content

Example output:
```json
{
  "summary": "Article discusses the latest developments in AI technology...",
  "topics": ["artificial intelligence", "machine learning", "tech industry"],
  "entities": ["OpenAI", "San Francisco", "Sam Altman"],
  "sentiment": "positive",
  "key_facts": ["New model released", "Performance improvements", "Beta testing"],
  "category": "technology",
  "confidence_score": 0.92
}
```

## ⚙️ Environment Setup

You can configure defaults using environment variables:

```bash
export WEBEXTRACT_MODEL="llama3:8b"
export WEBEXTRACT_LLM_PROVIDER="ollama"
export WEBEXTRACT_REQUEST_TIMEOUT="45"
export WEBEXTRACT_MAX_CONTENT="8000"
```

## 🏗 How It Works

1. **Modern Web Scraping** - Uses Playwright to handle JavaScript, SPAs, and modern websites
2. **Smart Content Processing** - Removes ads, navigation, and focuses on main content
3. **LLM Analysis** - Feeds clean content to your chosen LLM for intelligent extraction
4. **Structured Output** - Returns consistent, structured data you can actually use

## 🤔 Why I Built This

I was tired of:
- Writing custom scrapers for every website
- Dealing with HTML parsing edge cases
- Manually extracting insights from content
- Working with inconsistent data formats

This tool solves all of that by letting the LLM do the heavy lifting of understanding and structuring content.

## 🛡 Requirements

- Python 3.8+
- One of:
  - **Ollama** running locally (free, private)
  - **OpenAI API key** (paid, powerful)
  - **Anthropic API key** (paid, great reasoning)

## 🔧 Advanced Usage

**Custom extraction prompts:**
```bash
llm-webextract extract "https://example.com" \
  --prompt "Focus on extracting pricing and contact information"
```

**Batch processing:**
```python
urls = ["https://site1.com", "https://site2.com", "https://site3.com"]
for url in urls:
    result = extractor.extract(url)
    # Process each result
```

**Error handling:**
```python
try:
    result = extractor.extract("https://problematic-site.com")
except ExtractionError as e:
    print(f"Failed to extract: {e}")
```

## 🤝 Contributing

Found a bug? Want to add a feature? PRs are welcome!

**For Contributors:**
- 📖 Read our [Development Guide](DEVELOPMENT.md) for commit conventions, versioning, and release processes
- 🐛 Report bugs by opening an issue with detailed reproduction steps
- 💡 Suggest features by opening a discussion or issue
- 🔧 Submit PRs following our coding standards and commit message format

**Quick Start for Contributors:**
```bash
# Fork and clone the repo
git clone https://github.com/yourusername/llm-scraper.git
cd llm-scraper

# Install in development mode
pip install -e ".[dev]"

# Run tests and quality checks
python -m pytest && python -m black --check . && python -m flake8 --config .flake8
```

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Add tests if possible
5. Submit a PR

## 📄 License

MIT License - feel free to use this in your projects!

## 🙏 Thanks

Built with some amazing tools:
- [Ollama](https://ollama.ai/) - Local LLM inference
- [Playwright](https://playwright.dev/) - Modern web scraping
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [Pydantic](https://pydantic.dev/) - Data validation
- [Typer](https://typer.tiangolo.com/) - CLI framework

---

**Got questions?** Open an issue - I'm happy to help! 

**Find this useful?** Give it a ⭐ - it really helps! 