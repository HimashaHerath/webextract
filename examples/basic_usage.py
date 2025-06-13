#!/usr/bin/env python3
"""Basic usage example for LLM WebExtract"""

import webextract
import json

def main():
    print("🤖 LLM WebExtract - Basic Usage Example")
    print("=" * 50)
    
    test_urls = [
        "https://httpbin.org/html",
        "https://example.com",
    ]
    
    config = webextract.ConfigBuilder().with_model("gemma3:27b").build()
    extractor = webextract.WebExtractor(config)
    
    print("\n🔍 Testing connection...")
    if not extractor.test_connection():
        print("❌ Connection failed. Make sure Ollama is running.")
        return
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📄 Example {i}: {url}")
        print("-" * 30)
        
        try:
            result = extractor.extract(url)
            
            if result:
                print(f"✅ Success! Confidence: {result.confidence:.2f}")
                print(f"📝 Title: {result.content.title}")
                print(f"📊 Content length: {len(result.content.main_content)} chars")
                
                if result.structured_info:
                    print("\n🧠 LLM Analysis (sample):")
                    for key, value in list(result.structured_info.items())[:3]:
                        print(f"  {key}: {str(value)[:100]}...")
                
                output_file = f"examples/output_example_{i}.json"
                with open(output_file, 'w') as f:
                    json.dump(result.model_dump(), f, indent=2)
                print(f"💾 Saved to: {output_file}")
                
            else:
                print("❌ Extraction failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Examples completed!")

if __name__ == "__main__":
    main() 