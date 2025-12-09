"""
AI世界追踪器 - 数据采集模块
专注于收集最新AI研究、产品、开发者社区和行业信息

支持两种模式:
- 同步模式 (ThreadPoolExecutor): 兼容旧代码
- 异步模式 (asyncio + aiohttp): 高性能采集

使用方式:
    # 自动选择最优模式
    collector = DataCollector()
    data = collector.collect_all()
    
    # 强制使用异步模式
    collector = DataCollector(async_mode=True)
    data = collector.collect_all()
"""

import requests
import feedparser
import arxiv
import json
import os
import yaml
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from typing import List, Dict, Optional, Callable, Tuple, Any
from dataclasses import dataclass
import time
import random
import difflib
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from config import config
from logger import get_log_helper

# 导入国际化模块
try:
    from i18n import t, get_language
except ImportError:
    def t(key, **kwargs): return key
    def get_language(): return 'zh'

# 尝试导入异步库
try:
    import asyncio
    import aiohttp
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

# 模块日志器
log = get_log_helper('data_collector')

# 加载缓存目录配置
def _get_cache_dir():
    """获取缓存目录路径"""
    cache_dir = 'data/cache'
    try:
        if os.path.exists('config.yaml'):
            with open('config.yaml', 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
                cache_dir = cfg.get('data', {}).get('cache_dir', cache_dir)
    except Exception:
        pass
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

DATA_CACHE_DIR = _get_cache_dir()

# ============== 异步采集器配置 ==============

@dataclass
class AsyncCollectorConfig:
    """异步采集器配置"""
    # 并发控制
    max_concurrent_requests: int = 20      # 最大并发请求数
    max_concurrent_per_host: int = 3       # 每个主机最大并发数
    
    # 超时设置（秒）
    request_timeout: int = 15              # 单个请求超时
    total_timeout: int = 120               # 总采集超时
    
    # 重试设置
    max_retries: int = 2                   # 最大重试次数
    retry_delay: float = 1.0               # 重试延迟（秒）
    
    # 速率限制
    rate_limit_delay: float = 0.2          # 请求间隔（秒）
    
    # 数据目录
    cache_dir: str = 'data/cache'

def _load_async_config() -> AsyncCollectorConfig:
    """从 config.yaml 加载异步采集配置"""
    cfg = AsyncCollectorConfig()
    try:
        if os.path.exists('config.yaml'):
            with open('config.yaml', 'r', encoding='utf-8') as f:
                yaml_cfg = yaml.safe_load(f)
                async_cfg = yaml_cfg.get('async_collector', {})
                
                cfg.max_concurrent_requests = async_cfg.get('max_concurrent_requests', cfg.max_concurrent_requests)
                cfg.max_concurrent_per_host = async_cfg.get('max_concurrent_per_host', cfg.max_concurrent_per_host)
                cfg.request_timeout = async_cfg.get('request_timeout', cfg.request_timeout)
                cfg.total_timeout = async_cfg.get('total_timeout', cfg.total_timeout)
                cfg.max_retries = async_cfg.get('max_retries', cfg.max_retries)
                cfg.cache_dir = yaml_cfg.get('data', {}).get('cache_dir', cfg.cache_dir)
    except Exception:
        pass
    
    os.makedirs(cfg.cache_dir, exist_ok=True)
    return cfg

def _check_async_mode() -> bool:
    """检查是否应该使用异步模式"""
    if not ASYNC_AVAILABLE:
        return False
    
    # 从配置读取
    try:
        if os.path.exists('config.yaml'):
            with open('config.yaml', 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
                return cfg.get('collector', {}).get('async_mode', True)
    except Exception:
        pass
    
    return True  # 默认使用异步模式

# ============== AI相关常量定义 ==============

# AI领袖列表
AI_LEADERS = {
    "Sam Altman": "OpenAI CEO",
    "Elon Musk": "xAI Founder",
    "Jensen Huang": "NVIDIA CEO",
    "Demis Hassabis": "Google DeepMind CEO",
    "Yann LeCun": "Meta Chief AI Scientist",
    "Geoffrey Hinton": "AI Pioneer",
    "Andrew Ng": "AI Fund Managing General Partner",
    "Kai-Fu Lee": "01.AI CEO",
    "Robin Li": "Baidu CEO"
}

# AI相关关键词
AI_KEYWORDS = [
    'ai', 'artificial intelligence', 'machine learning', 'deep learning',
    'neural network', 'llm', 'gpt', 'transformer', 'chatgpt', 'claude',
    'gemini', 'llama', 'anthropic', 'openai',
    '人工智能', '机器学习', '深度学习', '神经网络', '大模型'
]

# HN搜索关键词
HN_SEARCH_TERMS = [
    'ai', 'llm', 'gpt', 'chatgpt', 'openai', 'anthropic', 'claude',
    'gemini', 'llama', 'transformer', 'machine learning', 'deep learning',
    'neural', 'diffusion', 'stable diffusion', 'midjourney', 'copilot',
    'langchain', 'rag', 'vector', 'embedding', 'fine-tune', 'rlhf'
]

# RSS源配置 - 统一配置
RSS_FEEDS = {
    'research': [
        'http://export.arxiv.org/rss/cs.AI',
        'http://export.arxiv.org/rss/cs.CL',
        'http://export.arxiv.org/rss/cs.CV',
        'http://export.arxiv.org/rss/cs.LG',
    ],
    'news': [
        'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',
        'https://techcrunch.com/category/artificial-intelligence/feed/',
        'https://www.wired.com/feed/tag/ai/latest/rss',
        'https://spectrum.ieee.org/rss/topic/artificial-intelligence',
        'https://www.technologyreview.com/feed/',
        'https://artificialintelligence-news.com/feed/',
        'https://syncedreview.com/feed/',
        'https://www.36kr.com/feed',
        'https://www.ithome.com/rss/',
        'https://www.jiqizhixin.com/rss',
        'https://www.qbitai.com/feed',
        'https://www.infoq.cn/feed/topic/18',
    ],
    'developer': [
        'https://github.blog/feed/',
        'https://huggingface.co/blog/feed.xml',
        'https://openai.com/blog/rss.xml',
        'https://blog.google/technology/ai/rss/',
    ],
    'product_news': [
        'https://openai.com/blog/rss.xml',
        'https://blog.google/technology/ai/rss/',
        'https://blogs.microsoft.com/ai/feed/',
    ],
    'community': [
        'https://www.producthunt.com/feed?category=artificial-intelligence',
    ],
    'leader_blogs': [
        {'url': 'http://blog.samaltman.com/posts.atom', 'author': 'Sam Altman', 'title': 'OpenAI CEO'},
        {'url': 'https://karpathy.github.io/feed.xml', 'author': 'Andrej Karpathy', 'title': 'AI Researcher'},
        {'url': 'https://lexfridman.com/feed/podcast/', 'author': 'Lex Fridman', 'title': 'Podcast Host', 'type': 'podcast'},
    ]
}

class AIDataCollector:
    """AI数据采集器 - 收集真实最新的AI信息
    
    支持两种模式:
    - 同步模式: 使用ThreadPoolExecutor并行采集
    - 异步模式: 使用asyncio+aiohttp高性能采集（推荐）
    
    Args:
        async_mode: 是否使用异步模式，None表示自动检测
    """
    
    def __init__(self, async_mode: Optional[bool] = None):
        # 确定采集模式
        if async_mode is None:
            self._use_async = _check_async_mode()
        else:
            self._use_async = async_mode and ASYNC_AVAILABLE
        
        # 异步采集器（当前版本未使用独立的异步采集器类）
        self._async_collector = None
        
        # 异步配置
        if self._use_async:
            self.async_config = _load_async_config()
            log.config("📡 Collector mode: Async (aiohttp)")
        else:
            self.async_config = None
            log.config("📡 Collector mode: Sync (ThreadPool)")
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 使用统一的RSS源配置
        self.rss_feeds = RSS_FEEDS
        
        # 采集历史缓存
        self.history_cache_file = os.path.join(DATA_CACHE_DIR, 'collection_history_cache.json')
        self.history_cache = self._load_history_cache()
        
        # 统计信息（用于异步模式）
        self.stats = {
            'requests_made': 0,
            'requests_failed': 0,
            'items_collected': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _load_history_cache(self) -> Dict:
        """加载采集历史缓存"""
        try:
            if os.path.exists(self.history_cache_file):
                with open(self.history_cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    # 验证缓存格式
                    if isinstance(cache, dict) and 'urls' in cache and 'titles' in cache:
                        # 检查缓存是否过期（超过7天）
                        last_updated = cache.get('last_updated', '')
                        if last_updated:
                            try:
                                last_time = datetime.fromisoformat(last_updated)
                                if (datetime.now() - last_time).days > 7:
                                    log.warning(t('dc_cache_expired'))
                                    return {'urls': set(), 'titles': set(), 'last_updated': ''}
                            except (ValueError, TypeError):
                                pass
                        # 转换为 set 以加速查找
                        cache['urls'] = set(cache['urls'])
                        cache['titles'] = set(cache['titles'])
                        log.data(t('dc_cache_loaded', url_count=len(cache['urls']), title_count=len(cache['titles'])))
                        return cache
        except Exception as e:
            log.error(t('dc_cache_load_failed', error=str(e)))
        return {'urls': set(), 'titles': set(), 'last_updated': ''}
    
    def _save_history_cache(self):
        """保存采集历史缓存"""
        try:
            # 转换 set 为 list 以便 JSON 序列化
            cache_to_save = {
                'urls': list(self.history_cache['urls']),
                'titles': list(self.history_cache['titles']),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.history_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(t('dc_cache_save_failed', error=str(e)))
    
    def _is_in_history(self, item: Dict) -> bool:
        """检查项目是否在历史缓存中（严格匹配 URL 或标题）"""
        url = item.get('url', '')
        title = item.get('title', '')
        
        # 严格匹配：URL 完全相同 或 标题完全相同
        if url and url in self.history_cache['urls']:
            return True
        if title and title in self.history_cache['titles']:
            return True
        return False
    
    def _add_to_history(self, item: Dict):
        """将项目添加到历史缓存"""
        url = item.get('url', '')
        title = item.get('title', '')
        if url:
            self.history_cache['urls'].add(url)
        if title:
            self.history_cache['titles'].add(title)
    
    def clear_history_cache(self):
        """清除采集历史缓存"""
        import os
        self.history_cache = {'urls': set(), 'titles': set(), 'last_updated': ''}
        if os.path.exists(self.history_cache_file):
            os.remove(self.history_cache_file)
        # 如果有异步采集器，也清除其缓存
        if self._async_collector:
            self._async_collector.clear_history_cache()
        log.success(t('dc_cache_cleared'))
    
    @property
    def is_async_mode(self) -> bool:
        """检查是否使用异步模式"""
        return self._use_async and self._async_collector is not None
    
    def collect_research_papers(self, max_results: int = 10) -> List[Dict]:
        """
        采集最新AI研究论文
        
        Args:
            max_results: 最大结果数
            
        Returns:
            研究论文列表
        """
        log.dual_start(t('dc_collect_research'))
        papers = []
        
        try:
            # 使用arXiv API获取最新论文
            client = arxiv.Client()
            
            # 构建查询 - 最新的AI相关论文
            search_query = arxiv.Search(
                query="cat:cs.AI OR cat:cs.LG OR cat:cs.CV OR cat:cs.CL",
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            for result in client.results(search_query):
                # 过滤非最近30天的论文
                if not self._is_recent(result.published):
                    continue
                    
                paper = {
                    'title': result.title,
                    'summary': self._clean_html(result.summary),
                    'authors': [str(author) for author in result.authors],
                    'url': result.entry_id,
                    'published': result.published.strftime('%Y-%m-%d'),
                    'categories': [str(cat) for cat in result.categories],
                    'source': 'arXiv'
                }
                papers.append(paper)
                
            log.dual_success(t('dc_got_papers', count=len(papers)))
            
        except Exception as e:
            log.error(t('dc_arxiv_failed', error=str(e)))
            # 提供备用数据
            papers = self._get_backup_research_data()
        
        return papers
    
    def collect_developer_content(self, max_results: int = 15) -> List[Dict]:
        """
        采集开发者社区内容
        
        Args:
            max_results: 最大结果数
            
        Returns:
            开发者内容列表
        """
        log.dual_start(t('dc_collect_developer'))
        content = []
        
        # 1. GitHub Trending AI项目
        github_projects = self._collect_github_trending()
        content.extend(github_projects[:max_results//3])
        
        # 2. Hugging Face最新模型/数据集
        hf_content = self._collect_huggingface_updates()
        content.extend(hf_content[:max_results//3])
        
        # 3. 开发者博客和教程
        dev_blogs = self._collect_dev_blogs()
        content.extend(dev_blogs[:max_results//3])
        
        log.dual_success(t('dc_got_developer', count=len(content)))
        return content
    
    def collect_product_releases(self, max_results: int = 10) -> List[Dict]:
        """
        采集AI产品发布信息
        
        Args:
            max_results: 最大结果数
            
        Returns:
            产品发布列表
        """
        log.dual_start(t('dc_collect_products'))
        products = []
        
        # 收集主要AI公司的产品发布信息
        company_sources = {
            'OpenAI': self._collect_openai_updates,
            'Google': self._collect_google_ai_updates,
            'Microsoft': self._collect_microsoft_ai_updates,
            'Meta': self._collect_meta_ai_updates,
            'Anthropic': self._collect_anthropic_updates,
            'China_Tech': self._collect_chinese_ai_updates  # 新增中国科技公司
        }
        
        for company, collector_func in company_sources.items():
            try:
                company_products = collector_func()
                # 过滤非最近发布的产品
                company_products = [p for p in company_products if self._is_recent(p.get('published', ''))]
                products.extend(company_products)
                time.sleep(1)  # 避免请求过快
            except Exception as e:
                log.warning(t('dc_product_failed', company=company, error=str(e)))
        
        # 按发布时间排序并限制数量
        products = products[:max_results]
        
        log.dual_success(t('dc_got_products', count=len(products)))
        return products
    
    def collect_ai_leaders_quotes(self, max_results: int = 15) -> List[Dict]:
        """
        采集全球AI领袖的近期言论
        
        Args:
            max_results: 最大结果数
            
        Returns:
            领袖言论列表
        """
        log.dual_start(t('dc_collect_leaders'))
        quotes = []
        
        leaders = {
            "Sam Altman": "OpenAI CEO",
            "Elon Musk": "xAI Founder",
            "Jensen Huang": "NVIDIA CEO",
            "Demis Hassabis": "Google DeepMind CEO",
            "Yann LeCun": "Meta Chief AI Scientist",
            "Geoffrey Hinton": "AI Pioneer",
            "Andrew Ng": "AI Fund Managing General Partner",
            "Kai-Fu Lee": "01.AI CEO",
            "Robin Li": "Baidu CEO"
        }
        
        # 1. 尝试使用新闻RSS搜索 (优先Bing News)
        base_url_google = "https://news.google.com/rss/search?q={}+AI+when:30d&hl=en-US&gl=US&ceid=US:en"
        base_url_bing = "https://www.bing.com/news/search?q={}+AI&format=rss"
        
        for leader_name, title in leaders.items():
            try:
                query_name = leader_name.replace(' ', '+')
                
                # 策略A: 优先使用 Bing News
                feed_url = base_url_bing.format(query_name)
                feed = feedparser.parse(feed_url)
                
                # 策略B: 如果 Bing News 为空，尝试 Google News
                if not feed.entries:
                    feed_url = base_url_google.format(query_name)
                    feed = feedparser.parse(feed_url)
                
                count = 0
                for entry in feed.entries:
                    if count >= 2: # 每个领袖最多取2条
                        break
                        
                    # 检查是否是最近30天
                    date_val = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        date_val = entry.published_parsed
                    elif entry.get('published'):
                        date_val = entry.get('published')
                    
                    if date_val and not self._is_recent(date_val):
                        continue
                        
                    # 简单的关键词过滤，确保是言论相关的
                    text = (entry.title + " " + entry.get('summary', '')).lower()
                    if any(k in text for k in ['said', 'says', 'stated', 'warns', 'believes', 'predicts', 'interview', 'speech', 'tweet', 'post']):
                        # 清理 summary 中的 HTML 标签
                        raw_summary = entry.get('summary', entry.title)
                        clean_summary = self._clean_html(raw_summary, max_length=300)
                        
                        quote = {
                            'title': f"{leader_name}: {entry.title}",
                            'summary': clean_summary,
                            'url': entry.link,
                            'published': entry.get('published', datetime.now().strftime('%Y-%m-%d')),
                            'source': f"News about {leader_name}",
                            'author': leader_name,
                            'author_title': title
                        }
                        quotes.append(quote)
                        count += 1
                
                time.sleep(0.5) # 避免请求过快
                
            except Exception as e:
                log.warning(t('dc_leader_failed', name=leader_name, error=str(e)))
        
        # 2. 采集个人博客和播客
        for source in self.rss_feeds.get('leader_blogs', []):
            try:
                feed = feedparser.parse(source['url'])
                for entry in feed.entries[:3]:
                    # 检查时间
                    date_val = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        date_val = entry.published_parsed
                    elif entry.get('published'):
                        date_val = entry.get('published')
                    
                    if date_val and not self._is_recent(date_val):
                        continue

                    # 如果是播客，检查标题是否包含关注的领袖名字
                    if source.get('type') == 'podcast':
                        found_leader = False
                        for leader_name in leaders.keys():
                            if leader_name.lower() in entry.title.lower():
                                found_leader = True
                                source['author'] = leader_name # 临时覆盖为嘉宾名
                                break
                        if not found_leader:
                            continue

                    quote = {
                        'title': f"[{source['author']}] {entry.title}",
                        'summary': self._clean_html(entry.get('summary', entry.get('description', ''))),
                        'url': entry.link,
                        'published': entry.get('published', datetime.now().strftime('%Y-%m-%d')),
                        'source': 'Personal Blog/Podcast',
                        'author': source['author'],
                        'author_title': source['title']
                    }
                    quotes.append(quote)
            except Exception as e:
                log.warning(t('dc_blog_failed', author=source['author'], error=str(e)))

        # 3. 如果采集数量不足，使用备用数据
        if len(quotes) < 5:
            log.warning(t('dc_fallback_data'))
            quotes.extend(self._get_backup_leaders_data())
            
        # 去重
        unique_quotes = []
        seen_urls = set()
        for q in quotes:
            if q['url'] not in seen_urls:
                unique_quotes.append(q)
                seen_urls.add(q['url'])
        
        # 按时间排序
        # 注意：这里简化处理，实际可能需要解析时间字符串
        
        result = unique_quotes[:max_results]
        log.dual_success(t('dc_got_leaders', count=len(result)))
        return result

    def collect_latest_news(self, max_results: int = 20) -> List[Dict]:
        """
        采集最新AI行业新闻
        
        Args:
            max_results: 最大结果数
            
        Returns:
            新闻列表
        """
        log.dual_start(t('dc_collect_news'))
        
        # 从产品发布新闻源采集
        product_news = []
        for feed_url in self.rss_feeds.get('product_news', []):
            try:
                feed_news = self._parse_rss_feed(feed_url, category='product')
                product_news.extend(feed_news)
                time.sleep(0.3)
            except Exception as e:
                log.warning(t('dc_product_feed_failed', url=feed_url, error=str(e)))
        
        # 从传统新闻源采集
        general_news = []
        for feed_url in self.rss_feeds['news']:
            try:
                feed_news = self._parse_rss_feed(feed_url, category='news')
                general_news.extend(feed_news)
                time.sleep(0.5)
            except Exception as e:
                log.warning(t('dc_rss_failed', url=feed_url, error=str(e)))
        
        # 合并两类新闻
        all_news = product_news + general_news
        
        # 过滤AI相关内容
        ai_news = [item for item in all_news if self._is_ai_related(item)]
        
        # 全局去重 - 提高信噪比
        ai_news = self._deduplicate_items(ai_news)
        
        # 按时间排序
        ai_news.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        # 优先显示产品发布新闻
        product_related = [item for item in ai_news if self._is_product_related(item)]
        other_news = [item for item in ai_news if not self._is_product_related(item)]
        
        # 按优先级排列：产品发布 > 其他AI新闻
        prioritized_news = product_related + other_news
        result = prioritized_news[:max_results]
        log.dual_success(t('dc_got_news', count=len(result)))
        return result
    
    def collect_community_trends(self, max_results: int = 15) -> List[Dict]:
        """
        采集社区热点 (Product Hunt, Hacker News)
        
        Hacker News 使用官方 API 获取更好的数据质量
        """
        log.dual_start(t('dc_collect_community'))
        trends = []
        
        # 1. 使用 HN 官方 API 采集
        try:
            hn_items = self._fetch_hacker_news_api(max_items=10)
            for item in hn_items:
                # 保留 score 信息供评估器使用
                trends.append(item)
        except Exception as e:
            log.dual_warning(t('dc_hn_api_failed', error=str(e)))
        
        # 2. 采集 Product Hunt 等其他 RSS 源
        for feed_url in self.rss_feeds.get('community', []):
            try:
                # 跳过 HN RSS (已用 API 替代)
                if "hnrss" in feed_url:
                    continue
                    
                # Determine source name for better labeling
                source_name = "Community"
                if "producthunt" in feed_url:
                    source_name = "Product Hunt"
                elif "reddit" in feed_url:
                    if "LocalLLaMA" in feed_url:
                        source_name = "Reddit (LocalLLaMA)"
                    else:
                        source_name = "Reddit (Singularity)"
                elif "lmsys" in feed_url:
                    source_name = "LMSYS Arena"

                feed_items = self._parse_rss_feed(feed_url, category='community')
                
                for item in feed_items:
                    item['source'] = source_name
                    trends.append(item)
                    time.sleep(0.2)
                    
            except Exception as e:
                log.warning(t('dc_community_failed', url=feed_url, error=str(e)))
        
        # Deduplicate
        trends = self._deduplicate_items(trends)
        
        # Sort by published date
        trends.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        result = trends[:max_results]
        log.dual_success(t('dc_got_community', count=len(result)))
        return result

    def collect_all(self, parallel: bool = True, max_workers: int = 6) -> Dict[str, List[Dict]]:
        """
        采集所有类型的数据
        
        Args:
            parallel: 是否启用并行采集（同步模式参数）
            max_workers: 并行采集的最大线程数（同步模式参数）
        
        Returns:
            分类的数据字典
        """
        # 如果使用异步模式，委托给异步采集
        if self._use_async and ASYNC_AVAILABLE:
            return self._collect_all_async_wrapper()
        
        # 同步模式 - 原有实现
        return self._collect_all_sync(parallel, max_workers)
    
    def _collect_all_async_wrapper(self) -> Dict[str, List[Dict]]:
        """异步采集的同步包装器"""
        try:
            # 在新的事件循环中运行异步采集
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._collect_all_async())
            finally:
                loop.close()
        except Exception as e:
            log.error(f"Async collection failed: {e}, falling back to sync mode")
            return self._collect_all_sync(True, 6)
    
    def _collect_all_sync(self, parallel: bool = True, max_workers: int = 6) -> Dict[str, List[Dict]]:
        """
        同步采集所有类型的数据（原有实现）
        
        Args:
            parallel: 是否启用并行采集（默认启用）
            max_workers: 并行采集的最大线程数（默认6）
        
        Returns:
            分类的数据字典
        """
        log.dual_start(t('dc_start_collection'))
        log.dual_separator("=", 50)
        
        all_data = {
            'research': [],
            'developer': [],
            'product': [],
            'news': [],
            'leader': [],
            'community': []
        }
        
        # 从配置读取采集数量
        product_count = config.get('collector.product_count', 10)
        community_count = config.get('collector.community_count', 10)
        leader_count = config.get('collector.leader_count', 15)
        research_count = config.get('collector.research_count', 15)
        developer_count = config.get('collector.developer_count', 20)
        news_count = config.get('collector.news_count', 25)
        
        # 从配置读取并行设置
        parallel = config.get('collector.parallel_enabled', parallel)
        max_workers = config.get('collector.parallel_workers', max_workers)
        
        # 定义采集任务
        collect_tasks: List[Tuple[str, Callable, int]] = [
            ('research', self.collect_research_papers, research_count),
            ('developer', self.collect_developer_content, developer_count),
            ('product', self.collect_product_releases, product_count),
            ('leader', self.collect_ai_leaders_quotes, leader_count),
            ('community', self.collect_community_trends, community_count),
            ('news', self.collect_latest_news, news_count),
        ]
        
        if parallel and max_workers > 1:
            # 并行采集模式
            log.dual_info(t('dc_parallel_mode', workers=max_workers))
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                futures = {
                    executor.submit(func, count): category 
                    for category, func, count in collect_tasks
                }
                
                # 收集结果
                for future in as_completed(futures):
                    category = futures[future]
                    try:
                        result = future.result()
                        all_data[category] = result
                        log.dual_success(t('dc_parallel_task_done', category=category, count=len(result)))
                    except Exception as e:
                        log.error(t('dc_parallel_task_failed', category=category, error=str(e)))
                        all_data[category] = []
            
            elapsed = time.time() - start_time
            log.dual_info(t('dc_parallel_complete', time=f"{elapsed:.1f}"))
        else:
            # 串行采集模式
            log.dual_info(t('dc_serial_mode'))
            for category, func, count in collect_tasks:
                all_data[category] = func(count)
        
        # 使用独立的采集历史缓存统计新内容（但不过滤，所有内容都传递给分类模块）
        new_stats = {}  # 记录每个类别的新内容数量
        cached_stats = {}  # 记录每个类别的缓存命中数量
        new_items_for_cache = []  # 记录新采集的项目，稍后添加到缓存
        
        for cat in all_data:
            new_count = 0
            cached_count = 0
            for item in all_data[cat]:
                if self._is_in_history(item):
                    cached_count += 1
                else:
                    new_count += 1
                    new_items_for_cache.append(item)
            new_stats[cat] = new_count
            cached_stats[cat] = cached_count
        
        # 将新采集的项目添加到历史缓存
        for item in new_items_for_cache:
            self._add_to_history(item)
        
        # 保存更新后的缓存
        if new_items_for_cache:
            self._save_history_cache()
        
        # 统计信息
        total_items = sum(len(items) for items in all_data.values())
        total_new = sum(new_stats.values())
        total_cached = sum(cached_stats.values())
        log.dual_done(t('dc_collection_done_v2', total=total_items, new=total_new, cached=total_cached))
        for category, items in all_data.items():
            new_count = new_stats.get(category, 0)
            cached_count = cached_stats.get(category, 0)
            log.dual_data(t('dc_category_stats_v2', category=category, count=len(items), new=new_count, cached=cached_count))
        
        return all_data
    
    def _collect_github_trending(self) -> List[Dict]:
        """采集GitHub AI热门项目 (关注近期热门)"""
        projects = []
        
        try:
            # 计算30天前的日期
            last_month = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # GitHub API获取AI相关热门项目
            url = "https://api.github.com/search/repositories"
            # 优化查询: 关注最近创建且高星的项目，发现"明日之星"
            query = f'(machine-learning OR artificial-intelligence OR deep-learning OR llm) created:>{last_month}'
            
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': 15
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for repo in data.get('items', []):
                    # 过滤非最近更新的项目
                    if not self._is_recent(repo['updated_at']):
                        continue
                        
                    project = {
                        'title': repo['full_name'],
                        'summary': repo['description'] or '无描述',
                        'url': repo['html_url'],
                        'stars': repo['stargazers_count'],
                        'language': repo['language'],
                        'updated': repo['updated_at'][:10],
                        'source': 'GitHub'
                    }
                    projects.append(project)
            
        except Exception as e:
            log.warning(t('dc_github_failed', error=str(e)))
            # 使用备用数据
            projects = self._get_backup_github_data()
        
        return projects
    
    def _collect_huggingface_updates(self) -> List[Dict]:
        """采集Hugging Face最新更新"""
        updates = []
        
        try:
            # Hugging Face模型API
            url = "https://huggingface.co/api/models"
            params = {
                'limit': 10,
                'sort': 'lastModified',
                'direction': -1
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                models = response.json()
                
                for model in models:
                    # 过滤非最近更新的模型
                    if not self._is_recent(model.get('lastModified', '')):
                        continue
                        
                    update = {
                        'title': f"HF Model: {model['id']}",
                        'summary': f"最新AI模型发布: {model['id']}，下载量: {model.get('downloads', 0)}",
                        'url': f"https://huggingface.co/{model['id']}",
                        'downloads': model.get('downloads', 0),
                        'updated': model.get('lastModified', '')[:10],
                        'source': 'Hugging Face'
                    }
                    updates.append(update)
        
        except Exception as e:
            log.warning(t('dc_hf_failed', error=str(e)))
            updates = self._get_backup_hf_data()
        
        return updates
    
    def _collect_dev_blogs(self) -> List[Dict]:
        """采集开发者博客内容"""
        blogs = []
        
        try:
            # 从GitHub博客RSS获取
            for feed_url in self.rss_feeds['developer']:
                feed_content = self._parse_rss_feed(feed_url, category='developer')
                blogs.extend(feed_content)
        
        except Exception as e:
            log.warning(t('dc_dev_blog_failed', error=str(e)))
            blogs = self._get_backup_blog_data()
        
        return blogs
    
    def _collect_openai_updates(self) -> List[Dict]:
        """采集OpenAI产品更新"""
        updates = []
        try:
            # 尝试从RSS获取
            rss_url = 'https://openai.com/blog/rss.xml'
            updates = self._parse_rss_feed(rss_url, category='product')
            for item in updates:
                item['company'] = 'OpenAI'
        except Exception:
            pass
            
        if updates:
            return updates
            
        # 备用数据
        return [
            {
                'title': 'OpenAI ChatGPT-4o 发布公告',
                'summary': 'OpenAI正式发布ChatGPT-4o，具备更强的多模态理解能力，支持文本、图像、音频的综合处理，响应速度显著提升。',
                'url': 'https://openai.com/index/hello-gpt-4o/',
                'company': 'OpenAI',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'OpenAI'
},
            {
                'title': 'OpenAI API 定价更新公告',
                'summary': 'OpenAI更新API定价策略，降低GPT-4使用成本，同时推出更经济的GPT-4 Turbo选项，为开发者提供更灵活的选择。',
                'url': 'https://openai.com/api/pricing/',
                'company': 'OpenAI',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'OpenAI'
}
        ]
    
    def _collect_google_ai_updates(self) -> List[Dict]:
        """采集Google AI产品更新"""
        updates = []
        try:
            rss_url = 'https://blog.google/technology/ai/rss/'
            updates = self._parse_rss_feed(rss_url, category='product')
            for item in updates:
                item['company'] = 'Google'
        except Exception:
            pass
            
        if updates:
            return updates

        return [
            {
                'title': 'Google Gemini 产品介绍页面',
                'summary': 'Google Gemini是下一代AI模型，具备先进的多模态理解能力，支持文本、代码、图像、音频和视频的综合处理。',
                'url': 'https://gemini.google.com/',
                'company': 'Google',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Google AI'
},
            {
                'title': 'Google AI Studio 产品发布',
                'summary': 'Google AI Studio为开发者提供快速原型设计和测试生成式AI想法的平台，支持Gemini模型的快速集成和部署。',
                'url': 'https://aistudio.google.com/',
                'company': 'Google',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Google AI'
}
        ]
    
    def _collect_microsoft_ai_updates(self) -> List[Dict]:
        """采集Microsoft AI产品更新"""
        updates = []
        try:
            rss_url = 'https://blogs.microsoft.com/ai/feed/'
            updates = self._parse_rss_feed(rss_url, category='product')
            for item in updates:
                item['company'] = 'Microsoft'
        except Exception:
            pass
            
        if updates:
            return updates

        return [
            {
                'title': 'Microsoft Copilot 产品页面',
                'summary': 'Microsoft Copilot是AI驱动的生产力工具，集成到Microsoft 365中，帮助用户提升工作效率，支持文档编写、数据分析等功能。',
                'url': 'https://copilot.microsoft.com/',
                'company': 'Microsoft',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Microsoft'
},
            {
                'title': 'Azure AI Services 产品介绍',
                'summary': 'Azure AI Services提供完整的AI和机器学习服务套件，包括认知服务、机器学习平台和OpenAI服务，为企业AI转型提供支持。',
                'url': 'https://azure.microsoft.com/en-us/products/ai-services',
                'company': 'Microsoft',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Microsoft Azure'
}
        ]
    
    def _collect_meta_ai_updates(self) -> List[Dict]:
        """采集Meta AI产品更新"""
        updates = []
        try:
            rss_url = 'https://ai.meta.com/blog/rss/'
            updates = self._parse_rss_feed(rss_url, category='product')
            for item in updates:
                item['company'] = 'Meta'
        except Exception:
            pass
            
        if updates:
            return updates

        return [
            {
                'title': 'Meta Llama 3.3 模型发布公告',
                'summary': 'Meta发布Llama 3.3，这是最新的开源大语言模型，在推理、代码生成和多语言支持方面有显著改进，支持商业使用。',
                'url': 'https://llama.meta.com/',
                'company': 'Meta',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Meta AI'
},
            {
                'title': 'Meta AI Assistant 产品介绍',
                'summary': 'Meta AI是智能助手产品，集成到Facebook、Instagram、WhatsApp等平台，为用户提供AI驱动的对话、创作和搜索体验。',
                'url': 'https://www.meta.ai/',
                'company': 'Meta',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Meta AI'
}
        ]
    
    def _collect_anthropic_updates(self) -> List[Dict]:
        """采集Anthropic AI产品更新"""
        updates = []
        try:
            rss_url = 'https://www.anthropic.com/news/rss'
            updates = self._parse_rss_feed(rss_url, category='product')
            for item in updates:
                item['company'] = 'Anthropic'
        except Exception:
            pass
            
        if updates:
            return updates

        return [
            {
                'title': 'Anthropic Claude 3.5 Sonnet 产品页面',
                'summary': 'Claude 3.5 Sonnet是Anthropic最新的AI模型，在推理、分析、编码等任务上表现出色，支持大容量上下文处理，具备强大的安全性和可靠性。',
                'url': 'https://www.anthropic.com/claude',
                'company': 'Anthropic',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Anthropic'
},
            {
                'title': 'Anthropic Claude API 文档',
                'summary': 'Anthropic提供Claude API服务，为开发者提供高质量的对话AI能力，支持多种使用场景，包括内容创作、分析和编程辅助等。',
                'url': 'https://docs.anthropic.com/',
                'company': 'Anthropic',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Anthropic'
}
        ]
    
    def _collect_chinese_ai_updates(self) -> List[Dict]:
        """采集中国AI公司产品更新"""
        updates = []
        
        # 1. 尝试从RSS获取
        chinese_feeds = [
            'https://www.jiqizhixin.com/rss',
            'https://www.qbitai.com/feed',
            'https://www.infoq.cn/feed/topic/18',
            'https://www.baidu.com/rss/news.xml',
            'https://cloud.tencent.com/developer/rss/articles',
            'https://www.alibabacloud.com/blog/rss.xml'
        ]
        
        for feed_url in chinese_feeds:
            try:
                feed_updates = self._parse_rss_feed(feed_url, category='product')
                # 过滤出大公司的产品新闻
                for item in feed_updates:
                    if any(c in item['title'] for c in ['百度', '阿里', '腾讯', '华为', '字节', '文心一言', '通义千问', '混元', '盘古', 'Kimi', '智谱', 'DeepSeek']):
                        item['company'] = 'China Tech'
                        updates.append(item)
            except Exception:
                continue
                
        if updates:
            return updates

        # 2. 备用数据 (如果RSS失败)
        return [
            {
                'title': '百度文心一言 4.0 发布',
                'summary': '百度发布文心一言4.0版本，在理解、生成、逻辑和记忆四大能力上都有显著提升，综合水平与GPT-4相比毫不逊色。',
                'url': 'https://yiyan.baidu.com/',
                'company': 'Baidu',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Baidu AI'
},
            {
                'title': '阿里通义千问 2.5 发布',
                'summary': '阿里云发布通义千问2.5，模型性能全面升级，在中文语境下表现优异，开源多款尺寸模型供开发者使用。',
                'url': 'https://tongyi.aliyun.com/',
                'company': 'Alibaba',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Aliyun'
},
             {
                'title': '腾讯混元大模型升级',
                'summary': '腾讯混元大模型迎来重要升级，扩展了上下文窗口，增强了代码生成和数学推理能力，已接入腾讯全系产品。',
                'url': 'https://hunyuan.tencent.com/',
                'company': 'Tencent',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Tencent Cloud'
},
            {
                'title': 'DeepSeek V2 开源发布',
                'summary': '深度求索(DeepSeek)发布DeepSeek-V2，这是一款强大的开源MoE大语言模型，在多项基准测试中表现优异，且推理成本极低。',
                'url': 'https://www.deepseek.com/',
                'company': 'DeepSeek',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'DeepSeek'
}
        ]
    
    def _fetch_hacker_news_api(self, max_items: int = 15, search_terms: List[str] = None) -> List[Dict]:
        """
        使用 Hacker News 官方 API 采集 AI 相关内容
        
        API 文档: https://github.com/HackerNews/API
        Base URL: https://hacker-news.firebaseio.com/v0/
        
        Args:
            max_items: 最大返回条目数
            search_terms: 搜索关键词列表，用于过滤相关内容
            
        Returns:
            采集到的数据列表
        """
        if search_terms is None:
            search_terms = ['ai', 'llm', 'gpt', 'chatgpt', 'openai', 'anthropic', 'claude', 
                          'gemini', 'llama', 'transformer', 'machine learning', 'deep learning',
                          'neural', 'diffusion', 'stable diffusion', 'midjourney', 'copilot',
                          'langchain', 'rag', 'vector', 'embedding', 'fine-tune', 'rlhf']
        
        HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
        items = []
        
        try:
            # 获取最新故事 ID 列表
            response = requests.get(f"{HN_API_BASE}/newstories.json", timeout=10)
            if response.status_code != 200:
                log.dual_warning(t('dc_hn_api_failed', error=f"HTTP {response.status_code}"))
                return []
            
            story_ids = response.json()[:100]  # 取最新100条进行筛选
            
            ai_stories = []
            for story_id in story_ids:
                if len(ai_stories) >= max_items * 2:  # 采集足够多再筛选
                    break
                    
                try:
                    # 获取故事详情
                    item_response = requests.get(f"{HN_API_BASE}/item/{story_id}.json", timeout=5)
                    if item_response.status_code != 200:
                        continue
                    
                    story = item_response.json()
                    if not story or story.get('deleted') or story.get('dead'):
                        continue
                    
                    title = story.get('title', '').lower()
                    text = story.get('text', '').lower() if story.get('text') else ''
                    url = story.get('url', '')
                    
                    # 检查是否与 AI 相关
                    combined_text = f"{title} {text} {url}".lower()
                    if any(term in combined_text for term in search_terms):
                        ai_stories.append(story)
                    
                    time.sleep(0.1)  # 避免请求过快
                    
                except Exception as e:
                    continue
            
            # 转换为统一格式
            for story in ai_stories[:max_items]:
                # 转换 Unix 时间戳为日期字符串
                pub_time = datetime.fromtimestamp(story.get('time', 0))
                
                # 检查是否是最近的内容
                if not self._is_recent(pub_time):
                    continue
                
                # 构建摘要：优先使用 text 字段，否则生成描述
                text_content = story.get('text', '')
                if text_content:
                    # 清理 HTML 标签
                    summary = self._clean_html(text_content)
                else:
                    # 如果没有 text，生成基于元数据的摘要
                    score = story.get('score', 0)
                    comments = story.get('descendants', 0)
                    author = story.get('by', 'unknown')
                    summary = f"Posted by {author} | {score} points | {comments} comments"
                    if story.get('url'):
                        # 从 URL 提取域名作为来源信息
                        from urllib.parse import urlparse
                        domain = urlparse(story.get('url')).netloc
                        summary += f" | Source: {domain}"
                
                item = {
                    'title': story.get('title', ''),
                    'summary': summary,
                    'url': story.get('url') or f"https://news.ycombinator.com/item?id={story.get('id')}",
                    'published': pub_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'Hacker News',
                    # HN 特有的元数据
                    'hn_id': story.get('id'),
                    'score': story.get('score', 0),
                    'comments': story.get('descendants', 0),
                    'author': story.get('by', '')
                }
                
                if self._is_valid_item(item):
                    items.append(item)
            
        except Exception as e:
            log.dual_warning(t('dc_hn_api_failed', error=str(e)))
        
        return items

    def _parse_rss_feed(self, feed_url: str, category: str) -> List[Dict]:
        """解析RSS源"""
        items = []
        
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:10]:  # 限制每个源最多10条
                # 检查日期
                date_val = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    date_val = entry.published_parsed
                elif entry.get('published'):
                    date_val = entry.get('published')
                
                if date_val and not self._is_recent(date_val):
                    continue

                # 清理 summary 中的 HTML 标签
                raw_summary = entry.get('summary', entry.get('description', ''))
                clean_summary = self._clean_html(raw_summary, max_length=300)

                item = {
                    'title': entry.get('title', ''),
                    'summary': clean_summary,
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': feed.feed.get('title', feed_url)
}
                
                if self._is_valid_item(item):
                    items.append(item)
        
        except Exception as e:
            log.warning(t('dc_rss_parse_failed', url=feed_url, error=str(e)))
        
        return items
    
    def _deduplicate_items(self, items: List[Dict], threshold: float = 0.6) -> List[Dict]:
        """
        对内容列表进行去重
        基于标题相似度
        """
        if not items:
            return []
            
        unique_items = []
        
        for item in items:
            is_duplicate = False
            for existing in unique_items:
                # 计算标题相似度
                seq = difflib.SequenceMatcher(None, item['title'].lower(), existing['title'].lower())
                if seq.ratio() > threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_items.append(item)
                
        return unique_items

    def _is_ai_related(self, item: Dict) -> bool:
        """检查内容是否与AI相关"""
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'llm', 'gpt', 'transformer', 'chatgpt',
            '人工智能', '机器学习', '深度学习', '神经网络'
        ]
        
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        return any(keyword in text for keyword in ai_keywords)
    
    def _is_product_related(self, item: Dict) -> bool:
        """检查内容是否与产品发布相关"""
        product_keywords = [
            'launch', 'release', 'announce', 'unveil', 'introduce', 'debut',
            'new product', 'new version', 'update', 'upgrade', 'available',
            'official', 'beta', 'preview', 'api', 'service', 'platform',
            '发布', '推出', '上线', '正式', '新版本', '新功能',
            '产品', '服务', '平台', '公测', '内测'
        ]
        
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        return any(keyword in text for keyword in product_keywords)
    
    def _is_valid_item(self, item: Dict) -> bool:
        """验证数据项有效性"""
        return (item.get('title') and 
                item.get('url') and 
                len(item.get('title', '')) > 10)
    
    def _clean_html(self, text: str, max_length: int = 300) -> str:
        """
        清理文本中的 HTML 标签
        
        Args:
            text: 原始文本（可能包含 HTML）
            max_length: 最大长度
            
        Returns:
            清理后的纯文本
        """
        if not text:
            return ''
        
        try:
            # 使用 BeautifulSoup 清理 HTML 标签
            # 注意：使用 features 参数并将 text 包装确保 BS4 不会误判为文件名
            from warnings import filterwarnings
            filterwarnings('ignore', category=MarkupResemblesLocatorWarning)
            soup = BeautifulSoup(text, features='html.parser')
            clean_text = soup.get_text(separator=' ', strip=True)
            
            # 清理多余空白
            clean_text = ' '.join(clean_text.split())
            
            # 截断到最大长度
            if len(clean_text) > max_length:
                clean_text = clean_text[:max_length] + '...'
            
            return clean_text
        except Exception:
            # 如果清理失败，返回原始文本的截断版本
            return text[:max_length] + '...' if len(text) > max_length else text
    
    def _is_recent(self, date_val) -> bool:
        """检查日期是否在最近30天内"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            if isinstance(date_val, datetime):
                # 处理时区感知的时间
                if date_val.tzinfo is not None:
                    # 如果cutoff_date没有时区，添加当前时区或UTC
                    if cutoff_date.tzinfo is None:
                        from dateutil import tz
                        cutoff_date = cutoff_date.replace(tzinfo=tz.tzlocal())
                    
                    # 再次检查，如果还是不匹配，尝试转换
                    if date_val.tzinfo != cutoff_date.tzinfo:
                         # 简单比较时间戳
                         return date_val.timestamp() >= cutoff_date.timestamp()
                return date_val >= cutoff_date
                
            if isinstance(date_val, str):
                # 尝试解析字符串日期
                try:
                    dt = date_parser.parse(date_val)
                    # 比较时间戳以避免时区问题
                    return dt.timestamp() >= cutoff_date.timestamp()
                except (ValueError, TypeError, AttributeError):
                    # 如果解析失败，尝试简单格式
                    if len(date_val) >= 10:
                        dt = datetime.strptime(date_val[:10], '%Y-%m-%d')
                        return dt >= cutoff_date
            
            # 如果是struct_time (feedparser)
            if isinstance(date_val, time.struct_time):
                dt = datetime.fromtimestamp(time.mktime(date_val))
                return dt >= cutoff_date
                
            return True # 无法解析时默认保留
        except Exception:
            return True
    
    def _get_backup_leaders_data(self) -> List[Dict]:
        """备用领袖言论数据"""
        return [
            {
                'title': 'Sam Altman: AI发展的速度将超出所有人的预期',
                'summary': 'OpenAI CEO Sam Altman在最近的采访中表示，AGI的到来可能比预期的要快，社会需要为此做好准备。',
                'url': 'https://openai.com/blog',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Interview',
                'author': 'Sam Altman',
                'author_title': 'OpenAI CEO'
},
            {
                'title': 'Elon Musk: AI安全是未来的首要任务',
                'summary': 'Elon Musk再次强调AI安全的重要性，并表示xAI的目标是理解宇宙的本质，构建最大限度追求真理的AI。',
                'url': 'https://x.ai',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'X (Twitter)',
                'author': 'Elon Musk',
                'author_title': 'xAI Founder'
},
            {
                'title': 'Jensen Huang: 生成式AI是计算领域的转折点',
                'summary': 'NVIDIA CEO黄仁勋表示，生成式AI正在重塑每一个行业，计算方式正在发生根本性的转变。',
                'url': 'https://nvidianews.nvidia.com/',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Keynote',
                'author': 'Jensen Huang',
                'author_title': 'NVIDIA CEO'
},
            {
                'title': 'Yann LeCun: 现在的LLM还不是真正的智能',
                'summary': 'Meta首席AI科学家Yann LeCun认为，目前的大语言模型缺乏对物理世界的理解，距离真正的通用人工智能还有很长的路要走。',
                'url': 'https://ai.meta.com/blog/',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Interview',
                'author': 'Yann LeCun',
                'author_title': 'Meta Chief AI Scientist'
},
            {
                'title': '李开复: AI 2.0时代已经到来',
                'summary': '零一万物CEO李开复表示，AI 2.0时代将带来比移动互联网大十倍的机会，中国在应用层有巨大优势。',
                'url': 'https://www.01.ai/',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Speech',
                'author': 'Kai-Fu Lee',
                'author_title': '01.AI CEO'
}
        ]

    def _get_backup_research_data(self) -> List[Dict]:
        """备用研究数据"""
        return [
            {
                'title': 'Attention Is All You Need: Transformer架构深度分析',
                'summary': '深入分析Transformer架构在自然语言处理中的革命性作用，探讨注意力机制的原理和应用。',
                'authors': ['AI Research Team'],
                'url': 'https://arxiv.org/abs/1706.03762',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'categories': ['cs.CL', 'cs.AI'],
                'source': 'arXiv'
}
        ]
    
    def _get_backup_github_data(self) -> List[Dict]:
        """备用GitHub数据"""
        return [
            {
                'title': 'transformers',
                'summary': '🤗 Transformers: State-of-the-art Machine Learning for PyTorch, TensorFlow, and JAX.',
                'url': 'https://github.com/huggingface/transformers',
                'stars': 132000,
                'language': 'Python',
                'updated': datetime.now().strftime('%Y-%m-%d'),
                'source': 'GitHub'
}
        ]
    
    def _get_backup_hf_data(self) -> List[Dict]:
        """备用Hugging Face数据"""
        return [
            {
                'title': 'HF Model: microsoft/DialoGPT-medium',
                'summary': '最新AI模型发布: microsoft/DialoGPT-medium，下载量: 1500000',
                'url': 'https://huggingface.co/microsoft/DialoGPT-medium',
                'downloads': 1500000,
                'updated': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Hugging Face'
}
        ]
    
    def _get_backup_blog_data(self) -> List[Dict]:
        """备用博客数据"""
        return [
            {
                'title': 'GitHub Copilot最新功能更新',
                'summary': 'GitHub Copilot推出新功能，支持更多编程语言和更智能的代码建议，提升开发效率。',
                'url': 'https://github.blog',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'GitHub Blog'
}
        ]
    
    # ============== 异步采集方法 ==============
    
    async def _fetch_url_async(self, session: aiohttp.ClientSession, url: str,
                                semaphore: asyncio.Semaphore) -> Optional[str]:
        """异步获取URL内容（带重试）"""
        async with semaphore:
            for attempt in range(self.async_config.max_retries + 1):
                try:
                    self.stats['requests_made'] += 1
                    await asyncio.sleep(self.async_config.rate_limit_delay)
                    
                    timeout = aiohttp.ClientTimeout(total=self.async_config.request_timeout)
                    async with session.get(url, headers=self.headers, timeout=timeout) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status == 429:
                            wait_time = self.async_config.retry_delay * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                        else:
                            return None
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    if attempt < self.async_config.max_retries:
                        await asyncio.sleep(self.async_config.retry_delay * (attempt + 1))
                except Exception:
                    pass
            
            self.stats['requests_failed'] += 1
            return None
    
    async def _fetch_json_async(self, session: aiohttp.ClientSession, url: str,
                                 semaphore: asyncio.Semaphore, params: Optional[Dict] = None) -> Optional[Any]:
        """异步获取JSON内容"""
        async with semaphore:
            for attempt in range(self.async_config.max_retries + 1):
                try:
                    self.stats['requests_made'] += 1
                    await asyncio.sleep(self.async_config.rate_limit_delay)
                    
                    timeout = aiohttp.ClientTimeout(total=self.async_config.request_timeout)
                    async with session.get(url, headers=self.headers, timeout=timeout, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:
                            wait_time = self.async_config.retry_delay * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    if attempt < self.async_config.max_retries:
                        await asyncio.sleep(self.async_config.retry_delay * (attempt + 1))
                except Exception:
                    pass
            
            self.stats['requests_failed'] += 1
            return None
    
    async def _parse_rss_feed_async(self, session: aiohttp.ClientSession,
                                     feed_url: str, category: str,
                                     semaphore: asyncio.Semaphore,
                                     enable_url_filter: bool = True) -> List[Dict]:
        """异步解析RSS源（支持URL预过滤）
        
        Args:
            enable_url_filter: 是否启用URL预过滤（默认True）
        """
        items = []
        try:
            content = await self._fetch_url_async(session, feed_url, semaphore)
            if not content:
                return items
            
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, content)
            
            # 先提取所有URL并进行预过滤
            entries_to_process = []
            if enable_url_filter:
                for entry in feed.entries[:10]:
                    url = entry.get('link', '')
                    if url and url not in self.history_cache['urls']:
                        entries_to_process.append(entry)
            else:
                entries_to_process = feed.entries[:10]
            
            # 只处理新URL的内容
            for entry in entries_to_process:
                date_val = entry.get('published_parsed') or entry.get('published')
                if date_val and not self._is_recent(date_val):
                    continue
                
                # 清理 summary 中的 HTML 标签
                raw_summary = entry.get('summary', entry.get('description', ''))
                clean_summary = self._clean_html(raw_summary, max_length=300)
                
                item = {
                    'title': entry.get('title', ''),
                    'summary': clean_summary,
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': feed.feed.get('title', feed_url)[:50],
                    '_source_type': category  # 内部分组用，不用于分类
}
                
                if self._is_valid_item(item):
                    items.append(item)
        except Exception:
            pass
        
        return items
    
    async def _collect_research_papers_async(self, max_results: int = 10) -> List[Dict]:
        """异步采集研究论文 (arxiv库不支持异步，使用executor)"""
        loop = asyncio.get_event_loop()
        papers = await loop.run_in_executor(None, self.collect_research_papers, max_results)
        # 添加 _source_type 用于内部分组
        for paper in papers:
            paper['_source_type'] = 'research'
        return papers
    
    async def _collect_github_trending_async(self, session: aiohttp.ClientSession, 
                                            semaphore: asyncio.Semaphore,
                                            enable_url_filter: bool = True) -> List[Dict]:
        """异步采集GitHub热门项目（支持URL预过滤）"""
        projects = []
        try:
            last_month = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            url = "https://api.github.com/search/repositories"
            query = f'(machine-learning OR artificial-intelligence OR deep-learning OR llm) created:>{last_month}'
            
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': 15
            }
            
            data = await self._fetch_json_async(session, url, semaphore, params)
            if data:
                # 先过滤掉已缓存的URL
                repos_to_process = []
                for repo in data.get('items', [])[:15]:
                    repo_url = repo.get('html_url', '')
                    if enable_url_filter:
                        if repo_url and repo_url not in self.history_cache['urls']:
                            repos_to_process.append(repo)
                    else:
                        repos_to_process.append(repo)
                
                # 只处理新repo
                for repo in repos_to_process:
                    if not self._is_recent(repo.get('updated_at', '')):
                        continue
                    
                    project = {
                        'title': repo['full_name'],
                        'summary': repo.get('description') or 'No description',
                        'url': repo['html_url'],
                        'stars': repo.get('stargazers_count', 0),
                        'language': repo.get('language', 'Unknown'),
                        'updated': repo['updated_at'][:10],
                        'published': repo['updated_at'][:10],
                        'source': 'GitHub',
                        '_source_type': 'developer'  # 内部分组用
                    }
                    projects.append(project)
        except Exception as e:
            log.warning(f"GitHub trending async failed: {e}")
        
        return projects
    
    async def _collect_huggingface_async(self, session: aiohttp.ClientSession,
                                        semaphore: asyncio.Semaphore,
                                        enable_url_filter: bool = True) -> List[Dict]:
        """异步采集Hugging Face更新（支持URL预过滤）"""
        updates = []
        try:
            url = "https://huggingface.co/api/models"
            params = {'limit': 10, 'sort': 'lastModified', 'direction': -1}
            
            data = await self._fetch_json_async(session, url, semaphore, params)
            if data:
                # 先过滤掉已缓存的URL
                models_to_process = []
                for model in data[:10]:
                    model_url = f"https://huggingface.co/{model['id']}"
                    if enable_url_filter:
                        if model_url and model_url not in self.history_cache['urls']:
                            models_to_process.append(model)
                    else:
                        models_to_process.append(model)
                
                # 只处理新模型
                for model in models_to_process:
                    if not self._is_recent(model.get('lastModified', '')):
                        continue
                    
                    update = {
                        'title': f"HF Model: {model['id']}",
                        'summary': f"Latest AI model: {model['id']}, downloads: {model.get('downloads', 0)}",
                        'url': f"https://huggingface.co/{model['id']}",
                        'downloads': model.get('downloads', 0),
                        'updated': model.get('lastModified', '')[:10],
                        'published': model.get('lastModified', '')[:10],
                        'source': 'Hugging Face',
                        '_source_type': 'developer'  # 内部分组用
                    }
                    updates.append(update)
        except Exception as e:
            log.warning(f"Hugging Face async failed: {e}")
        
        return updates
    
    async def _collect_hacker_news_async(self, session: aiohttp.ClientSession,
                                        semaphore: asyncio.Semaphore,
                                        max_items: int = 10,
                                        enable_url_filter: bool = True) -> List[Dict]:
        """异步采集Hacker News（支持URL预过滤）"""
        items = []
        try:
            # 获取top stories
            top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            story_ids = await self._fetch_json_async(session, top_url, semaphore, None)
            
            if not story_ids:
                return items
            
            # 并发获取story详情
            ai_keywords = ['ai', 'llm', 'gpt', 'machine learning', 'deep learning', 
                          'neural', 'openai', 'anthropic', 'chatgpt']
            
            # 为每个story ID构建URL，用于预过滤
            story_tasks = []
            for story_id in story_ids[:50]:  # 检查前50个
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                # 注意：HN的URL实际是story本身的url字段，这里我们仍需要获取详情来判断
                # 但可以先检查story ID是否已处理过（通过构造标准URL）
                story_tasks.append(self._fetch_json_async(session, story_url, semaphore, None))
            
            stories = await asyncio.gather(*story_tasks, return_exceptions=True)
            
            for story in stories:
                if isinstance(story, dict) and story.get('title'):
                    title_lower = story['title'].lower()
                    if any(kw in title_lower for kw in ai_keywords):
                        # 构建URL用于过滤检查
                        story_url = story.get('url', f"https://news.ycombinator.com/item?id={story['id']}")
                        
                        # URL预过滤：跳过已缓存的URL
                        if enable_url_filter and story_url in self.history_cache['urls']:
                            continue
                        
                        # 检查时间
                        if story.get('time'):
                            published = datetime.fromtimestamp(story['time'])
                            if not self._is_recent(published):
                                continue
                            published_str = published.strftime('%Y-%m-%d')
                        else:
                            published_str = datetime.now().strftime('%Y-%m-%d')
                        
                        item = {
                            'title': story['title'],
                            'summary': self._clean_html(story.get('text', story['title'])),
                            'url': story_url,
                            'published': published_str,
                            'source': 'Hacker News',
                            'score': story.get('score', 0),
                            '_source_type': 'community'  # 内部分组用
                        }
                        items.append(item)
                        
                        if len(items) >= max_items:
                            break
        except Exception as e:
            log.warning(f"Hacker News async failed: {e}")
        
        return items
    
    async def _collect_product_releases_async(self, session: aiohttp.ClientSession,
                                             semaphore: asyncio.Semaphore,
                                             max_results: int = 10) -> List[Dict]:
        """异步采集产品发布（通过RSS源）"""
        products = []
        
        # 使用产品相关的RSS源
        product_feeds = RSS_FEEDS.get('product_news', [])
        
        tasks = []
        for feed_url in product_feeds:
            tasks.append(self._parse_rss_feed_async(session, feed_url, 'product', semaphore))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                for item in result:
                    if self._is_product_related(item):
                        products.append(item)
        
        # 按发布时间排序
        products.sort(key=lambda x: x.get('published', ''), reverse=True)
        return products[:max_results]
    
    async def _collect_leaders_quotes_async(self, session: aiohttp.ClientSession,
                                           semaphore: asyncio.Semaphore,
                                           max_results: int = 15) -> List[Dict]:
        """异步采集AI领袖言论"""
        quotes = []
        
        leaders = {
            "Sam Altman": "OpenAI CEO",
            "Elon Musk": "xAI Founder",
            "Jensen Huang": "NVIDIA CEO",
            "Demis Hassabis": "Google DeepMind CEO",
            "Yann LeCun": "Meta Chief AI Scientist",
            "Geoffrey Hinton": "AI Pioneer",
            "Andrew Ng": "AI Fund Managing General Partner",
            "Kai-Fu Lee": "01.AI CEO",
            "Robin Li": "Baidu CEO"
        }
        
        # 使用Google News RSS搜索每个领袖
        tasks = []
        for leader_name in leaders.keys():
            query_name = leader_name.replace(' ', '+')
            feed_url = f"https://news.google.com/rss/search?q={query_name}+AI+when:30d&hl=en-US&gl=US&ceid=US:en"
            tasks.append(self._parse_rss_feed_async(session, feed_url, 'leader', semaphore))
        
        # 同时采集个人博客
        for source in self.rss_feeds.get('leader_blogs', []):
            tasks.append(self._parse_rss_feed_async(session, source['url'], 'leader', semaphore))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(results):
            if isinstance(result, list):
                for item in result:
                    # 如果是新闻搜索结果，添加领袖信息
                    if i < len(leaders):
                        leader_name = list(leaders.keys())[i]
                        item['author'] = leader_name
                        item['author_title'] = leaders[leader_name]
                    
                    quotes.append(item)
        
        # 如果数量不足，添加备用数据
        if len(quotes) < 5:
            backup_data = self._get_backup_leaders_data()
            for item in backup_data:
                item['_source_type'] = 'leader'  # 为备用数据添加分组标记
            quotes.extend(backup_data)
        
        # 去重
        quotes = self._deduplicate_items(quotes)
        return quotes[:max_results]
    
    async def _collect_community_async(self, session: aiohttp.ClientSession,
                                      semaphore: asyncio.Semaphore,
                                      max_results: int = 15) -> List[Dict]:
        """异步采集社区热点"""
        trends = []
        
        # Hacker News (使用API)
        hn_items = await self._collect_hacker_news_async(session, semaphore, max_items=10)
        trends.extend(hn_items)
        
        # 其他社区RSS源
        community_feeds = [f for f in self.rss_feeds.get('community', []) if 'hnrss' not in f]
        
        tasks = []
        for feed_url in community_feeds:
            tasks.append(self._parse_rss_feed_async(session, feed_url, 'community', semaphore))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                for item in result:
                    trends.append(item)
        
        # 去重并排序
        trends = self._deduplicate_items(trends)
        trends.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        return trends[:max_results]
    
    async def _collect_all_async(self) -> Dict[str, List[Dict]]:
        """
        异步采集所有类型的数据（带URL预过滤优化）
        
        Returns:
            分类的数据字典
        """
        self.stats['start_time'] = time.time()
        log.dual_start(t('dc_start_collection'))
        log.dual_separator("=", 50)
        log.dual_info("🚀 异步采集模式 + URL预过滤优化 (Async Mode with URL Pre-filtering)", emoji="")
        
        all_data = {
            'research': [],
            'developer': [],
            'product': [],
            'news': [],
            'leader': [],
            'community': []
        }
        
        # 从配置读取采集数量
        product_count = config.get('collector.product_count', 15)
        community_count = config.get('collector.community_count', 10)
        leader_count = config.get('collector.leader_count', 15)
        research_count = config.get('collector.research_count', 15)
        developer_count = config.get('collector.developer_count', 20)
        news_count = config.get('collector.news_count', 25)
        
        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(self.async_config.max_concurrent_requests)
        
        # 创建共享的aiohttp会话
        connector = aiohttp.TCPConnector(
            limit=self.async_config.max_concurrent_requests,
            limit_per_host=self.async_config.max_concurrent_per_host
        )
        timeout = aiohttp.ClientTimeout(total=self.async_config.total_timeout)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 并发采集所有数据源
            log.dual_info("📡 启动并发采集任务...", emoji="")
            
            # 创建所有采集任务
            tasks = []
            
            # 1. 新闻RSS源
            news_feeds = RSS_FEEDS['news'] + RSS_FEEDS.get('product_news', [])
            for feed_url in news_feeds:
                tasks.append(self._parse_rss_feed_async(session, feed_url, 'news', semaphore))
            
            # 2. 开发者内容 (GitHub + Hugging Face + 博客RSS)
            tasks.append(self._collect_github_trending_async(session, semaphore))
            tasks.append(self._collect_huggingface_async(session, semaphore))
            for feed_url in RSS_FEEDS['developer']:
                tasks.append(self._parse_rss_feed_async(session, feed_url, 'developer', semaphore))
            
            # 3. 产品发布
            tasks.append(self._collect_product_releases_async(session, semaphore, product_count))
            
            # 4. AI领袖言论
            tasks.append(self._collect_leaders_quotes_async(session, semaphore, leader_count))
            
            # 5. 社区热点
            tasks.append(self._collect_community_async(session, semaphore, community_count))
            
            # 6. 研究论文 (在executor中运行)
            tasks.append(self._collect_research_papers_async(research_count))
            
            # 并发执行所有任务
            log.dual_info(f"⚡ 并发执行 {len(tasks)} 个采集任务", emoji="")
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 分类收集结果
            for result in all_results:
                if isinstance(result, list):
                    for item in result:
                        # 使用 _source_type 进行内部分组（不是分类标签）
                        source_type = item.pop('_source_type', 'news')  # 移除并获取，默认为 news
                        if source_type in all_data:
                            all_data[source_type].append(item)
                elif isinstance(result, Exception):
                    log.warning(f"Task failed: {result}")
        
        # 去重
        for cat in all_data:
            all_data[cat] = self._deduplicate_items(all_data[cat])
        
        # 统计新旧内容
        new_stats = {}
        cached_stats = {}
        new_items_for_cache = []
        
        for cat in all_data:
            new_count = 0
            cached_count = 0
            for item in all_data[cat]:
                if self._is_in_history(item):
                    cached_count += 1
                else:
                    new_count += 1
                    new_items_for_cache.append(item)
            new_stats[cat] = new_count
            cached_stats[cat] = cached_count
        
        # 更新历史缓存
        for item in new_items_for_cache:
            self._add_to_history(item)
        
        if new_items_for_cache:
            self._save_history_cache()
        
        # 更新统计信息
        self.stats['end_time'] = time.time()
        self.stats['items_collected'] = sum(len(items) for items in all_data.values())
        
        # 打印统计
        total_items = self.stats['items_collected']
        total_new = sum(new_stats.values())
        total_cached = sum(cached_stats.values())
        elapsed = self.stats['end_time'] - self.stats['start_time']
        
        log.dual_separator("=", 50)
        log.dual_done(f"采集完成: {total_items} items ({total_new} new, {total_cached} cached)")
        log.dual_info(f"⏱️ 耗时: {elapsed:.1f}s | 请求: {self.stats['requests_made']} | 失败: {self.stats['requests_failed']}", emoji="")
        
        for category, items in all_data.items():
            new_count = new_stats.get(category, 0)
            log.dual_data(f"  {category}: {len(items)} ({new_count} new)")
        
        return all_data

# 用于向后兼容
DataCollector = AIDataCollector
