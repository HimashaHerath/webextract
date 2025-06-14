# Changelog

All notable changes to LLM WebExtract will be documented in this file.

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

## [Unreleased]

### Planned
- Add support for more LLM providers
- Implement batch processing capabilities
- Add configuration file support (YAML/JSON)
- Improve error handling and retry logic
- Add more extraction profiles
- Performance optimizations 