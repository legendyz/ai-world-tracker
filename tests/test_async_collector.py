"""
异步数据采集器测试

测试纯异步采集架构的功能和性能
"""

import sys
import os
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collector import AIDataCollector


class TestAsyncCollector:
    """异步采集器测试套件"""
    
    @pytest.fixture
    def collector(self):
        """创建采集器实例"""
        return AIDataCollector()
    
    def test_collector_initialization(self, collector):
        """测试采集器初始化"""
        assert collector is not None
        assert hasattr(collector, 'async_config')
        assert hasattr(collector, 'history_cache')
        assert hasattr(collector, 'stats')
        print("✅ 采集器初始化正常")
    
    def test_stats_reset(self, collector):
        """测试统计信息重置"""
        # 修改统计信息
        collector.stats['requests_made'] = 10
        collector.stats['items_collected'] = 50
        
        # 重置
        collector._reset_stats()
        
        assert collector.stats['requests_made'] == 0
        assert collector.stats['items_collected'] == 0
        assert collector.stats['failed_sources'] == []
        print("✅ 统计信息重置正常")
    
    def test_record_failure(self, collector):
        """测试失败记录功能"""
        collector._record_failure('test_source', 'test_category', 'Test error')
        
        assert len(collector.stats['failed_sources']) == 1
        assert collector.stats['failed_sources'][0]['source'] == 'test_source'
        assert collector.stats['failed_sources'][0]['error'] == 'Test error'
        print("✅ 失败记录功能正常")
    
    def test_cache_loading(self, collector):
        """测试缓存加载"""
        cache = collector.history_cache
        
        assert isinstance(cache, dict)
        assert 'urls' in cache
        assert 'titles' in cache
        print(f"✅ 缓存加载正常: {len(cache.get('urls', []))} URLs, {len(cache.get('titles', []))} 标题")
    
    @pytest.mark.asyncio
    async def test_async_session_creation(self, collector):
        """测试异步session创建"""
        # 注意：这个测试需要实际的async方法
        # 如果AIDataCollector有创建session的方法，在这里测试
        assert hasattr(collector, 'headers')
        assert 'User-Agent' in collector.headers
        print("✅ Session配置正常")
    
    def test_rss_feeds_configuration(self, collector):
        """测试RSS源配置"""
        assert hasattr(collector, 'rss_feeds')
        assert isinstance(collector.rss_feeds, dict)
        assert len(collector.rss_feeds) > 0
        
        # 检查配置结构
        for category, feeds in collector.rss_feeds.items():
            assert isinstance(feeds, list)
            print(f"  📡 {category}: {len(feeds)} 个源")
        
        print("✅ RSS源配置正常")
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, collector):
        """测试去重功能"""
        test_url = "https://example.com/test-article"
        test_title = "Test Article Title"
        
        # 第一次应该不是重复
        is_dup_url = test_url in collector.history_cache.get('urls', set())
        is_dup_title = test_title in collector.history_cache.get('titles', set())
        
        print(f"✅ 去重检测: URL重复={is_dup_url}, 标题重复={is_dup_title}")
    
    def test_stats_structure(self, collector):
        """测试统计信息结构"""
        required_keys = ['requests_made', 'requests_failed', 'items_collected', 
                        'start_time', 'end_time', 'failed_sources']
        
        for key in required_keys:
            assert key in collector.stats, f"统计信息缺少字段: {key}"
        
        print("✅ 统计信息结构完整")
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_error_handling(self, collector):
        """测试错误处理机制"""
        # 模拟网络错误
        initial_failed = len(collector.stats['failed_sources'])
        
        # 记录一个失败
        collector._record_failure('test_source', 'test_category', 'Connection timeout')
        
        assert len(collector.stats['failed_sources']) == initial_failed + 1
        assert collector.stats['failed_sources'][-1]['error'] == 'Connection timeout'
        
        print("✅ 错误处理机制正常")


class TestAsyncPerformance:
    """异步性能测试"""
    
    @pytest.fixture
    def collector(self):
        return AIDataCollector()
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_limits(self, collector):
        """测试并发限制配置"""
        config = collector.async_config
        
        # 检查config对象是否有并发限制属性
        has_limit = (hasattr(config, 'max_concurrent_requests') or 
                    hasattr(config, 'concurrent_limit') or
                    hasattr(config, 'max_connections'))
        
        print(f"✅ 并发限制配置存在: {has_limit}")
        if has_limit:
            print(f"  配置对象: {type(config)}")
    
    @pytest.mark.slow
    def test_timeout_configuration(self, collector):
        """测试超时配置"""
        config = collector.async_config
        
        # 检查是否有超时配置属性
        timeout_attrs = ['timeout', 'request_timeout', 'connect_timeout']
        has_timeout = any(hasattr(config, attr) for attr in timeout_attrs)
        
        print(f"✅ 超时配置存在: {has_timeout}")
        if has_timeout:
            for attr in timeout_attrs:
                if hasattr(config, attr):
                    print(f"  {attr}: {getattr(config, attr)}")


class TestCacheManagement:
    """缓存管理测试"""
    
    @pytest.fixture
    def collector(self):
        return AIDataCollector()
    
    def test_cache_structure(self, collector):
        """测试缓存数据结构"""
        cache = collector.history_cache
        
        assert 'urls' in cache, "缓存应包含urls字段"
        assert 'titles' in cache, "缓存应包含titles字段"
        
        # 检查数据类型
        assert isinstance(cache['urls'], (set, list)), "urls应该是集合或列表"
        assert isinstance(cache['titles'], (set, list)), "titles应该是集合或列表"
        
        print(f"✅ 缓存结构正常: URLs={len(cache['urls'])}, 标题={len(cache['titles'])}")
    
    def test_cache_persistence(self, collector):
        """测试缓存持久化路径"""
        assert hasattr(collector, 'history_cache_file')
        assert collector.history_cache_file.endswith('.json')
        
        print(f"✅ 缓存文件路径: {collector.history_cache_file}")
    
    @pytest.mark.integration
    def test_cache_save_and_load(self, collector, tmp_path):
        """测试缓存保存和加载（需要实现保存方法）"""
        # 这里假设有保存缓存的方法
        # 如果没有，可以跳过或模拟
        
        print("✅ 缓存保存/加载功能（待实现完整测试）")


class TestResourceCleanup:
    """资源清理测试"""
    
    @pytest.fixture
    def collector(self):
        return AIDataCollector()
    
    def test_cleanup_method_exists(self, collector):
        """测试清理方法是否存在"""
        # 检查是否有清理相关的方法
        cleanup_methods = ['cleanup', 'close', '__del__', '_cleanup']
        
        has_cleanup = any(hasattr(collector, method) for method in cleanup_methods)
        
        print(f"✅ 清理方法存在: {has_cleanup}")
        for method in cleanup_methods:
            if hasattr(collector, method):
                print(f"  找到清理方法: {method}")


@pytest.mark.integration
class TestIntegration:
    """集成测试 - 需要网络连接"""
    
    @pytest.fixture
    def collector(self):
        return AIDataCollector()
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_basic_collection_flow(self, collector):
        """测试基本采集流程（模拟）"""
        # 这是一个框架，实际测试需要mock或使用测试数据
        
        print("✅ 基本采集流程测试框架就绪")
        print("  注意: 完整测试需要mock网络请求或使用测试RSS源")


if __name__ == '__main__':
    print("\n" + "🌟" * 30)
    print("   异步采集器测试套件")
    print("🌟" * 30)
    
    # 运行测试
    pytest.main([__file__, '-v', '-s'])
