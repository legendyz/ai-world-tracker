"""
测试 LLM 分类器的智能降级策略

测试场景:
1. 超时错误 - 应触发快速降级
2. 连接错误 - 应触发断路器
3. 解析错误 - 应重试后降级
4. 限流错误 - 应等待后重试
5. 断路器机制 - 连续失败后自动开启/关闭
"""

import sys
import os
import time
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_classifier import LLMClassifier, FallbackStrategy, FallbackReason


class TestFallbackStrategy(unittest.TestCase):
    """测试降级策略类"""
    
    def setUp(self):
        """每个测试前初始化"""
        self.strategy = FallbackStrategy()
    
    def test_initial_state(self):
        """测试初始状态"""
        self.assertTrue(self.strategy.should_use_llm())
        self.assertFalse(self.strategy.circuit_breaker_open)
        self.assertEqual(len(self.strategy.error_counts), 0)
    
    def test_timeout_fallback_action(self):
        """测试超时错误 - 应返回 'quick'"""
        item = {'title': 'Test'}
        action = self.strategy.get_fallback_action(FallbackReason.TIMEOUT, item)
        self.assertEqual(action, 'quick')
    
    def test_connection_error_retry(self):
        """测试连接错误 - 断路器关闭时应重试"""
        item = {'title': 'Test'}
        action = self.strategy.get_fallback_action(FallbackReason.CONNECTION_ERROR, item)
        self.assertEqual(action, 'retry')
    
    def test_parse_error_retry(self):
        """测试解析错误 - 首次应重试"""
        item = {'title': 'Test'}
        action = self.strategy.get_fallback_action(FallbackReason.PARSE_ERROR, item)
        self.assertEqual(action, 'retry')
        
        # 第二次应该仍然重试
        self.strategy.record_error(FallbackReason.PARSE_ERROR)
        action = self.strategy.get_fallback_action(FallbackReason.PARSE_ERROR, item)
        self.assertEqual(action, 'retry')
        
        # 第三次应该降级
        self.strategy.record_error(FallbackReason.PARSE_ERROR)
        action = self.strategy.get_fallback_action(FallbackReason.PARSE_ERROR, item)
        self.assertEqual(action, 'full_rule')
    
    def test_rate_limit_retry(self):
        """测试限流错误 - 应等待后重试"""
        item = {'title': 'Test'}
        start = time.time()
        action = self.strategy.get_fallback_action(FallbackReason.RATE_LIMIT, item)
        elapsed = time.time() - start
        
        self.assertEqual(action, 'retry')
        self.assertGreaterEqual(elapsed, 2.0)  # 应该等待至少2秒
    
    def test_circuit_breaker_opens(self):
        """测试断路器 - 连续错误后应打开"""
        self.assertTrue(self.strategy.should_use_llm())
        
        # 记录5次错误（阈值）
        for _ in range(5):
            self.strategy.record_error(FallbackReason.CONNECTION_ERROR)
        
        # 断路器应该打开
        self.assertTrue(self.strategy.circuit_breaker_open)
        self.assertFalse(self.strategy.should_use_llm())
    
    def test_circuit_breaker_closes_after_timeout(self):
        """测试断路器 - 超时后应关闭"""
        # 打开断路器
        for _ in range(5):
            self.strategy.record_error(FallbackReason.API_ERROR)
        
        self.assertTrue(self.strategy.circuit_breaker_open)
        
        # 修改超时时间为1秒（方便测试）
        self.strategy.circuit_breaker_timeout = 1
        
        # 等待超时
        time.sleep(1.1)
        
        # 断路器应该关闭
        self.assertTrue(self.strategy.should_use_llm())
        self.assertFalse(self.strategy.circuit_breaker_open)
    
    def test_success_resets_errors(self):
        """测试成功调用重置错误计数"""
        # 记录一些错误
        self.strategy.record_error(FallbackReason.PARSE_ERROR)
        self.strategy.record_error(FallbackReason.TIMEOUT)
        
        self.assertGreater(len(self.strategy.error_counts), 0)
        
        # 记录成功
        self.strategy.record_success()
        
        # 错误计数应被重置
        self.assertEqual(len(self.strategy.error_counts), 0)
        self.assertEqual(len(self.strategy.last_error_time), 0)
    
    def test_circuit_breaker_affects_fallback_action(self):
        """测试断路器状态影响降级策略"""
        item = {'title': 'Test'}
        
        # 打开断路器
        for _ in range(5):
            self.strategy.record_error(FallbackReason.CONNECTION_ERROR)
        
        # 连接错误应该返回 full_rule 而不是 retry
        action = self.strategy.get_fallback_action(FallbackReason.CONNECTION_ERROR, item)
        self.assertEqual(action, 'full_rule')


class TestLLMClassifierWithFallback(unittest.TestCase):
    """测试 LLM 分类器的降级集成"""
    
    def setUp(self):
        """初始化模拟的 LLM 分类器"""
        # 使用 patch 避免实际初始化 Ollama
        with patch('llm_classifier.check_ollama_status') as mock_status:
            mock_status.return_value = {
                'running': True,
                'models': ['qwen3:8b'],
                'recommended': 'qwen3:8b'
            }
            
            with patch('llm_classifier.detect_gpu') as mock_gpu:
                mock_gpu.return_value = None
                
                self.classifier = LLMClassifier(
                    provider='ollama',
                    model='qwen3:8b',
                    enable_cache=False  # 禁用缓存以便测试
                )
    
    @patch('llm_classifier.LLMClassifier._call_ollama')
    def test_timeout_triggers_quick_fallback(self, mock_call):
        """测试超时触发快速降级"""
        # 模拟超时
        mock_call.return_value = (None, FallbackReason.TIMEOUT)
        
        item = {
            'title': 'Test Article',
            'summary': 'Test content',
            'source': 'test'
        }
        
        result = self.classifier.classify_item(item)
        
        # 应该降级到规则分类
        self.assertIn('classified_by', result)
        self.assertIn('timeout', result['classified_by'])
        self.assertEqual(self.classifier.stats['fallback_calls'], 1)
    
    @patch('llm_classifier.LLMClassifier._call_ollama')
    def test_success_after_retry(self, mock_call):
        """测试重试后成功"""
        # 第一次失败，第二次成功
        mock_call.side_effect = [
            (None, FallbackReason.PARSE_ERROR),
            ('{"category": "research", "confidence": 0.9}', None)
        ]
        
        item = {
            'title': 'AI Research Paper',
            'summary': 'Deep learning advances',
            'source': 'arxiv'
        }
        
        result = self.classifier.classify_item(item)
        
        # 应该成功分类
        self.assertEqual(result.get('content_type'), 'research')
        self.assertEqual(mock_call.call_count, 2)  # 调用了2次（1次失败+1次成功）
    
    @patch('llm_classifier.LLMClassifier._call_ollama')
    def test_circuit_breaker_prevents_calls(self, mock_call):
        """测试断路器阻止 LLM 调用"""
        # 模拟连续连接失败
        mock_call.return_value = (None, FallbackReason.CONNECTION_ERROR)
        
        items = [
            {'title': f'Test {i}', 'summary': 'Content', 'source': 'test'}
            for i in range(10)
        ]
        
        for item in items:
            self.classifier.classify_item(item)
        
        # 断路器应该在5次失败后打开
        self.assertTrue(self.classifier.fallback_strategy.circuit_breaker_open)
        
        # 后续调用应该减少（因为断路器打开）
        initial_calls = mock_call.call_count
        self.assertLessEqual(initial_calls, 7)  # 最多5次失败 + 1-2次重试


class TestIntegrationScenarios(unittest.TestCase):
    """集成测试场景"""
    
    @patch('llm_classifier.check_ollama_status')
    @patch('llm_classifier.detect_gpu')
    @patch('llm_classifier.LLMClassifier._call_ollama')
    def test_realistic_mixed_errors(self, mock_call, mock_gpu, mock_status):
        """测试真实场景的混合错误"""
        # 设置模拟
        mock_status.return_value = {'running': True, 'models': ['qwen3:8b'], 'recommended': 'qwen3:8b'}
        mock_gpu.return_value = None
        
        # 模拟不同错误类型
        mock_call.side_effect = [
            ('{"category": "research", "confidence": 0.9}', None),  # 成功
            (None, FallbackReason.TIMEOUT),  # 超时
            ('{"category": "product", "confidence": 0.85}', None),  # 成功
            (None, FallbackReason.PARSE_ERROR),  # 解析错误
            ('{"category": "market", "confidence": 0.8}', None),  # 重试成功
        ]
        
        classifier = LLMClassifier(provider='ollama', model='qwen3:8b', enable_cache=False)
        
        items = [
            {'title': f'Item {i}', 'summary': 'Content', 'source': 'test'}
            for i in range(4)
        ]
        
        results = []
        for item in items:
            result = classifier.classify_item(item)
            results.append(result)
        
        # 检查统计
        stats = classifier.get_stats()
        print("\n=== 测试统计 ===")
        print(f"LLM 成功调用: {stats['llm_calls']}")
        print(f"降级调用: {stats['fallback_calls']}")
        print(f"错误次数: {stats['errors']}")
        print(f"缓存命中: {stats['cache_hits']}")
        
        # 验证结果
        self.assertGreater(stats['llm_calls'], 0)
        self.assertGreater(stats['fallback_calls'], 0)


def print_test_header(test_name: str):
    """打印测试标题"""
    print(f"\n{'='*70}")
    print(f"  {test_name}")
    print(f"{'='*70}")


if __name__ == '__main__':
    print_test_header("LLM 分类器降级策略测试")
    
    # 运行测试
    unittest.main(verbosity=2)
