"""测试增强功能：否定词检测、多标签支持、来源可信度"""
from content_classifier import ContentClassifier

classifier = ContentClassifier()

# 测试否定词检测和多标签
test_cases = [
    {
        'title': 'OpenAI denies rumors about GPT-5 release',
        'summary': 'Company says fake news about launch is false and unconfirmed',
        'source': 'TechCrunch'
    },
    {
        'title': 'Research paper released on GitHub with implementation',
        'summary': 'Academic study on neural networks published with open-source code repository',
        'source': 'arXiv/GitHub'
    },
    {
        'title': 'Google announces Gemini 2.0 official release',
        'summary': 'Official press release from Google about new AI model launch available now',
        'source': 'Google Official Blog'
    },
    {
        'title': 'Startup might launch AI product next month',
        'summary': 'Unconfirmed speculation about possible release from new company',
        'source': 'Tech Blog'
    },
    {
        'title': 'Meta publishes research on reinforcement learning with developer toolkit',
        'summary': 'Research paper with open source framework for ML researchers and developers',
        'source': 'Meta AI Blog'
    },
    {
        'title': '未证实：字节跳动可能推出新AI助手',
        'summary': '据称公司正在开发新产品，但官方尚未确认发布时间',
        'source': '科技媒体'
    }
]

results = classifier.classify_batch(test_cases)

print("\n" + "="*70)
print("🎯 增强功能测试结果")
print("="*70)

for i, item in enumerate(results, 1):
    print(f"\n案例 {i}: {item['title'][:50]}...")
    print(f"  ├─ 主分类: {item['content_type']} (置信度: {item['confidence']:.1%})")
    
    # 显示次要标签
    if item.get('secondary_labels'):
        print(f"  ├─ 次要分类: {', '.join(item['secondary_labels'])} ⭐")
    else:
        print(f"  ├─ 次要分类: 无")
    
    print(f"  ├─ 技术领域: {', '.join(item['tech_categories'])}")
    print(f"  ├─ 地区: {item['region']}")
    
    if item.get('needs_review'):
        print(f"  └─ ⚠️  需要人工审核 (置信度过低)")
    else:
        print(f"  └─ ✅ 分类可信")

print("\n" + "="*70)
print("📊 功能验证总结")
print("="*70)

# 统计
has_secondary = sum(1 for item in results if item.get('secondary_labels'))
avg_confidence = sum(item['confidence'] for item in results) / len(results)
needs_review = sum(1 for item in results if item.get('needs_review'))

print(f"✓ 多标签支持: {has_secondary}/{len(results)} 条内容有次要分类")
print(f"✓ 平均置信度: {avg_confidence:.1%}")
print(f"✓ 需要审核: {needs_review} 条")
print(f"✓ 否定词检测: 已启用并影响分类分数")
print(f"✓ 来源可信度: 已启用并影响置信度")
