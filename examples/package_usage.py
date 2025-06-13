#!/usr/bin/env python3
"""Comprehensive usage examples for LLM WebExtract package"""

import webextract
import json

def basic_example():
    """Basic extraction example"""
    print("🔹 Basic Example")
    print("-" * 20)
    
    result = webextract.quick_extract("https://example.com")
    print(f"Summary: {result.summary if hasattr(result, 'summary') else 'N/A'}")
    print(f"Topics: {result.structured_info.get('topics', 'N/A')}")

def custom_config_example():
    """Custom configuration example"""
    print("\n🔹 Custom Configuration")
    print("-" * 25)
    
    config = (webextract.ConfigBuilder()
              .with_model("llama3:8b")
              .with_timeout(60)
              .with_custom_prompt("Extract key facts and figures")
              .build())
    
    extractor = webextract.WebExtractor(config)
    result = extractor.extract("https://news.ycombinator.com")
    
    print(f"Title: {result.content.title}")
    print(f"Confidence: {result.confidence}")

def profile_examples():
    """Pre-built profile examples"""
    print("\n🔹 Profile Examples")
    print("-" * 18)
    
    # News scraping
    news_extractor = webextract.WebExtractor(webextract.ConfigProfiles.news_scraping())
    result = news_extractor.extract("https://techcrunch.com")
    print(f"News analysis: {result.structured_info.get('category', 'N/A')}")
    
    # Research papers
    research_extractor = webextract.WebExtractor(webextract.ConfigProfiles.research_papers())
    print("Research extractor ready")

def cloud_provider_examples():
    """Cloud LLM provider examples"""
    print("\n🔹 Cloud Providers")
    print("-" * 17)
    
    # Note: These require API keys
    print("OpenAI example (requires API key):")
    print("result = webextract.extract_with_openai('https://example.com', 'sk-...')")
    
    print("Anthropic example (requires API key):")
    print("result = webextract.extract_with_anthropic('https://example.com', 'sk-ant-...')")

def batch_processing_example():
    """Batch processing example"""
    print("\n🔹 Batch Processing")
    print("-" * 18)
    
    urls = [
        "https://httpbin.org/html",
        "https://example.com"
    ]
    
    extractor = webextract.WebExtractor()
    results = []
    
    for url in urls:
        try:
            result = extractor.extract(url)
            results.append({
                'url': url,
                'title': result.content.title,
                'success': True
            })
        except Exception as e:
            results.append({
                'url': url,
                'error': str(e),
                'success': False
            })
    
    print(f"Processed {len(results)} URLs")
    success_count = sum(1 for r in results if r['success'])
    print(f"Success rate: {success_count}/{len(results)}")

def error_handling_example():
    """Error handling example"""
    print("\n🔹 Error Handling")
    print("-" * 16)
    
    extractor = webextract.WebExtractor()
    
    try:
        result = extractor.extract("https://invalid-url-example")
    except Exception as e:
        print(f"Handled error: {type(e).__name__}")

def main():
    """Run all examples"""
    print("🤖 LLM WebExtract - Package Usage Examples")
    print("=" * 50)
    
    try:
        basic_example()
        custom_config_example()
        profile_examples()
        cloud_provider_examples()
        batch_processing_example()
        error_handling_example()
        
        print("\n✅ All examples completed!")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        print("Make sure Ollama is running with a compatible model")

if __name__ == "__main__":
    main() 