"""测试 Qwen3:8b 优化后的效果"""
from llm_classifier import LLMClassifier
import time

# 测试用例
test_cases = [
    {
        'title': 'OpenAI officially launches GPT-4o with new features',
        'summary': 'OpenAI announces the general availability of GPT-4o model with multimodal capabilities',
        'source': 'TechCrunch',
        'expected': 'llm/product'
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
print("🚀 Qwen3:8b 优化测试 (Chat API + think=false)")
print("=" * 60)

classifier = LLMClassifier(
    provider='ollama',
    model='qwen3:8b',
    enable_cache=False
)

total_time = 0

for i, test in enumerate(test_cases, 1):
    print(f"\n📝 测试 {i}: {test['title'][:40]}...")
    
    start = time.time()
    result = classifier.classify_item(test)
    elapsed = time.time() - start
    total_time += elapsed
    
    print(f"   预期: {test['expected']}")
    print(f"   实际: {result.get('content_type')}")
    print(f"   置信度: {result.get('confidence', 0):.0%}")
    print(f"   耗时: {elapsed:.1f}s")
    print(f"   理由: {result.get('llm_reasoning', 'N/A')[:50]}")

print("\n" + "=" * 60)
print("📊 测试总结")
print("=" * 60)
print(f"   总测试数: {len(test_cases)}")
print(f"   总耗时: {total_time:.1f}s")
print(f"   平均耗时: {total_time/len(test_cases):.1f}s")

stats = classifier.get_stats()
print(f"\n📈 分类器统计:")
print(f"   LLM调用: {stats['llm_calls']}")
print(f"   降级调用: {stats['fallback_calls']}")
print(f"   错误: {stats['errors']}")
