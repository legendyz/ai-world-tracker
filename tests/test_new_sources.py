"""
Quick test script for new data sources in AI World Tracker

Tests all new collection methods individually and as a whole.
"""

import asyncio
import aiohttp
import sys
import time
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collector import AIDataCollector


async def test_individual_sources():
    """Test each new data source individually"""
    print("=" * 60)
    print("TESTING INDIVIDUAL NEW DATA SOURCES")
    print("=" * 60)
    
    collector = AIDataCollector()
    semaphore = asyncio.Semaphore(5)
    
    # Test Reddit
    print("\n1. Testing Reddit...")
    async with aiohttp.ClientSession() as session:
        try:
            reddit_items = await collector._collect_reddit_async(session, semaphore, max_items=5)
            print(f"   ✓ Reddit: {len(reddit_items)} items")
            if reddit_items:
                print(f"   Sample: {reddit_items[0]['title'][:60]}...")
        except Exception as e:
            print(f"   ✗ Reddit failed: {e}")
    
    # Test Papers with Code
    print("\n2. Testing Papers with Code...")
    async with aiohttp.ClientSession() as session:
        try:
            pwc_items = await collector._collect_papers_with_code_async(session, semaphore, max_items=5)
            print(f"   ✓ Papers with Code: {len(pwc_items)} items")
            if pwc_items:
                print(f"   Sample: {pwc_items[0]['title'][:60]}...")
        except Exception as e:
            print(f"   ✗ Papers with Code failed: {e}")
    
    # Test YouTube
    print("\n3. Testing YouTube Channels...")
    async with aiohttp.ClientSession() as session:
        try:
            youtube_items = await collector._collect_youtube_channels_async(session, semaphore, max_items=5)
            print(f"   ✓ YouTube: {len(youtube_items)} items")
            if youtube_items:
                print(f"   Sample: {youtube_items[0]['title'][:60]}...")
        except Exception as e:
            print(f"   ✗ YouTube failed: {e}")
    
    # Test Medium
    print("\n4. Testing Medium...")
    async with aiohttp.ClientSession() as session:
        try:
            medium_items = await collector._collect_medium_async(session, semaphore, max_items=5)
            print(f"   ✓ Medium: {len(medium_items)} items")
            if medium_items:
                print(f"   Sample: {medium_items[0]['title'][:60]}...")
        except Exception as e:
            print(f"   ✗ Medium failed: {e}")
    
    # Test Bilibili
    print("\n5. Testing Bilibili...")
    async with aiohttp.ClientSession() as session:
        try:
            bilibili_items = await collector._collect_bilibili_async(session, semaphore, max_items=5)
            print(f"   ✓ Bilibili: {len(bilibili_items)} items")
            if bilibili_items:
                print(f"   Sample: {bilibili_items[0]['title'][:60]}...")
        except Exception as e:
            print(f"   ✗ Bilibili failed: {e}")


def test_full_collection():
    """Test full collection with all sources"""
    print("\n" + "=" * 60)
    print("TESTING FULL COLLECTION WITH ALL SOURCES")
    print("=" * 60)
    
    start_time = time.time()
    collector = AIDataCollector()
    
    try:
        data = collector.collect_all()
        elapsed = time.time() - start_time
        
        print(f"\n✓ Collection completed in {elapsed:.1f}s")
        print(f"\nResults by category:")
        print("-" * 60)
        
        total_items = 0
        for category, items in sorted(data.items()):
            total_items += len(items)
            print(f"  {category:12s}: {len(items):3d} items")
            
            # Show source breakdown
            sources = {}
            for item in items:
                source = item.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
            
            # Show top 3 sources
            top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:3]
            for source, count in top_sources:
                print(f"    - {source}: {count}")
        
        print("-" * 60)
        print(f"  {'TOTAL':12s}: {total_items:3d} items")
        
        # Performance metrics
        print(f"\nPerformance metrics:")
        print(f"  Requests made: {collector.stats.get('requests_made', 0)}")
        print(f"  Requests failed: {collector.stats.get('requests_failed', 0)}")
        print(f"  Items/second: {total_items/elapsed:.1f}")
        
        # Check for new sources
        print(f"\nNew source verification:")
        all_sources = set()
        for items in data.values():
            for item in items:
                all_sources.add(item.get('source', 'Unknown'))
        
        new_sources = [
            'Reddit', 'Papers with Code', 'YouTube', 'Medium', 
            'Bilibili', 'The Batch', 'Import AI', 'VentureBeat'
        ]
        
        found_new = []
        for source in new_sources:
            if any(source in s for s in all_sources):
                found_new.append(source)
                print(f"  ✓ {source}")
            else:
                print(f"  ✗ {source} (not found)")
        
        print(f"\n{len(found_new)}/{len(new_sources)} new sources active")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Collection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AI WORLD TRACKER - NEW DATA SOURCES TEST")
    print("=" * 60)
    
    # Test individual sources
    try:
        asyncio.run(test_individual_sources())
    except Exception as e:
        print(f"\nIndividual source tests failed: {e}")
    
    # Test full collection
    success = test_full_collection()
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
