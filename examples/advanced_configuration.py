#!/usr/bin/env python3
"""
Advanced Configuration Example - WebExtract Library
===================================================

This example demonstrates all the advanced configuration options available
in the WebExtract library, including custom prompts, different models,
timeouts, and content limits.

Requirements:
- Ollama running locally
- Multiple models available (gemma3:27b, gemma3:8b, etc.)
"""

import time

from webextract import ConfigBuilder, WebExtractor


def main():
    print("⚡ WebExtract - Advanced Configuration Example")
    print("=" * 60)

    # Test URL
    url = "https://dev.to/nodeshiftcloud/claude-4-opus-vs-sonnet-benchmarks-and-dev-workflow-with-claude-code-11fa"

    # Configuration 1: Custom prompt for specific data extraction
    print("\n1️⃣ Custom Prompt Configuration:")
    print("-" * 40)

    custom_prompt_extractor = WebExtractor(
        ConfigBuilder()
        .with_model("gemma3:27b")
        .with_content_limit(8000)
        .with_timeout(60)
        .with_custom_prompt(
            """
            Analyze this technical article and extract:

            1. TECHNICAL_DETAILS: Key technical concepts, tools, or technologies mentioned
            2. BENCHMARKS: Any performance metrics, scores, or comparisons
            3. COMPANIES: Organizations or companies mentioned
            4. TOOLS: Software tools, platforms, or services discussed
            5. SUMMARY: 2-sentence executive summary
            6. TARGET_AUDIENCE: Who this article is written for

            Return as JSON with these exact field names.
            Make sure all fields are present, use empty arrays/strings if no data found.
            """
        )
        .build()
    )

    try:
        start_time = time.time()
        result = custom_prompt_extractor.extract(url)
        extraction_time = time.time() - start_time

        if result:
            print(f"✅ Success in {extraction_time:.1f}s")
            print(f"🎯 Confidence: {result.confidence:.1%}")

            info = result.structured_info

            if "TECHNICAL_DETAILS" in info and info["TECHNICAL_DETAILS"]:
                print(f"🔧 Technical Details: {info['TECHNICAL_DETAILS']}")

            if "BENCHMARKS" in info and info["BENCHMARKS"]:
                print(f"📊 Benchmarks: {info['BENCHMARKS']}")

            if "COMPANIES" in info and info["COMPANIES"]:
                print(
                    f"🏢 Companies: {', '.join(info['COMPANIES']) if isinstance(info['COMPANIES'], list) else info['COMPANIES']}"
                )

            if "SUMMARY" in info:
                print(f"📝 Summary: {info['SUMMARY']}")

    except Exception as e:
        print(f"❌ Custom prompt extraction failed: {e}")

    # Configuration 2: Speed-optimized configuration
    print(f"\n2️⃣ Speed-Optimized Configuration:")
    print("-" * 40)

    speed_extractor = WebExtractor(
        ConfigBuilder()
        .with_model("gemma3:8b")  # Smaller, faster model
        .with_content_limit(3000)  # Less content to process
        .with_timeout(20)  # Quick timeout
        .build()
    )

    try:
        start_time = time.time()
        result = speed_extractor.extract(url)
        extraction_time = time.time() - start_time

        if result:
            print(f"⚡ Fast extraction completed in {extraction_time:.1f}s")
            print(f"🎯 Confidence: {result.confidence:.1%}")

            if result.structured_info and "summary" in result.structured_info:
                summary = (
                    result.structured_info["summary"][:100] + "..."
                    if len(result.structured_info["summary"]) > 100
                    else result.structured_info["summary"]
                )
                print(f"📝 Quick summary: {summary}")

    except Exception as e:
        print(f"❌ Speed extraction failed: {e}")

    # Configuration 3: High-accuracy configuration
    print(f"\n3️⃣ High-Accuracy Configuration:")
    print("-" * 40)

    accuracy_extractor = WebExtractor(
        ConfigBuilder()
        .with_model("gemma3:27b")  # Larger model for better accuracy
        .with_content_limit(15000)  # More content for context
        .with_timeout(90)  # Longer timeout for thorough processing
        .with_custom_prompt(
            """
            Perform a comprehensive analysis of this content. Extract:

            - MAIN_TOPIC: Primary subject matter
            - KEY_POINTS: List of 3-5 most important points
            - TECHNICAL_TERMS: Technical vocabulary or jargon used
            - AUDIENCE_LEVEL: Beginner, Intermediate, or Advanced
            - CONTENT_TYPE: Tutorial, News, Review, Analysis, etc.
            - ACTIONABLE_ITEMS: What readers should do after reading
            - RELATED_TOPICS: What else readers might be interested in

            Be thorough and accurate. Return valid JSON.
            """
        )
        .build()
    )

    try:
        start_time = time.time()
        result = accuracy_extractor.extract(url)
        extraction_time = time.time() - start_time

        if result:
            print(f"🎯 Detailed analysis completed in {extraction_time:.1f}s")
            print(f"🏆 Confidence: {result.confidence:.1%}")

            info = result.structured_info

            for field in ["MAIN_TOPIC", "AUDIENCE_LEVEL", "CONTENT_TYPE"]:
                if field in info:
                    print(f"📋 {field.replace('_', ' ').title()}: {info[field]}")

            if "KEY_POINTS" in info and info["KEY_POINTS"]:
                print(f"💡 Key Points:")
                for i, point in enumerate(info["KEY_POINTS"][:3], 1):
                    print(f"   {i}. {point}")

    except Exception as e:
        print(f"❌ High-accuracy extraction failed: {e}")

    # Configuration 4: Minimal configuration (defaults)
    print(f"\n4️⃣ Minimal Configuration (All Defaults):")
    print("-" * 40)

    minimal_extractor = WebExtractor()  # Uses all default settings

    try:
        start_time = time.time()
        result = minimal_extractor.extract(url)
        extraction_time = time.time() - start_time

        if result:
            print(f"✅ Default extraction in {extraction_time:.1f}s")
            print(f"🎯 Confidence: {result.confidence:.1%}")
            print(
                f"📊 Available fields: {list(result.structured_info.keys()) if result.structured_info else 'None'}"
            )

    except Exception as e:
        print(f"❌ Minimal extraction failed: {e}")

    print(f"\n" + "=" * 60)
    print("🔧 Configuration Summary:")
    print("   • Custom prompts: Tailor extraction to your specific needs")
    print("   • Model selection: Balance speed vs accuracy")
    print("   • Content limits: Control processing time and costs")
    print("   • Timeouts: Prevent hanging on slow operations")
    print("   • Default config: Quick start with sensible defaults")


if __name__ == "__main__":
    main()
