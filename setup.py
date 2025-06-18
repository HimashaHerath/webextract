"""Setup script for WebExtract package."""

from pathlib import Path

from setuptools import find_packages, setup

# Read README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements file
requirements = []
try:
    with open("requirements.txt", "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = [
        "playwright>=1.40.0",
        "beautifulsoup4>=4.12.0",
        "pydantic>=2.0.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "ollama>=0.1.7",
        "lxml>=4.9.0",
    ]

setup(
    name="llm-webextract",
    version="1.2.2",
    author="Himasha Herath",
    author_email="himasha626@gmail.com",
    description="AI-powered web content extraction with Large Language Models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HimashaHerath/webextract",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio",
            "black",
            "flake8",
            "mypy",
            "isort",
            "pylint",
            "safety",
            "bandit",
        ],
        "openai": ["openai>=1.0.0"],
        "anthropic": ["anthropic>=0.8.0"],
        "all": [
            "openai>=1.0.0",
            "anthropic>=0.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "llm-webextract=webextract.cli:main",
        ],
    },
    include_package_data=True,
    project_urls={
        "Bug Reports": "https://github.com/HimashaHerath/webextract/issues",
        "Source": "https://github.com/HimashaHerath/webextract",
    },
    keywords="web scraping, llm, ai, content extraction, playwright, ollama, openai, anthropic",
)
