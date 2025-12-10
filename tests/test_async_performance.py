"""
异步采集器性能测试
比较同步模式和异步模式的采集速度
"""

import asyncio
import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_sync_mode():
    """测试同步模式"""
    from data_collector import AIDataCollector
    
    print("\n" + "="*60)
    print("🔄 Testing SYNC Mode (ThreadPool)")
    print("="*60)
    
    # 强制使用同步模式
    collector = AIDataCollector(async_mode=False)
    
    start_time = time.time()
    data = collector.collect_all(parallel=True, max_workers=6)
    elapsed = time.time() - start_time
    
    total = sum(len(items) for items in data.values())
    print(f"\n⏱️ Sync Mode: {total} items in {elapsed:.1f}s")
    
    return elapsed, total


def test_async_mode():
    """测试异步模式"""
    from data_collector import AIDataCollector
    
    print("\n" + "="*60)
    print("🚀 Testing ASYNC Mode (aiohttp)")
    print("="*60)
    
    # 强制使用异步模式
    collector = AIDataCollector(async_mode=True)
    
    start_time = time.time()
    data = collector.collect_all()
    elapsed = time.time() - start_time
    
    total = sum(len(items) for items in data.values())
    print(f"\n⏱️ Async Mode: {total} items in {elapsed:.1f}s")
    
    return elapsed, total


def main():
    """运行性能对比测试"""
    print("\n" + "="*70)
    print("        📊 Data Collector Performance Comparison")
    print("="*70)
    
    # 测试异步模式（先测试，热缓存）
    async_time, async_count = test_async_mode()
    
    # 等待一下避免速率限制
    print("\n⏳ Waiting 3 seconds before sync test...")
    time.sleep(3)
    
    # 测试同步模式
    sync_time, sync_count = test_sync_mode()
    
    # 结果对比
    print("\n" + "="*70)
    print("                   📈 Performance Results")
    print("="*70)
    print(f"\n  {'Mode':<15} {'Items':<10} {'Time':<10} {'Speed':<15}")
    print(f"  {'-'*50}")
    print(f"  {'Async':<15} {async_count:<10} {async_time:.1f}s{'':<5} {async_count/async_time:.1f} items/s")
    print(f"  {'Sync':<15} {sync_count:<10} {sync_time:.1f}s{'':<5} {sync_count/sync_time:.1f} items/s")
    
    if async_time < sync_time:
        speedup = sync_time / async_time
        print(f"\n  ✅ Async mode is {speedup:.1f}x faster!")
    else:
        slowdown = async_time / sync_time
        print(f"\n  ⚠️ Sync mode is {slowdown:.1f}x faster (unusual)")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
