# Changelog

All notable changes to LLM WebExtract will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.2] - 2024-12-18

### 🆕 New Features
- **Added**: `extract_with_ollama()` convenience function for simplified Ollama usage
- **Enhanced**: Updated README with improved provider setup examples
- **Added**: Quick one-liner examples for all providers in documentation

### 📚 Documentation
- **Updated**: README.md with `extract_with_ollama` function examples
- **Improved**: Provider setup section with both ConfigBuilder and convenience function usage
- **Enhanced**: Quick start examples now show multiple usage patterns

## [1.1.2] - 2024-12-16

### 🚀 Major Improvements

#### ✅ Multi-Provider LLM Support (BREAKING FIX)
- **FIXED**: Multi-provider support now actually works (was broken in previous versions)
- **Added**: Full OpenAI GPT integration with proper error handling
- **Added**: Complete Anthropic Claude integration
- **Added**: LLM provider factory for dynamic client creation
- **Added**: Provider availability checking and fallback strategies

#### 🛡️ Robust Error Handling
- **Added**: Comprehensive exception hierarchy (`ExtractionError`, `ScrapingError`, `LLMError`, `AuthenticationError`, `ConfigurationError`)
- **Fixed**: Proper error propagation instead of silent failures
- **Added**: Specific error messages for debugging different failure types
- **Added**: Graceful handling of missing dependencies and invalid API keys

#### 📧 Configuration Updates
- **Updated**: Email address to himasha626@gmail.com
- **Fixed**: Version consistency across all configuration files (1.1.2)
- **Fixed**: Repository URLs pointing to correct GitHub repository
- **Fixed**: Default model name consistency (llama3.2)

### 📚 Documentation Overhaul

#### 📖 Enhanced Documentation
- **Added**: Comprehensive README with badges, clear examples, and troubleshooting
- **Added**: Complete API reference documentation (API_REFERENCE.md)
- **Added**: Mermaid architecture diagrams showing how the system works
- **Added**: Multiple usage patterns from basic to advanced
- **Added**: Provider-specific setup instructions
- **Added**: Real-world use cases and examples

#### 🔧 Improved Examples
- **Updated**: basic_usage.py with multi-provider examples
- **Added**: multi_provider_example.py demonstrating fallback strategies
- **Added**: Error handling examples throughout
- **Added**: Cloud provider integration examples

### 🏗️ Infrastructure Improvements

#### ⚡ GitHub Actions Workflows
- **Improved**: CI workflow with better caching and parallel execution
- **Enhanced**: Release workflow with automatic changelog generation
- **Added**: Comprehensive code quality checks with auto-formatting
- **Added**: Security analysis with safety and bandit
- **Added**: Multi-Python version testing (3.8-3.12)
- **Added**: Manual release triggers for better control

#### 🧹 Project Cleanup
- **Removed**: Build artifacts and temporary files
- **Organized**: Clean project structure
- **Updated**: All workflows to use latest GitHub Actions
- **Added**: Better artifact management and retention policies

### 🔧 Code Quality

#### 🏛️ Architecture Improvements
- **Refactored**: LLM client architecture with proper base class
- **Added**: Abstract base class for LLM clients (`BaseLLMClient`)
- **Improved**: Configuration handling with proper validation
- **Added**: Factory pattern for LLM client creation

#### 🔒 Type Safety & Validation
- **Enhanced**: Pydantic models with better validation
- **Added**: Comprehensive type hints throughout codebase
- **Improved**: Configuration validation and error reporting
- **Added**: Runtime type checking for critical operations

### 🆕 New Features

#### 🎛️ Enhanced Configuration
- **Added**: `ConfigBuilder` fluent API for easy setup
- **Added**: Environment variable support for all configuration options
- **Added**: Pre-built profiles for different content types
- **Added**: Custom prompt and schema support

#### 📊 Better Data Handling
- **Added**: Confidence scoring for extraction quality
- **Added**: Smart caching with configurable policies
- **Added**: Batch processing capabilities
- **Added**: Content length limits and intelligent truncation

### 🐛 Bug Fixes
- **Fixed**: JSON parsing reliability with multiple fallback strategies
- **Fixed**: Content extraction edge cases
- **Fixed**: Memory leaks in browser management
- **Fixed**: Rate limiting implementation
- **Fixed**: URL validation and error handling

### 💔 Breaking Changes
- **BREAKING**: Exception handling - specific exception types instead of generic ones
- **BREAKING**: Configuration API - some legacy config methods deprecated
- **BREAKING**: LLM client initialization - now requires proper configuration

### 📦 Dependencies
- **Updated**: All dependencies to latest compatible versions
- **Added**: Optional dependencies for OpenAI and Anthropic
- **Improved**: Dependency management with proper optional extras

### 🔄 Migration Guide
For users upgrading from 1.0.x:

```python
# Old way (still works but deprecated)
from webextract import WebExtractor
extractor = WebExtractor()  # Used Ollama hardcoded

# New way (recommended)
from webextract import WebExtractor, ConfigBuilder
config = ConfigBuilder().with_ollama("llama3.2").build()
extractor = WebExtractor(config)

# Multi-provider support (now actually works!)
config = ConfigBuilder().with_openai("sk-...", "gpt-4o-mini").build()
extractor = WebExtractor(config)
```

## [1.0.4] - 2024-06-14

### Fixed
- Fixed JSON parsing errors in LLM responses
- Improved structured data validation and type checking
- Enhanced error handling with better fallback responses
- Resolved "Structured data missing required fields" warnings
- Fixed single quotes to double quotes conversion in JSON
- Added robust JSON string repair mechanisms

### Added
- Comprehensive example files for different use cases
- Enhanced LLM prompts for more consistent JSON output
- Better field type validation and normalization
- Improved debugging and logging for JSON parsing issues

### Changed
- Enhanced default prompt template for clearer JSON instructions
- Improved validation logic for structured data fields
- More robust fallback response generation

## [1.0.0] - 2024-12-13

### Added
- Initial release of LLM WebExtract
- Support for multiple LLM providers (Ollama, OpenAI, Anthropic)
- Modern web scraping with Playwright
- Flexible configuration system with builder pattern
- Pre-built configuration profiles for common use cases
- CLI interface with rich output formatting
- Structured data extraction with confidence scoring
- Comprehensive documentation and examples

### Package Features
- Cross-platform support (Windows, macOS, Linux)
- Python 3.8+ compatibility
- Comprehensive test suite
- GitHub Actions CI/CD pipeline
- Automatic PyPI publishing on releases
- Security scanning and code quality checks

### Author
- Created by Himasha Herath

---

**Note**: Version 1.1.2 represents a major stability and functionality improvement over previous versions. The multi-provider support that was advertised but broken in earlier versions now works correctly.
