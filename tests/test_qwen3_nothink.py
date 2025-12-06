"""快速测试 Qwen3:8b (no_think 模式)"""
from llm_classifier import LLMClassifier
import time

classifier = LLMClassifier(
    provider='ollama',
    model='qwen3:8b',
    enable_cache=False
)

test_item = {
    'title': 'OpenAI officially launches GPT-4o with new features',
    'summary': 'OpenAI announces the general availability of GPT-4o model with multimodal capabilities',
    'source': 'TechCrunch'
}

print("=" * 60)
print("测试 Qwen3:8b (no_think 模式)")
print("=" * 60)

start = time.time()
result = classifier.classify_item(test_item)
elapsed = time.time() - start

print(f"\n📝 标题: {test_item['title']}")
print(f"\n📊 结果:")
print(f"   类别: {result.get('content_type')}")
print(f"   置信度: {result.get('confidence', 0):.0%}")
print(f"   分类器: {result.get('classified_by')}")
print(f"   理由: {result.get('llm_reasoning', 'N/A')}")
print(f"\n⏱️ 耗时: {elapsed:.1f}s")
