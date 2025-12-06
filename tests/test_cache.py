"""测试 LLM 分类器的缓存功能"""
from llm_classifier import LLMClassifier
import time

# 启用缓存
classifier = LLMClassifier(
    provider='ollama',
    model='qwen3:8b',
    enable_cache=True
)

test_item = {
    'title': 'OpenAI officially launches GPT-4o with new features',
    'summary': 'OpenAI announces the general availability of GPT-4o model',
    'source': 'TechCrunch'
}

print('=' * 50)
print('🔄 测试缓存功能')
print('=' * 50)

# 第一次调用
print('\n📝 第一次调用 (无缓存)...')
start = time.time()
result1 = classifier.classify_item(test_item)
t1 = time.time() - start
print(f'   结果: {result1.get("content_type")}')
print(f'   耗时: {t1:.1f}s')
print(f'   缓存命中: {result1.get("from_cache", False)}')

# 第二次调用 (应该命中缓存)
print('\n📝 第二次调用 (应命中缓存)...')
start = time.time()
result2 = classifier.classify_item(test_item)
t2 = time.time() - start
print(f'   结果: {result2.get("content_type")}')
print(f'   耗时: {t2:.4f}s')
print(f'   缓存命中: {result2.get("from_cache", False)}')

# 第三次调用 (验证缓存)
print('\n📝 第三次调用 (验证缓存)...')
start = time.time()
result3 = classifier.classify_item(test_item)
t3 = time.time() - start
print(f'   结果: {result3.get("content_type")}')
print(f'   耗时: {t3:.4f}s')
print(f'   缓存命中: {result3.get("from_cache", False)}')

# 统计
print('\n' + '=' * 50)
print('📊 统计')
print('=' * 50)
stats = classifier.get_stats()
print(f'   LLM调用: {stats["llm_calls"]}')
print(f'   缓存命中: {stats["cache_hits"]}')
print(f'   速度提升: {t1/t2:.0f}x (第一次 vs 第二次)')
