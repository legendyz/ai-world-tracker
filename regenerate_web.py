"""快速重新生成网页"""
import json
import glob
import os
import yaml
from web_publisher import WebPublisher

# 加载数据目录配置
def _get_exports_dir():
    exports_dir = 'data/exports'
    try:
        if os.path.exists('config.yaml'):
            with open('config.yaml', 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
                exports_dir = cfg.get('data', {}).get('exports_dir', exports_dir)
    except Exception:
        pass
    return exports_dir

DATA_EXPORTS_DIR = _get_exports_dir()

# 自动找到最新的数据文件
data_pattern = os.path.join(DATA_EXPORTS_DIR, 'ai_tracker_data_*.json')
data_files = glob.glob(data_pattern)
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
