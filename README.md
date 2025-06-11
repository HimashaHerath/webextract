# 📊 WebExtract

Transform any webpage into structured data using the power of Large Language Models! This tool combines robust web scraping with local LLM processing to extract meaningful information from websites.

## ✨ What does it do?

Ever wanted to quickly extract structured information from a webpage? This tool does exactly that:

1. **Scrapes** any webpage intelligently using modern browser automation
2. **Processes** the content with your local LLM (via Ollama)
3. **Extracts** structured data like topics, entities, sentiment, and key points
4. **Outputs** clean JSON or pretty-formatted results

Perfect for researchers, developers, or anyone who needs to quickly understand and extract information from web content, including JavaScript-heavy sites and single-page applications.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- An Ollama model (we recommend `gemma3:27b` or similar)

### Installation

```bash
git clone https://github.com/HimashaHerath/webextract.git
cd webextract
pip install -r requirements.txt
playwright install chromium
```

### Your First Extraction

```bash
# Test if everything works
python main.py test

# Extract from any website
python main.py scrape "https://example.com"

# Get a nice formatted output with summary
python main.py scrape "https://github.com/microsoft/vscode" --format pretty --summary
```

## 💡 Features

🌐 **Modern Web Scraping** - Uses Playwright for reliable scraping of modern websites, including SPAs and JavaScript-heavy sites

🛡️ **Robust & Reliable** - Handles errors gracefully, retries failed requests, and works with anti-bot measures

🧠 **Smart Extraction** - Uses your local LLM to understand content and extract meaningful information

⚡ **Fast & Efficient** - Optimized for speed with intelligent content processing and browser automation

🎨 **Beautiful Output** - Clean JSON or rich terminal formatting

🔧 **Highly Configurable** - Customize everything from timeouts to extraction prompts

📊 **Built-in Monitoring** - Confidence scores and performance metrics included

## 🎯 Usage Examples

### Basic Extraction
```bash
# Simple extraction to JSON
python main.py scrape "https://news.bbc.co.uk/article/123"

# Save results to file
python main.py scrape "https://docs.python.org" --output python_docs.json
```

### Advanced Options
```bash
# Pretty output with extra details
python main.py scrape "https://github.com/user/repo" \
  --format pretty \
  --summary \
  --verbose

# Custom extraction focus
python main.py scrape "https://news-site.com" \
  --prompt "Focus on extracting key facts, dates, and people mentioned in this news article"

# Works great with modern web apps
python main.py scrape "https://react-app.com" --format pretty
```

### Available Commands
- `test` - Check if Ollama is running and your model is available
- `example` - Run a quick demo extraction  
- `scrape` - Extract data from any URL

## 🛠 Configuration

You can customize the behavior using environment variables:

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export DEFAULT_MODEL="gemma3:27b"
export REQUEST_TIMEOUT="30"
export MAX_CONTENT_LENGTH="5000"
export REQUEST_DELAY="1.0"
```

Or modify `config/settings.py` directly.

## 📋 What Gets Extracted?

The LLM analyzes web content and extracts:

- **Topics & Themes** - Main subjects discussed
- **Entities** - People, organizations, locations mentioned
- **Key Points** - Important takeaways and facts
- **Sentiment** - Overall tone (positive/negative/neutral)
- **Summary** - Concise overview of the content
- **Metadata** - Title, description, important links
- **Category** - Content classification
- **Important Dates** - Key dates mentioned in the content

## 🏗 Project Structure

```
webextract/
├── src/
│   ├── models.py          # Data structures
│   ├── scraper.py         # Playwright-based web scraping
│   ├── llm_client.py      # Ollama integration
│   └── extractor.py       # Main coordination
├── config/
│   └── settings.py        # Configuration
├── examples/
│   └── basic_usage.py     # Code examples
├── main.py               # CLI interface
└── requirements.txt      # Dependencies
```

## 🚀 Technical Highlights

- **Browser Automation**: Uses Playwright for reliable, modern web scraping
- **Dynamic Content**: Handles JavaScript-rendered content and SPAs
- **Smart Rate Limiting**: Respects website resources with configurable delays
- **Error Recovery**: Comprehensive retry logic with exponential backoff
- **Resource Management**: Proper browser lifecycle management
- **Anti-Detection**: Rotates user agents and uses realistic browser behavior

## 🤝 Contributing

Found a bug? Have an idea? Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Ollama](https://ollama.ai/) for local LLM processing
- Uses [Playwright](https://playwright.dev/) for modern web scraping
- HTML parsing with [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- CLI powered by [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)

---

**⭐ If this tool helps you, consider giving it a star!** 