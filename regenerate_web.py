"""快速重新生成网页"""
import json
from web_publisher import WebPublisher

# 加载现有数据
data_file = 'ai_tracker_data_20251204_235937.json'
with open(data_file, 'r', encoding='utf-8') as f:
    result = json.load(f)

# 重新生成网页
publisher = WebPublisher()
html_file = publisher.generate_html_page(
    result['data'], 
    result.get('trends', {}), 
    {}
)

print(f"\n✅ 网页已重新生成: {html_file}")
print("\n现在 Milliondollarllm.com 应该不再总是排第一了！")
