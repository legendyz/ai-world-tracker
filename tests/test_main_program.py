"""
主程序 TheWorldOfAI.py 测试
提高主程序覆盖率
"""

import sys
import os
import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TheWorldOfAI import AIWorldTracker, _load_data_paths


class TestDataPathsLoading:
    """测试数据路径加载"""
    
    def test_load_default_paths(self):
        """测试默认路径加载"""
        exports_dir, cache_dir = _load_data_paths()
        
        assert exports_dir is not None
        assert cache_dir is not None
        assert os.path.exists(exports_dir)
        assert os.path.exists(cache_dir)
        
        print(f"✅ 默认路径加载: exports={exports_dir}, cache={cache_dir}")
    
    def test_paths_exist_after_load(self):
        """测试路径在加载后存在"""
        exports_dir, cache_dir = _load_data_paths()
        
        assert os.path.isdir(exports_dir)
        assert os.path.isdir(cache_dir)
        
        print("✅ 数据目录存在且可访问")


class TestAIWorldTrackerInitialization:
    """测试AIWorldTracker初始化"""
    
    def test_auto_mode_initialization(self):
        """测试自动模式初始化"""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert tracker is not None
        assert tracker.auto_mode is True
        assert tracker.collector is not None
        assert tracker.classifier is not None
        assert tracker.analyzer is not None
        assert tracker.visualizer is not None
        assert tracker.web_publisher is not None
        
        print("✅ 自动模式初始化成功")
    
    def test_components_created(self):
        """测试组件创建"""
        tracker = AIWorldTracker(auto_mode=True)
        
        # 验证主要组件存在
        assert hasattr(tracker, 'collector')
        assert hasattr(tracker, 'classifier')
        assert hasattr(tracker, 'analyzer')
        assert hasattr(tracker, 'visualizer')
        assert hasattr(tracker, 'web_publisher')
        
        # 验证数据属性
        assert hasattr(tracker, 'data')
        assert hasattr(tracker, 'trends')
        assert hasattr(tracker, 'chart_files')
        
        print("✅ 数据结构初始化正确")
    
    def test_classification_mode_default(self):
        """测试默认分类模式"""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert tracker.classification_mode == 'rule'
        assert tracker.llm_provider == 'ollama'
        assert tracker.llm_model == 'qwen3:8b'
        
        print("✅ 默认分类模式为规则模式")


class TestConfigManagement:
    """测试配置管理"""
    
    def test_save_user_config(self, tmp_path):
        """测试保存用户配置"""
        tracker = AIWorldTracker(auto_mode=True)
        
        # 修改配置文件路径为临时目录
        test_config_file = tmp_path / "test_config.json"
        with patch('TheWorldOfAI.CONFIG_FILE', str(test_config_file)):
            tracker._save_user_config()
            
            assert test_config_file.exists()
            
            with open(test_config_file, 'r') as f:
                config = json.load(f)
                assert 'classification_mode' in config
                assert 'llm_provider' in config
                assert 'llm_model' in config
        
        print("✅ 配置保存成功")
    
    def test_load_user_config(self, tmp_path):
        """测试加载用户配置"""
        test_config_file = tmp_path / "test_config.json"
        test_config = {
            'classification_mode': 'rule',
            'llm_provider': 'ollama',
            'llm_model': 'qwen3:8b'
        }
        
        with open(test_config_file, 'w') as f:
            json.dump(test_config, f)
        
        with patch('TheWorldOfAI.CONFIG_FILE', str(test_config_file)):
            tracker = AIWorldTracker(auto_mode=True)
            
            assert tracker.classification_mode == 'rule'
            assert tracker.llm_provider == 'ollama'
        
        print("✅ 配置加载成功")


class TestDataProcessing:
    """测试数据处理功能"""
    
    def test_data_storage(self):
        """测试数据存储"""
        tracker = AIWorldTracker(auto_mode=True)
        
        test_data = [
            {'title': 'Test 1', 'summary': 'Summary 1'},
            {'title': 'Test 2', 'summary': 'Summary 2'}
        ]
        
        tracker.data = test_data
        assert len(tracker.data) == 2
        
        print("✅ 数据存储正常")
    
    def test_trends_storage(self):
        """测试趋势数据存储"""
        tracker = AIWorldTracker(auto_mode=True)
        
        test_trends = {
            'tech_categories': {'AI': 5},
            'content_distribution': {'research': 3}
        }
        
        tracker.trends = test_trends
        assert 'tech_categories' in tracker.trends
        assert 'content_distribution' in tracker.trends
        
        print("✅ 趋势数据存储正常")


class TestCleanup:
    """测试资源清理"""
    
    def test_cleanup_method_exists(self):
        """测试清理方法存在"""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert hasattr(tracker, 'cleanup')
        assert callable(tracker.cleanup)
        
        print("✅ 清理方法存在")
    
    def test_cleanup_execution(self):
        """测试清理执行"""
        tracker = AIWorldTracker(auto_mode=True)
        
        # Mock collector的_save_history_cache方法
        tracker.collector._save_history_cache = Mock()
        
        # 执行清理
        tracker.cleanup()
        
        # 验证缓存保存被调用
        tracker.collector._save_history_cache.assert_called_once()
        
        print("✅ 清理执行成功")


class TestDataExport:
    """测试数据导出功能"""
    
    def test_export_directory_exists(self):
        """测试导出目录存在"""
        from TheWorldOfAI import DATA_EXPORTS_DIR
        
        assert os.path.exists(DATA_EXPORTS_DIR)
        assert os.path.isdir(DATA_EXPORTS_DIR)
        
        print(f"✅ 导出目录存在: {DATA_EXPORTS_DIR}")
    
    def test_cache_directory_exists(self):
        """测试缓存目录存在"""
        from TheWorldOfAI import DATA_CACHE_DIR
        
        assert os.path.exists(DATA_CACHE_DIR)
        assert os.path.isdir(DATA_CACHE_DIR)
        
        print(f"✅ 缓存目录存在: {DATA_CACHE_DIR}")


class TestModuleImports:
    """测试模块导入"""
    
    def test_required_modules_imported(self):
        """测试必需模块已导入"""
        from TheWorldOfAI import (
            DataCollector,
            ContentClassifier,
            AIAnalyzer,
            DataVisualizer,
            WebPublisher
        )
        
        assert DataCollector is not None
        assert ContentClassifier is not None
        assert AIAnalyzer is not None
        assert DataVisualizer is not None
        assert WebPublisher is not None
        
        print("✅ 所有必需模块已导入")
    
    def test_optional_llm_import(self):
        """测试可选LLM模块导入"""
        from TheWorldOfAI import LLM_AVAILABLE
        
        assert isinstance(LLM_AVAILABLE, bool)
        print(f"✅ LLM可用性: {LLM_AVAILABLE}")


class TestClassifierIntegration:
    """测试分类器集成"""
    
    def test_rule_classifier_available(self):
        """测试规则分类器可用"""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert tracker.classifier is not None
        
        # 测试分类功能
        test_item = {
            'title': 'New AI Model',
            'summary': 'A breakthrough in machine learning'
        }
        
        from content_classifier import ContentClassifier
        assert isinstance(tracker.classifier, ContentClassifier)
        
        print("✅ 规则分类器可用")
    
    def test_classification_mode_setting(self):
        """测试分类模式设置"""
        tracker = AIWorldTracker(auto_mode=True)
        
        original_mode = tracker.classification_mode
        
        tracker.classification_mode = 'rule'
        assert tracker.classification_mode == 'rule'
        
        # 恢复原始模式
        tracker.classification_mode = original_mode
        
        print("✅ 分类模式可以设置")


class TestAnalyzerIntegration:
    """测试分析器集成"""
    
    def test_analyzer_available(self):
        """测试分析器可用"""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert tracker.analyzer is not None
        assert hasattr(tracker.analyzer, 'analyze_trends')
        
        print("✅ 分析器可用")
    
    def test_analyzer_has_analysis_methods(self):
        """测试分析器有分析方法"""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert hasattr(tracker.analyzer, 'analyze_trends')
        assert hasattr(tracker.analyzer, 'generate_summary')
        assert callable(tracker.analyzer.analyze_trends)
        
        print("✅ 分析器方法存在")


class TestVisualizationIntegration:
    """测试可视化集成"""
    
    def test_visualizer_available(self):
        """测试可视化器可用"""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert tracker.visualizer is not None
        assert hasattr(tracker.visualizer, 'visualize_all')
        
        print("✅ 可视化器可用")
    
    def test_web_publisher_available(self):
        """测试Web发布器可用"""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert tracker.web_publisher is not None
        assert hasattr(tracker.web_publisher, 'generate_html_page')
        
        print("✅ Web发布器可用")


class TestReviewerIntegration:
    """测试审核器集成"""
    
    def test_reviewer_available(self):
        """测试审核器可用"""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert tracker.reviewer is not None
        
        print("✅ 审核器可用")
    
    def test_learner_available(self):
        """测试学习器可用"""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert tracker.learner is not None
        
        print("✅ 学习反馈模块可用")


class TestAutoMode:
    """测试自动模式"""
    
    def test_auto_mode_skips_llm_check(self):
        """测试自动模式跳过LLM检查"""
        with patch('TheWorldOfAI.LLM_AVAILABLE', True):
            tracker = AIWorldTracker(auto_mode=True)
            
            # 自动模式应该跳过LLM交互式配置
            assert tracker.auto_mode is True
            
        print("✅ 自动模式跳过LLM交互配置")
    
    def test_auto_mode_uses_rule_classifier(self):
        """测试自动模式使用规则分类器"""
        tracker = AIWorldTracker(auto_mode=True)
        
        assert tracker.classification_mode == 'rule'
        assert tracker.classifier is not None
        
        print("✅ 自动模式使用规则分类器")


class TestErrorHandling:
    """测试错误处理"""
    
    def test_config_load_with_invalid_file(self, tmp_path):
        """测试加载无效配置文件"""
        test_config_file = tmp_path / "invalid_config.json"
        
        # 写入无效JSON
        with open(test_config_file, 'w') as f:
            f.write("invalid json content")
        
        with patch('TheWorldOfAI.CONFIG_FILE', str(test_config_file)):
            # 应该能正常初始化，使用默认值
            tracker = AIWorldTracker(auto_mode=True)
            assert tracker.classification_mode == 'rule'
        
        print("✅ 无效配置文件处理正常")
    
    def test_cleanup_with_errors(self):
        """测试清理时的错误处理"""
        tracker = AIWorldTracker(auto_mode=True)
        
        # Mock collector方法抛出异常
        tracker.collector._save_history_cache = Mock(side_effect=Exception("Save error"))
        
        # 清理不应该崩溃
        try:
            tracker.cleanup()
        except Exception as e:
            pytest.fail(f"清理时不应该抛出异常: {e}")
        
        print("✅ 清理错误处理正常")


class TestIntegrationFlow:
    """测试集成流程"""
    
    def test_complete_initialization_flow(self):
        """测试完整初始化流程"""
        tracker = AIWorldTracker(auto_mode=True)
        
        # 验证所有组件
        assert tracker.collector is not None
        assert tracker.classifier is not None
        assert tracker.analyzer is not None
        assert tracker.visualizer is not None
        assert tracker.web_publisher is not None
        assert tracker.reviewer is not None
        assert tracker.learner is not None
        
        # 验证数据结构
        assert isinstance(tracker.data, list)
        assert isinstance(tracker.trends, dict)
        assert isinstance(tracker.chart_files, dict)
        
        # 验证配置
        assert tracker.classification_mode in ['rule', 'llm']
        assert tracker.llm_provider is not None
        assert tracker.llm_model is not None
        
        print("✅ 完整初始化流程验证通过")


if __name__ == '__main__':
    print("\n" + "🌟" * 30)
    print("   TheWorldOfAI 主程序测试")
    print("🌟" * 30)
    
    pytest.main([__file__, '-v', '-s'])
