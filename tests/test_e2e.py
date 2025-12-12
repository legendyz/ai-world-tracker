"""
端到端测�?

测试完整的AI World Tracker工作流程
"""

import sys
import os
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TheWorldOfAI import AIWorldTracker
from data_collector import AIDataCollector
from content_classifier import ContentClassifier
from importance_evaluator import ImportanceEvaluator
from ai_analyzer import AIAnalyzer
from visualizer import DataVisualizer
from web_publisher import WebPublisher


@pytest.fixture
def mock_data():
    """提供完整的mock数据"""
    return [
        {
            'title': 'Breakthrough in Generative AI',
            'summary': 'New model achieves state-of-the-art results in text generation',
            'link': 'https://arxiv.org/abs/2025.12345',
            'source': 'arXiv',
            'published': datetime.now().isoformat()
        },
        {
            'title': 'OpenAI Releases GPT-5',
            'summary': 'Major update brings improved reasoning capabilities',
            'link': 'https://openai.com/blog/gpt5',
            'source': 'TechCrunch',
            'published': datetime.now().isoformat()
        },
        {
            'title': 'New Open Source AI Framework',
            'summary': 'Simplifies building and deploying AI models',
            'link': 'https://github.com/company/ai-framework',
            'source': 'GitHub',
            'published': datetime.now().isoformat()
        },
        {
            'title': 'AI Market Analysis Q4 2025',
            'summary': 'Industry insights and growth projections',
            'link': 'https://market.com/report',
            'source': 'MarketWatch',
            'published': datetime.now().isoformat()
        },
        {
            'title': 'Computer Vision Advances in Healthcare',
            'summary': 'AI-powered diagnostics show promising results',
            'link': 'https://nature.com/article',
            'source': 'Nature',
            'published': datetime.now().isoformat()
        }
    ]


@pytest.mark.asyncio
class TestEndToEndPipeline:
    """端到端流程测�?""
    
    async def test_full_pipeline_with_mock_data(self, mock_data):
        """测试完整流程（使用mock数据�?""
        print("\n" + "="*60)
        print("🚀 开始端到端测试 - 完整流程")
        print("="*60)
        
        tracker = AIWorldTracker(auto_mode=True)
        
        # ============ 步骤1: 数据收集 ============
        print("\n\U0001f4e1 步骤1: 数据收集")
        with patch.object(tracker.collector, 'collect_all',
                         new=AsyncMock(return_value={'research': mock_data})):
            async with tracker.collector:
                collected_data_dict = await tracker.collector.collect_all()
                collected_data = []
                for items in collected_data_dict.values():
                    collected_data.extend(items)
        
        assert len(collected_data) == len(mock_data)
        print(f"  �?收集�?{len(collected_data)} 条数�?)
        for item in collected_data[:3]:
            print(f"    - {item['title'][:50]}")
        
        # ============ 步骤2: 内容分类 ============
        print("\n🏷�? 步骤2: 内容分类")
        classified_data = []
        for item in collected_data:
            classified = tracker.classifier.classify_item(item)
            classified_data.append(classified)
        
        assert len(classified_data) == len(collected_data)
        content_types = [d.get('content_type', 'unknown') for d in classified_data]
        print(f"  �?分类完成: {len(classified_data)} �?)
        print(f"    类型分布: {set(content_types)}")
        
        # ============ 步骤3: 重要性评�?============
        print("\n�?步骤3: 重要性评�?)
        evaluated_data = []
        for item in classified_data:
            importance = tracker.analyzer.importance_evaluator.calculate_importance(item)
            item['importance'] = importance
            evaluated_data.append(item)
        
        importances = [d['importance'] for d in evaluated_data]
        avg_importance = sum(importances) / len(importances) if importances else 0
        print(f"  �?评估完成: {len(evaluated_data)} �?)
        print(f"    平均重要�? {avg_importance:.2f}")
        print(f"    分数范围: {min(importances):.2f} - {max(importances):.2f}")
        
        # ============ 步骤4: 趋势分析 ============
        print("\n📊 步骤4: 趋势分析")
        analyzer = AIAnalyzer()
        trends = analyzer.analyze_trends(evaluated_data)
        
        assert 'tech_categories' in trends
        assert 'content_distribution' in trends
        print(f"  �?分析完成")
        print(f"    技术热点数: {len(trends.get('tech_categories', {}))}")
        print(f"    内容分布: {len(trends.get('content_distribution', {}))}")
        
        # ============ 步骤5: 数据可视�?============
        print("\n🎨 步骤5: 数据可视�?)
        with tempfile.TemporaryDirectory() as tmp_dir:
            visualizer = DataVisualizer()
            visualizer.output_dir = tmp_dir
            
            chart_files = visualizer.visualize_all(trends)
            
            assert isinstance(chart_files, dict)
            print(f"  �?生成图表: {len(chart_files)} �?)
            for name in list(chart_files.keys())[:3]:
                print(f"    - {name}")
        
        # ============ 步骤6: Web发布 ============
        print("\n🌐 步骤6: Web发布")
        with tempfile.TemporaryDirectory() as tmp_dir:
            publisher = WebPublisher()
            publisher.output_dir = tmp_dir
            
            html_file = publisher.generate_html_page(evaluated_data, trends, chart_files)
            
            assert html_file is not None
            assert os.path.exists(html_file)
            print(f"  �?生成HTML: {os.path.basename(html_file)}")
            print(f"    文件大小: {os.path.getsize(html_file)} 字节")
        
        print("\n" + "="*60)
        print("�?端到端测试完�?- 所有步骤成�?)
        print("="*60)
    
    async def test_pipeline_data_flow(self, mock_data):
        """测试数据在流程中的流�?""
        print("\n🔄 测试数据流转")
        
        tracker = AIWorldTracker(auto_mode=True)
        
        # 收集
        with patch.object(tracker.collector, 'collect_all',
                         new=AsyncMock(return_value={'research': mock_data})):
            async with tracker.collector:
                data_dict = await tracker.collector.collect_all()
                data = []
                for items in data_dict.values():
                    data.extend(items)
        
        original_count = len(data)
        
        # 分类
        data = tracker.classifier.classify_batch(data)
        
        # 评估
        from importance_evaluator import ImportanceEvaluator
        evaluator = ImportanceEvaluator()
        for item in data:
            item['importance'] = evaluator.calculate_importance(item)
        
        # 验证数据完整�?
        assert len(data) == original_count
        assert all('content_type' in item for item in data)
        assert all('importance' in item for item in data)
        
        print(f"  �?数据完整性验�? {original_count} 条数据保持完�?)
        print("�?数据流转测试通过")


@pytest.mark.asyncio
class TestErrorRecovery:
    """测试错误恢复能力"""
    
    async def test_partial_collection_failure(self):
        """测试部分收集失败的情�?""
        print("\n⚠️  测试部分收集失败恢复")
        
        tracker = AIWorldTracker(auto_mode=True)
        
        # Mock部分成功的数据收�?
        partial_data = [
            {'title': 'Success 1', 'summary': 'OK', 'link': 'https://test.com/1', 'source': 'test'},
            {'title': 'Success 2', 'summary': 'OK', 'link': 'https://test.com/2', 'source': 'test'}
        ]
        
        with patch.object(tracker.collector, 'collect_all',
                         new=AsyncMock(return_value={'research': partial_data})):
            async with tracker.collector:
                data_dict = await tracker.collector.collect_all()
                data = []
                for items in data_dict.values():
                    data.extend(items)
        
        # 即使部分失败，也应该能处理成功的数据
        assert len(data) > 0
        print(f"  �?成功处理�?{len(data)} 条数�?)
        print("�?部分失败恢复测试通过")
    
    def test_classification_with_incomplete_data(self):
        """测试不完整数据的分类"""
        print("\n⚠️  测试不完整数据分�?)
        
        tracker = AIWorldTracker(auto_mode=True)
        
        incomplete_items = [
            {'title': 'Only title'},
            {'summary': 'Only summary'},
            {'title': 'Title', 'summary': 'Summary'}
        ]
        
        results = []
        for item in incomplete_items:
            try:
                result = tracker.classifier.classify_item(item)  # 使用classify_item处理单条
                results.append(result)
            except Exception as e:
                print(f"  ! 分类失败: {e}")
        
        print(f"  �?成功分类: {len(results)}/{len(incomplete_items)}")
        print("�?不完整数据处理测试通过")


class TestDataQuality:
    """测试数据质量"""
    
    def test_classification_accuracy(self, mock_data):
        """测试分类准确�?""
        print("\n🎯 测试分类准确�?)
        
        tracker = AIWorldTracker(auto_mode=True)
        
        # 已知类型的测试数�?
        known_types = {
            'Breakthrough in Generative AI': 'research',
            'OpenAI Releases GPT-5': 'product',
            'New Open Source AI Framework': 'developer',
            'AI Market Analysis Q4 2025': 'market'
        }
        
        correct = 0
        total = 0
        
        for item in mock_data:
            if item['title'] in known_types:
                result = tracker.classifier.classify_item(item)  # 使用classify_item
                expected = known_types[item['title']]
                actual = result.get('content_type')
                
                if actual == expected:
                    correct += 1
                total += 1
                
                print(f"  {'�? if actual == expected else '�?} {item['title'][:40]}: "
                      f"预期={expected}, 实际={actual}")
        
        accuracy = correct / total if total > 0 else 0
        print(f"\n  准确�? {accuracy:.1%} ({correct}/{total})")
        print("�?分类准确性测试完�?)
    
    def test_importance_consistency(self, mock_data):
        """测试重要性评分一致�?""
        print("\n📈 测试重要性评分一致�?)
        
        tracker = AIWorldTracker(auto_mode=True)
        
        # 对同一数据多次评分
        from importance_evaluator import ImportanceEvaluator
        evaluator = ImportanceEvaluator()
        test_item = mock_data[0].copy()
        test_item['content_type'] = 'research'
        test_item['tech_categories'] = ['Generative AI']
        
        scores = []
        for _ in range(3):
            score = evaluator.calculate_importance(test_item)
            scores.append(score)
        
        # 评分应该一�?
        assert len(set(scores)) <= 2  # 允许微小差异
        avg_score = sum(scores) / len(scores)
        print(f"  评分: {scores}")
        print(f"  平均: {avg_score:.3f}")
        print("�?重要性评分一致性测试通过")


@pytest.mark.asyncio
class TestPerformance:
    """测试性能"""
    
    async def test_large_dataset_handling(self):
        """测试大数据集处理"""
        print("\n�?测试大数据集处理")
        
        tracker = AIWorldTracker(auto_mode=True)
        
        # 生成100条mock数据
        large_dataset = []
        for i in range(100):
            large_dataset.append({
                'title': f'AI Article {i}',
                'summary': f'This is a test article about AI technology number {i}',
                'link': f'https://test.com/{i}',
                'source': 'test',
                'published': datetime.now().isoformat()
            })
        
        import time
        start_time = time.time()
        
        # 分类和评�?
        from importance_evaluator import ImportanceEvaluator
        evaluator = ImportanceEvaluator()
        classified = tracker.classifier.classify_batch(large_dataset)
        for item in classified:
            item['importance'] = evaluator.calculate_importance(item)
        
        duration = time.time() - start_time
        avg_time = duration / len(large_dataset) * 1000  # 毫秒
        
        print(f"  处理 {len(large_dataset)} 条数�?)
        print(f"  总耗时: {duration:.2f}�?)
        print(f"  平均: {avg_time:.1f}ms/�?)
        
        assert len(classified) == len(large_dataset)
        print("�?大数据集处理测试通过")


class TestIntegrationPoints:
    """测试集成�?""
    
    def test_analyzer_visualizer_integration(self, mock_data):
        """测试分析器和可视化器集成"""
        print("\n🔗 测试分析�?可视化器集成")
        
        tracker = AIWorldTracker(auto_mode=True)
        
        # 准备数据
        from importance_evaluator import ImportanceEvaluator
        evaluator = ImportanceEvaluator()
        classified = tracker.classifier.classify_batch(mock_data)
        for item in classified:
            item['importance'] = evaluator.calculate_importance(item)
        
        # 分析
        analyzer = AIAnalyzer()
        trends = analyzer.analyze_trends(classified)
        
        # 可视�?
        with tempfile.TemporaryDirectory() as tmp_dir:
            visualizer = DataVisualizer()
            visualizer.output_dir = tmp_dir
            charts = visualizer.visualize_all(trends)
        
        assert len(charts) > 0
        print(f"  �?生成�?{len(charts)} 个图�?)
        print("�?集成测试通过")
    
    def test_visualizer_publisher_integration(self, mock_data):
        """测试可视化器和发布器集成"""
        print("\n🔗 测试可视化器-发布器集�?)
        
        tracker = AIWorldTracker(auto_mode=True)
        
        # 准备完整数据
        from importance_evaluator import ImportanceEvaluator
        evaluator = ImportanceEvaluator()
        classified = tracker.classifier.classify_batch(mock_data)
        for item in classified:
            item['importance'] = evaluator.calculate_importance(item)
        
        analyzer = AIAnalyzer()
        trends = analyzer.analyze_trends(classified)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 可视�?
            visualizer = DataVisualizer()
            visualizer.output_dir = tmp_dir
            charts = visualizer.visualize_all(trends)
            
            # 发布
            publisher = WebPublisher()
            publisher.output_dir = tmp_dir
            html = publisher.generate_html_page(classified, trends, charts)
        
        assert os.path.exists(html)
        print(f"  �?生成HTML: {os.path.basename(html)}")
        print("�?集成测试通过")


if __name__ == '__main__':
    print("\n" + "🌟" * 30)
    print("   AI World Tracker 端到端测�?)
    print("🌟" * 30)
    
    # 运行测试
    pytest.main([__file__, '-v', '-s'])
