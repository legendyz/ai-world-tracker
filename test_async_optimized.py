"""
测试优化后的异步采集实现
"""
import sys
import time
from data_collector import DataCollector

def test_async_collection():
    """测试异步采集性能"""
    print("\n" + "="*60)
    print("测试优化后的异步采集实现")
    print("="*60)
    
    # 创建采集器（强制使用异步模式）
    collector = DataCollector(async_mode=True)
    
    print(f"\n采集模式: {'异步' if collector._use_async else '同步'}")
    print(f"并发请求数: {collector.async_config.max_concurrent_requests}")
    print(f"每主机并发数: {collector.async_config.max_concurrent_per_host}")
    
    # 开始采集
    start_time = time.time()
    print("\n开始采集数据...")
    
    try:
        data = collector.collect_all()
        
        elapsed = time.time() - start_time
        
        # 统计结果
        print("\n" + "="*60)
        print("采集完成统计")
        print("="*60)
        print(f"总耗时: {elapsed:.1f}秒")
        print(f"总请求数: {collector.stats['requests_made']}")
        print(f"失败请求: {collector.stats['requests_failed']}")
        print(f"平均速度: {collector.stats['requests_made']/elapsed:.1f} 请求/秒")
        
        print("\n数据分布:")
        total_items = 0
        for category, items in data.items():
            print(f"  {category}: {len(items)} 条")
            total_items += len(items)
        print(f"  总计: {total_items} 条")
        
        # 性能评估
        print("\n" + "="*60)
        print("性能评估")
        print("="*60)
        
        if elapsed < 30:
            print("✅ 优秀！采集速度非常快")
        elif elapsed < 60:
            print("✅ 良好！采集速度符合预期")
        elif elapsed < 120:
            print("⚠️  一般，有优化空间")
        else:
            print("❌ 较慢，需要进一步优化")
        
        if collector.stats['requests_failed'] == 0:
            print("✅ 完美！无失败请求")
        elif collector.stats['requests_failed'] < 5:
            print("✅ 良好！失败率较低")
        else:
            print(f"⚠️  有 {collector.stats['requests_failed']} 个请求失败")
        
        if total_items > 150:
            print(f"✅ 采集数据丰富！共 {total_items} 条")
        elif total_items > 100:
            print(f"✅ 采集数据充足，共 {total_items} 条")
        else:
            print(f"⚠️  采集数据较少，仅 {total_items} 条")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 采集失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_async_collection()
    sys.exit(0 if success else 1)
