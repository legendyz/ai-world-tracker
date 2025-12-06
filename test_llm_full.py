"""全面测试 LLM 分类器 - DeepSeek R1:8b"""
from llm_classifier import LLMClassifier

# 使用8b模型测试
classifier = LLMClassifier(
    provider='ollama',
    model='deepseek-r1:8b',
    enable_cache=True
)

# 多个测试用例
test_cases = [
    {
        'title': 'OpenAI officially launches GPT-4o with new features',
        'summary': 'OpenAI announces the general availability of GPT-4o model with multimodal capabilities',
        'source': 'TechCrunch',
        'expected': 'llm or product'
    },
    {
        'title': 'New research paper: Attention is All You Need 2.0',
        'summary': 'Researchers publish groundbreaking paper on transformer architecture improvements',
        'source': 'arXiv',
        'expected': 'research'
    },
    {
        'title': 'Tesla unveils humanoid robot Optimus Gen 3',
        'summary': 'Tesla announces next generation of its humanoid robot with improved capabilities',
        'source': 'The Verge',
        'expected': 'robotics'
    },
    {
        'title': 'EU passes comprehensive AI regulation act',
        'summary': 'European Union finalizes AI Act with strict requirements for high-risk AI systems',
        'source': 'Reuters',
        'expected': 'ethics'
    }
]

print("=" * 60)
print("LLM 分类器全面测试 - DeepSeek R1:8b")
print("=" * 60)

for i, test in enumerate(test_cases, 1):
    print(f"\n📝 测试 {i}: {test['title'][:40]}...")
    print(f"   预期类别: {test['expected']}")
    
    result = classifier.classify_item(test)
    
    print(f"   实际类别: {result.get('content_type')}")
    print(f"   置信度: {result.get('confidence', 0):.1%}")
    print(f"   分类器: {result.get('classified_by', 'N/A')}")
    print(f"   理由: {result.get('llm_reasoning', 'N/A')}")

# 打印统计信息
print("\n" + "=" * 60)
print("📊 统计信息")
print("=" * 60)
stats = classifier.get_stats()
print(f"   总调用: {stats['total_calls']}")
print(f"   LLM调用: {stats['llm_calls']}")
print(f"   缓存命中: {stats['cache_hits']}")
print(f"   降级调用: {stats['fallback_calls']}")
print(f"   错误: {stats['errors']}")
