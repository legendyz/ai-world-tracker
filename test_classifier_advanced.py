"""测试增强的分类器功能"""
from content_classifier import ContentClassifier

classifier = ContentClassifier()

# 测试更多边界情况
test_cases = [
    {
        'title': 'Rumor: GPT-5 release is fake news',
        'summary': 'Not confirmed by OpenAI, speculation about GPT-5 launch is false',
        'source': 'TechNews'
    },
    {
        'title': 'GitHub releases new AI code assistant',
        'summary': 'Official launch of Copilot X with enhanced capabilities',
        'source': 'GitHub Blog'
    },
    {
        'title': 'Deep Learning paper on arXiv',
        'summary': 'Research study on neural network optimization published on arxiv.org',
        'source': 'arXiv'
    },
    {
        'title': '小公司推出AI助手',
        'summary': '一家创业公司发布了新的AI对话产品',
        'source': 'Tech媒体'
    },
    {
        'title': 'Sam Altman interview on AI safety',
        'summary': 'OpenAI CEO stated his views on artificial intelligence alignment in exclusive interview',
        'source': 'The Verge'
    }
]

results = classifier.classify_batch(test_cases)

print("\n" + "="*60)
print("详细分类结果分析")
print("="*60)

for i, item in enumerate(results, 1):
    print(f"\n案例 {i}: {item['title']}")
    print(f"  ├─ 分类: {item['content_type']}")
    print(f"  ├─ 置信度: {item['confidence']:.1%}")
    print(f"  ├─ 技术领域: {', '.join(item['tech_categories'])}")
    print(f"  ├─ 地区: {item['region']}")
    if item.get('needs_review'):
        print(f"  └─ ⚠️  需要人工审核")
    else:
        print(f"  └─ ✅ 分类可信")
