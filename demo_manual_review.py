"""
人工审核功能演示
展示完整的审核流程
"""

from manual_reviewer import ManualReviewer

print("="*70)
print("🎬 人工审核功能演示")
print("="*70)

# 创建测试数据（模拟低置信度的分类结果）
test_data = [
    {
        'title': 'OpenAI might release GPT-5 next month according to rumors',
        'summary': 'Unconfirmed speculation about possible launch from tech sources',
        'source': 'Tech Blog',
        'content_type': 'product',
        'confidence': 0.35,
        'needs_review': True,
        'tech_categories': ['Generative AI'],
        'region': 'USA'
    },
    {
        'title': 'Research paper on GitHub with TensorFlow implementation',
        'summary': 'Academic study about neural architecture search published on arXiv with code',
        'source': 'arXiv/GitHub',
        'content_type': 'developer',
        'confidence': 0.55,
        'secondary_labels': ['research'],
        'needs_review': True,
        'tech_categories': ['General AI'],
        'region': 'Global'
    },
    {
        'title': 'Google officially announces Gemini 2.0 release',
        'summary': 'Official press release from Google about new AI model available now',
        'source': 'Google Official Blog',
        'content_type': 'product',
        'confidence': 0.95,
        'needs_review': False,
        'tech_categories': ['Generative AI'],
        'region': 'USA'
    },
    {
        'title': 'Spam: Click here for free AI tools!!!',
        'summary': 'Advertisement link with no real content',
        'source': 'Unknown',
        'content_type': 'market',
        'confidence': 0.12,
        'needs_review': True,
        'tech_categories': ['General AI'],
        'region': 'Global'
    }
]

reviewer = ManualReviewer()

print("\n📊 演示数据统计:")
print(f"   总数据: {len(test_data)} 条")

review_items = reviewer.get_items_for_review(test_data, min_confidence=0.6)
print(f"   需要审核: {len(review_items)} 条")

print("\n" + "="*70)
print("需要审核的内容概览:")
print("="*70)

for i, item in enumerate(review_items, 1):
    print(f"\n[{i}] {item['title']}")
    print(f"    当前分类: {item['content_type']}")
    print(f"    置信度: {item['confidence']:.1%}")
    print(f"    建议操作:")
    
    # 给出审核建议
    if item['confidence'] < 0.2:
        print(f"       ⚠️  极低置信度 - 建议检查是否为垃圾内容")
    elif item['confidence'] < 0.4:
        print(f"       ⚠️  低置信度 - 建议重新分类")
    elif item['confidence'] < 0.6:
        print(f"       ℹ️  中等置信度 - 建议确认分类")
    
    if 'rumor' in item['title'].lower() or 'might' in item['title'].lower():
        print(f"       🔍 检测到不确定性词汇 - 注意验证真实性")
    
    if item.get('secondary_labels'):
        print(f"       💡 有次要标签 {item['secondary_labels']} - 考虑是否为主分类")

print("\n" + "="*70)
print("💡 使用说明:")
print("="*70)
print("""
在实际使用中，你可以：

1. 在主程序中选择 "5. 📝 人工审核分类"
2. 系统会显示类似上面的内容列表
3. 逐条审核时，你可以：
   - 输入 1: 确认分类正确
   - 输入 2: 修改分类（会显示选项菜单）
   - 输入 3: 修改技术领域
   - 输入 4: 修改地区
   - 输入 5: 删除垃圾内容
   - 输入 0: 跳过（稍后处理）

4. 审核完成后自动保存结果和历史记录

示例审核场景:

案例1 (传闻新闻，置信度35%):
  → 应该降级为 "market" 或标记为垃圾

案例2 (GitHub研究项目，置信度55%):
  → 保持 "developer" 分类，次要标签已正确标注

案例3 (官方发布，置信度95%):
  → 无需审核，置信度很高

案例4 (垃圾内容，置信度12%):
  → 应该选择选项5删除
""")

print("\n" + "="*70)
print("🚀 现在运行主程序开始实际审核:")
print("   python TheWorldOfAI.py")
print("="*70)
