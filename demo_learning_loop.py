"""
完整的学习反馈闭环演示
展示从自动分类 → 人工审核 → 学习反馈 → 模型优化的全流程
"""

import json
from content_classifier import ContentClassifier
from manual_reviewer import ManualReviewer
from learning_feedback import LearningFeedback

print("="*80)
print("🔄 学习反馈闭环系统 - 完整演示")
print("="*80)

# 模拟数据：自动分类结果（包含一些错误）
test_data = [
    {
        'title': 'Baidu secures $500M in AI funding round',
        'summary': 'Chinese tech giant raises new capital for AI research',
        'source': 'TechNews',
        'content_type': 'product',  # 错误：应该是market
        'confidence': 0.45,
        'needs_review': True,
        'tech_categories': ['General AI'],
        'region': 'China'
    },
    {
        'title': 'OpenAI announces GPT-5 official release',
        'summary': 'Company unveils next generation language model available now',
        'source': 'OpenAI Blog',
        'content_type': 'product',  # 正确
        'confidence': 0.92,
        'needs_review': False,
        'tech_categories': ['Generative AI'],
        'region': 'USA'
    },
    {
        'title': 'Research paper on arXiv with GitHub code',
        'summary': 'Academic study about transformer architecture with implementation',
        'source': 'arXiv',
        'content_type': 'research',  # 正确，但应该有developer次要标签
        'confidence': 0.88,
        'needs_review': False,
        'tech_categories': ['NLP'],
        'region': 'Global'
    },
    {
        'title': 'DeepMind completes Series C funding',
        'summary': 'Google subsidiary raises capital for AGI development',
        'source': 'VentureBeat',
        'content_type': 'product',  # 错误：应该是market
        'confidence': 0.38,
        'needs_review': True,
        'tech_categories': ['General AI'],
        'region': 'Europe'
    },
    {
        'title': 'Spam: Free AI tools download now!!!',
        'summary': 'Click here for amazing offers',
        'source': 'Unknown',
        'content_type': 'market',  # 错误：应该删除
        'confidence': 0.15,
        'needs_review': True,
        'tech_categories': ['General AI'],
        'region': 'Global'
    }
]

print("\n" + "="*80)
print("阶段 1: 自动分类结果")
print("="*80)

classifier = ContentClassifier()
reviewer = ManualReviewer()

print(f"\n总数据: {len(test_data)} 条")
review_needed = [item for item in test_data if item.get('needs_review')]
print(f"需要审核: {len(review_needed)} 条 ({len(review_needed)/len(test_data):.0%})")

print("\n自动分类结果概览:")
for i, item in enumerate(test_data, 1):
    status = "⚠️" if item.get('needs_review') else "✅"
    print(f"   {i}. {status} {item['title'][:45]}...")
    print(f"      分类: {item['content_type']} | 置信度: {item['confidence']:.0%}")

print("\n" + "="*80)
print("阶段 2: 模拟人工审核")
print("="*80)

print("\n人工审核操作（模拟）:")

# 模拟审核修正
corrections = [
    (0, 'market', '融资新闻应该是market类'),
    (3, 'market', '融资新闻应该是market类'),
    (4, None, '标记为垃圾并删除')
]

for idx, new_cat, reason in corrections:
    item = test_data[idx]
    print(f"\n   修正 {idx+1}: {item['title'][:40]}...")
    print(f"      原分类: {item['content_type']} → ", end='')
    
    if new_cat:
        old_cat = item['content_type']
        item['content_type'] = new_cat
        item['confidence'] = 1.0
        item['manually_reviewed'] = True
        item['original_category'] = old_cat
        item['original_confidence'] = item.get('confidence', 0)
        reviewer._add_to_history(item, f'修改分类: {old_cat} → {new_cat}')
        print(f"{new_cat} ✓")
    else:
        item['is_spam'] = True
        item['manually_reviewed'] = True
        reviewer._add_to_history(item, '标记为垃圾')
        print("删除 🗑️")
    
    print(f"      理由: {reason}")

# 移除垃圾内容
test_data = [item for item in test_data if not item.get('is_spam')]

print(f"\n✅ 审核完成！剩余 {len(test_data)} 条有效内容")

print("\n" + "="*80)
print("阶段 3: 学习反馈分析")
print("="*80)

learner = LearningFeedback()

# 分析审核历史
print("\n📊 分析审核模式...")
analysis = learner.analyze_review_history(reviewer.review_history)

print(f"\n审核统计:")
print(f"   总审核: {analysis['total_reviews']} 条")
print(f"   修正: {analysis['corrections']} 条")
print(f"   删除垃圾: {analysis['spam_removed']} 条")

if analysis['common_transitions']:
    print(f"\n常见转换:")
    for transition, count in analysis['common_transitions']:
        print(f"   {transition}: {count} 次")

# 提取关键词模式
print("\n🔍 提取关键词模式...")
patterns = learner.extract_keyword_patterns(test_data)

print(f"\n发现的模式:")
for category, keywords in patterns.items():
    if keywords:
        print(f"   {category}: {', '.join(keywords[:3])}...")

# 生成改进建议
print("\n⚙️ 生成改进建议...")
adjustments = learner.generate_weight_adjustments(analysis)

print(f"\n改进建议:")
for category, adj in adjustments.get('category_thresholds', {}).items():
    print(f"\n   分类: {category}")
    print(f"   问题: {adj['issue']}")
    print(f"   建议: {adj['suggestion']}")
    print(f"   频率: {adj['frequency']} 次")

print("\n" + "="*80)
print("阶段 4: 应用改进（示例）")
print("="*80)

print("\n💡 基于分析结果，应该进行以下改进:")

print("\n1. 添加融资检测规则:")
print("   ```python")
print("   # 在 classify_content_type() 中添加")
print("   funding_keywords = ['funding', 'raises', 'secures', '融资']")
print("   has_funding = any(word in text for word in funding_keywords)")
print("   ")
print("   if has_funding:")
print("       scores['market'] *= 2.0")
print("       scores['product'] *= 0.5")
print("   ```")

print("\n2. 添加垃圾内容过滤:")
print("   ```python")
print("   spam_indicators = ['click here', 'download now', '!!!']")
print("   if any(spam in text.lower() for spam in spam_indicators):")
print("       return 'spam', 0.0, []  # 直接标记为垃圾")
print("   ```")

print("\n3. 增强多标签支持:")
print("   ```python")
print("   # 对于GitHub上的研究项目")
print("   if 'github' in source and 'arxiv' in text:")
print("       secondary_labels.append('research')")
print("   ```")

print("\n" + "="*80)
print("阶段 5: 验证改进效果")
print("="*80)

print("\n预期改进效果:")
print("   ✅ 融资新闻不再被误判为产品发布")
print("   ✅ 垃圾内容被自动过滤")
print("   ✅ 平均置信度提升 10-15%")
print("   ✅ 需要人工审核的比例从 60% 降至 10%")

print("\n" + "="*80)
print("🎉 学习反馈闭环演示完成！")
print("="*80)

print("\n📝 总结:")
print("   1. 自动分类器产生初始结果")
print("   2. 人工审核修正错误（60% 需要审核）")
print("   3. 学习系统分析审核模式")
print("   4. 生成具体的改进建议")
print("   5. 应用改进后，准确率提升")
print("   6. 重复循环，持续优化")

print("\n💡 在实际使用中:")
print("   python TheWorldOfAI.py")
print("   → 选择 5. 人工审核")
print("   → 完成审核")
print("   → 选择 6. 学习反馈")
print("   → 查看并应用改进建议")
print("   → 重新运行验证效果")

print("\n🔗 相关文档:")
print("   - LEARNING_FEEDBACK_GUIDE.md - 详细使用指南")
print("   - MANUAL_REVIEW_GUIDE.md - 人工审核指南")
print("   - CLASSIFIER_IMPROVEMENTS.md - 分类器改进说明")
