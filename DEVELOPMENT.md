# 🛠️ Development Guide

This guide covers development practices, commit conventions, versioning, and release processes for the LLM WebExtract project.

## 📝 Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification for consistent and meaningful commit messages.

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat: add support for Claude 3.5 Sonnet model` |
| `fix` | Bug fix | `fix: resolve WebExtractConfig AttributeError` |
| `docs` | Documentation changes | `docs: update installation instructions` |
| `style` | Code style changes (formatting, etc.) | `style: apply black formatting to core modules` |
| `refactor` | Code refactoring | `refactor: simplify configuration builder pattern` |
| `perf` | Performance improvements | `perf: optimize content extraction for large pages` |
| `test` | Adding or updating tests | `test: add integration tests for OpenAI provider` |
| `build` | Build system or dependencies | `build: update playwright to v1.40.0` |
| `ci` | CI/CD changes | `ci: add automated security scanning` |
| `chore` | Maintenance tasks | `chore: update pre-commit hooks` |
| `revert` | Revert previous commit | `revert: revert "feat: experimental batch processing"` |

### Scope Examples
- `core`: Core extraction logic
- `config`: Configuration system
- `cli`: Command line interface
- `llm`: LLM client implementations
- `scraper`: Web scraping functionality
- `models`: Data models and schemas
- `deps`: Dependencies

### Examples

**Good commit messages:**
```bash
feat(llm): add support for Anthropic Claude 3.5 Sonnet
fix(core): resolve memory leak in batch processing
docs: add troubleshooting section to README
ci: add automated PyPI publishing workflow
test(config): add unit tests for ConfigBuilder
```

**Bad commit messages:**
```bash
fix bug          # Too vague
Update README    # Missing type
WIP             # Not descriptive
asdf            # Meaningless
```

## 🏷️ Versioning and Tagging Strategy

We use [Semantic Versioning (SemVer)](https://semver.org/) for version numbers: `MAJOR.MINOR.PATCH`

### Version Types

#### MAJOR (X.0.0)
- Breaking changes that require user code modifications
- API changes that break backward compatibility
- Major architectural changes

**Examples:**
- Removing deprecated methods
- Changing function signatures
- Restructuring configuration format

```bash
# Example: v2.0.0
git tag -a v2.0.0 -m "v2.0.0: Major API redesign with breaking changes

BREAKING CHANGES:
- ConfigBuilder API completely redesigned
- WebExtractor constructor signature changed
- Removed deprecated quick_extract function

Migration guide available in MIGRATION.md"
```

#### MINOR (x.Y.0)
- New features that maintain backward compatibility
- New LLM provider support
- New configuration options
- Performance improvements

**Examples:**
- Adding new LLM providers
- New extraction profiles
- Additional CLI commands

```bash
# Example: v1.2.0
git tag -a v1.2.0 -m "v1.2.0: Add Google Gemini support and batch processing

Features:
- Add Google Gemini Pro integration
- Implement batch URL processing
- Add new ConfigProfiles for social media extraction
- Improve error handling and retry logic"
```

#### PATCH (x.y.Z)
- Bug fixes
- Security patches
- Documentation updates
- Minor improvements

**Examples:**
- Fixing crashes or errors
- Security vulnerabilities
- Documentation corrections

```bash
# Example: v1.1.3
git tag -a v1.1.3 -m "v1.1.3: Fix WebExtractConfig AttributeError

Fixes:
- Resolve configuration compatibility issue
- Fix model_name attribute access
- Improve error messages for missing models"
```

## 🚀 Release Workflow

### 1. Development Process

```bash
# Create feature branch
git checkout -b feat/add-gemini-support

# Make changes with proper commits
git commit -m "feat(llm): add Google Gemini client implementation"
git commit -m "test(llm): add unit tests for Gemini integration"
git commit -m "docs: update README with Gemini setup instructions"

# Push and create PR
git push origin feat/add-gemini-support
```

### 2. Pre-Release Checklist

Before creating a release:

- [ ] All tests pass (`python -m pytest`)
- [ ] Code quality checks pass (`flake8`, `black`, `isort`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Version number is bumped in `webextract/__init__.py`
- [ ] All dependencies are up to date

### 3. Creating Releases

#### For Bug Fixes (Patch Release)
```bash
# Update version in code
# webextract/__init__.py: __version__ = "1.1.4"

# Commit version bump
git add webextract/__init__.py
git commit -m "chore: bump version to 1.1.4"

# Create and push tag
git tag -a v1.1.4 -m "v1.1.4: Critical bug fixes

Fixes:
- Fix memory leak in batch processing
- Resolve timeout issues with large pages
- Fix CLI argument parsing edge case"

git push origin main
git push origin v1.1.4
```

#### For New Features (Minor Release)
```bash
# Update version in code
# webextract/__init__.py: __version__ = "1.2.0"

# Commit version bump
git add webextract/__init__.py CHANGELOG.md
git commit -m "chore: bump version to 1.2.0"

# Create and push tag
git tag -a v1.2.0 -m "v1.2.0: Add Gemini support and enhanced profiles

Features:
- Google Gemini Pro integration
- New social media extraction profiles
- Improved batch processing performance
- Enhanced error reporting

Breaking Changes: None
Migration Required: No"

git push origin main
git push origin v1.2.0
```

#### For Breaking Changes (Major Release)
```bash
# Update version in code
# webextract/__init__.py: __version__ = "2.0.0"

# Create migration guide
# docs/MIGRATION_v2.md

# Commit version bump and migration guide
git add webextract/__init__.py CHANGELOG.md docs/MIGRATION_v2.md
git commit -m "chore: bump version to 2.0.0"

# Create and push tag
git tag -a v2.0.0 -m "v2.0.0: Major API redesign

BREAKING CHANGES:
- Complete ConfigBuilder API redesign
- WebExtractor constructor signature changed
- Removed deprecated methods: quick_extract, extract_with_*
- New async-first API design

Migration:
- See docs/MIGRATION_v2.md for detailed migration guide
- Update all WebExtractor instantiations
- Replace quick_extract with new async API

New Features:
- Async-first design for better performance
- Streaming extraction for large content
- Plugin system for custom extractors"

git push origin main
git push origin v2.0.0
```

## 🔄 Automated Release Process

Our GitHub Actions workflow automatically:

1. **On Push to Main**: Runs tests and quality checks
2. **On Tag Push (v*)**: 
   - Runs full test suite
   - Builds package
   - Publishes to PyPI
   - Creates GitHub release with changelog
   - Updates documentation

### Triggering Automated Release

```bash
# This will trigger the full release pipeline
git push origin v1.2.0
```

## 📋 Development Commands

### Setup Development Environment
```bash
# Clone and setup
git clone https://github.com/yourusername/llm-scraper.git
cd llm-scraper

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Code Quality Checks
```bash
# Format code
python -m black .
python -m isort .

# Lint code
python -m flake8 --config .flake8

# Type checking
python -m mypy webextract/

# Security scan
python -m bandit -r webextract/

# Run all checks
python -m pytest && python -m black --check . && python -m isort --check-only . && python -m flake8 --config .flake8
```

### Testing
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=webextract --cov-report=html

# Run specific test file
python -m pytest tests/test_extractor.py

# Run integration tests (requires Ollama)
python -m pytest tests/integration/
```

## 🏗️ Branch Strategy

### Main Branches
- `main`: Production-ready code, protected branch
- `develop`: Integration branch for features (if using GitFlow)

### Feature Branches
- `feat/feature-name`: New features
- `fix/bug-description`: Bug fixes
- `docs/update-description`: Documentation updates
- `refactor/component-name`: Code refactoring

### Branch Naming Examples
```bash
feat/add-gemini-support
fix/config-attribute-error
docs/update-installation-guide
refactor/simplify-llm-clients
ci/add-security-scanning
test/integration-test-suite
```

## 🔍 Code Review Guidelines

### Before Submitting PR
- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] No sensitive information in code
- [ ] Performance impact considered

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
```

## 📚 Additional Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

---

**Questions about development practices?** Open an issue or discussion - we're here to help! 🚀 