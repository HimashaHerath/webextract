# LLM WebExtract

[![PyPI version](https://badge.fury.io/py/llm-webextract.svg)](https://pypi.org/project/llm-webextract/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Python library and command-line tool that turns a web page into structured JSON.
It loads the page in headless Chromium with Playwright, pulls out the main text,
and asks a language model to return a summary, topics, named entities, key facts,
dates and figures. It works with a local model through Ollama, or with OpenAI or
Anthropic models through their APIs. It is meant for cases where writing a
separate HTML parser for each site is not worth the effort.

## Install

```bash
pip install llm-webextract
playwright install chromium
```

OpenAI and Anthropic support are optional extras:

```bash
pip install "llm-webextract[openai]"
pip install "llm-webextract[anthropic]"
pip install "llm-webextract[all]"
```

The default provider is Ollama. To use it, install [Ollama](https://ollama.com),
then run `ollama pull llama3.2` and keep `ollama serve` running.

## Quick start

### Command line

The command is `llm-webextract`. It uses Ollama unless the environment variables
below say otherwise.

```bash
llm-webextract test                                   # check the model is reachable
llm-webextract extract https://example.com            # JSON to stdout
llm-webextract extract https://example.com --format pretty
llm-webextract extract https://example.com --model llama3.2 --output result.json
```

`extract` options: `--format` (`json`, `pretty`, `csv`, or `yaml`, which needs
`pyyaml` installed), `--output`, `--model`, `--prompt`, `--max-content`,
`--base-url`, `--temperature`, `--timeout`, `--summary` and `--retry`.
`llm-webextract version` prints the version.

### Python

The package is imported as `webextract`.

```python
import webextract

result = webextract.quick_extract("https://example.com", model="llama3.2")

if result.is_successful:
    print(result.get_summary())
    print(result.get_topics())
    print(result.confidence)
else:
    print(result.content.metadata["error"])
```

For more control, build a configuration and create a `WebExtractor`:

```python
from webextract import ConfigBuilder, WebExtractor

config = (
    ConfigBuilder()
    .with_ollama("llama3.2")
    .with_content_limit(20000)
    .with_timeout(60)
    .build()
)
extractor = WebExtractor(config)

result = extractor.extract("https://example.com")

# Ask for your own fields instead of the default set
product = extractor.extract_with_custom_schema(
    "https://example.com/product",
    {"name": "Product name", "price": "Current price"},
)

# Several URLs at once, in a thread pool
results = extractor.extract_batch(["https://example.com", "https://example.org"], max_workers=2)
```

The field-to-description schema above works with Ollama and OpenAI. The
Anthropic client sends the schema as its tool's input schema, so there it has to
be a JSON Schema object (`{"type": "object", "properties": {...}}`).

`extract()` does not raise when a page cannot be fetched or the model fails. It
returns a result with `is_successful == False`, `confidence == 0.0` and the
reason in `result.content.metadata["error"]`. Pass full URLs including the
scheme (`https://`); a URL without one raises a Pydantic `ValidationError`.
Creating a `WebExtractor` can raise `ConfigurationError` (for example, a missing
API key) or `LLMError` (for example, the provider package is not installed).

## What a result contains

`extract()` returns a `StructuredData` object (a Pydantic model):

| Field | Contents |
|---|---|
| `url`, `extracted_at` | The page and an ISO timestamp |
| `content` | `title`, `description`, `main_content`, up to 10 `links`, and `metadata` |
| `structured_info` | A `StructuredInfo` model with `summary`, `topics`, `category`, `sentiment`, `entities` (`people`, `organizations`, `locations`), `key_facts`, `important_dates` and `statistics`. With a custom schema it is a plain dict of your fields |
| `confidence` | 0.0 to 1.0, a heuristic based on how much text was found and how many fields the model filled in |

`result.model_dump_json(indent=2)` gives the whole result as JSON.

## Providers and configuration

| Provider | Install | Python | Default model |
|---|---|---|---|
| Ollama (local) | included | `ConfigBuilder().with_ollama(model, base_url)` or `extract_with_ollama(url, model)` | `llama3.2` |
| OpenAI | `[openai]` extra | `ConfigBuilder().with_openai(api_key, model)` or `extract_with_openai(url, api_key, model)` | `gpt-4o-mini` |
| Anthropic | `[anthropic]` extra | `ConfigBuilder().with_anthropic(api_key, model)` or `extract_with_anthropic(url, api_key, model)` | `claude-3-5-sonnet-20241022` |

Other `ConfigBuilder` methods: `with_model`, `with_timeout`, `with_content_limit`,
`with_custom_prompt` (replaces the default extraction instructions) and
`with_temperature`.

`ConfigProfiles` has six ready-made Ollama configurations: `news_scraping`,
`research_papers`, `ecommerce`, `documentation`, `fast_extraction` and
`accurate_extraction`. Each one sets a fixed model tag (for example `gemma3:27b`
or `codellama:13b`, which you need to have pulled) and a content limit, and the
first four also set a prompt.

```python
from webextract import ConfigProfiles, WebExtractor

extractor = WebExtractor(ConfigProfiles.news_scraping())
```

When no configuration is passed (and for the CLI), settings come from these
environment variables:

| Variable | Default |
|---|---|
| `WEBEXTRACT_LLM_PROVIDER` | `ollama` (or `openai`, `anthropic`) |
| `WEBEXTRACT_MODEL` | `llama3.2` |
| `WEBEXTRACT_API_KEY` | none |
| `WEBEXTRACT_LLM_BASE_URL` | `http://localhost:11434` |
| `WEBEXTRACT_TEMPERATURE`, `WEBEXTRACT_MAX_TOKENS`, `WEBEXTRACT_LLM_TIMEOUT` | `0.1`, `4000`, `60` |
| `WEBEXTRACT_MAX_CONTENT` | `10000` characters |
| `WEBEXTRACT_REQUEST_TIMEOUT`, `WEBEXTRACT_RETRY_ATTEMPTS`, `WEBEXTRACT_REQUEST_DELAY` | `30`, `3`, `1.0` |

The base URL default is Ollama's, so to use OpenAI this way also set
`WEBEXTRACT_LLM_BASE_URL=https://api.openai.com/v1`.

The content limit is a hard limit: if the cleaned page text is longer, the
extraction fails with `ContentTooLargeError` instead of being cut short. Raise it
with `with_content_limit()` or `--max-content` for long pages.

## How it works

1. Playwright opens the URL in headless Chromium and reads the HTML once the DOM has loaded.
2. BeautifulSoup picks the main text: `<main>`, `<article>` or content-like class and id names first, then the highest-scoring block by amount of text and paragraphs. Scripts, navigation, headers, footers and ad or share blocks are removed.
3. The title, description and text go to the model with a prompt that asks for JSON only (OpenAI uses JSON mode; Anthropic uses a tool definition unless a custom prompt is set).
4. The reply is parsed, repaired if the JSON is malformed, checked for the expected fields, and given a confidence score.

Results with a confidence above 0.3 are cached in memory per `WebExtractor`
instance, keyed by URL. Pass `force_refresh=True` to `extract()` or call
`clear_cache()` to skip it.

## Development

```bash
git clone https://github.com/HimashaHerath/webextract.git
cd webextract
pip install -e ".[dev]"
playwright install chromium
python -m pytest
```

`tests/test_basic.py` holds ten smoke tests for imports, configuration and
object creation. They do not fetch pages or call a model, so they run without
Ollama or an API key.

## License

MIT. See [LICENSE](LICENSE).
