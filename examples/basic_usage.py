#!/usr/bin/env python3
"""
Basic Usage Example - WebExtract Library
==========================================

This example shows the simplest way to extract structured data from web pages.
Perfect for getting started with the library.

Requirements:
- Ollama running locally with llama3.2 model (or modify to use your available model)
- OR OpenAI/Anthropic API key
"""

import webextract
from webextract import ConfigBuilder, ConfigProfiles, WebExtractor


def main():
    print("🚀 WebExtract - Basic Usage Example")
    print("=" * 50)

    # Method 1: Quick extraction (simplest)
    print("\n⚡ Quick Extraction:")
    url = "https://techcrunch.com/2024/01/15/ai-industry-trends/"

    try:
        print(f"🔍 Extracting from: {url}")
        result = webextract.quick_extract(url)  # Uses Ollama by default

        if result and result.is_successful:
            print("✅ Quick extraction successful!")
            print(f"🎯 Confidence: {result.confidence:.1%}")
            print(f"📝 Summary: {result.get_summary()[:150]}...")
            print(f"🏷️ Topics: {', '.join(result.get_topics()[:3])}")
        else:
            print("❌ Quick extraction failed")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure Ollama is running: ollama serve")
        print("   2. Check available models: ollama list")
        print("   3. Pull required model: ollama pull llama3.2")

    # Method 2: Using pre-configured profiles
    print(f"\n" + "=" * 50)
    print("📰 Using News Scraping Profile:")
    try:
        news_extractor = WebExtractor(ConfigProfiles.news_scraping())
        result = news_extractor.extract(url)

        if result and result.is_successful:
            print("✅ Profile extraction successful!")
            print(f"🎯 Confidence: {result.confidence:.1%}")

            # Access structured information
            info = result.structured_info
            if isinstance(info, dict):
                print(f"\n📄 Article Details:")
                print(f"   Title: {result.content.title}")
                print(f"   Category: {info.get('category', 'Unknown')}")
                print(f"   Sentiment: {info.get('sentiment', 'neutral')}")

                # Entities
                entities = info.get("entities", {})
                if entities.get("organizations"):
                    orgs = entities["organizations"][:3]
                    print(f"   Organizations: {', '.join(orgs)}")

        else:
            print("❌ Profile extraction failed")

    except Exception as e:
        print(f"❌ Error with profile: {e}")

    # Method 3: Custom configuration
    print(f"\n" + "=" * 50)
    print("🔧 Using Custom Configuration:")

    try:
        # Build custom configuration
        config = (
            ConfigBuilder()
            .with_ollama("llama3.2")  # Specify model
            .with_timeout(45)  # Custom timeout
            .with_content_limit(8000)  # Content limit
            .with_temperature(0.1)  # Low temperature for consistency
            .build()
        )

        custom_extractor = WebExtractor(config)
        result = custom_extractor.extract(url)

        if result and result.is_successful:
            print("✅ Custom extraction successful!")
            print(f"🎯 Confidence: {result.confidence:.1%}")

            # Show confidence and quality indicators
            print(f"\n📊 Quality Metrics:")
            print(f"   High confidence: {result.has_high_confidence}")
            print(f"   Content length: {result.content.content_length:,} chars")
            print(f"   Links found: {len(result.content.links)}")

        else:
            print("❌ Custom extraction failed")

    except Exception as e:
        print(f"❌ Error with custom config: {e}")

    # Method 4: Cloud provider example (commented out - requires API key)
    print(f"\n" + "=" * 50)
    print("☁️ Cloud Provider Examples (commented out):")
    print(
        """
    # OpenAI Example:
    # result = webextract.extract_with_openai(
    #     url,
    #     api_key="sk-your-openai-key",
    #     model="gpt-4o-mini"
    # )

    # Anthropic Example:
    # result = webextract.extract_with_anthropic(
    #     url,
    #     api_key="sk-ant-your-anthropic-key",
    #     model="claude-3-5-sonnet-20241022"
    # )
    """
    )


if __name__ == "__main__":
    main()
