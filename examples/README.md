# WebExtract Examples

This directory contains comprehensive examples demonstrating how to use the WebExtract library for AI-powered web content extraction.

## 📋 Available Examples

### 🚀 [basic_usage.py](basic_usage.py)
**Perfect for beginners** - Shows the simplest way to get started with WebExtract.
- Uses pre-configured profiles
- Default configuration options
- Basic error handling
- Simple output formatting

```bash
python examples/basic_usage.py
```

### ⚡ [advanced_configuration.py](advanced_configuration.py)
**For power users** - Demonstrates all advanced configuration options.
- Custom prompts for specific data extraction
- Speed vs accuracy optimizations
- Timeout and content limit configurations
- Performance comparisons

```bash
python examples/advanced_configuration.py
```

### 📊 [batch_extraction.py](batch_extraction.py)
**For processing multiple URLs** - Shows efficient batch processing techniques.
- Sequential vs parallel processing
- Error handling for batch operations
- Progress tracking and statistics
- Result aggregation and analysis
- Saving results to files

```bash
python examples/batch_extraction.py
```

### 🔍 [profile_comparison.py](profile_comparison.py)
**For choosing the right profile** - Compares all built-in configuration profiles.
- Performance benchmarking
- Feature comparison
- Speed vs accuracy trade-offs
- Recommendations for different use cases

```bash
python examples/profile_comparison.py
```

## 🛠️ Prerequisites

Before running the examples, make sure you have:

1. **Ollama installed and running**
   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Start Ollama service
   ollama serve
   ```

2. **Required models downloaded**
   ```bash
   # For most examples
   ollama pull gemma3:27b
   ollama pull gemma3:8b
   ollama pull gemma3:2b
   
   # For documentation examples
   ollama pull codellama:13b
   ```

3. **WebExtract library installed**
   ```bash
   pip install webextract
   
   # Or if running from source
   pip install -e .
   ```

## 📚 Configuration Profiles Quick Reference

| Profile | Best For | Model | Speed | Accuracy |
|---------|----------|-------|-------|----------|
| **news_scraping()** | Blog posts, news articles | gemma3:27b | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **research_papers()** | Academic papers, research | gemma3:27b | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **ecommerce()** | Product pages, reviews | gemma3:8b | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **documentation()** | Technical docs, APIs | codellama:13b | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **fast_extraction()** | Quick overviews, batch processing | gemma3:2b | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **accurate_extraction()** | Detailed analysis | gemma3:27b | ⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🎯 Usage Patterns

### Quick Start (Minimal Code)
```python
from webextract import WebExtractor, ConfigProfiles

# Use a pre-configured profile
extractor = WebExtractor(ConfigProfiles.news_scraping())
result = extractor.extract("https://example.com/article")

if result:
    print(f"Title: {result.content.title}")
    print(f"Summary: {result.structured_info.get('summary', 'N/A')}")
```

### Custom Configuration
```python
from webextract import WebExtractor, ConfigBuilder

# Build your own configuration
extractor = WebExtractor(
    ConfigBuilder()
    .with_model("gemma3:27b")
    .with_content_limit(5000)
    .with_custom_prompt("Extract key points as bullet list...")
    .build()
)
```

### Batch Processing
```python
from webextract import WebExtractor, ConfigProfiles

extractor = WebExtractor(ConfigProfiles.fast_extraction())
urls = ["url1", "url2", "url3"]

results = []
for url in urls:
    result = extractor.extract(url)
    if result:
        results.append(result)
```

## 🐛 Troubleshooting

### Common Issues

**❌ "Model not available" error**
```bash
# Check available models
ollama list

# Pull missing models
ollama pull gemma3:27b
```

**❌ "Connection failed" error**
```bash
# Make sure Ollama is running
ollama serve

# Check if service is running
curl http://localhost:11434/api/tags
```

**❌ "Extraction failed" or low confidence**
- Try a different profile
- Check if the URL is accessible
- Verify the content is in a supported language
- Use a larger model for complex content

### Performance Tips

- Use `fast_extraction()` for batch processing
- Set appropriate `content_limit` to avoid processing huge pages
- Use parallel processing carefully (respect rate limits)
- Consider caching results for repeated URLs

## 📖 Additional Resources

- [Main Documentation](../README.md)
- [API Reference](../QUICK_REFERENCE.md)
- [Development Guide](../DEVELOPMENT.md)
- [Configuration Options](../webextract/config/settings.py)

## 🤝 Contributing Examples

Have a useful example to share? Please contribute!

1. Create your example file with clear documentation
2. Add it to this README
3. Test it thoroughly
4. Submit a pull request

Examples should be:
- Well-documented with docstrings
- Include error handling
- Show practical, real-world usage
- Follow the existing code style 