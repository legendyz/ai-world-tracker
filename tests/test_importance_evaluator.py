"""
测试多维度重要性评估功能

验证 ImportanceEvaluator 在规则分类和LLM分类中的表现
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_classifier import ContentClassifier
from importance_evaluator import ImportanceEvaluator


def test_importance_evaluator_standalone():
    """测试独立的重要性评估器"""
    print("\n" + "=" * 60)
    print("🧪 测试 ImportanceEvaluator 独立功能")
    print("=" * 60)
    
    evaluator = ImportanceEvaluator()
    
    # 测试用例
    test_cases = [
        {
            'name': '高重要性 - OpenAI官方发布',
            'item': {
                'title': 'OpenAI Announces GPT-5 Release',
                'summary': 'OpenAI officially launches GPT-5 with breakthrough reasoning capabilities',
                'source': 'openai.com/blog',
                'url': 'https://openai.com/blog/gpt-5',
                'published': '2025-12-07',
                'stars': 0
            },
            'classification': {'content_type': 'product', 'confidence': 0.95}
        },
        {
            'name': '中等重要性 - Reddit讨论',
            'item': {
                'title': 'Local LLM comparison: Llama vs Qwen',
                'summary': 'Community discussion about running LLMs locally',
                'source': 'Reddit (LocalLLaMA)',
                'url': 'https://reddit.com/r/LocalLLaMA/...',
                'published': '2025-12-05',
                'score': 150
            },
            'classification': {'content_type': 'community', 'confidence': 0.70}
        },
        {
            'name': '高重要性 - ArXiv研究',
            'item': {
                'title': 'SOTA: New Transformer Architecture Achieves State-of-the-Art',
                'summary': 'A breakthrough paper on efficient transformers with benchmark results',
                'source': 'arXiv',
                'url': 'https://arxiv.org/abs/2512.xxxxx',
                'published': '2025-12-06'
            },
            'classification': {'content_type': 'research', 'confidence': 0.92}
        },
        {
            'name': '低重要性 - 旧新闻',
            'item': {
                'title': 'AI trends in 2025',
                'summary': 'General overview of AI industry trends',
                'source': 'generic-news.com',
                'url': 'https://generic-news.com/ai-trends',
                'published': '2025-11-01'
            },
            'classification': {'content_type': 'news', 'confidence': 0.55}
        },
        {
            'name': '高重要性 - GitHub热门项目',
            'item': {
                'title': 'microsoft/DeepSpeed',
                'summary': 'DeepSpeed is a deep learning optimization library',
                'source': 'GitHub',
                'url': 'https://github.com/microsoft/DeepSpeed',
                'published': '2025-12-07',
                'stars': 35000
            },
            'classification': {'content_type': 'developer', 'confidence': 0.88}
        },
    ]
    
    print("\n📊 评估结果:\n")
    
    for case in test_cases:
        importance, breakdown = evaluator.calculate_importance(
            case['item'], 
            case['classification']
        )
        level, emoji = evaluator.get_importance_level(importance)
        
        print(f"{emoji} {case['name']}")
        print(f"   总分: {importance:.3f} ({level})")
        print(f"   明细: 来源={breakdown['source_authority']:.2f} | "
              f"时效={breakdown['recency']:.2f} | "
              f"置信={breakdown['confidence']:.2f} | "
              f"相关={breakdown['relevance']:.2f} | "
              f"热度={breakdown['engagement']:.2f}")
        print()
    
    return True


def test_rule_classifier_with_importance():
    """测试规则分类器集成重要性评估"""
    print("\n" + "=" * 60)
    print("🧪 测试 ContentClassifier 集成重要性评估")
    print("=" * 60)
    
    classifier = ContentClassifier()
    
    test_items = [
        {
            'title': 'Google releases Gemini 2.0 with multimodal capabilities',
            'summary': 'Google officially announces Gemini 2.0, featuring advanced reasoning and multimodal support',
            'source': 'blog.google',
            'url': 'https://blog.google/technology/ai/gemini-2',
            'published': '2025-12-07'
        },
        {
            'title': 'New paper: Efficient Attention Mechanisms',
            'summary': 'A survey on efficient attention mechanisms for large language models from arxiv',
            'source': 'arXiv',
            'url': 'https://arxiv.org/abs/2512.12345',
            'published': '2025-12-06',
            'category': 'research'
        },
        {
            'title': 'huggingface/transformers v5.0 released',
            'summary': 'Major update to the transformers library with new model architectures',
            'source': 'GitHub',
            'url': 'https://github.com/huggingface/transformers',
            'published': '2025-12-05',
            'stars': 132000,
            'category': 'developer'
        },
    ]
    
    print("\n📊 分类与重要性评估结果:\n")
    
    for item in test_items:
        result = classifier.classify_item(item)
        
        level, emoji = classifier.importance_evaluator.get_importance_level(result['importance'])
        
        print(f"{emoji} {result['title'][:50]}...")
        print(f"   类型: {result['content_type']} (置信度: {result['confidence']:.2%})")
        print(f"   重要性: {result['importance']:.3f} ({result['importance_level']})")
        if 'importance_breakdown' in result:
            bd = result['importance_breakdown']
            print(f"   明细: 来源={bd['source_authority']:.2f} | "
                  f"时效={bd['recency']:.2f} | "
                  f"置信={bd['confidence']:.2f} | "
                  f"相关={bd['relevance']:.2f} | "
                  f"热度={bd['engagement']:.2f}")
        print()
    
    return True


def test_batch_classification():
    """测试批量分类"""
    print("\n" + "=" * 60)
    print("🧪 测试批量分类重要性统计")
    print("=" * 60)
    
    classifier = ContentClassifier()
    
    items = [
        {'title': 'OpenAI GPT-5', 'summary': 'Major release', 'source': 'openai.com', 'published': '2025-12-07'},
        {'title': 'AI News roundup', 'summary': 'Weekly AI news', 'source': 'news.com', 'published': '2025-12-05'},
        {'title': 'New paper on transformers', 'summary': 'Research breakthrough', 'source': 'arxiv', 'published': '2025-12-06'},
        {'title': 'GitHub trending: LLM project', 'summary': 'Open source', 'source': 'github.com', 'published': '2025-12-04', 'stars': 5000},
        {'title': 'Sam Altman interview', 'summary': 'CEO says AGI coming', 'source': 'interview', 'published': '2025-12-07', 'author': 'Sam Altman'},
    ]
    
    print("\n📊 开始批量分类...\n")
    results = classifier.classify_batch(items)
    
    print("\n📋 详细结果:")
    for r in results:
        level, emoji = classifier.importance_evaluator.get_importance_level(r['importance'])
        print(f"   {emoji} {r['title'][:40]}... -> {r['content_type']} | 重要性: {r['importance']:.2f}")
    
    return True


if __name__ == '__main__':
    print("\n" + "🌟" * 30)
    print("   多维度重要性评估测试")
    print("🌟" * 30)
    
    # 运行测试
    test_importance_evaluator_standalone()
    test_rule_classifier_with_importance()
    test_batch_classification()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)
