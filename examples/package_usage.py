#!/usr/bin/env python3
"""Comprehensive usage examples for LLM WebExtract package"""

import asyncio

import webextract
from webextract import Extractor


async def example_basic_url_extraction():
    """Basic URL extraction example"""
    print("🔹 Basic Example")
    print("-" * 20)

    extractor = Extractor()
    result = await extractor.extract(
        "https://example.com", {"summary": "Brief summary of the page"}
    )
    print(f"Summary: {result.get('summary', 'N/A')}")


async def example_batch_processing():
    """Batch processing example"""
    print("\n🔹 Batch Processing")
    print("-" * 18)

    urls = ["https://httpbin.org/html", "https://example.com"]
    schema = {"title": "Page title", "description": "Brief description"}

    extractor = Extractor()
    results = await extractor.extract_batch(urls, schema)

    print(f"Processed {len(results)} URLs")
    for i, result in enumerate(results):
        print(f"URL {i+1}: {result.get('title', 'N/A')}")


async def example_custom_schema():
    """Custom schema example"""
    print("\n🔹 Custom Schema")
    print("-" * 16)

    schema = {
        "title": "Page title",
        "main_topic": "What is the main topic discussed?",
        "key_points": "List 3 key points from the content",
    }

    extractor = Extractor()
    result = await extractor.extract("https://example.com", schema)

    print(f"Title: {result.get('title', 'N/A')}")
    print(f"Topic: {result.get('main_topic', 'N/A')}")


async def example_chunked_extraction():
    """Chunked extraction example for large content"""
    print("\n🔹 Chunked Extraction")
    print("-" * 20)

    extractor = Extractor()
    result = await extractor.extract(
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        {
            "summary": "Brief summary of AI",
            "history": "Brief history of AI development",
        },
    )

    print(f"AI Summary: {result.get('summary', 'N/A')}")
    print(f"History: {result.get('history', 'N/A')}")


def basic_sync_example():
    """Basic sync example using the legacy API"""
    print("\n🔹 Legacy Sync Example")
    print("-" * 20)

    try:
        result = webextract.quick_extract("https://example.com")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Note: Legacy API may not be available: {e}")


async def main():
    """Run all examples"""
    print("🤖 LLM WebExtract - Package Usage Examples")
    print("=" * 50)

    try:
        await example_basic_url_extraction()
        await example_batch_processing()
        await example_custom_schema()
        await example_chunked_extraction()
        basic_sync_example()

        print("\n✅ All examples completed!")

    except Exception as e:
        print(f"❌ Example failed: {e}")
        print("Make sure you have a compatible LLM provider configured")


if __name__ == "__main__":
    asyncio.run(main())
