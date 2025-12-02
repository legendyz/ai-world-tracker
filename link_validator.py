"""
链接验证测试脚本
验证采集的所有链接是否可访问
"""

import json
import requests
from typing import List, Dict
import time
from urllib.parse import urlparse


def validate_link_access(url: str, timeout: int = 10) -> bool:
    """
    验证链接是否可访问
    
    Args:
        url: 要验证的URL
        timeout: 超时时间（秒）
        
    Returns:
        是否可访问
    """
    if not url or not url.startswith(('http://', 'https://')):
        return False
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except Exception:
        return False


def test_data_links(json_file: str):
    """
    测试JSON数据文件中的所有链接
    
    Args:
        json_file: JSON数据文件路径
    """
    print("🔍 开始验证数据链接...")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_items = data.get('data', [])
        
        if not all_items:
            print("⚠️ 没有找到数据项")
            return
        
        total_items = len(all_items)
        links_checked = 0
        valid_links = 0
        
        print(f"📊 共有 {total_items} 条数据，开始验证链接...")
        print("-" * 60)
        
        for i, item in enumerate(all_items, 1):
            title = item.get('title', 'No title')[:50]
            url = item.get('url', '')
            pdf_url = item.get('pdf_url', '')
            clone_url = item.get('clone_url', '')
            source = item.get('source', 'Unknown')
            
            print(f"{i:2d}. {title}...")
            
            # 检查主链接
            if url:
                links_checked += 1
                if validate_link_access(url):
                    valid_links += 1
                    print(f"    ✅ 主链接可访问: {urlparse(url).netloc}")
                else:
                    print(f"    ❌ 主链接无法访问: {url}")
            
            # 检查PDF链接
            if pdf_url and pdf_url != url:
                links_checked += 1
                if validate_link_access(pdf_url):
                    valid_links += 1
                    print(f"    ✅ PDF链接可访问: {urlparse(pdf_url).netloc}")
                else:
                    print(f"    ❌ PDF链接无法访问: {pdf_url}")
            
            # 检查克隆链接
            if clone_url and clone_url != url:
                links_checked += 1
                if validate_link_access(clone_url):
                    valid_links += 1
                    print(f"    ✅ 克隆链接可访问: {urlparse(clone_url).netloc}")
                else:
                    print(f"    ❌ 克隆链接无法访问: {clone_url}")
            
            # 避免请求过于频繁
            if i % 10 == 0:
                print(f"    ... 已检查 {i}/{total_items} 条数据")
                time.sleep(1)
        
        print("-" * 60)
        print(f"🎯 验证完成！")
        print(f"📈 统计结果:")
        print(f"   - 总数据项: {total_items}")
        print(f"   - 总链接数: {links_checked}")
        print(f"   - 有效链接: {valid_links}")
        print(f"   - 成功率: {valid_links/links_checked*100:.1f}%" if links_checked > 0 else "   - 成功率: 0%")
        
        # 按来源统计
        source_stats = {}
        for item in all_items:
            source = item.get('source', 'Unknown')
            if source not in source_stats:
                source_stats[source] = {'total': 0, 'with_links': 0}
            source_stats[source]['total'] += 1
            if item.get('url'):
                source_stats[source]['with_links'] += 1
        
        print(f"\n📊 按来源统计:")
        for source, stats in source_stats.items():
            coverage = stats['with_links']/stats['total']*100 if stats['total'] > 0 else 0
            print(f"   - {source}: {stats['with_links']}/{stats['total']} ({coverage:.1f}%)")
        
    except FileNotFoundError:
        print(f"❌ 文件不存在: {json_file}")
    except json.JSONDecodeError:
        print(f"❌ JSON文件格式错误: {json_file}")
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")


def sample_link_test():
    """快速测试几个示例链接"""
    print("🔬 快速链接测试...")
    
    test_links = [
        ("arXiv", "http://arxiv.org/abs/2511.23478v1"),
        ("GitHub", "https://github.com/openai/openai-python"),
        ("百度官方", "https://baijiahao.baidu.com/s?id=1783456789"),
        ("阿里云", "https://www.alibabacloud.com/zh/product/dashscope")
    ]
    
    for name, url in test_links:
        status = "✅ 可访问" if validate_link_access(url) else "❌ 无法访问"
        print(f"   {name}: {status}")
        time.sleep(0.5)  # 避免请求过快


if __name__ == "__main__":
    print("🔗 AI World Tracker - 链接验证工具")
    print("=" * 60 + "\n")
    
    # 快速测试
    sample_link_test()
    
    print("\n" + "=" * 60 + "\n")
    
    # 查找最新的JSON文件
    import glob
    json_files = glob.glob("ai_tracker_data_*.json")
    
    if json_files:
        latest_file = sorted(json_files)[-1]
        print(f"📁 发现数据文件: {latest_file}")
        
        choice = input("是否验证所有链接？这可能需要几分钟时间 (Y/N): ").strip().lower()
        if choice in ['y', 'yes', '是']:
            test_data_links(latest_file)
        else:
            print("⏭️ 跳过完整验证")
    else:
        print("⚠️ 未找到数据文件，请先运行数据采集")
    
    print("\n✨ 验证完成！")