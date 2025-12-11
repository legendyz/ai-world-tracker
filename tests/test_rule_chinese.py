# -*- coding: utf-8 -*-
"""简单测试规则分类器对中文引语词的识别"""
import sys
sys.path.insert(0, '.')

from content_classifier import ContentClassifier

classifier = ContentClassifier()

tests = [
    ('马斯克表示AI将在5年内超越人类', 'leader'),
    ('黄仁勋称英伟达将继续主导AI芯片市场', 'leader'),
    ('李彦宏：文心一言用户已超1亿', 'leader'),
    ('奥特曼预测AGI将在2年内实现', 'leader'),
    ('Sam Altman says GPT-5 will be revolutionary', 'leader'),
    ('OpenAI发布GPT-5重大更新', 'product'),
    ('字节跳动AI团队扩张至5000人', 'market'),
]

print('规则分类器中文引语词测试')
print('=' * 60)

correct = 0
for title, expected in tests:
    item = {'title': title, 'summary': '', 'source': 'test'}
    result = classifier.classify_item(item)
    actual = result['content_type']
    status = '✓' if actual == expected else '✗'
    if actual == expected:
        correct += 1
    print(f'{status} {title[:28]:30} -> {actual:10} (期望: {expected})')

print('=' * 60)
print(f'准确率: {correct}/{len(tests)} ({correct/len(tests)*100:.0f}%)')
