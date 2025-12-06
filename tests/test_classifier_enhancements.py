"""
测试增强版内容分类器
"""
from content_classifier import ContentClassifier

def test_enhanced_classifier():
    classifier = ContentClassifier()

    # 测试用例
    test_items = [
        # 产品发布测试
        {'title': 'OpenAI officially launches GPT-4o with new features', 
         'summary': 'OpenAI announces the general availability of GPT-4o model',
         'source': 'TechCrunch'},
        
        # 研究论文测试
        {'title': 'We propose a novel approach for chain-of-thought reasoning',
         'summary': 'Our method achieves state-of-the-art results on benchmark datasets',
         'source': 'arXiv'},
        
        # 市场融资测试
        {'title': 'AI startup raises $100 million in Series B funding',
         'summary': 'The company is now valued at $1 billion',
         'source': '36kr'},
        
        # 领袖言论测试
        {'title': 'Sam Altman says AI will transform everything in interview',
         'summary': 'OpenAI CEO predicts major changes in the next 5 years',
         'source': 'The Verge'},
        
        # 开发者内容测试
        {'title': 'New open source LLM framework released on GitHub',
         'summary': 'A comprehensive SDK for building AI applications',
         'source': 'Hacker News'},
        
        # 中文产品发布测试
        {'title': '字节跳动正式发布豆包大模型',
         'summary': '豆包全面开放，支持多模态生成',
         'source': '量子位'},
        
        # 边界测试：Product Hunt来源
        {'title': 'New AI coding assistant launched',
         'summary': 'A tool to help developers write better code',
         'source': 'Product Hunt'},
        
        # 边界测试：标题包含多个关键词
        {'title': 'Google releases new Gemini 2.0 model with enhanced reasoning',
         'summary': 'The model is now available for all developers',
         'source': 'Google AI Blog'},
    ]

    print('='*70)
    print('内容分类系统 - 增强版测试')
    print('='*70)
    print('\n新增功能:')
    print('  ✅ 关键词库更新 (2024-2025新产品/研究方向)')
    print('  ✅ 标题/内容权重分离 (标题权重 x1.5)')
    print('  ✅ 上下文短语匹配 (正则表达式模式)')
    print('  ✅ 来源先验概率 (基于来源的分类倾向)')
    print('='*70)

    expected_results = {
        0: 'product',   # OpenAI launches GPT-4o
        1: 'research',  # arXiv paper
        2: 'market',    # Funding round
        3: 'leader',    # Sam Altman interview
        4: 'developer', # GitHub framework
        5: 'product',   # 豆包发布
        6: 'product',   # Product Hunt
        7: 'product',   # Google Gemini
    }

    correct = 0
    total = len(test_items)

    for i, item in enumerate(test_items):
        content_type, confidence, secondary = classifier.classify_content_type(item)
        expected = expected_results.get(i, 'unknown')
        is_correct = content_type == expected
        
        if is_correct:
            correct += 1
            status = '✅'
        else:
            status = '❌'
        
        print(f'\n{status} 测试 {i+1}: {item["title"][:45]}...')
        print(f'   来源: {item["source"]}')
        print(f'   分类: {content_type} (置信度: {confidence:.1%})')
        print(f'   预期: {expected}')
        if secondary:
            print(f'   次要标签: {secondary}')

    print('\n' + '='*70)
    print(f'测试结果: {correct}/{total} 通过 ({correct/total:.0%})')
    print('='*70)

if __name__ == '__main__':
    test_enhanced_classifier()
