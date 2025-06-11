#!/usr/bin/env python3
"""
Basic usage example for LLM Web Scraper
"""

import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extractor import DataExtractor
from src.models import ExtractionConfig
import json


def main():
    """Run basic extraction examples."""
    
    print("🚀 LLM Web Scraper - Basic Usage Example")
    print("=" * 50)
    
    # Example URLs to try
    test_urls = [
        "https://httpbin.org/html",  # Simple test page
        "https://example.com",       # Very basic page
    ]
    
    # Create extraction config
    config = ExtractionConfig(
        model_name="gemma3:27b",
        max_content_length=3000,
        custom_prompt="Analyze this webpage and extract key information in a structured format."
    )
    
    # Initialize extractor
    extractor = DataExtractor(config)
    
    # Test connection
    print("\n🔍 Testing Ollama connection...")
    if not extractor.test_connection():
        print("❌ Connection failed. Make sure Ollama is running with gemma3:27b model.")
        return
    
    # Process each URL
    for i, url in enumerate(test_urls, 1):
        print(f"\n📄 Example {i}: {url}")
        print("-" * 30)
        
        try:
            result = extractor.extract(url)
            
            if result:
                print(f"✅ Success! Confidence: {result.confidence:.2f}")
                print(f"📝 Title: {result.content.title}")
                print(f"📊 Content length: {len(result.content.main_content)} chars")
                print(f"🔗 Links found: {len(result.content.links)}")
                
                # Show some structured data
                if result.structured_info:
                    print("\n🧠 LLM Analysis (sample):")
                    for key, value in list(result.structured_info.items())[:3]:
                        print(f"  {key}: {str(value)[:100]}...")
                
                # Save result
                output_file = f"examples/output_example_{i}.json"
                with open(output_file, 'w') as f:
                    json.dump(result.model_dump(), f, indent=2)
                print(f"💾 Saved to: {output_file}")
                
            else:
                print("❌ Extraction failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Basic usage examples completed!")
    print("Check the examples/ directory for output files.")


if __name__ == "__main__":
    main() 