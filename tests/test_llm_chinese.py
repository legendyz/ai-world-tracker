"""
测试 LLM 分类器对中英文内容的分类效果
"""
import sys
sys.path.insert(0, '.')

from llm_classifier import LLMClassifier

def main():
    # 创建 LLM 分类器
    classifier = LLMClassifier(provider='ollama', model='qwen3:8b', enable_cache=False)

    # 测试用例：中英文混合
    test_items = [
        # 中文 leader 测试（应分类为 leader）
        {'title': '马斯克表示AI将在5年内超越人类', 'summary': '特斯拉CEO马斯克在最新采访中表示，人工智能将在五年内达到人类智能水平', 'source': '36氪'},
        {'title': '黄仁勋称英伟达将继续主导AI芯片市场', 'summary': '英伟达CEO在GTC大会上称，公司将继续保持在AI芯片领域的领先地位', 'source': '新浪科技'},
        {'title': '李彦宏：文心一言用户已超1亿', 'summary': '百度创始人李彦宏透露文心一言用户规模', 'source': '百度'},
        {'title': '奥特曼预测AGI将在2年内实现', 'summary': 'OpenAI CEO对AGI时间表的最新预测', 'source': '机器之心'},
        
        # 中文非 leader 测试（无引语词）
        {'title': 'OpenAI发布GPT-5重大更新', 'summary': '新版本支持更长上下文和多模态能力', 'source': '机器之心'},
        {'title': '字节跳动AI团队扩张至5000人', 'summary': '字节跳动持续加大AI投入', 'source': '晚点'},
        
        # 英文 leader 测试
        {'title': 'Sam Altman says GPT-5 will be revolutionary', 'summary': 'OpenAI CEO discusses next generation model', 'source': 'TechCrunch'},
        {'title': 'Jensen Huang believes AI approach human intelligence', 'summary': 'NVIDIA CEO on AI progress', 'source': 'Reuters'},
        
        # 非 AI 测试（应给低 ai_relevance）
        {'title': '苹果iPhone 17将采用钛合金边框', 'summary': '据供应链消息，新款iPhone将使用钛合金', 'source': '9to5Mac'},
        {'title': '特斯拉Model Y降价2万元', 'summary': '特斯拉中国宣布Model Y降价', 'source': '汽车之家'},
    ]

    print('=' * 70)
    print('LLM 分类测试 - 中英文内容')
    print('=' * 70)

    # 预热模型
    classifier.warmup_model()

    # 逐条分类测试
    results = []
    for i, item in enumerate(test_items, 1):
        result = classifier.classify_item(item, use_cache=False)
        
        title_short = item['title'][:35] + '...' if len(item['title']) > 35 else item['title']
        content_type = result.get('content_type', '?')
        ai_relevance = result.get('ai_relevance', 0)
        confidence = result.get('confidence', 0)
        reasoning = result.get('llm_reasoning', result.get('reasoning', 'N/A'))
        
        print(f'\n[{i}] {title_short}')
        print(f'    类型: {content_type:<12} AI相关性: {ai_relevance:.2f}  置信度: {confidence:.2f}')
        print(f'    推理: {reasoning[:60]}...' if len(str(reasoning)) > 60 else f'    推理: {reasoning}')
        
        results.append({
            'title': item['title'],
            'expected_type': 'leader' if i <= 4 or i in [7, 8] else ('product' if i == 5 else 'market'),
            'actual_type': content_type,
            'ai_relevance': ai_relevance,
            'is_correct': (content_type == 'leader') == (i <= 4 or i in [7, 8])
        })

    # 统计结果
    print('\n' + '=' * 70)
    print('测试结果统计')
    print('=' * 70)
    
    leader_tests = [r for r in results if r['expected_type'] == 'leader']
    leader_correct = sum(1 for r in leader_tests if r['actual_type'] == 'leader')
    print(f'Leader 分类准确率: {leader_correct}/{len(leader_tests)} ({leader_correct/len(leader_tests)*100:.0f}%)')
    
    # 中文 leader 测试（前4条）
    chinese_leader = results[:4]
    chinese_correct = sum(1 for r in chinese_leader if r['actual_type'] == 'leader')
    print(f'  - 中文 Leader: {chinese_correct}/4')
    
    # 英文 leader 测试（第7-8条）
    english_leader = [results[6], results[7]]
    english_correct = sum(1 for r in english_leader if r['actual_type'] == 'leader')
    print(f'  - 英文 Leader: {english_correct}/2')
    
    # 非 AI 内容测试
    non_ai = [results[8], results[9]]
    low_relevance = sum(1 for r in non_ai if r['ai_relevance'] < 0.5)
    print(f'非AI内容识别率: {low_relevance}/2 (ai_relevance < 0.5)')

    # 卸载模型
    classifier.unload_model()
    
    print('\n' + '=' * 70)
    print('测试完成')
    print('=' * 70)

if __name__ == '__main__':
    main()
