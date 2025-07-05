#!/usr/bin/env python3
"""
Batch Extraction Example - WebExtract Library
==============================================

This example demonstrates how to extract data from multiple URLs efficiently,
including error handling, progress tracking, and result aggregation.

Requirements:
- Ollama running locally
- gemma3:27b model (or modify to use your available model)
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

# Add the tests directory to the path for test data access
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

from example_test_data import TestDataCategories

from webextract import ConfigBuilder, ConfigProfiles, WebExtractor


def extract_single_url(extractor: WebExtractor, url: str, url_index: int) -> Dict[str, Any]:
    """Extract data from a single URL with error handling"""
    try:
        print(f"🔍 [{url_index}] Processing: {url}")
        start_time = time.time()

        result = extractor.extract(url)
        extraction_time = time.time() - start_time

        if result:
            return {
                "index": url_index,
                "url": url,
                "success": True,
                "extraction_time": extraction_time,
                "confidence": result.confidence,
                "title": result.content.title if result.content else "No title",
                "content_length": (len(result.content.main_content) if result.content else 0),
                "structured_data": result.structured_info,
                "error": None,
            }
        else:
            return {
                "index": url_index,
                "url": url,
                "success": False,
                "extraction_time": extraction_time,
                "error": "No result returned",
            }

    except Exception as e:
        return {
            "index": url_index,
            "url": url,
            "success": False,
            "extraction_time": 0,
            "error": str(e),
        }


def main():
    print("🚀 WebExtract - Batch Extraction Example")
    print("=" * 60)

    # Use reliable test URLs instead of hardcoded URLs that may break
    print("🔗 Using reliable test URLs from managed test data...")
    urls = TestDataCategories.get_batch_urls(3)  # Get 3 URLs for batch processing

    print("📋 Test URLs:")
    for i, url in enumerate(urls, 1):
        print(f"   {i}. {url}")

    print(f"📋 Processing {len(urls)} URLs...")

    # Method 1: Sequential processing
    print(f"\n1️⃣ Sequential Processing:")
    print("-" * 40)

    # Use fast extraction for batch processing
    extractor = WebExtractor(ConfigProfiles.fast_extraction())

    sequential_results = []
    total_start_time = time.time()

    for i, url in enumerate(urls, 1):
        result = extract_single_url(extractor, url, i)
        sequential_results.append(result)

        if result["success"]:
            title_preview = result["title"][:50]
            time_taken = result["extraction_time"]
            print(f"✅ [{i}] Success ({time_taken:.1f}s) - {title_preview}...")
        else:
            print(f"❌ [{i}] Failed: {result['error']}")

    total_sequential_time = time.time() - total_start_time
    successful_count = len([r for r in sequential_results if r["success"]])
    print(f"\n📊 Sequential Results: {successful_count}/{len(urls)} successful")
    print(f"⏱️  Total time: {total_sequential_time:.1f}s")

    # Method 2: Parallel processing (be careful with rate limits)
    print(f"\n2️⃣ Parallel Processing (Limited Concurrency):")
    print("-" * 40)

    parallel_results = []
    total_start_time = time.time()

    # Use ThreadPoolExecutor with limited workers to avoid overwhelming the server
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(extract_single_url, extractor, url, i): (url, i)
            for i, url in enumerate(urls, 1)
        }

        # Process completed tasks
        for future in as_completed(future_to_url):
            result = future.result()
            parallel_results.append(result)

            if result["success"]:
                idx = result["index"]
                time_taken = result["extraction_time"]
                title_preview = result["title"][:50]
                print(f"✅ [{idx}] Success ({time_taken:.1f}s) - {title_preview}...")
            else:
                print(f"❌ [{result['index']}] Failed: {result['error']}")

    total_parallel_time = time.time() - total_start_time
    successful_count = len([r for r in parallel_results if r["success"]])
    print(f"\n📊 Parallel Results: {successful_count}/{len(urls)} successful")
    print(f"⏱️  Total time: {total_parallel_time:.1f}s")
    speed_improvement = total_sequential_time / total_parallel_time
    print(f"🚀 Speed improvement: {speed_improvement:.1f}x faster")

    # Method 3: Batch analysis with aggregation
    print(f"\n3️⃣ Batch Analysis & Aggregation:")
    print("-" * 40)

    successful_results = [r for r in parallel_results if r["success"]]

    if successful_results:
        # Calculate statistics
        avg_confidence = sum(r["confidence"] for r in successful_results) / len(successful_results)
        total_content_len = sum(r["content_length"] for r in successful_results)
        avg_content_length = total_content_len / len(successful_results)
        total_content = sum(r["content_length"] for r in successful_results)

        print(f"📈 Batch Statistics:")
        success_count = len(successful_results)
        success_rate = success_count / len(urls) * 100
        print(f"   • Success rate: {success_count}/{len(urls)} ({success_rate:.1f}%)")
        print(f"   • Average confidence: {avg_confidence:.1%}")
        print(f"   • Average content length: {avg_content_length:.0f} chars")
        print(f"   • Total content processed: {total_content:,} chars")

        # Aggregate topics/themes across all articles
        all_topics = []
        all_organizations = []

        for result in successful_results:
            if result["structured_data"]:
                # Extract topics if available
                if "topics" in result["structured_data"]:
                    topics = result["structured_data"]["topics"]
                    if isinstance(topics, list):
                        all_topics.extend(topics)

                # Extract organizations if available
                if "organizations" in result["structured_data"]:
                    orgs = result["structured_data"]["organizations"]
                    if isinstance(orgs, list):
                        all_organizations.extend(orgs)

        if all_topics:
            # Count topic frequency
            topic_counts = {}
            for topic in all_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

            print(f"\n🏷️  Common Topics:")
            sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for topic, count in sorted_topics:
                print(f"   • {topic} ({count} mentions)")

        if all_organizations:
            # Count organization frequency
            org_counts = {}
            for org in all_organizations:
                org_counts[org] = org_counts.get(org, 0) + 1

            print(f"\n🏢 Organizations Mentioned:")
            sorted_orgs = sorted(org_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for org, count in sorted_orgs:
                print(f"   • {org} ({count} mentions)")

        # Save results to file (create examples directory if needed)
        examples_dir = Path("examples")
        examples_dir.mkdir(exist_ok=True)
        output_file = examples_dir / "batch_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(parallel_results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {output_file}")

    print(f"\n" + "=" * 60)
    print("💡 Batch Processing Tips:")
    print("   • Use fast_extraction() profile for better throughput")
    print("   • Limit concurrent requests to avoid rate limiting")
    print("   • Handle errors gracefully for production use")
    print("   • Consider saving intermediate results for large batches")
    print("   • Aggregate results for insights across multiple sources")


if __name__ == "__main__":
    main()
