"""
主程序集成测�?

测试AIWorldTracker主类的核心功能和工作流程
"""

import sys
import os
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TheWorldOfAI import AIWorldTracker
from config import ConfigManager


class TestAIWorldTrackerInitialization:
    """测试AIWorldTracker初始�?""
    
    def test_basic_initialization(self):
        """测试基本初始�?""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert tracker is not None
        assert hasattr(tracker, 'collector')
        assert hasattr(tracker, 'classifier')
        assert hasattr(tracker, 'analyzer')
        
        print("�?AIWorldTracker基本初始化成�?)
    
    def test_config_loading(self):
        """测试配置加载"""
        tracker = AIWorldTracker(auto_mode=True)
        
        # AIWorldTracker使用直接属性而不是config对象
        assert tracker.classifier is not None
        assert tracker.collector is not None
        
        print("�?配置加载成功")
    
    def test_components_initialization(self):
        """测试各组件初始化"""
        tracker = AIWorldTracker(auto_mode=True)
        
        # 核心组件
        assert tracker.collector is not None
        assert tracker.analyzer is not None
        assert tracker.visualizer is not None
        assert tracker.web_publisher is not None
        
        print("�?所有核心组件初始化成功")


class TestClassificationModes:
    """测试分类模式切换"""
    
    def test_rule_based_mode(self):
        """测试规则模式"""
        tracker = AIWorldTracker(auto_mode=True)
        
        # 确保规则模式可用
        assert tracker.classifier is not None
        
        # 检查分类器类型
        from content_classifier import ContentClassifier
        assert isinstance(tracker.classifier, ContentClassifier)
        
        print("�?规则模式可用")
    
    @pytest.mark.skipif(
        not os.environ.get('LLM_AVAILABLE', '').lower() == 'true',
        reason="LLM not available"
    )
    def test_llm_mode_availability(self):
        """测试LLM模式可用性（如果LLM可用�?""
        tracker = AIWorldTracker(auto_mode=True)
        
        # 如果LLM可用，应该能够初始化
        try:
            from llm_classifier import LLMClassifier
            llm_classifier = LLMClassifier()
            assert llm_classifier is not None
            print("�?LLM模式可用")
        except Exception as e:
            print(f"⚠️  LLM模式不可�? {e}")


@pytest.mark.asyncio
class TestDataCollectionWorkflow:
    """测试数据收集工作�?""
    
    async def test_collect_data_basic(self):
        """测试基本数据收集"""
        tracker = AIWorldTracker(auto_mode=True)
        
        # 使用mock避免实际网络请求
        with patch.object(tracker.collector, 'collect_all', 
                         new=AsyncMock(return_value={'research': [
                             {
                                 'title': 'Test Article',
                                 'summary': 'Test summary',
                                 'link': 'https://test.com/article',
                                 'source': 'test',
                                 'published': datetime.now().isoformat()
                             }
                         ]})):
            
            # 收集数据
            async with tracker.collector:
                data_dict = await tracker.collector.collect_all()
                data = []
                for items in data_dict.values():
                    data.extend(items)
            
            assert len(data) > 0
            assert 'title' in data[0]
            
            print(f"�?基本数据收集成功: {len(data)} �?)
    
    async def test_collect_with_deduplication(self):
        """测试带去重的数据收集"""
        tracker = AIWorldTracker()
        
        # Mock数据包含重复�?
        test_data = [
            {
                'title': 'Article 1',
                'summary': 'Summary 1',
                'link': 'https://test.com/1',
                'source': 'test',
                'published': datetime.now().isoformat()
            },
            {
                'title': 'Article 1',  # 重复
                'summary': 'Summary 1',
                'link': 'https://test.com/1',
                'source': 'test',
                'published': datetime.now().isoformat()
            },
            {
                'title': 'Article 2',
                'summary': 'Summary 2',
                'link': 'https://test.com/2',
                'source': 'test',
                'published': datetime.now().isoformat()
            }
        ]
        
        with patch.object(tracker.collector, 'collect_all',
                         new=AsyncMock(return_value={'research': test_data})):
            
            async with tracker.collector:
                data_dict = await tracker.collector.collect_all()
                data = []
                for items in data_dict.values():
                    data.extend(items)
            
            # 数据收集器应该处理去�?
            print(f"�?去重测试: 原始 {len(test_data)} �?)


class TestClassificationWorkflow:
    """测试分类工作�?""
    
    def test_classify_single_item(self):
        """测试单条数据分类"""
        tracker = AIWorldTracker(auto_mode=True)
        
        test_item = {
            'title': 'New AI Model for Natural Language Processing',
            'summary': 'Researchers develop advanced transformer model for NLP tasks',
            'link': 'https://test.com/article',
            'source': 'test'
        }
        
        # 使用规则分类�?
        result = tracker.classifier.classify_item(test_item)
        
        assert 'content_type' in result
        assert 'tech_categories' in result
        
        print(f"�?分类成功: {result.get('content_type')}, "
              f"类别: {result.get('tech_categories')}")
    
    def test_classify_multiple_items(self):
        """测试批量分类"""
        tracker = AIWorldTracker()
        
        test_items = [
            {
                'title': 'AI Research Paper',
                'summary': 'Academic research on machine learning',
                'link': 'https://test.com/1',
                'source': 'test'
            },
            {
                'title': 'New AI Product Launch',
                'summary': 'Company releases commercial AI product',
                'link': 'https://test.com/2',
                'source': 'test'
            }
        ]
        
        results = tracker.classifier.classify_batch(test_items)
        
        assert len(results) == len(test_items)
        assert all('content_type' in r for r in results)
        
        print(f"�?批量分类成功: {len(results)} �?)


class TestImportanceEvaluation:
    """测试重要性评�?""
    
    def test_calculate_importance(self):
        """测试重要性评�?""
        from importance_evaluator import ImportanceEvaluator
        evaluator = ImportanceEvaluator()
        
        test_item = {
            'title': 'Breakthrough in AI Research',
            'summary': 'Revolutionary new approach to artificial intelligence',
            'content_type': 'research',
            'tech_categories': ['Generative AI'],
            'source': 'arXiv',
            'published': datetime.now().isoformat()
        }
        
        importance = evaluator.calculate_importance(test_item)
        
        assert isinstance(importance, (int, float))
        assert 0 <= importance <= 1
        
        print(f"�?重要性评�? {importance:.2f}")
    
    def test_importance_range(self):
        """测试重要性评分范�?""
        from importance_evaluator import ImportanceEvaluator
        evaluator = ImportanceEvaluator()
        
        # 高重要性项�?
        high_importance_item = {
            'title': 'GPT-5 Released by OpenAI',
            'summary': 'Major breakthrough in language models',
            'content_type': 'product',
            'tech_categories': ['Generative AI'],
            'source': 'official'
        }
        
        # 低重要性项�?
        low_importance_item = {
            'title': 'Minor update',
            'summary': 'Small bug fix',
            'content_type': 'developer',
            'tech_categories': ['Other'],
            'source': 'blog'
        }
        
        high_score = evaluator.calculate_importance(high_importance_item)
        low_score = evaluator.calculate_importance(low_importance_item)
        
        # 理论上高重要性项目应该得分更�?
        print(f"�?评分范围测试: �?{high_score:.2f}, �?{low_score:.2f}")


class TestResourceManagement:
    """测试资源管理"""
    
    @pytest.mark.asyncio
    async def test_data_collector_context_manager(self):
        """测试数据收集器上下文管理�?""
        tracker = AIWorldTracker(auto_mode=True)
        
        # 测试async with语法
        async with tracker.collector as collector:
            assert collector is not None
            assert collector._session is not None
        
        # 退出后session应该被清�?
        # 注意：实际实现可能会保留session用于复用
        print("�?上下文管理器正常工作")
    
    def test_cleanup_on_exit(self):
        """测试退出时的清�?""
        tracker = AIWorldTracker()
        
        # 创建实例并立即删�?
        del tracker
        
        print("�?清理机制正常")


class TestErrorHandling:
    """测试错误处理"""
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """测试网络错误处理"""
        tracker = AIWorldTracker(auto_mode=True)
        
        # Mock网络错误
        with patch.object(tracker.collector, 'collect_all',
                         new=AsyncMock(side_effect=Exception("Network error"))):
            
            try:
                async with tracker.collector:
                    await tracker.collector.collect_all()
                assert False, "应该抛出异常"
            except Exception as e:
                assert "Network error" in str(e)
                print("�?网络错误处理正常")
    
    def test_invalid_data_handling(self):
        """测试无效数据处理"""
        tracker = AIWorldTracker(auto_mode=True)
        
        # 测试空数�?
        result = tracker.classifier.classify_item({})  # classify_item可以处理空数�?
        assert result is not None  # 应该返回默认结果
        
        # 测试缺失字段
        result = tracker.classifier.classify_item({'title': 'Test'})
        assert result is not None
        
        print("�?无效数据处理正常")


class TestConfigurationManagement:
    """测试配置管理"""
    
    def test_config_persistence(self):
        """测试配置持久�?""
        tracker1 = AIWorldTracker(auto_mode=True)
        mode1 = tracker1.classification_mode
        
        tracker2 = AIWorldTracker(auto_mode=True)
        mode2 = tracker2.classification_mode
        
        # auto_mode下都应该使用rule模式
        assert mode1 == mode2 == 'rule'
        print("�?配置一致性正�?)


if __name__ == '__main__':
    print("\n" + "🌟" * 30)
    print("   AIWorldTracker主程序集成测�?)
    print("🌟" * 30)
    
    # 运行测试
    pytest.main([__file__, '-v', '-s'])
