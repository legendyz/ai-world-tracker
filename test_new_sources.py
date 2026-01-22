"""
测试新添加的数据源是否可用
"""
import asyncio
import aiohttp
import feedparser
from datetime import datetime
import sys
import io

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 新添加的数据源
NEW_SOURCES = {
    'NVIDIA AI Blog': 'https://blogs.nvidia.com/blog/category/deep-learning/feed/',
    'Apple ML Blog': 'https://machinelearning.apple.com/rss.xml',
    'Mistral AI': 'https://mistral.ai/news/rss/',
    'Perplexity AI': 'https://www.perplexity.ai/hub/blog/rss',
    'Baidu AI Forum': 'https://ai.baidu.com/forum/feed',
    'Aliyun Developer': 'https://developer.aliyun.com/feed',
    'Tencent Cloud': 'https://cloud.tencent.com/developer/column/feed',
}

async def test_source(session, name, url):
    """测试单个数据源"""
    result = {
        'name': name,
        'url': url,
        'accessible': False,
        'valid_rss': False,
        'items_count': 0,
        'error': None,
        'status_code': None
    }
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            result['status_code'] = response.status
            
            if response.status == 200:
                result['accessible'] = True
                content = await response.text()
                
                # 使用feedparser解析
                feed = feedparser.parse(content)
                
                if feed.entries:
                    result['valid_rss'] = True
                    result['items_count'] = len(feed.entries)
                else:
                    result['error'] = 'No entries found in feed'
            else:
                result['error'] = f'HTTP {response.status}'
                
    except asyncio.TimeoutError:
        result['error'] = 'Timeout (>15s)'
    except aiohttp.ClientError as e:
        result['error'] = f'Connection error: {type(e).__name__}'
    except Exception as e:
        result['error'] = f'Parse error: {str(e)[:50]}'
    
    return result

async def test_all_sources():
    """测试所有新数据源"""
    print("=" * 80)
    print(f"测试新添加的数据源 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    async with aiohttp.ClientSession(
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    ) as session:
        tasks = [test_source(session, name, url) for name, url in NEW_SOURCES.items()]
        results = await asyncio.gather(*tasks)
    
    # 统计结果
    success_count = sum(1 for r in results if r['valid_rss'])
    accessible_count = sum(1 for r in results if r['accessible'])
    
    # 显示详细结果
    print("详细测试结果:")
    print("-" * 80)
    
    for result in results:
        status = "✓ 成功" if result['valid_rss'] else "✗ 失败"
        print(f"\n{status} | {result['name']}")
        print(f"  URL: {result['url']}")
        
        if result['valid_rss']:
            print(f"  状态: HTTP {result['status_code']} | 条目数: {result['items_count']}")
        elif result['accessible']:
            print(f"  状态: HTTP {result['status_code']} | 错误: {result['error']}")
        else:
            print(f"  错误: {result['error']}")
    
    # 显示汇总
    print("\n" + "=" * 80)
    print("测试汇总:")
    print("-" * 80)
    print(f"总计测试: {len(results)} 个数据源")
    print(f"可访问: {accessible_count} 个 ({accessible_count/len(results)*100:.1f}%)")
    print(f"有效RSS: {success_count} 个 ({success_count/len(results)*100:.1f}%)")
    print(f"失败: {len(results) - success_count} 个")
    
    # 列出失败的源
    failed = [r for r in results if not r['valid_rss']]
    if failed:
        print("\n失败的数据源:")
        for r in failed:
            print(f"  × {r['name']}: {r['error']}")
    
    print("=" * 80)
    
    return results

if __name__ == '__main__':
    asyncio.run(test_all_sources())
