"""
演示人工审核中的网页链接功能
"""

from manual_reviewer import ManualReviewer


def demo_review_with_links():
    """演示审核界面中的链接显示"""
    
    # 模拟一些带链接的待审核内容
    test_items = [
        {
            'title': 'OpenAI Launches GPT-5 with Enhanced Reasoning',
            'source': 'TechCrunch',
            'link': 'https://techcrunch.com/2025/openai-gpt5',
            'summary': 'OpenAI today announced GPT-5, featuring significant improvements in logical reasoning and multi-step problem solving...',
            'content_type': 'product',  # 可能应该是research
            'confidence': 0.55,
            'tech_categories': ['NLP', 'LLM'],
            'region': 'Global'
        },
        {
            'title': 'Google Releases Open Source ML Framework',
            'source': 'GitHub',
            'url': 'https://github.com/google/new-ml-framework',  # 使用url字段
            'description': 'A new machine learning framework for efficient model training...',
            'content_type': 'developer',
            'confidence': 0.58,
            'tech_categories': ['ML Framework'],
            'region': 'Global'
        },
        {
            'title': 'AI Startup Raises $100M Series B',
            'source': 'VentureBeat',
            'link': 'https://venturebeat.com/ai-startup-funding',
            'summary': 'AI startup focused on enterprise solutions announced $100M funding...',
            'content_type': 'product',  # 应该是market
            'confidence': 0.52,
            'tech_categories': ['Enterprise AI'],
            'region': 'US'
        },
        {
            'title': 'No Link Example - Research Paper',
            'source': 'arXiv',
            'summary': 'A theoretical paper on advanced neural architectures...',
            'content_type': 'research',
            'confidence': 0.48,
            'tech_categories': ['Deep Learning'],
            'region': 'Global'
        }
    ]
    
    print("="*70)
    print("📋 人工审核演示 - 网页链接功能")
    print("="*70)
    print(f"\n共有 {len(test_items)} 条内容需要审核")
    print("\n新功能:")
    print("  ✅ 显示内容的网页链接")
    print("  ✅ 可以直接在浏览器中打开链接查看完整内容")
    print("  ✅ 支持 'link' 和 'url' 两种字段")
    print("\n" + "="*70)
    
    # 创建审核器
    reviewer = ManualReviewer()
    
    # 显示每条内容的信息
    print("\n待审核内容预览:")
    for i, item in enumerate(test_items, 1):
        link = item.get('link') or item.get('url')
        has_link = "🔗 有链接" if link else "❌ 无链接"
        print(f"\n{i}. {item['title']}")
        print(f"   分类: {item['content_type']} (置信度: {item['confidence']:.1%})")
        print(f"   {has_link}")
        if link:
            print(f"   链接: {link}")
    
    # 询问是否开始审核
    print("\n" + "="*70)
    response = input("\n是否开始交互式审核? (Y/N): ").strip().lower()
    
    if response == 'y':
        print("\n开始审核...\n")
        print("提示:")
        print("  - 看到链接后，可以选择 '6' 在浏览器中打开查看")
        print("  - 查看完内容后返回终端继续选择操作")
        print("  - 如果不需要查看链接，直接选择其他操作即可")
        print("\n按 Enter 继续...")
        input()
        
        # 开始批量审核
        reviewed_items = reviewer.batch_review(
            test_items,
            min_confidence=0.6,
            auto_skip_high=False
        )
        
        # 显示审核结果
        print("\n" + "="*70)
        print("📊 审核结果总结")
        print("="*70)
        
        reviewed_count = sum(1 for item in reviewed_items if item.get('manually_reviewed'))
        spam_count = sum(1 for item in reviewed_items if item.get('is_spam'))
        modified_count = sum(1 for item in reviewed_items 
                            if item.get('manually_reviewed') and 
                            item.get('original_category') and
                            item.get('original_category') != item.get('content_type'))
        
        print(f"\n总共审核: {reviewed_count} 条")
        print(f"修改分类: {modified_count} 条")
        print(f"标记垃圾: {spam_count} 条")
        print(f"保持不变: {reviewed_count - modified_count - spam_count} 条")
        
        # 显示审核历史
        if reviewer.review_history:
            print("\n审核历史:")
            for record in reviewer.review_history:
                print(f"  - {record['title'][:50]}...")
                print(f"    操作: {record['action']}")
                print(f"    时间: {record['reviewed_at']}")
    else:
        print("\n取消审核")
    
    print("\n" + "="*70)
    print("演示结束")
    print("="*70)


def show_feature_comparison():
    """显示新旧版本对比"""
    print("\n" + "="*70)
    print("🆚 功能对比")
    print("="*70)
    
    print("\n旧版本审核界面:")
    print("""
    标题: OpenAI Launches GPT-5
    来源: TechCrunch
    摘要: OpenAI today announced...
    
    当前分类: product
    置信度: 55.0%
    
    操作选项:
      1. 保持当前分类
      2. 修改分类
      3. 修改技术领域
      4. 修改地区
      5. 标记为垃圾内容（删除）
      0. 跳过（稍后处理）
    """)
    
    print("\n新版本审核界面:")
    print("""
    标题: OpenAI Launches GPT-5
    来源: TechCrunch
    🔗 链接: https://techcrunch.com/2025/openai-gpt5
    摘要: OpenAI today announced...
    
    当前分类: product
    置信度: 55.0%
    
    操作选项:
      1. 保持当前分类
      2. 修改分类
      3. 修改技术领域
      4. 修改地区
      5. 标记为垃圾内容（删除）
      6. 在浏览器中打开链接  ← 新功能！
      0. 跳过（稍后处理）
    """)
    
    print("\n✨ 改进点:")
    print("  1. 显著显示网页链接（🔗 图标）")
    print("  2. 新增选项 6：直接在浏览器中打开链接")
    print("  3. 支持 'link' 和 'url' 两种字段名")
    print("  4. 打开链接后可以继续选择其他操作")
    print("  5. 审核者可以查看完整原文再做决定")
    
    print("\n💡 使用场景:")
    print("  - 标题不清晰时，打开链接查看完整内容")
    print("  - 摘要太短时，查看原文了解详情")
    print("  - 不确定分类时，阅读完整文章再判断")
    print("  - 验证来源可信度时，检查原始网页")


if __name__ == '__main__':
    # 显示功能对比
    show_feature_comparison()
    
    # 运行演示
    print("\n")
    demo_review_with_links()
