#!/usr/bin/env python3
"""
Basic Usage Example - WebExtract Library
==========================================

This example shows the simplest way to extract structured data from web pages.
Perfect for getting started with the library.

Requirements:
- Ollama running locally
- gemma3:27b model (or modify to use your available model)
"""

from webextract import WebExtractor, ConfigProfiles


def main():
    print("🚀 WebExtract - Basic Usage Example")
    print("=" * 50)

    # Method 1: Use a pre-configured profile (easiest)
    print("\n📰 Using News Scraping Profile:")
    news_extractor = WebExtractor(ConfigProfiles.news_scraping())

    # Test URL
    url = "https://dev.to/nodeshiftcloud/claude-4-opus-vs-sonnet-benchmarks-and-dev-workflow-with-claude-code-11fa"

    try:
        print(f"🔍 Extracting from: {url}")
        result = news_extractor.extract(url)

        if result:
            print("✅ Extraction successful!")
            print(f"🎯 Confidence: {result.confidence:.1%}")

            # Basic information
            print(f"\n📄 Basic Info:")
            print(f"   Title: {result.content.title}")
            print(f"   Content length: {len(result.content.main_content)} characters")

            # LLM extracted data
            if result.structured_info:
                info = result.structured_info

                if "summary" in info:
                    print(f"\n📝 Summary:")
                    print(f"   {info['summary']}")

                if "organizations" in info and info["organizations"]:
                    print(f"\n🏢 Organizations: {', '.join(info['organizations'])}")

        else:
            print("❌ Extraction failed")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure Ollama is running: ollama serve")
        print("   2. Check available models: ollama list")
        print("   3. Pull required model: ollama pull gemma3:27b")

    # Method 2: Simple default configuration
    print(f"\n" + "=" * 50)
    print("🔧 Using Default Configuration:")

    default_extractor = WebExtractor()  # Uses all defaults

    try:
        result = default_extractor.extract(url)
        if result:
            print("✅ Default extraction successful!")
            print(f"🎯 Confidence: {result.confidence:.1%}")

            if result.structured_info and "summary" in result.structured_info:
                summary = (
                    result.structured_info["summary"][:150] + "..."
                    if len(result.structured_info["summary"]) > 150
                    else result.structured_info["summary"]
                )
                print(f"📝 Summary: {summary}")
        else:
            print("❌ Default extraction failed")

    except Exception as e:
        print(f"❌ Error with default config: {e}")


if __name__ == "__main__":
    main()
