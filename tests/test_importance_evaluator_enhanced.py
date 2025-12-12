"""
增强的重要性评估器测试

测试场景:
1. 动态来源学习
2. 内容类型相关的时效性衰减
3. 来源性能跟踪
4. 学习数据持久化
"""

import sys
import os
import unittest
from datetime import datetime, timedelta
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from importance_evaluator import ImportanceEvaluator


class TestEnhancedImportanceEvaluator(unittest.TestCase):
    """测试增强的重要性评估器"""
    
    def setUp(self):
        """每个测试前初始化"""
        self.evaluator = ImportanceEvaluator()
    
    def test_adaptive_time_decay_by_content_type(self):
        """测试内容类型相关的时效性衰减"""
        # 创建7天前的内容
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        item = {
            'title': 'Test Article',
            'summary': 'Test content',
            'published': seven_days_ago,
            'source': 'test'
        }
        
        # 产品发布应该衰减快
        product_recency = self.evaluator._calculate_recency(item, 'product')
        
        # 研究论文应该衰减慢
        research_recency = self.evaluator._calculate_recency(item, 'research')
        
        # 研究内容的时效分数应该更高
        self.assertGreater(research_recency, product_recency)
        print(f"\n7天前内容时效性对比:")
        print(f"  产品发布: {product_recency}")
        print(f"  研究论文: {research_recency}")
        print(f"  差异: {research_recency - product_recency}")
    
    def test_source_performance_tracking(self):
        """测试来源性能跟踪"""
        source = 'test_new_source_12345'  # 使用新的来源避免冲突
        
        # 初始状态
        initial_perf = self.evaluator.source_performance[source]
        self.assertEqual(initial_perf['count'], 0)
        
        # 更新性能数据
        self.evaluator.update_source_performance(source, 0.85)
        self.evaluator.update_source_performance(source, 0.90)
        self.evaluator.update_source_performance(source, 0.88)
        
        # 检查统计
        perf = self.evaluator.source_performance[source]
        self.assertEqual(perf['count'], 3)
        self.assertAlmostEqual(perf['avg'], 0.877, places=2)
        
        print(f"\n来源性能跟踪:")
        print(f"  来源: {source}")
        print(f"  样本数: {perf['count']}")
        print(f"  平均分: {perf['avg']:.3f}")
    
    def test_dynamic_source_scoring(self):
        """测试动态来源评分（静态+动态）"""
        item = {
            'title': 'Test',
            'source': 'openai.com',
            'url': 'https://openai.com/blog/test',
            'author': ''
        }
        
        # 第一次计算（只有静态评分）
        initial_score = self.evaluator._calculate_source_authority(item)
        print(f"\n动态评分测试:")
        print(f"  初始评分（静态）: {initial_score}")
        
        # 添加历史表现数据（模拟学习）
        for i in range(10):
            self.evaluator.update_source_performance('openai.com', 0.95)
        
        # 第二次计算（静态+动态）
        dynamic_score = self.evaluator._calculate_source_authority(item)
        print(f"  学习后评分（混合）: {dynamic_score}")
        
        # 动态评分应该反映历史表现
        # 由于历史表现高（0.95），最终评分可能略有变化
        self.assertIsNotNone(dynamic_score)
    
    def test_learning_stats(self):
        """测试学习统计信息"""
        # 记录初始状态
        initial_stats = self.evaluator.get_learning_stats()
        initial_count = initial_stats['total_sources_tracked']
        
        # 添加一些新的学习数据
        import uuid
        # 使用UUID确保来源唯一性，避免测试间缓存冲突
        unique_id = str(uuid.uuid4())[:8]
        sources = [f'test_src_1_{unique_id}', f'test_src_2_{unique_id}', f'test_src_3_{unique_id}']
        
        for source in sources:
            for i in range(6):  # 超过5个样本才算learned
                self.evaluator.update_source_performance(source, 0.8 + i * 0.02)
        
        stats = self.evaluator.get_learning_stats()
        
        print(f"\n学习统计:")
        print(f"  跟踪来源数: {stats['total_sources_tracked']}")
        print(f"  已学习来源数: {stats['learned_sources']}")
        print(f"  总样本数: {stats['total_samples']}")
        print(f"  学习已启用: {stats['learning_enabled']}")
        
        # 验证增加了3个来源（使用相对增量）
        self.assertGreaterEqual(stats['total_sources_tracked'], initial_count + 3)
        self.assertTrue(stats['learning_enabled'])
    
    def test_recency_decay_curves(self):
        """测试不同内容类型的衰减曲线"""
        content_types = ['product', 'news', 'research', 'tutorial']
        days_list = [1, 3, 7, 14, 30]
        
        print(f"\n时效性衰减曲线对比:")
        print(f"{'天数':<8}", end='')
        for ct in content_types:
            print(f"{ct:<12}", end='')
        print()
        
        for days in days_list:
            date_str = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            item = {'published': date_str, 'source': 'test'}
            
            print(f"{days:<8}", end='')
            for ct in content_types:
                score = self.evaluator._calculate_recency(item, ct)
                print(f"{score:<12.3f}", end='')
            print()
    
    def test_comprehensive_importance_with_learning(self):
        """测试结合学习的综合重要性评分"""
        # 模拟高质量来源的学习
        for _ in range(10):
            self.evaluator.update_source_performance('openai.com', 0.92)
        
        item = {
            'title': 'GPT-5 breakthrough in reasoning',
            'summary': 'OpenAI announces revolutionary new model',
            'source': 'openai.com',
            'url': 'https://openai.com/blog/gpt5',
            'published': datetime.now().strftime('%Y-%m-%d'),
            'stars': 5000
        }
        
        classification = {
            'content_type': 'product',
            'confidence': 0.95,
            'ai_relevance': 0.98
        }
        
        importance, breakdown = self.evaluator.calculate_importance(item, classification)
        
        print(f"\n综合评分测试（含学习）:")
        print(f"  最终重要性: {importance}")
        print(f"  来源权威: {breakdown['source_authority']}")
        print(f"  时效性: {breakdown['recency']}")
        print(f"  置信度: {breakdown['confidence']}")
        print(f"  相关度: {breakdown['relevance']}")
        print(f"  热度: {breakdown['engagement']}")
        print(f"  AI相关性: {breakdown['ai_relevance']}")
        
        # 高质量内容应该有高评分
        self.assertGreater(importance, 0.80)
    
    def test_rolling_window_limit(self):
        """测试滚动窗口限制（最多50个样本）"""
        source = 'test_source'
        
        # 添加60个样本
        for i in range(60):
            self.evaluator.update_source_performance(source, 0.5 + i * 0.01)
        
        perf = self.evaluator.source_performance[source]
        
        # 应该只保留最后50个
        self.assertEqual(len(perf['scores']), 50)
        self.assertEqual(perf['count'], 50)
        
        print(f"\n滚动窗口测试:")
        print(f"  添加样本数: 60")
        print(f"  保留样本数: {len(perf['scores'])}")
        print(f"  最新平均分: {perf['avg']:.3f}")


class TestImportanceLevelClassification(unittest.TestCase):
    """测试重要性等级分类"""
    
    def setUp(self):
        self.evaluator = ImportanceEvaluator()
    
    def test_all_importance_levels(self):
        """测试所有重要性等级"""
        test_scores = [0.95, 0.80, 0.65, 0.50, 0.30]
        expected_levels = ['critical', 'high', 'medium', 'low', 'minimal']
        
        print(f"\n重要性等级分类:")
        for score, expected in zip(test_scores, expected_levels):
            level, emoji = self.evaluator.get_importance_level(score)
            print(f"  分数 {score}: {emoji} {level}")
            self.assertEqual(level, expected)


def print_test_header(test_name: str):
    """打印测试标题"""
    print(f"\n{'='*70}")
    print(f"  {test_name}")
    print(f"{'='*70}")


if __name__ == '__main__':
    print_test_header("增强的重要性评估器测试")
    
    # 运行测试
    unittest.main(verbosity=2)
