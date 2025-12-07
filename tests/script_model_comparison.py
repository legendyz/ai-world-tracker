"""测试 Qwen3:8b vs DeepSeek R1:8b 分类效果对比"""
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

def run_model_test(model_name: str):
    """运行单个模型测试（非 pytest 测试函数）"""
    print(f"\n{'=' * 60}")
    print(f"测试模型: {model_name}")
    print(f"{'=' * 60}")
    
    classifier = LLMClassifier(
        provider='ollama',
        model=model_name,
        enable_cache=False  # 禁用缓存以便公平测试
    )
    
    total_time = 0
    results = []
    
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
        
        results.append({
            'expected': test['expected'],
            'actual': result.get('content_type'),
            'time': elapsed
        })
    
    print(f"\n📊 {model_name} 总结:")
    print(f"   平均耗时: {total_time/len(test_cases):.1f}s")
    print(f"   总耗时: {total_time:.1f}s")
    
    return results

# 测试 Qwen3:8b
print("\n" + "🚀" * 30)
print("   Qwen3:8b vs DeepSeek R1:8b 对比测试")
print("🚀" * 30)

qwen_results = run_model_test('qwen3:8b')

print("\n" + "-" * 60)

r1_results = run_model_test('deepseek-r1:8b')

# 对比总结
print("\n" + "=" * 60)
print("📊 最终对比")
print("=" * 60)
print(f"{'测试项':<30} {'Qwen3:8b':<15} {'DeepSeek R1:8b':<15}")
print("-" * 60)
for i, (q, r) in enumerate(zip(qwen_results, r1_results), 1):
    print(f"测试 {i} 结果:                  {q['actual']:<15} {r['actual']:<15}")
print("-" * 60)
qwen_avg = sum(r['time'] for r in qwen_results) / len(qwen_results)
r1_avg = sum(r['time'] for r in r1_results) / len(r1_results)
print(f"{'平均响应时间:':<30} {qwen_avg:.1f}s{'':<10} {r1_avg:.1f}s")
print(f"{'速度提升:':<30} {r1_avg/qwen_avg:.1f}x 更快" if qwen_avg < r1_avg else f"{'速度对比:':<30} 相近")
