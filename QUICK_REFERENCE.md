# 🚀 Quick Reference Card

## 📝 Common Commit Types

```bash
# Bug fixes (patch version)
git commit -m "fix(core): resolve memory leak in batch processing"
git commit -m "fix(config): handle missing model configuration gracefully"

# New features (minor version)
git commit -m "feat(llm): add Google Gemini Pro support"
git commit -m "feat(cli): add batch processing command"

# Documentation
git commit -m "docs: update installation guide for Windows"
git commit -m "docs(api): add examples for ConfigBuilder usage"

# Code improvements
git commit -m "refactor(core): simplify extraction pipeline"
git commit -m "perf(scraper): optimize content parsing for large pages"

# Tests
git commit -m "test(llm): add integration tests for OpenAI client"
git commit -m "test: increase coverage for configuration module"

# CI/Build
git commit -m "ci: add automated security scanning"
git commit -m "build: update dependencies to latest versions"
```

## 🏷️ Tagging Cheat Sheet

### Patch Release (Bug Fixes)
```bash
# Update version: 1.0.1 → 1.0.2
git tag -a v1.0.2 -m "v1.0.2: Bug fixes and improvements

Fixes:
- Fix WebExtractConfig AttributeError
- Resolve timeout issues with large pages
- Improve error handling for missing models"

git push origin v1.0.2
```

### Minor Release (New Features)
```bash
# Update version: 1.0.2 → 1.1.0
git tag -a v1.1.0 -m "v1.1.0: Add new features and improvements

Features:
- Google Gemini Pro integration
- Batch URL processing
- New social media extraction profiles
- Enhanced CLI with progress bars"

git push origin v1.1.0
```

### Major Release (Breaking Changes)
```bash
# Update version: 1.1.0 → 2.0.0
git tag -a v2.0.0 -m "v2.0.0: Major API redesign

BREAKING CHANGES:
- New async-first API design
- ConfigBuilder API completely redesigned
- Removed deprecated quick_extract function

See MIGRATION.md for upgrade guide"

git push origin v2.0.0
```

## 🔄 Common Workflows

### Feature Development
```bash
# 1. Create feature branch
git checkout -b feat/add-gemini-support

# 2. Make changes with proper commits
git commit -m "feat(llm): add Gemini client implementation"
git commit -m "test(llm): add unit tests for Gemini"
git commit -m "docs: update README with Gemini setup"

# 3. Push and create PR
git push origin feat/add-gemini-support
```

### Bug Fix
```bash
# 1. Create fix branch
git checkout -b fix/config-attribute-error

# 2. Fix the issue
git commit -m "fix(config): resolve WebExtractConfig AttributeError"

# 3. Add test to prevent regression
git commit -m "test(config): add test for WebExtractConfig compatibility"

# 4. Push and create PR
git push origin fix/config-attribute-error
```

### Release Process
```bash
# 1. Update version in webextract/__init__.py
# 2. Update CHANGELOG.md
# 3. Commit version bump
git commit -m "chore: bump version to 1.2.0"

# 4. Create and push tag
git tag -a v1.2.0 -m "v1.2.0: Feature release with Gemini support"
git push origin main
git push origin v1.2.0

# 5. GitHub Actions will automatically:
#    - Run tests
#    - Build package
#    - Publish to PyPI
#    - Create GitHub release
```

## 🛠️ Development Commands

```bash
# Setup
pip install -e ".[dev]"
pre-commit install

# Code quality
python -m black .                    # Format code
python -m isort .                    # Sort imports
python -m flake8 --config .flake8    # Lint code

# Testing
python -m pytest                     # Run all tests
python -m pytest --cov=webextract    # Run with coverage
python -m pytest -v tests/test_core.py  # Run specific test

# All checks (before commit)
python -m pytest && python -m black --check . && python -m isort --check-only . && python -m flake8 --config .flake8
```

## 📊 Version Decision Tree

```
Is this a breaking change?
├─ YES → Major version (2.0.0)
└─ NO
   ├─ New feature/functionality?
   │  ├─ YES → Minor version (1.1.0)
   │  └─ NO → Patch version (1.0.1)
   └─ Bug fix/documentation/refactor?
      └─ YES → Patch version (1.0.1)
```

## 🎯 Commit Message Examples by Scenario

### Adding New LLM Provider
```bash
git commit -m "feat(llm): add support for Google Gemini Pro

- Implement GeminiClient with streaming support
- Add configuration options for Gemini models
- Include rate limiting and error handling
- Update ConfigBuilder with .with_gemini() method"
```

### Fixing Configuration Issue
```bash
git commit -m "fix(config): resolve WebExtractConfig AttributeError

- Update DataExtractor to handle both config types
- Add proper type checking for configuration objects
- Maintain backward compatibility with ExtractionConfig
- Add comprehensive tests for configuration scenarios"
```

### Performance Improvement
```bash
git commit -m "perf(scraper): optimize content extraction for large pages

- Implement streaming content processing
- Reduce memory usage by 40% for pages >1MB
- Add content chunking for better LLM processing
- Benchmark shows 2x faster processing on large sites"
```

### Documentation Update
```bash
git commit -m "docs: add comprehensive troubleshooting guide

- Add common error solutions
- Include Ollama setup instructions
- Add model compatibility matrix
- Provide debugging tips for each LLM provider"
```

---

💡 **Pro Tip**: Use `git log --oneline --graph` to visualize your commit history and ensure it tells a clear story!

📖 **Need more details?** Check the full [Development Guide](DEVELOPMENT.md) for comprehensive information. 