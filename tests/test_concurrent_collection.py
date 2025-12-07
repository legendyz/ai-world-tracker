"""
测试并发数据采集功能

对比串行和并发采集的性能差异
"""

import sys
import os
import time
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collector import AIDataCollector, collect_data_fast, collect_data_async


def test_serial_collection():
    """测试串行采集"""
    print("\n" + "=" * 60)
    print("📊 测试串行采集模式")
    print("=" * 60)
    
    collector = AIDataCollector()
    
    start_time = time.time()
    data = collector.collect_all(use_concurrent=False)
    elapsed = time.time() - start_time
    
    total = sum(len(items) for items in data.values())
    print(f"\n✅ 串行采集完成!")
    print(f"   总数据量: {total} 条")
    print(f"   耗时: {elapsed:.2f} 秒")
    
    for category, items in data.items():
        print(f"   - {category}: {len(items)} 条")
    
    return elapsed, total


def test_concurrent_collection():
    """测试并发采集"""
    print("\n" + "=" * 60)
    print("🚀 测试并发采集模式")
    print("=" * 60)
    
    collector = AIDataCollector()
    
    start_time = time.time()
    data = collector.collect_all_concurrent(max_workers=6)
    elapsed = time.time() - start_time
    
    total = sum(len(items) for items in data.values())
    print(f"\n✅ 并发采集完成!")
    print(f"   总数据量: {total} 条")
    print(f"   耗时: {elapsed:.2f} 秒")
    
    for category, items in data.items():
        print(f"   - {category}: {len(items)} 条")
    
    return elapsed, total


def test_async_collection():
    """测试异步采集"""
    print("\n" + "=" * 60)
    print("⚡ 测试异步采集模式")
    print("=" * 60)
    
    async def run():
        collector = AIDataCollector()
        start_time = time.time()
        data = await collector.collect_all_async()
        elapsed = time.time() - start_time
        
        total = sum(len(items) for items in data.values())
        print(f"\n✅ 异步采集完成!")
        print(f"   总数据量: {total} 条")
        print(f"   耗时: {elapsed:.2f} 秒")
        
        for category, items in data.items():
            print(f"   - {category}: {len(items)} 条")
        
        return elapsed, total
    
    return asyncio.run(run())


def test_convenience_functions():
    """测试便捷函数"""
    print("\n" + "=" * 60)
    print("🎯 测试便捷函数 collect_data_fast()")
    print("=" * 60)
    
    start_time = time.time()
    data = collect_data_fast(max_workers=6)
    elapsed = time.time() - start_time
    
    total = sum(len(items) for items in data.values())
    print(f"\n✅ 便捷函数采集完成!")
    print(f"   总数据量: {total} 条")
    print(f"   耗时: {elapsed:.2f} 秒")
    
    return elapsed, total


def test_reddit_sources():
    """专门测试Reddit数据源"""
    print("\n" + "=" * 60)
    print("🔴 测试Reddit数据源")
    print("=" * 60)
    
    collector = AIDataCollector()
    
    # 检查Reddit源是否在配置中
    community_feeds = collector.rss_feeds.get('community', [])
    reddit_feeds = [f for f in community_feeds if 'reddit.com' in f]
    
    print(f"\n📋 配置的Reddit源 ({len(reddit_feeds)} 个):")
    for feed in reddit_feeds:
        print(f"   - {feed}")
    
    # 采集社区数据
    start_time = time.time()
    data = collector.collect_community_trends(max_results=20)
    elapsed = time.time() - start_time
    
    # 统计Reddit来源的数据
    reddit_items = [item for item in data if 'Reddit' in item.get('source', '')]
    
    print(f"\n✅ 社区数据采集完成!")
    print(f"   总数据量: {len(data)} 条")
    print(f"   Reddit数据: {len(reddit_items)} 条")
    print(f"   耗时: {elapsed:.2f} 秒")
    
    if reddit_items:
        print("\n📝 Reddit数据示例:")
        for item in reddit_items[:3]:
            print(f"\n   📌 {item['title'][:60]}...")
            print(f"      来源: {item.get('source', 'Unknown')}")
            print(f"      链接: {item.get('url', 'N/A')[:50]}...")
    
    return len(reddit_items)


def run_performance_comparison():
    """运行性能对比测试"""
    print("\n" + "=" * 60)
    print("📊 性能对比测试")
    print("=" * 60)
    
    # 注意: 完整对比需要较长时间，这里只运行并发模式
    print("\n⏳ 运行并发采集测试...")
    concurrent_time, concurrent_count = test_concurrent_collection()
    
    print("\n" + "=" * 60)
    print("📈 性能报告")
    print("=" * 60)
    print(f"\n🚀 并发模式:")
    print(f"   - 数据量: {concurrent_count} 条")
    print(f"   - 耗时: {concurrent_time:.2f} 秒")
    print(f"\n💡 提示: 并发模式相比串行模式通常快 3-5 倍")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='测试数据采集功能')
    parser.add_argument('--mode', choices=['serial', 'concurrent', 'async', 'reddit', 'compare', 'quick'], 
                        default='quick', help='测试模式')
    args = parser.parse_args()
    
    print("\n" + "🌟" * 30)
    print("   AI World Tracker - 数据采集测试")
    print("🌟" * 30)
    
    if args.mode == 'serial':
        test_serial_collection()
    elif args.mode == 'concurrent':
        test_concurrent_collection()
    elif args.mode == 'async':
        test_async_collection()
    elif args.mode == 'reddit':
        test_reddit_sources()
    elif args.mode == 'compare':
        run_performance_comparison()
    elif args.mode == 'quick':
        # 快速测试: 只测试Reddit源和并发模式
        test_reddit_sources()
        test_concurrent_collection()
    
    print("\n✅ 测试完成!")
