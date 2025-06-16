#!/usr/bin/env python3
"""
Multi-Provider Example - WebExtract Library
===========================================

This example demonstrates how to use different LLM providers (Ollama, OpenAI, Anthropic)
with proper error handling and fallback strategies.

Requirements:
- At least one of: Ollama (local), OpenAI API key, or Anthropic API key
- Set environment variables or modify the API keys below
"""

import os
from webextract import (
    WebExtractor,
    ConfigBuilder,
    # Exception types for proper error handling
    ExtractionError,
    ScrapingError,
    LLMError,
    AuthenticationError,
    ConfigurationError,
)
from webextract.core.llm_factory import get_available_providers


def demo_provider_availability():
    """Check which LLM providers are available."""
    print("🔍 Checking Available Providers:")
    print("=" * 40)
    
    providers = get_available_providers()
    for name, info in providers.items():
        status = "✅ Available" if info["available"] else "❌ Not installed"
        print(f"   {name.title()}: {status}")
        print(f"      Requires: {info['requires']}")

    return providers


def try_ollama_extraction(url: str):
    """Try extraction with local Ollama."""
    print("\n🏠 Trying Ollama (Local):")
    print("-" * 30)
    
    try:
        config = ConfigBuilder().with_ollama("llama3.2").build()
        extractor = WebExtractor(config)
        
        # Test connection first
        if not extractor.test_connection():
            print("❌ Ollama connection failed")
            return None

        print("✅ Ollama connection successful")
        result = extractor.extract(url)
        
        if result and result.is_successful:
            print(f"✅ Extraction successful! Confidence: {result.confidence:.1%}")
            return result
        else:
            print("❌ Extraction failed")
            return None
            
    except LLMError as e:
        print(f"❌ LLM Error: {e}")
        print("💡 Try: ollama serve && ollama pull llama3.2")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def try_openai_extraction(url: str, api_key: str = None):
    """Try extraction with OpenAI."""
    print("\n☁️ Trying OpenAI:")
    print("-" * 20)
    
    # Get API key from environment or parameter
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ No OpenAI API key provided")
        print("💡 Set OPENAI_API_KEY environment variable or pass api_key parameter")
        return None

    try:
        config = ConfigBuilder().with_openai(api_key, "gpt-4o-mini").build()
        extractor = WebExtractor(config)
        
        print("✅ OpenAI configuration created")
        result = extractor.extract(url)
        
        if result and result.is_successful:
            print(f"✅ Extraction successful! Confidence: {result.confidence:.1%}")
            return result
        else:
            print("❌ Extraction failed")
            return None
            
    except AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        print("💡 Check your OpenAI API key")
        return None
    except LLMError as e:
        print(f"❌ LLM Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def try_anthropic_extraction(url: str, api_key: str = None):
    """Try extraction with Anthropic Claude."""
    print("\n🧠 Trying Anthropic:")
    print("-" * 22)
    
    # Get API key from environment or parameter
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ No Anthropic API key provided")
        print("💡 Set ANTHROPIC_API_KEY environment variable or pass api_key parameter")
        return None

    try:
        config = (
            ConfigBuilder()
            .with_anthropic(api_key, "claude-3-5-sonnet-20241022")
            .build()
        )
        extractor = WebExtractor(config)
        
        print("✅ Anthropic configuration created")
        result = extractor.extract(url)
        
        if result and result.is_successful:
            print(f"✅ Extraction successful! Confidence: {result.confidence:.1%}")
            return result
        else:
            print("❌ Extraction failed")
            return None
            
    except AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        print("💡 Check your Anthropic API key")
        return None
    except LLMError as e:
        print(f"❌ LLM Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def compare_results(results: dict):
    """Compare results from different providers."""
    if not results:
        print("\n❌ No successful extractions to compare")
        return

    print(f"\n📊 Comparison of {len(results)} Provider(s):")
    print("=" * 50)
    
    for provider, result in results.items():
        print(f"\n{provider.upper()}:")
        print(f"   Confidence: {result.confidence:.1%}")
        print(f"   Summary length: {len(result.get_summary() or '')} chars")
        print(f"   Topics count: {len(result.get_topics())}")
        
        # Show first topic as example
        topics = result.get_topics()
        if topics:
            print(f"   First topic: {topics[0]}")


def fallback_extraction_strategy(url: str):
    """Demonstrate a fallback strategy across providers."""
    print("\n🔄 Fallback Strategy Demo:")
    print("=" * 40)
    print("Trying providers in order: Ollama → OpenAI → Anthropic")
    
    # Strategy: Try local first, then cloud providers
    providers_to_try = [
        ("ollama", try_ollama_extraction),
        ("openai", try_openai_extraction),
        ("anthropic", try_anthropic_extraction),
    ]
    
    for provider_name, extraction_func in providers_to_try:
        print(f"\n🎯 Attempting {provider_name.title()}...")
        
        try:
            result = extraction_func(url)
            if result and result.is_successful:
                print(f"✅ Success with {provider_name.title()}!")
                print(f"📝 Summary: {result.get_summary()[:100]}...")
                return result
            else:
                print(f"❌ {provider_name.title()} failed, trying next...")

        except Exception as e:
            print(f"❌ {provider_name.title()} error: {e}")
            continue

    print("\n❌ All providers failed!")
    return None


def main():
    """Main demonstration function."""
    print("🚀 WebExtract - Multi-Provider Example")
    print("=" * 50)
    
    # Test URL
    url = "https://techcrunch.com/2024/01/15/ai-industry-trends/"
    print(f"\n🎯 Target URL: {url}")
    
    # Check provider availability
    providers = demo_provider_availability()
    
    # Try each available provider
    results = {}
    
    # Try Ollama if available
    if providers["ollama"]["available"]:
        result = try_ollama_extraction(url)
        if result:
            results["ollama"] = result
    
    # Try OpenAI if available (uncomment and add API key)
    if providers["openai"]["available"]:
        # result = try_openai_extraction(url, "sk-your-openai-key-here")
        # if result:
        #     results["openai"] = result
        print("\n☁️ OpenAI: Uncomment and add API key to test")
    
    # Try Anthropic if available (uncomment and add API key)  
    if providers["anthropic"]["available"]:
        # result = try_anthropic_extraction(url, "sk-ant-your-anthropic-key-here")
        # if result:
        #     results["anthropic"] = result
        print("\n🧠 Anthropic: Uncomment and add API key to test")
    
    # Compare results
    compare_results(results)
    
    # Demonstrate fallback strategy
    fallback_extraction_strategy(url)
    
    print("\n" + "=" * 50)
    print("💡 Tips:")
    print("   1. Set environment variables for API keys")
    print("   2. Use fallback strategies for reliability")
    print("   3. Monitor confidence scores for quality")
    print("   4. Handle specific exception types for better UX")


if __name__ == "__main__":
    main()