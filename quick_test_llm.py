"""快速测试LLM分类"""
from llm_classifier import LLMClassifier

# 使用Qwen3:8b模型测试
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

print('测试LLM分类（使用qwen3:8b模型）...')
result = classifier.classify_item(test_item)

print(f'\n分类结果:')
print(f'  类型: {result.get("content_type")}')
print(f'  置信度: {result.get("confidence", 0):.1%}')
print(f'  理由: {result.get("llm_reasoning", "N/A")}')
print(f'  分类器: {result.get("classified_by", "N/A")}')
