"""
AI世界追踪器 - 异步数据采集模块
使用 asyncio + aiohttp 实现高性能并发采集

特性:
- 全异步I/O，比线程池更高效
- 自动重试机制
- 速率限制（避免被封）
- 信号量控制并发数
- 超时保护
- 与同步API兼容
"""

import asyncio
import aiohttp
import feedparser
import arxiv
import json
import os
import yaml
import time
import random
import difflib
import hashlib
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from typing import List, Dict, Optional, Callable, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from config import config
from logger import get_log_helper

# 导入国际化模块
try:
    from i18n import t, get_language
except ImportError:
    def t(key, **kwargs): return key
    def get_language(): return 'zh'

# 模块日志器
log = get_log_helper('async_collector')


# ============== 配置 ==============

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


# ============== RSS源配置 ==============

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


# ============== 异步数据采集器 ==============

class AsyncDataCollector:
    """异步AI数据采集器"""
    
    def __init__(self, config: Optional[AsyncCollectorConfig] = None):
        self.config = config or _load_async_config()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 采集历史缓存
        self.history_cache_file = os.path.join(self.config.cache_dir, 'collection_history_cache.json')
        self.history_cache = self._load_history_cache()
        
        # 统计信息
        self.stats = {
            'requests_made': 0,
            'requests_failed': 0,
            'items_collected': 0,
            'start_time': None,
            'end_time': None
        }
    
    # ============== 缓存管理 ==============
    
    def _load_history_cache(self) -> Dict:
        """加载采集历史缓存"""
        try:
            if os.path.exists(self.history_cache_file):
                with open(self.history_cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
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
                        cache['urls'] = set(cache['urls'])
                        cache['titles'] = set(cache['titles'])
                        return cache
        except Exception as e:
            log.error(f"Failed to load history cache: {e}")
        return {'urls': set(), 'titles': set(), 'last_updated': ''}
    
    def _save_history_cache(self):
        """保存采集历史缓存"""
        try:
            cache_to_save = {
                'urls': list(self.history_cache['urls']),
                'titles': list(self.history_cache['titles']),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.history_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"Failed to save history cache: {e}")
    
    def _is_in_history(self, item: Dict) -> bool:
        """检查项目是否在历史缓存中"""
        url = item.get('url', '')
        title = item.get('title', '')
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
        self.history_cache = {'urls': set(), 'titles': set(), 'last_updated': ''}
        if os.path.exists(self.history_cache_file):
            os.remove(self.history_cache_file)
        log.success(t('dc_cache_cleared'))
    
    # ============== 工具方法 ==============
    
    def _is_recent(self, date_val) -> bool:
        """检查日期是否在最近30天内"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            if isinstance(date_val, datetime):
                if date_val.tzinfo is not None:
                    return date_val.timestamp() >= cutoff_date.timestamp()
                return date_val >= cutoff_date
            
            if isinstance(date_val, str):
                try:
                    dt = date_parser.parse(date_val)
                    return dt.timestamp() >= cutoff_date.timestamp()
                except (ValueError, TypeError, AttributeError):
                    if len(date_val) >= 10:
                        dt = datetime.strptime(date_val[:10], '%Y-%m-%d')
                        return dt >= cutoff_date
            
            if isinstance(date_val, time.struct_time):
                dt = datetime.fromtimestamp(time.mktime(date_val))
                return dt >= cutoff_date
            
            return True
        except Exception:
            return True
    
    def _is_ai_related(self, item: Dict) -> bool:
        """检查内容是否与AI相关"""
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        return any(keyword in text for keyword in AI_KEYWORDS)
    
    def _is_product_related(self, item: Dict) -> bool:
        """检查内容是否与产品发布相关"""
        product_keywords = [
            'launch', 'release', 'announce', 'unveil', 'available',
            '发布', '推出', '上线', '正式', '新版本'
        ]
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        return any(keyword in text for keyword in product_keywords)
    
    def _is_valid_item(self, item: Dict) -> bool:
        """验证数据项有效性"""
        return (item.get('title') and 
                item.get('url') and 
                len(item.get('title', '')) > 10)
    
    def _calculate_importance(self, title: str, summary: str) -> float:
        """计算内容重要性"""
        text = f"{title} {summary}".lower()
        high_value_keywords = [
            'breakthrough', 'new', 'launch', 'release',
            '突破', '发布', '新', '最新'
        ]
        score = 0.5
        for keyword in high_value_keywords:
            if keyword in text:
                score += 0.1
        return min(score, 1.0)
    
    def _deduplicate_items(self, items: List[Dict], threshold: float = 0.6) -> List[Dict]:
        """对内容列表进行去重"""
        if not items:
            return []
        
        unique_items = []
        sorted_items = sorted(items, key=lambda x: x.get('importance', 0), reverse=True)
        
        for item in sorted_items:
            is_duplicate = False
            for existing in unique_items:
                seq = difflib.SequenceMatcher(None, item['title'].lower(), existing['title'].lower())
                if seq.ratio() > threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_items.append(item)
        
        return unique_items
    
    # ============== 异步HTTP请求 ==============
    
    async def _fetch_url(self, session: aiohttp.ClientSession, url: str, 
                         semaphore: asyncio.Semaphore) -> Optional[str]:
        """
        异步获取URL内容（带重试）
        
        Args:
            session: aiohttp会话
            url: 要获取的URL
            semaphore: 并发控制信号量
            
        Returns:
            响应内容或None
        """
        async with semaphore:
            for attempt in range(self.config.max_retries + 1):
                try:
                    self.stats['requests_made'] += 1
                    
                    # 速率限制
                    await asyncio.sleep(self.config.rate_limit_delay)
                    
                    timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
                    async with session.get(url, headers=self.headers, timeout=timeout) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status == 429:  # Too Many Requests
                            wait_time = self.config.retry_delay * (2 ** attempt)
                            log.warning(f"Rate limited on {url}, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                        else:
                            log.warning(f"HTTP {response.status} for {url}")
                            return None
                            
                except asyncio.TimeoutError:
                    log.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
                except aiohttp.ClientError as e:
                    log.warning(f"Client error fetching {url}: {e}")
                except Exception as e:
                    log.error(f"Error fetching {url}: {e}")
                
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
            
            self.stats['requests_failed'] += 1
            return None
    
    async def _fetch_json(self, session: aiohttp.ClientSession, url: str,
                          semaphore: asyncio.Semaphore, params: Optional[Dict] = None) -> Optional[Dict]:
        """异步获取JSON内容"""
        async with semaphore:
            for attempt in range(self.config.max_retries + 1):
                try:
                    self.stats['requests_made'] += 1
                    await asyncio.sleep(self.config.rate_limit_delay)
                    
                    timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
                    async with session.get(url, headers=self.headers, timeout=timeout, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:
                            wait_time = self.config.retry_delay * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                        else:
                            return None
                            
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    log.warning(f"Error fetching JSON from {url}: {e}")
                
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
            
            self.stats['requests_failed'] += 1
            return None
    
    # ============== RSS解析 ==============
    
    async def _parse_rss_feed_async(self, session: aiohttp.ClientSession, 
                                     feed_url: str, category: str,
                                     semaphore: asyncio.Semaphore) -> List[Dict]:
        """异步解析RSS源"""
        items = []
        
        try:
            content = await self._fetch_url(session, feed_url, semaphore)
            if not content:
                return items
            
            # feedparser 是同步的，在线程池中运行
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, content)
            
            for entry in feed.entries[:10]:
                date_val = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    date_val = entry.published_parsed
                elif entry.get('published'):
                    date_val = entry.get('published')
                
                if date_val and not self._is_recent(date_val):
                    continue
                
                item = {
                    'title': entry.get('title', ''),
                    'summary': (entry.get('summary', entry.get('description', ''))[:300] + "...") 
                               if len(entry.get('summary', entry.get('description', ''))) > 300 else 
                               entry.get('summary', entry.get('description', '')),
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': feed.feed.get('title', feed_url)[:50],
                    'category': category,
                    'importance': 0.6
                }
                
                if self._is_valid_item(item):
                    items.append(item)
        
        except Exception as e:
            log.warning(f"Failed to parse RSS {feed_url}: {e}")
        
        return items
    
    # ============== 各类数据采集 ==============
    
    async def collect_research_papers_async(self, max_results: int = 15) -> List[Dict]:
        """异步采集arXiv研究论文"""
        log.dual_start(t('dc_collect_research'))
        papers = []
        
        try:
            # arxiv 库是同步的，在线程池中运行
            loop = asyncio.get_event_loop()
            
            def fetch_arxiv():
                client = arxiv.Client()
                search_query = arxiv.Search(
                    query="cat:cs.AI OR cat:cs.LG OR cat:cs.CV OR cat:cs.CL",
                    max_results=max_results,
                    sort_by=arxiv.SortCriterion.SubmittedDate
                )
                return list(client.results(search_query))
            
            results = await loop.run_in_executor(None, fetch_arxiv)
            
            for result in results:
                if not self._is_recent(result.published):
                    continue
                
                paper = {
                    'title': result.title,
                    'summary': result.summary[:300] + "..." if len(result.summary) > 300 else result.summary,
                    'authors': [str(author) for author in result.authors[:5]],
                    'url': result.entry_id,
                    'published': result.published.strftime('%Y-%m-%d'),
                    'categories': [str(cat) for cat in result.categories],
                    'source': 'arXiv',
                    'category': 'research',
                    'importance': self._calculate_importance(result.title, result.summary)
                }
                papers.append(paper)
            
            log.dual_success(t('dc_got_papers', count=len(papers)))
            
        except Exception as e:
            log.error(f"arXiv collection failed: {e}")
            papers = self._get_backup_research_data()
        
        return papers
    
    async def collect_github_trending_async(self, session: aiohttp.ClientSession,
                                            semaphore: asyncio.Semaphore) -> List[Dict]:
        """异步采集GitHub AI热门项目"""
        projects = []
        
        try:
            last_month = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            url = "https://api.github.com/search/repositories"
            params = {
                'q': f'(machine-learning OR artificial-intelligence OR deep-learning OR llm) created:>{last_month}',
                'sort': 'stars',
                'order': 'desc',
                'per_page': 15
            }
            
            data = await self._fetch_json(session, url, semaphore, params)
            
            if data:
                for repo in data.get('items', []):
                    if not self._is_recent(repo.get('updated_at', '')):
                        continue
                    
                    project = {
                        'title': repo['full_name'],
                        'summary': repo.get('description', '无描述') or '无描述',
                        'url': repo['html_url'],
                        'stars': repo['stargazers_count'],
                        'language': repo.get('language', ''),
                        'updated': repo['updated_at'][:10],
                        'source': 'GitHub',
                        'category': 'developer',
                        'importance': min(repo['stargazers_count'] / 1000, 1.0)
                    }
                    projects.append(project)
        
        except Exception as e:
            log.warning(f"GitHub collection failed: {e}")
            projects = self._get_backup_github_data()
        
        return projects
    
    async def collect_huggingface_async(self, session: aiohttp.ClientSession,
                                        semaphore: asyncio.Semaphore) -> List[Dict]:
        """异步采集Hugging Face更新"""
        updates = []
        
        try:
            url = "https://huggingface.co/api/models"
            params = {'limit': 10, 'sort': 'lastModified', 'direction': -1}
            
            models = await self._fetch_json(session, url, semaphore, params)
            
            if models:
                for model in models:
                    if not self._is_recent(model.get('lastModified', '')):
                        continue
                    
                    update = {
                        'title': f"HF Model: {model['id']}",
                        'summary': f"最新AI模型发布: {model['id']}，下载量: {model.get('downloads', 0)}",
                        'url': f"https://huggingface.co/{model['id']}",
                        'downloads': model.get('downloads', 0),
                        'updated': model.get('lastModified', '')[:10] if model.get('lastModified') else '',
                        'source': 'Hugging Face',
                        'category': 'developer',
                        'importance': min(model.get('downloads', 0) / 10000, 1.0)
                    }
                    updates.append(update)
        
        except Exception as e:
            log.warning(f"Hugging Face collection failed: {e}")
            updates = self._get_backup_hf_data()
        
        return updates
    
    async def collect_hacker_news_async(self, session: aiohttp.ClientSession,
                                        semaphore: asyncio.Semaphore,
                                        max_items: int = 15) -> List[Dict]:
        """异步采集Hacker News AI相关内容"""
        items = []
        HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
        
        try:
            # 获取最新故事ID
            story_ids = await self._fetch_json(session, f"{HN_API_BASE}/newstories.json", semaphore)
            
            if not story_ids:
                return items
            
            # 并发获取故事详情
            async def fetch_story(story_id: int) -> Optional[Dict]:
                return await self._fetch_json(session, f"{HN_API_BASE}/item/{story_id}.json", semaphore)
            
            # 限制检查的故事数量
            tasks = [fetch_story(sid) for sid in story_ids[:80]]
            stories = await asyncio.gather(*tasks, return_exceptions=True)
            
            ai_stories = []
            for story in stories:
                if isinstance(story, Exception) or not story:
                    continue
                if story.get('deleted') or story.get('dead'):
                    continue
                
                title = story.get('title', '').lower()
                text = (story.get('text', '') or '').lower()
                url = story.get('url', '')
                combined_text = f"{title} {text} {url}".lower()
                
                if any(term in combined_text for term in HN_SEARCH_TERMS):
                    ai_stories.append(story)
                    if len(ai_stories) >= max_items * 2:
                        break
            
            # 转换格式
            for story in ai_stories[:max_items]:
                pub_time = datetime.fromtimestamp(story.get('time', 0))
                if not self._is_recent(pub_time):
                    continue
                
                text_content = story.get('text', '')
                if text_content:
                    soup = BeautifulSoup(text_content, 'html.parser')
                    summary = soup.get_text()[:300]
                else:
                    score = story.get('score', 0)
                    comments = story.get('descendants', 0)
                    author = story.get('by', 'unknown')
                    summary = f"Posted by {author} | {score} points | {comments} comments"
                
                item = {
                    'title': story.get('title', ''),
                    'summary': summary,
                    'url': story.get('url') or f"https://news.ycombinator.com/item?id={story.get('id')}",
                    'published': pub_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'Hacker News',
                    'category': 'community',
                    'importance': 0.7,
                    'score': story.get('score', 0),
                    'comments': story.get('descendants', 0)
                }
                
                if self._is_valid_item(item):
                    items.append(item)
        
        except Exception as e:
            log.warning(f"Hacker News collection failed: {e}")
        
        return items
    
    async def collect_leader_news_async(self, session: aiohttp.ClientSession,
                                        semaphore: asyncio.Semaphore,
                                        max_results: int = 15) -> List[Dict]:
        """异步采集AI领袖相关新闻"""
        quotes = []
        
        # 并发获取所有领袖的新闻
        async def fetch_leader_news(leader_name: str, title: str) -> List[Dict]:
            results = []
            query_name = leader_name.replace(' ', '+')
            
            # 使用Bing News RSS
            feed_url = f"https://www.bing.com/news/search?q={query_name}+AI&format=rss"
            
            try:
                content = await self._fetch_url(session, feed_url, semaphore)
                if content:
                    loop = asyncio.get_event_loop()
                    feed = await loop.run_in_executor(None, feedparser.parse, content)
                    
                    count = 0
                    for entry in feed.entries:
                        if count >= 2:
                            break
                        
                        date_val = entry.get('published_parsed') or entry.get('published')
                        if date_val and not self._is_recent(date_val):
                            continue
                        
                        text = (entry.title + " " + entry.get('summary', '')).lower()
                        if any(k in text for k in ['said', 'says', 'stated', 'warns', 'believes', 'interview']):
                            quote = {
                                'title': f"{leader_name}: {entry.title}",
                                'summary': entry.get('summary', entry.title)[:300],
                                'url': entry.link,
                                'published': entry.get('published', datetime.now().strftime('%Y-%m-%d')),
                                'source': f"News about {leader_name}",
                                'category': 'leader',
                                'author': leader_name,
                                'author_title': title,
                                'importance': 0.95
                            }
                            results.append(quote)
                            count += 1
            except Exception as e:
                log.warning(f"Failed to fetch news for {leader_name}: {e}")
            
            return results
        
        # 并发获取所有领袖新闻
        tasks = [fetch_leader_news(name, title) for name, title in AI_LEADERS.items()]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in all_results:
            if isinstance(result, list):
                quotes.extend(result)
        
        # 采集领袖个人博客
        for source in RSS_FEEDS.get('leader_blogs', []):
            try:
                feed_items = await self._parse_rss_feed_async(
                    session, source['url'], 'leader', semaphore
                )
                for item in feed_items[:3]:
                    if source.get('type') == 'podcast':
                        found_leader = False
                        for leader_name in AI_LEADERS.keys():
                            if leader_name.lower() in item['title'].lower():
                                found_leader = True
                                item['author'] = leader_name
                                break
                        if not found_leader:
                            continue
                    else:
                        item['author'] = source['author']
                    
                    item['author_title'] = source['title']
                    item['importance'] = 1.0
                    item['category'] = 'leader'
                    quotes.append(item)
            except Exception as e:
                log.warning(f"Failed to fetch blog for {source.get('author')}: {e}")
        
        # 去重
        unique_quotes = []
        seen_urls = set()
        for q in quotes:
            if q['url'] not in seen_urls:
                unique_quotes.append(q)
                seen_urls.add(q['url'])
        
        # 如果数量不足，使用备用数据
        if len(unique_quotes) < 5:
            unique_quotes.extend(self._get_backup_leaders_data())
        
        return unique_quotes[:max_results]
    
    async def collect_product_releases_async(self, session: aiohttp.ClientSession,
                                             semaphore: asyncio.Semaphore,
                                             max_results: int = 10) -> List[Dict]:
        """异步采集AI产品发布信息"""
        products = []
        
        # 公司RSS源
        company_feeds = [
            ('OpenAI', 'https://openai.com/blog/rss.xml', 0.95),
            ('Google', 'https://blog.google/technology/ai/rss/', 0.92),
            ('Microsoft', 'https://blogs.microsoft.com/ai/feed/', 0.90),
        ]
        
        # 并发采集所有公司
        async def fetch_company_products(company: str, feed_url: str, importance: float) -> List[Dict]:
            items = await self._parse_rss_feed_async(session, feed_url, 'product', semaphore)
            for item in items:
                item['company'] = company
                item['importance'] = importance
            return items
        
        tasks = [fetch_company_products(c, f, i) for c, f, i in company_feeds]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in all_results:
            if isinstance(result, list):
                # 过滤非最近的产品
                recent_items = [p for p in result if self._is_recent(p.get('published', ''))]
                products.extend(recent_items)
        
        # 添加中国AI公司的备用数据
        if len(products) < max_results // 2:
            products.extend(self._get_backup_chinese_ai_data())
        
        # 按重要性排序
        products.sort(key=lambda x: x.get('importance', 0), reverse=True)
        return products[:max_results]
    
    async def collect_news_async(self, session: aiohttp.ClientSession,
                                 semaphore: asyncio.Semaphore,
                                 max_results: int = 25) -> List[Dict]:
        """异步采集AI行业新闻"""
        all_news = []
        
        # 并发采集所有新闻RSS
        news_feeds = RSS_FEEDS['news'] + RSS_FEEDS.get('product_news', [])
        
        tasks = [
            self._parse_rss_feed_async(session, feed_url, 'news', semaphore)
            for feed_url in news_feeds
        ]
        
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in all_results:
            if isinstance(result, list):
                all_news.extend(result)
        
        # 过滤AI相关内容
        ai_news = [item for item in all_news if self._is_ai_related(item)]
        
        # 去重
        ai_news = self._deduplicate_items(ai_news)
        
        # 按时间排序
        ai_news.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        # 产品相关新闻优先
        product_related = [item for item in ai_news if self._is_product_related(item)]
        other_news = [item for item in ai_news if not self._is_product_related(item)]
        
        prioritized_news = product_related + other_news
        return prioritized_news[:max_results]
    
    async def collect_developer_content_async(self, session: aiohttp.ClientSession,
                                              semaphore: asyncio.Semaphore,
                                              max_results: int = 20) -> List[Dict]:
        """异步采集开发者社区内容"""
        content = []
        
        # 并发采集GitHub、HuggingFace和开发者博客
        github_task = self.collect_github_trending_async(session, semaphore)
        hf_task = self.collect_huggingface_async(session, semaphore)
        
        blog_tasks = [
            self._parse_rss_feed_async(session, feed_url, 'developer', semaphore)
            for feed_url in RSS_FEEDS['developer']
        ]
        
        results = await asyncio.gather(
            github_task, hf_task, *blog_tasks,
            return_exceptions=True
        )
        
        # 合并结果
        for result in results:
            if isinstance(result, list):
                content.extend(result[:max_results // 3])
        
        return content[:max_results]
    
    async def collect_community_async(self, session: aiohttp.ClientSession,
                                      semaphore: asyncio.Semaphore,
                                      max_results: int = 15) -> List[Dict]:
        """异步采集社区热点"""
        trends = []
        
        # Hacker News
        hn_task = self.collect_hacker_news_async(session, semaphore, max_items=10)
        
        # Product Hunt等RSS
        rss_tasks = [
            self._parse_rss_feed_async(session, feed_url, 'community', semaphore)
            for feed_url in RSS_FEEDS['community']
        ]
        
        results = await asyncio.gather(hn_task, *rss_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, list):
                for item in result:
                    if i == 0:  # HN结果
                        score = item.get('score', 0)
                        if score > 100:
                            item['importance'] = 0.85
                        elif score > 50:
                            item['importance'] = 0.75
                        else:
                            item['importance'] = 0.65
                    else:
                        item['importance'] = item.get('importance', 0.6) + 0.1
                    trends.append(item)
        
        # 去重
        trends = self._deduplicate_items(trends)
        trends.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        return trends[:max_results]
    
    # ============== 主采集入口 ==============
    
    async def collect_all_async(self) -> Dict[str, List[Dict]]:
        """
        异步采集所有类型的数据
        
        Returns:
            分类的数据字典
        """
        self.stats['start_time'] = time.time()
        log.dual_start(t('dc_start_collection'))
        log.dual_separator("=", 50)
        log.dual_info("🚀 异步采集模式 (Async Mode)", emoji="")
        
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
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        # 创建共享的aiohttp会话
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent_requests,
            limit_per_host=self.config.max_concurrent_per_host
        )
        timeout = aiohttp.ClientTimeout(total=self.config.total_timeout)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 并发执行所有采集任务
            tasks = [
                ('research', self.collect_research_papers_async(research_count)),
                ('developer', self.collect_developer_content_async(session, semaphore, developer_count)),
                ('product', self.collect_product_releases_async(session, semaphore, product_count)),
                ('leader', self.collect_leader_news_async(session, semaphore, leader_count)),
                ('community', self.collect_community_async(session, semaphore, community_count)),
                ('news', self.collect_news_async(session, semaphore, news_count)),
            ]
            
            # 使用 gather 并发执行
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            # 收集结果
            for i, (category, _) in enumerate(tasks):
                result = results[i]
                if isinstance(result, Exception):
                    log.error(f"Task {category} failed: {result}")
                    all_data[category] = []
                else:
                    all_data[category] = result
                    log.dual_success(f"✓ {category}: {len(result)} items")
        
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
            cached_count = cached_stats.get(category, 0)
            log.dual_data(f"  {category}: {len(items)} ({new_count} new)")
        
        return all_data
    
    def collect_all(self, parallel: bool = True, max_workers: int = 6) -> Dict[str, List[Dict]]:
        """
        同步接口 - 兼容旧代码
        
        Args:
            parallel: 忽略（总是使用异步）
            max_workers: 忽略（使用配置中的并发数）
        
        Returns:
            分类的数据字典
        """
        return asyncio.run(self.collect_all_async())
    
    # ============== 备用数据 ==============
    
    def _get_backup_research_data(self) -> List[Dict]:
        """备用研究数据"""
        return [{
            'title': 'Attention Is All You Need: Transformer架构深度分析',
            'summary': '深入分析Transformer架构在自然语言处理中的革命性作用。',
            'authors': ['AI Research Team'],
            'url': 'https://arxiv.org/abs/1706.03762',
            'published': datetime.now().strftime('%Y-%m-%d'),
            'categories': ['cs.CL', 'cs.AI'],
            'source': 'arXiv',
            'category': 'research',
            'importance': 0.95
        }]
    
    def _get_backup_github_data(self) -> List[Dict]:
        """备用GitHub数据"""
        return [{
            'title': 'huggingface/transformers',
            'summary': '🤗 Transformers: State-of-the-art Machine Learning for PyTorch, TensorFlow, and JAX.',
            'url': 'https://github.com/huggingface/transformers',
            'stars': 132000,
            'language': 'Python',
            'updated': datetime.now().strftime('%Y-%m-%d'),
            'source': 'GitHub',
            'category': 'developer',
            'importance': 0.98
        }]
    
    def _get_backup_hf_data(self) -> List[Dict]:
        """备用Hugging Face数据"""
        return [{
            'title': 'HF Model: microsoft/DialoGPT-medium',
            'summary': '最新AI模型发布: microsoft/DialoGPT-medium，下载量: 1500000',
            'url': 'https://huggingface.co/microsoft/DialoGPT-medium',
            'downloads': 1500000,
            'updated': datetime.now().strftime('%Y-%m-%d'),
            'source': 'Hugging Face',
            'category': 'developer',
            'importance': 0.85
        }]
    
    def _get_backup_leaders_data(self) -> List[Dict]:
        """备用领袖言论数据"""
        return [
            {
                'title': 'Sam Altman: AI发展的速度将超出所有人的预期',
                'summary': 'OpenAI CEO Sam Altman在最近的采访中表示，AGI的到来可能比预期的要快。',
                'url': 'https://openai.com/blog',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Interview',
                'category': 'leader',
                'author': 'Sam Altman',
                'author_title': 'OpenAI CEO',
                'importance': 0.98
            },
            {
                'title': 'Jensen Huang: 生成式AI是计算领域的转折点',
                'summary': 'NVIDIA CEO黄仁勋表示，生成式AI正在重塑每一个行业。',
                'url': 'https://nvidianews.nvidia.com/',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Keynote',
                'category': 'leader',
                'author': 'Jensen Huang',
                'author_title': 'NVIDIA CEO',
                'importance': 0.92
            }
        ]
    
    def _get_backup_chinese_ai_data(self) -> List[Dict]:
        """备用中国AI公司数据"""
        return [
            {
                'title': '百度文心一言 4.0 发布',
                'summary': '百度发布文心一言4.0版本，在理解、生成、逻辑和记忆四大能力上都有显著提升。',
                'url': 'https://yiyan.baidu.com/',
                'company': 'Baidu',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Baidu AI',
                'category': 'product',
                'importance': 0.92
            },
            {
                'title': 'DeepSeek V2 开源发布',
                'summary': '深度求索(DeepSeek)发布DeepSeek-V2，强大的开源MoE大语言模型。',
                'url': 'https://www.deepseek.com/',
                'company': 'DeepSeek',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'DeepSeek',
                'category': 'product',
                'importance': 0.95
            }
        ]


# ============== 向后兼容 ==============

# 创建一个包装类，使异步采集器可以被原有代码直接使用
class DataCollector(AsyncDataCollector):
    """数据采集器 - 异步版本（兼容同步调用）"""
    pass


# ============== 独立测试 ==============

async def _test_async_collector():
    """测试异步采集器"""
    print("\n" + "="*60)
    print("🧪 Testing AsyncDataCollector")
    print("="*60 + "\n")
    
    collector = AsyncDataCollector()
    
    # 测试单个采集
    print("Testing individual collectors...")
    
    semaphore = asyncio.Semaphore(10)
    connector = aiohttp.TCPConnector(limit=10)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # 测试GitHub
        print("\n1. Testing GitHub...")
        github_data = await collector.collect_github_trending_async(session, semaphore)
        print(f"   Got {len(github_data)} GitHub projects")
        
        # 测试Hacker News
        print("\n2. Testing Hacker News...")
        hn_data = await collector.collect_hacker_news_async(session, semaphore, max_items=5)
        print(f"   Got {len(hn_data)} HN stories")
    
    # 测试完整采集
    print("\n3. Testing full collection...")
    all_data = await collector.collect_all_async()
    
    print("\n" + "="*60)
    print("✅ Test completed!")
    print("="*60)
    
    return all_data


if __name__ == "__main__":
    asyncio.run(_test_async_collector())
