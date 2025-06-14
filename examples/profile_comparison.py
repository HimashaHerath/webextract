#!/usr/bin/env python3
"""
Profile Comparison Example - WebExtract Library
===============================================

This example demonstrates all the built-in configuration profiles
and compares their performance, output, and use cases.

Requirements:
- Ollama running locally
- Multiple models available (gemma3:27b, gemma3:8b, gemma3:2b, codellama:13b)
"""

from webextract import WebExtractor, ConfigProfiles
import time

def test_profile(profile_name: str, extractor: WebExtractor, url: str) -> dict:
    """Test a single profile and return results"""
    try:
        print(f"🧪 Testing {profile_name}...")
        start_time = time.time()
        
        result = extractor.extract(url)
        extraction_time = time.time() - start_time
        
        if result:
            return {
                "profile": profile_name,
                "success": True,
                "time": extraction_time,
                "confidence": result.confidence,
                "content_length": len(result.content.main_content) if result.content else 0,
                "structured_fields": list(result.structured_info.keys()) if result.structured_info else [],
                "field_count": len(result.structured_info) if result.structured_info else 0,
                "summary": result.structured_info.get('summary', 'No summary') if result.structured_info else 'No summary',
                "error": None
            }
        else:
            return {
                "profile": profile_name,
                "success": False,
                "time": extraction_time,
                "error": "No result returned"
            }
            
    except Exception as e:
        return {
            "profile": profile_name,
            "success": False,
            "time": 0,
            "error": str(e)
        }

def main():
    print("🔍 WebExtract - Profile Comparison Example")
    print("=" * 60)
    
    # Test URL
    url = "https://dev.to/nodeshiftcloud/claude-4-opus-vs-sonnet-benchmarks-and-dev-workflow-with-claude-code-11fa"
    
    print(f"🌐 Test URL: {url}")
    print(f"📋 Testing all available profiles...\n")
    
    # Define all profiles to test
    profiles_to_test = [
        ("News Scraping", ConfigProfiles.news_scraping()),
        ("Research Papers", ConfigProfiles.research_papers()),
        ("E-commerce", ConfigProfiles.ecommerce()),
        ("Documentation", ConfigProfiles.documentation()),
        ("Fast Extraction", ConfigProfiles.fast_extraction()),
        ("Accurate Extraction", ConfigProfiles.accurate_extraction()),
    ]
    
    results = []
    
    # Test each profile
    for profile_name, config in profiles_to_test:
        print(f"=" * 50)
        extractor = WebExtractor(config)
        result = test_profile(profile_name, extractor, url)
        results.append(result)
        
        if result["success"]:
            print(f"✅ {profile_name}")
            print(f"   ⏱️  Time: {result['time']:.1f}s")
            print(f"   🎯 Confidence: {result['confidence']:.1%}")
            print(f"   📊 Fields extracted: {result['field_count']}")
            print(f"   🔤 Available fields: {', '.join(result['structured_fields'][:5])}{'...' if len(result['structured_fields']) > 5 else ''}")
            
            # Show a snippet of the summary
            summary = result['summary'][:100] + "..." if len(result['summary']) > 100 else result['summary']
            print(f"   📝 Summary: {summary}")
        else:
            print(f"❌ {profile_name}")
            print(f"   ⚠️  Error: {result['error']}")
        
        print()  # Empty line for readability
    
    # Performance comparison
    print(f"=" * 60)
    print("📊 PERFORMANCE COMPARISON")
    print(f"=" * 60)
    
    successful_results = [r for r in results if r["success"]]
    
    if successful_results:
        print(f"\n⚡ Speed Ranking (fastest to slowest):")
        speed_sorted = sorted(successful_results, key=lambda x: x["time"])
        for i, result in enumerate(speed_sorted, 1):
            print(f"   {i}. {result['profile']}: {result['time']:.1f}s")
        
        print(f"\n🎯 Confidence Ranking (highest to lowest):")
        confidence_sorted = sorted(successful_results, key=lambda x: x["confidence"], reverse=True)
        for i, result in enumerate(confidence_sorted, 1):
            print(f"   {i}. {result['profile']}: {result['confidence']:.1%}")
        
        print(f"\n📋 Data Richness (most fields to least):")
        fields_sorted = sorted(successful_results, key=lambda x: x["field_count"], reverse=True)
        for i, result in enumerate(fields_sorted, 1):
            print(f"   {i}. {result['profile']}: {result['field_count']} fields")
        
        # Calculate averages
        avg_time = sum(r["time"] for r in successful_results) / len(successful_results)
        avg_confidence = sum(r["confidence"] for r in successful_results) / len(successful_results)
        avg_fields = sum(r["field_count"] for r in successful_results) / len(successful_results)
        
        print(f"\n📈 Overall Statistics:")
        print(f"   • Success rate: {len(successful_results)}/{len(results)} ({len(successful_results)/len(results)*100:.1f}%)")
        print(f"   • Average time: {avg_time:.1f}s")
        print(f"   • Average confidence: {avg_confidence:.1%}")
        print(f"   • Average fields: {avg_fields:.1f}")
    
    # Recommendations
    print(f"\n" + "="*60)
    print("💡 PROFILE RECOMMENDATIONS")
    print(f"=" + "="*60)
    
    print("\n🎯 Choose the right profile for your use case:")
    print("\n📰 News Scraping:")
    print("   • Best for: Blog posts, news articles, press releases")
    print("   • Extracts: Headlines, summaries, people, organizations")
    print("   • Model: gemma3:27b (balanced speed/accuracy)")
    
    print("\n📚 Research Papers:")
    print("   • Best for: Academic papers, research documents")
    print("   • Extracts: Abstracts, methodology, findings, citations")
    print("   • Model: gemma3:27b (high accuracy for complex content)")
    
    print("\n🛒 E-commerce:")
    print("   • Best for: Product pages, reviews, shopping sites")
    print("   • Extracts: Prices, specifications, reviews, ratings")
    print("   • Model: gemma3:8b (fast for high-volume processing)")
    
    print("\n📖 Documentation:")
    print("   • Best for: Technical docs, API references, tutorials")
    print("   • Extracts: Code examples, instructions, configurations")
    print("   • Model: codellama:13b (specialized for technical content)")
    
    print("\n⚡ Fast Extraction:")
    print("   • Best for: Quick overviews, batch processing")
    print("   • Extracts: Basic summaries and key points")
    print("   • Model: gemma3:2b (fastest processing)")
    
    print("\n🎯 Accurate Extraction:")
    print("   • Best for: Detailed analysis, important documents")
    print("   • Extracts: Comprehensive structured data")
    print("   • Model: gemma3:27b (highest quality output)")
    
    # Show speed vs accuracy trade-off
    if len(successful_results) >= 2:
        fastest = min(successful_results, key=lambda x: x["time"])
        most_accurate = max(successful_results, key=lambda x: x["confidence"])
        
        print(f"\n⚖️  Speed vs Accuracy Trade-off:")
        print(f"   • Fastest: {fastest['profile']} ({fastest['time']:.1f}s, {fastest['confidence']:.1%} confidence)")
        print(f"   • Most Accurate: {most_accurate['profile']} ({most_accurate['time']:.1f}s, {most_accurate['confidence']:.1%} confidence)")

if __name__ == "__main__":
    main() 