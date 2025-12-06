"""快速重新生成网页"""
import json
import glob
import os
from web_publisher import WebPublisher

# 自动找到最新的数据文件
data_files = glob.glob('ai_tracker_data_*.json')
if not data_files:
    print("❌ 没有找到数据文件")
    exit(1)

data_file = max(data_files, key=os.path.getmtime)
print(f"📂 使用数据文件: {data_file}")

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
