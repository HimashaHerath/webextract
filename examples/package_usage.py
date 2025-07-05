#!/usr/bin/env python3
"""Comprehensive usage examples for LLM WebExtract package"""

import asyncio
import os
import sys
from pathlib import Path

# Add the tests directory to the path for test data access
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

from example_test_data import TestDataCategories

import webextract
from webextract import Extractor


async def example_basic_url_extraction():
    """Basic URL extraction example"""
    print("🔹 Basic Example")
    print("-" * 20)

    # Use reliable test URL instead of hardcoded URL
    test_urls = TestDataCategories.get_content_types()
    extractor = Extractor()
    result = await extractor.extract(test_urls["news"], {"summary": "Brief summary of the page"})
    print(f"Summary: {result.get('summary', 'N/A')}")


async def example_batch_processing():
    """Batch processing example"""
    print("\n🔹 Batch Processing")
    print("-" * 18)

    # Use reliable test URLs for batch processing
    urls = TestDataCategories.get_batch_urls(2)
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

    # Use reliable test URL
    test_urls = TestDataCategories.get_content_types()
    extractor = Extractor()
    result = await extractor.extract(test_urls["blog"], schema)

    print(f"Title: {result.get('title', 'N/A')}")
    print(f"Topic: {result.get('main_topic', 'N/A')}")


async def example_chunked_extraction():
    """Chunked extraction example for large content"""
    print("\n🔹 Chunked Extraction")
    print("-" * 20)

    # Use reliable test URL for large content testing
    test_urls = TestDataCategories.get_edge_cases()
    extractor = Extractor()
    result = await extractor.extract(
        test_urls["large_content"],
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
        # Use reliable test URL
        test_urls = TestDataCategories.get_content_types()
        result = webextract.quick_extract(test_urls["news"])
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
