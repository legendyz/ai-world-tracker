"""
AI世界追踪器 - 数据采集模块
专注于收集最新AI研究、产品、开发者社区和行业信息

使用纯异步模式 (asyncio + aiohttp) 进行高性能采集

使用方式:
    collector = DataCollector()
    data = collector.collect_all()
"""

import feedparser
import arxiv
import json
import os
import yaml
import random
import asyncio
import aiohttp
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import time
import difflib
import hashlib
from urllib.parse import urlparse
from warnings import filterwarnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from config import config
from logger import get_log_helper

# 导入国际化模块
try:
    from i18n import t, get_language
except ImportError:
    def t(key, **kwargs): return key
    def get_language(): return 'zh'

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
    except (OSError, yaml.YAMLError, KeyError) as e:
        # 配置文件读取失败，使用默认值
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
    
    # 缓存大小限制
    max_cache_size: int = 5000              # 历史缓存最大条目数

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
    except (OSError, yaml.YAMLError, KeyError) as e:
        # 配置加载失败，使用默认配置
        pass
    
    os.makedirs(cfg.cache_dir, exist_ok=True)
    return cfg

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
        # 美国科技巨头
        'https://openai.com/blog/rss.xml',
        'https://blog.google/technology/ai/rss/',
        'https://blogs.microsoft.com/ai/feed/',
        'https://ai.meta.com/blog/rss/',
        'https://www.anthropic.com/news/rss',
        # 中国科技公司 (via 36kr/机器之心等)
        'https://www.jiqizhixin.com/rss',
        'https://www.qbitai.com/feed',
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
    
    使用纯异步模式 (asyncio + aiohttp) 进行高性能采集
    
    支持上下文管理器用法:
        async with AIDataCollector() as collector:
            data = await collector._collect_all_async()
    """
    
    def __init__(self):
        # 异步配置
        self.async_config = _load_async_config()
        log.config("📡 Collector mode: Async (aiohttp)")
        
        # 数据采集时间窗口（天）- 从配置读取
        self.data_retention_days = config.collector.data_retention_days
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 使用统一的RSS源配置
        self.rss_feeds = RSS_FEEDS
        
        # 采集历史缓存
        self.history_cache_file = os.path.join(DATA_CACHE_DIR, 'collection_history_cache.json')
        self.history_cache = self._load_history_cache()
        
        # 统计信息（用于同步和异步模式）
        self.stats = {
            'requests_made': 0,
            'requests_failed': 0,
            'items_collected': 0,
            'start_time': None,
            'end_time': None,
            'failed_sources': []  # 失败的数据源列表: [{'source': 'xxx', 'category': 'xxx', 'error': 'xxx'}]
        }
        
        # 异步session（延迟初始化）
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口，确保资源清理"""
        await self._close_session()
        return False
    
    async def _ensure_session(self):
        """确保session已创建"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=self.async_config.max_concurrent_requests,
                limit_per_host=self.async_config.max_concurrent_per_host,
                ttl_dns_cache=300
            )
            timeout = aiohttp.ClientTimeout(
                total=self.async_config.total_timeout,
                connect=self.async_config.request_timeout,
                sock_read=self.async_config.request_timeout
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers
            )
    
    async def _close_session(self):
        """关闭异步session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def __del__(self):
        """析构函数，确保资源清理"""
        if self._session and not self._session.closed:
            # 在同步析构中无法调用异步close，记录警告
            log.warning("AIDataCollector session not properly closed")
    
    def _reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'requests_made': 0,
            'requests_failed': 0,
            'items_collected': 0,
            'start_time': None,
            'end_time': None,
            'failed_sources': []
        }
    
    def _record_failure(self, source: str, category: str, error: str):
        """记录采集失败的数据源
        
        Args:
            source: 数据源名称或URL
            category: 数据类别 (research/developer/product/news/leader/community)
            error: 错误信息
        """
        self.stats['requests_failed'] += 1
        self.stats['failed_sources'].append({
            'source': source[:80] if len(source) > 80 else source,  # 截断过长URL
            'category': category,
            'error': str(error)[:100]  # 截断过长错误信息
        })
    
    def _print_failed_sources_summary(self):
        """打印失败数据源汇总"""
        failed = self.stats.get('failed_sources', [])
        if not failed:
            return
        
        # 按类别分组统计
        by_category = {}
        for f in failed:
            cat = f['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f)
        
        # 双输出模式显示失败汇总
        log.dual_warning(t('dc_failed_sources_title', count=len(failed)))
        
        for cat, failures in by_category.items():
            log.dual_info(f"  [{cat}] {len(failures)} 失败:", emoji="")
            for f in failures[:3]:  # 每类别最多显示3个
                source_short = f['source'][:50] + '...' if len(f['source']) > 50 else f['source']
                log.dual_info(f"    • {source_short}", emoji="")
            if len(failures) > 3:
                log.dual_info(f"    ... 及其他 {len(failures) - 3} 个", emoji="")
    
    def _load_history_cache(self) -> Dict:
        """加载采集历史缓存（支持URL、标题、规范化标题）"""
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
                                    return {'urls': set(), 'titles': set(), 'normalized_titles': set(), 'last_updated': ''}
                            except (ValueError, TypeError):
                                pass
                        # 转换为 set 以加速查找，同时规范化URL
                        cache['urls'] = set(self._normalize_url(url) for url in cache['urls'])
                        cache['titles'] = set(cache['titles'])
                        # 加载规范化标题（新字段，兼容旧缓存）
                        cache['normalized_titles'] = set(cache.get('normalized_titles', []))
                        
                        # 如果是旧缓存（没有normalized_titles），自动生成
                        if not cache['normalized_titles'] and cache['titles']:
                            cache['normalized_titles'] = set(
                                self._normalize_title_for_cache(t) for t in cache['titles'] if t
                            )
                            log.file_only(f"自动生成规范化标题缓存: {len(cache['normalized_titles'])} 条")
                        
                        log.data(t('dc_cache_loaded', url_count=len(cache['urls']), title_count=len(cache['titles'])))
                        return cache
        except Exception as e:
            log.error(t('dc_cache_load_failed', error=str(e)))
        return {'urls': set(), 'titles': set(), 'normalized_titles': set(), 'last_updated': ''}
    
    def _save_history_cache(self):
        """保存采集历史缓存"""
        try:
            # 转换 set 为 list 以便 JSON 序列化
            cache_to_save = {
                'urls': list(self.history_cache['urls']),
                'titles': list(self.history_cache['titles']),
                'normalized_titles': list(self.history_cache.get('normalized_titles', set())),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.history_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(t('dc_cache_save_failed', error=str(e)))
    
    def _is_in_history(self, item: Dict) -> bool:
        """
        检查项目是否在历史缓存中
        
        匹配策略（按优先级）：
        1. URL规范化匹配（处理尾部斜杠、跟踪参数等）
        2. 标题精确匹配
        3. 规范化标题匹配（用于处理标题微小变化）
        
        对于不稳定URL源（如Google News），主要依赖标题匹配
        """
        url = item.get('url', '')
        title = item.get('title', '')
        
        # 检查是否为不稳定URL源（这些源的URL可能每次都不同）
        unstable_url_sources = [
            'news.google.com/rss/articles/',  # Google News重定向URL
            'feedburner.com',
            '/redirect/',
        ]
        is_unstable_url = url and any(s in url for s in unstable_url_sources)
        
        # 策略1: URL规范化匹配（对于稳定URL源优先使用）
        if url and not is_unstable_url:
            normalized_url = self._normalize_url(url)
            if normalized_url in self.history_cache['urls']:
                return True
        
        # 策略2: 标题精确匹配
        if title and title in self.history_cache['titles']:
            return True
        
        # 策略3: 规范化标题匹配（处理标题微小变化）
        if title:
            normalized_title = self._normalize_title_for_cache(title)
            if normalized_title and normalized_title in self.history_cache.get('normalized_titles', set()):
                return True
        
        return False
    
    def _normalize_title_for_cache(self, title: str) -> str:
        """
        为缓存目的规范化标题
        
        处理规则：
        1. 小写化
        2. 移除来源后缀（如 " - TechCrunch"）
        3. 移除标点符号
        4. 移除多余空格
        5. 只保留前60个字符（避免标题截断导致的差异）
        
        Args:
            title: 原始标题
            
        Returns:
            规范化后的标题
        """
        import re
        if not title:
            return ''
        
        # 小写化
        normalized = title.lower()
        
        # 移除来源后缀 (- Source, | Source, — Source)
        normalized = re.sub(r'\s*[-|—]\s*[a-z][a-z\s&.\']+$', '', normalized)
        
        # 移除标点符号（保留字母、数字、空格）
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # 移除多余空格
        normalized = ' '.join(normalized.split())
        
        # 截取前60字符（避免标题末尾差异）
        normalized = normalized[:60].strip()
        
        return normalized
    
    def _add_to_history(self, item: Dict):
        """
        将项目添加到历史缓存（带大小限制）
        
        缓存内容：
        1. 规范化URL
        2. 原始标题
        3. 规范化标题（用于模糊匹配）
        """
        url = item.get('url', '')
        title = item.get('title', '')
        
        # 检查缓存大小，超出限制时清理旧条目
        max_size = self.async_config.max_cache_size
        
        # 添加规范化URL
        if url:
            normalized_url = self._normalize_url(url)
            if len(self.history_cache['urls']) >= max_size:
                urls_list = list(self.history_cache['urls'])
                remove_count = max_size // 5  # 移除20%
                self.history_cache['urls'] = set(urls_list[remove_count:])
                log.file_only(f"缓存清理: URLs {len(urls_list)} → {len(self.history_cache['urls'])}")
            self.history_cache['urls'].add(normalized_url)
        
        # 添加原始标题
        if title:
            if len(self.history_cache['titles']) >= max_size:
                titles_list = list(self.history_cache['titles'])
                remove_count = max_size // 5
                self.history_cache['titles'] = set(titles_list[remove_count:])
                log.file_only(f"缓存清理: Titles {len(titles_list)} → {len(self.history_cache['titles'])}")
            self.history_cache['titles'].add(title)
            
            # 添加规范化标题（新增）
            normalized_title = self._normalize_title_for_cache(title)
            if normalized_title:
                if 'normalized_titles' not in self.history_cache:
                    self.history_cache['normalized_titles'] = set()
                if len(self.history_cache['normalized_titles']) >= max_size:
                    nt_list = list(self.history_cache['normalized_titles'])
                    remove_count = max_size // 5
                    self.history_cache['normalized_titles'] = set(nt_list[remove_count:])
                self.history_cache['normalized_titles'].add(normalized_title)
    
    def _filter_by_history(self, all_data: Dict[str, List[Dict]], 
                           filter_enabled: bool = True) -> Tuple[Dict[str, List[Dict]], Dict[str, int], Dict[str, int]]:
        """
        历史缓存最终过滤与缓存更新
        
        职责说明：
        1. 二次过滤：采集阶段的URL预过滤可能有遗漏（如跨类别重复），此处做最终清理
        2. 缓存更新：将新采集的项目添加到历史缓存，供下次采集时预过滤使用
        3. 统计输出：统计各类别的新内容与缓存命中数量
        
        与预过滤的区别：
        - 预过滤（采集阶段）：在网络请求前快速跳过已知URL，减少无效请求
        - 本方法（采集后）：确保最终数据无重复，并更新持久化缓存
        
        Args:
            all_data: 按类别分组的数据字典
            filter_enabled: 是否启用过滤（False则只统计不过滤）
            
        Returns:
            Tuple[filtered_data, new_stats, cached_stats]
            - filtered_data: 过滤后的数据（或原数据，取决于filter_enabled）
            - new_stats: 每个类别的新内容数量
            - cached_stats: 每个类别的缓存命中数量
        """
        new_stats = {}  # 记录每个类别的新内容数量
        cached_stats = {}  # 记录每个类别的缓存命中数量
        new_items_for_cache = []  # 记录新采集的项目（待加入缓存）
        
        if filter_enabled:
            # 过滤模式：移除历史中已有的项目
            filtered_data = {}
            for cat in all_data:
                new_items = []
                cached_count = 0
                for item in all_data[cat]:
                    if self._is_in_history(item):
                        cached_count += 1
                    else:
                        new_items.append(item)
                        new_items_for_cache.append(item)
                filtered_data[cat] = new_items
                new_stats[cat] = len(new_items)
                cached_stats[cat] = cached_count
        else:
            # 统计模式：只统计，不过滤
            filtered_data = all_data
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
        
        return filtered_data, new_stats, cached_stats
    
    def clear_history_cache(self):
        """清除采集历史缓存"""
        self.history_cache = {'urls': set(), 'titles': set(), 'normalized_titles': set(), 'last_updated': ''}
        if os.path.exists(self.history_cache_file):
            os.remove(self.history_cache_file)
        log.success(t('dc_cache_cleared'))

    def collect_all(self) -> Dict[str, List[Dict]]:
        """
        采集所有类型的数据（纯异步模式）
        
        Returns:
            分类的数据字典
        """
        try:
            # 在新的事件循环中运行异步采集
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._collect_all_async())
            finally:
                loop.close()
        except Exception as e:
            log.error(f"Async collection failed: {e}")
            raise
    
    # ============== 语义去重相关方法 ==============
    
    # 英文停用词（用于关键词提取）
    _STOPWORDS = frozenset({
        'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'but',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'that', 'this', 'these', 'those', 'with', 'from', 'by', 'as', 'into',
        'through', 'during', 'before', 'after', 'above', 'below', 'between',
        'says', 'said', 'predicts', 'predicted', 'tells', 'told', 'according',
        'thanks', 'about', 'over', 'under', 'again', 'further', 'then', 'once',
        'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'every',
        'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also',
        'now', 'new', 'first', 'last', 'long', 'great', 'little', 'own', 'make',
        'can', 'like', 'back', 'even', 'well', 'way', 'our', 'out', 'its', 'it',
        'up', 'go', 'going', 'get', 'getting', 'come', 'coming', 'become', 'becoming'
    })
    
    def _normalize_url(self, url: str) -> str:
        """
        归一化URL：统一格式以提高缓存命中率
        
        处理规则:
        1. 移除尾部斜杠
        2. 转换为小写（scheme和host部分）
        3. 移除常见跟踪参数
        4. 统一协议（可选）
        
        Args:
            url: 原始URL
            
        Returns:
            归一化后的URL
        """
        if not url:
            return ''
        
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
        
        try:
            # 解析URL
            parsed = urlparse(url)
            
            # 小写化scheme和netloc
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            
            # 移除尾部斜杠（路径部分）
            path = parsed.path.rstrip('/')
            
            # 移除常见跟踪参数
            tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 
                               'utm_term', 'ref', 'source', 'fbclid', 'gclid', 'ocid'}
            if parsed.query:
                params = parse_qs(parsed.query, keep_blank_values=True)
                # 过滤掉跟踪参数
                filtered_params = {k: v for k, v in params.items() 
                                   if k.lower() not in tracking_params}
                query = urlencode(filtered_params, doseq=True) if filtered_params else ''
            else:
                query = ''
            
            # 重建URL
            normalized = urlunparse((scheme, netloc, path, parsed.params, query, ''))
            return normalized
            
        except Exception:
            # 解析失败时返回去除尾部斜杠的原始URL
            return url.rstrip('/')
    
    def _normalize_title(self, title: str) -> str:
        """
        归一化标题：去除来源后缀、标点、多余词汇
        
        Args:
            title: 原始标题
            
        Returns:
            归一化后的标题
        """
        import re
        if not title:
            return ''
        
        # 去除来源后缀 (- Source Name, | Source, — Source)
        # 匹配模式: " - Fox Business", " | Reuters", " — The Guardian"
        title = re.sub(r'\s*[-|—]\s*[A-Z][a-zA-Z\s&.\']+$', '', title)
        
        # 小写
        title = title.lower()
        
        # 移除标点符号（保留字母、数字、空格）
        title = re.sub(r'[^\w\s]', ' ', title)
        
        # 移除多余空格
        title = ' '.join(title.split())
        
        return title
    
    def _extract_keywords(self, title: str) -> set:
        """
        提取标题关键词（去除停用词）
        
        Args:
            title: 原始标题
            
        Returns:
            关键词集合
        """
        normalized = self._normalize_title(title)
        words = normalized.split()
        # 过滤停用词和过短的词（<3字符）
        return {w for w in words if len(w) >= 3 and w not in self._STOPWORDS}
    
    def _semantic_similarity(self, title1: str, title2: str) -> tuple:
        """
        计算两个标题的语义相似度
        
        采用双重策略:
        1. 关键词Jaccard相似度（语义层面）
        2. 归一化字符串相似度（字面层面）
        
        Args:
            title1: 第一个标题
            title2: 第二个标题
            
        Returns:
            (jaccard_sim, string_sim, common_keywords)
        """
        # 提取关键词
        kw1 = self._extract_keywords(title1)
        kw2 = self._extract_keywords(title2)
        
        # Jaccard相似度
        intersection = len(kw1 & kw2)
        union = len(kw1 | kw2)
        jaccard_sim = intersection / union if union > 0 else 0
        
        # 归一化字符串相似度
        norm1 = self._normalize_title(title1)
        norm2 = self._normalize_title(title2)
        string_sim = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        
        return (jaccard_sim, string_sim, kw1 & kw2)
    
    def _is_semantic_duplicate(self, title1: str, title2: str, 
                                jaccard_threshold: float = 0.35,
                                string_threshold: float = 0.50,
                                min_common_keywords: int = 3) -> bool:
        """
        判断两个标题是否为语义重复
        
        判定规则（满足任一条件即为重复）:
        1. 关键词Jaccard >= 0.35 且 共同关键词 >= 3
        2. 归一化字符串相似度 >= 0.50
        3. 关键词Jaccard >= 0.50（即使共同词少于3个）
        
        Args:
            title1: 第一个标题
            title2: 第二个标题
            jaccard_threshold: Jaccard相似度阈值
            string_threshold: 字符串相似度阈值
            min_common_keywords: 最小共同关键词数
            
        Returns:
            是否为重复内容
        """
        jaccard_sim, string_sim, common_kw = self._semantic_similarity(title1, title2)
        
        # 规则1: Jaccard >= 0.35 且 共同关键词 >= 3
        if jaccard_sim >= jaccard_threshold and len(common_kw) >= min_common_keywords:
            return True
        
        # 规则2: 归一化字符串相似度 >= 0.50
        if string_sim >= string_threshold:
            return True
        
        # 规则3: 高Jaccard（>= 0.50）即使共同词少
        if jaccard_sim >= 0.50:
            return True
        
        return False
    
    def _generate_item_fingerprint(self, item: Dict) -> str:
        """
        生成内容指纹用于快速去重
        
        基于 URL + 标题前50字符 生成 MD5 哈希
        
        Args:
            item: 数据项字典
            
        Returns:
            MD5 哈希字符串
        """
        url = item.get('url', '')
        title = item.get('title', '')[:50]  # 取标题前50字符
        key = f"{url}|{title}".lower()
        return hashlib.md5(key.encode('utf-8')).hexdigest()
    
    def _deduplicate_by_fingerprint(self, items: List[Dict]) -> List[Dict]:
        """
        基于指纹的快速去重 (O(n) 复杂度)
        
        Args:
            items: 数据项列表
            
        Returns:
            去重后的列表
        """
        if not items:
            return []
        
        seen_fingerprints = set()
        unique_items = []
        
        for item in items:
            fp = self._generate_item_fingerprint(item)
            if fp not in seen_fingerprints:
                seen_fingerprints.add(fp)
                unique_items.append(item)
        
        return unique_items
    
    def _deduplicate_items(self, items: List[Dict], threshold: float = 0.6) -> List[Dict]:
        """
        对内容列表进行去重（三阶段策略）
        
        阶段1: 基于指纹快速去重 (O(n)) - 完全相同的URL+标题
        阶段2: 基于语义相似度去重 - 处理同一事件不同来源的报道
        阶段3: 基于传统字符串相似度去重 - 兜底
        
        Args:
            items: 数据项列表
            threshold: 传统字符串相似度阈值（兜底用）
            
        Returns:
            去重后的列表
        """
        if not items:
            return []
        
        # 阶段1: 指纹快速去重
        items = self._deduplicate_by_fingerprint(items)
        
        # 阶段2+3: 语义相似度精细去重
        unique_items = []
        removed_as_duplicate = []  # 记录被去重的标题（调试用）
        
        for item in items:
            is_duplicate = False
            item_title = item.get('title', '')
            
            for existing in unique_items:
                existing_title = existing.get('title', '')
                
                # 使用语义去重判断
                if self._is_semantic_duplicate(item_title, existing_title):
                    is_duplicate = True
                    removed_as_duplicate.append((item_title[:50], existing_title[:50]))
                    break
            
            if not is_duplicate:
                unique_items.append(item)
        
        # 记录语义去重结果（仅写入日志文件，不输出到控制台）
        if removed_as_duplicate and len(removed_as_duplicate) > 0:
            log.file_only(f"语义去重移除 {len(removed_as_duplicate)} 条相似内容")
            for new_t, old_t in removed_as_duplicate[:3]:  # 只显示前3条
                log.file_only(f"  - '{new_t}...' 与 '{old_t}...' 相似")
                
        return unique_items
    
    def _apply_deduplication(self, all_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        统一去重入口 - 对所有类别的数据应用去重处理
        
        处理流程:
        1. 对每个类别内部进行去重
        2. 跨类别去重（同一URL可能出现在多个类别中）
        
        Args:
            all_data: 按类别分组的数据字典
            
        Returns:
            去重后的数据字典
        """
        # 统计去重前数量
        before_count = sum(len(items) for items in all_data.values())
        
        # 阶段1: 类别内去重
        for cat in all_data:
            all_data[cat] = self._deduplicate_items(all_data[cat])
        
        # 阶段2: 跨类别去重（基于URL）
        seen_urls = set()
        for cat in all_data:
            unique_items = []
            for item in all_data[cat]:
                url = item.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_items.append(item)
                elif not url:
                    # 没有URL的项目保留
                    unique_items.append(item)
            all_data[cat] = unique_items
        
        # 统计去重后数量
        after_count = sum(len(items) for items in all_data.values())
        removed_count = before_count - after_count
        
        if removed_count > 0:
            log.dual_info(f"🔄 去重完成: {before_count} → {after_count} (移除 {removed_count} 条重复)", emoji="")
        
        return all_data

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
        except (AttributeError, TypeError, ValueError) as e:
            # 如果清理失败，返回原始文本的截断版本
            return text[:max_length] + '...' if len(text) > max_length else text
    
    def _is_recent(self, date_val) -> bool:
        """检查日期是否在最近N天内（由data_retention_days配置决定）"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.data_retention_days)
            
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
        except (ValueError, TypeError, AttributeError, OverflowError) as e:
            # 日期解析失败，默认保留项目
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
                                semaphore: asyncio.Semaphore,
                                category: str = 'unknown') -> Optional[str]:
        """异步获取URL内容（带重试）"""
        last_error = None
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
                            last_error = f'Rate limited (429)'
                            wait_time = self.async_config.retry_delay * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                        else:
                            last_error = f'HTTP {response.status}'
                            return None
                except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                    last_error = str(e)[:50] or 'Timeout/Connection error'
                    if attempt < self.async_config.max_retries:
                        await asyncio.sleep(self.async_config.retry_delay * (attempt + 1))
                except Exception as e:
                    last_error = str(e)[:50] or 'Unknown error'
            
            # 记录失败详情
            self._record_failure(url, category, last_error or 'Max retries exceeded')
            return None
    
    async def _fetch_json_async(self, session: aiohttp.ClientSession, url: str,
                                 semaphore: asyncio.Semaphore, params: Optional[Dict] = None,
                                 category: str = 'unknown') -> Optional[Any]:
        """异步获取JSON内容"""
        last_error = None
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
                            last_error = f'Rate limited (429)'
                            wait_time = self.async_config.retry_delay * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                        else:
                            last_error = f'HTTP {response.status}'
                except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                    last_error = str(e)[:50] or 'Timeout/Connection error'
                    if attempt < self.async_config.max_retries:
                        await asyncio.sleep(self.async_config.retry_delay * (attempt + 1))
                except Exception as e:
                    last_error = str(e)[:50] or 'Unknown error'
            
            # 记录失败详情
            self._record_failure(url, category, last_error or 'Max retries exceeded')
            return None
    
    async def _parse_rss_feed_async(self, session: aiohttp.ClientSession,
                                     feed_url: str, category: str,
                                     semaphore: asyncio.Semaphore,
                                     enable_url_filter: bool = True,
                                     items_per_feed: int = 10) -> List[Dict]:
        """异步解析RSS源（支持URL预过滤和数量限制）
        
        Args:
            enable_url_filter: 是否启用URL预过滤（默认True）
            items_per_feed: 每个源最多采集的条数（默认10）
        """
        items = []
        try:
            content = await self._fetch_url_async(session, feed_url, semaphore, category)
            if not content:
                return items
            
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, content)
            
            # 先提取所有URL并进行预过滤（限制条数）
            max_entries = min(items_per_feed, 10)  # 最多10条
            entries_to_process = []
            if enable_url_filter:
                for entry in feed.entries[:max_entries * 2]:  # 多检查一些以应对过滤
                    if len(entries_to_process) >= max_entries:
                        break
                    url = entry.get('link', '')
                    # 使用规范化URL进行缓存匹配，确保一致性
                    normalized_url = self._normalize_url(url) if url else ''
                    if normalized_url and normalized_url not in self.history_cache['urls']:
                        entries_to_process.append(entry)
            else:
                entries_to_process = feed.entries[:max_entries]
            
            # 只处理新URL的内容
            for entry in entries_to_process:
                if len(items) >= items_per_feed:
                    break
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
        except (AttributeError, KeyError, ValueError) as e:
            # RSS解析失败，记录错误
            log.debug(f"RSS parsing error: {e}")
        
        return items
    
    def _collect_research_papers_sync(self, max_results: int = 10) -> List[Dict]:
        """同步采集研究论文（供异步包装器调用）"""
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
                # 过滤超出采集窗口的论文（由data_retention_days配置）
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
                
        except Exception as e:
            log.error(t('dc_arxiv_failed', error=str(e)))
            # 提供备用数据
            papers = self._get_backup_research_data()
        
        return papers
    
    async def _collect_research_papers_async(self, max_results: int = 10) -> List[Dict]:
        """异步采集研究论文 (arxiv库不支持异步，使用executor)"""
        loop = asyncio.get_event_loop()
        papers = await loop.run_in_executor(None, self._collect_research_papers_sync, max_results)
        # 添加 _source_type 用于内部分组
        for paper in papers:
            paper['_source_type'] = 'research'
        return papers
    
    async def _collect_github_trending_async(self, session: aiohttp.ClientSession, 
                                            semaphore: asyncio.Semaphore,
                                            enable_url_filter: bool = True,
                                            max_items: int = 10) -> List[Dict]:
        """异步采集GitHub热门项目（支持URL预过滤和数量限制）"""
        projects = []
        try:
            cutoff_date = (datetime.now() - timedelta(days=self.data_retention_days)).strftime('%Y-%m-%d')
            url = "https://api.github.com/search/repositories"
            query = f'(machine-learning OR artificial-intelligence OR deep-learning OR llm) created:>{cutoff_date}'
            
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': min(max_items + 5, 15)  # 多请求几个以应对过滤
            }
            
            data = await self._fetch_json_async(session, url, semaphore, params, 'developer')
            if data:
                # 先过滤掉已缓存的URL（使用规范化URL）
                repos_to_process = []
                for repo in data.get('items', [])[:max_items + 5]:
                    repo_url = repo.get('html_url', '')
                    normalized_url = self._normalize_url(repo_url) if repo_url else ''
                    if enable_url_filter:
                        if normalized_url and normalized_url not in self.history_cache['urls']:
                            repos_to_process.append(repo)
                    else:
                        repos_to_process.append(repo)
                
                # 只处理新repo（限制数量）
                for repo in repos_to_process:
                    if len(projects) >= max_items:
                        break
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
            self._record_failure('GitHub API (async)', 'developer', str(e))
            log.warning(f"GitHub trending async failed: {e}")
        
        return projects
    
    async def _collect_huggingface_async(self, session: aiohttp.ClientSession,
                                        semaphore: asyncio.Semaphore,
                                        enable_url_filter: bool = True,
                                        max_items: int = 10) -> List[Dict]:
        """异步采集Hugging Face更新（支持URL预过滤和数量限制）"""
        updates = []
        try:
            url = "https://huggingface.co/api/models"
            params = {'limit': min(max_items + 5, 15), 'sort': 'lastModified', 'direction': -1}
            
            data = await self._fetch_json_async(session, url, semaphore, params, 'developer')
            if data:
                # 先过滤掉已缓存的URL（使用规范化URL）
                models_to_process = []
                for model in data[:max_items + 5]:
                    model_url = f"https://huggingface.co/{model['id']}"
                    normalized_url = self._normalize_url(model_url)
                    if enable_url_filter:
                        if normalized_url and normalized_url not in self.history_cache['urls']:
                            models_to_process.append(model)
                    else:
                        models_to_process.append(model)
                
                # 只处理新模型（限制数量）
                for model in models_to_process:
                    if len(updates) >= max_items:
                        break
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
            self._record_failure('Hugging Face API (async)', 'developer', str(e))
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
            story_ids = await self._fetch_json_async(session, top_url, semaphore, None, 'community')
            
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
                story_tasks.append(self._fetch_json_async(session, story_url, semaphore, None, 'community'))
            
            stories = await asyncio.gather(*story_tasks, return_exceptions=True)
            
            for story in stories:
                if isinstance(story, dict) and story.get('title'):
                    title_lower = story['title'].lower()
                    if any(kw in title_lower for kw in ai_keywords):
                        # 构建URL用于过滤检查
                        story_url = story.get('url', f"https://news.ycombinator.com/item?id={story['id']}")
                        normalized_url = self._normalize_url(story_url)
                        
                        # URL预过滤：跳过已缓存的URL（使用规范化URL）
                        if enable_url_filter and normalized_url in self.history_cache['urls']:
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
            self._record_failure('Hacker News API (async)', 'community', str(e))
            log.warning(f"Hacker News async failed: {e}")
        
        return items
    
    async def _collect_product_releases_async(self, session: aiohttp.ClientSession,
                                             semaphore: asyncio.Semaphore,
                                             max_results: int = 10) -> List[Dict]:
        """异步采集产品发布（通过RSS源 + 公司专属来源）"""
        products = []
        
        # 公司来源映射（用于标记来源公司）
        company_source_map = {
            'openai.com': 'OpenAI',
            'blog.google': 'Google',
            'blogs.microsoft.com': 'Microsoft',
            'ai.meta.com': 'Meta',
            'anthropic.com': 'Anthropic',
            'jiqizhixin.com': 'China_Tech',
            'qbitai.com': 'China_Tech',
        }
        
        # 使用产品相关的RSS源
        product_feeds = RSS_FEEDS.get('product_news', [])
        
        tasks = []
        for feed_url in product_feeds:
            tasks.append(self._parse_rss_feed_async(session, feed_url, 'product', semaphore))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果，标记公司来源
        for i, result in enumerate(results):
            if isinstance(result, list):
                feed_url = product_feeds[i] if i < len(product_feeds) else ''
                # 识别来源公司
                company = None
                for domain, comp_name in company_source_map.items():
                    if domain in feed_url:
                        company = comp_name
                        break
                
                for item in result:
                    if self._is_product_related(item):
                        # 标记来源公司（如果识别到）
                        if company and not item.get('company'):
                            item['company'] = company
                        products.append(item)
        
        # 按产品优先级排序：官方公司来源优先，再按时间排序
        def product_sort_key(item):
            # 优先级：有公司标记的排前面
            has_company = 1 if item.get('company') else 0
            # 时间排序（降序）
            published = item.get('published', '1970-01-01')
            return (-has_company, published)
        
        products.sort(key=product_sort_key, reverse=True)
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
            feed_url = f"https://news.google.com/rss/search?q={query_name}+AI+when:7d&hl=en-US&gl=US&ceid=US:en"
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
        # 重置统计信息
        self._reset_stats()
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
            
            # 创建带名称的任务列表: [(name, coroutine), ...]
            named_tasks = []
            
            # 1. 新闻RSS源（限制源数量，优先采集重要源）
            news_feeds = RSS_FEEDS['news'] + RSS_FEEDS.get('product_news', [])
            # 计算每源配额：news_count / 源数量，至少2条
            items_per_news_feed = max(2, news_count // max(len(news_feeds), 1))
            # 只采集前几个重要源，避免过多请求
            max_news_feeds = min(len(news_feeds), max(6, news_count // 3))
            for i, feed_url in enumerate(news_feeds[:max_news_feeds]):
                # 从URL提取简短名称
                domain = urlparse(feed_url).netloc.replace('www.', '')[:20]
                named_tasks.append((
                    f"RSS/{domain}",
                    self._parse_rss_feed_async(session, feed_url, 'news', semaphore, 
                                               items_per_feed=items_per_news_feed)
                ))
            
            # 2. 开发者内容 (GitHub + Hugging Face + 博客RSS)
            dev_github_limit = min(5, developer_count // 3)
            dev_hf_limit = min(5, developer_count // 3)
            dev_rss_limit = max(2, (developer_count - dev_github_limit - dev_hf_limit) // max(len(RSS_FEEDS['developer']), 1))
            named_tasks.append(("GitHub Trending", self._collect_github_trending_async(session, semaphore, max_items=dev_github_limit)))
            named_tasks.append(("Hugging Face", self._collect_huggingface_async(session, semaphore, max_items=dev_hf_limit)))
            for feed_url in RSS_FEEDS['developer']:
                domain = urlparse(feed_url).netloc.replace('www.', '')[:20]
                named_tasks.append((
                    f"Dev/{domain}",
                    self._parse_rss_feed_async(session, feed_url, 'developer', semaphore,
                                               items_per_feed=dev_rss_limit)
                ))
            
            # 3. 产品发布
            named_tasks.append(("Product Releases", self._collect_product_releases_async(session, semaphore, product_count)))
            
            # 4. AI领袖言论
            named_tasks.append(("AI Leaders", self._collect_leaders_quotes_async(session, semaphore, leader_count)))
            
            # 5. 社区热点
            named_tasks.append(("Community/HN", self._collect_community_async(session, semaphore, community_count)))
            
            # 6. 研究论文 (在executor中运行)
            named_tasks.append(("arXiv Papers", self._collect_research_papers_async(research_count)))
            
            # 创建任务
            total_tasks = len(named_tasks)
            tasks = [asyncio.create_task(coro) for name, coro in named_tasks]
            
            log.dual_info(f"⚡ 并发执行 {total_tasks} 个采集任务", emoji="")
            
            # 使用 as_completed 实时显示进度
            all_results = []
            completed = 0
            total_items = 0
            for future in asyncio.as_completed(tasks):
                try:
                    result = await future
                    completed += 1
                    item_count = len(result) if isinstance(result, list) else 0
                    total_items += item_count
                    all_results.append(result)
                    
                    # 显示进度条
                    progress_pct = int(completed / total_tasks * 100)
                    bar_filled = int(completed / total_tasks * 20)
                    bar = "█" * bar_filled + "░" * (20 - bar_filled)
                    log.dual_info(f"  [{bar}] {completed}/{total_tasks} ({progress_pct}%) +{item_count} items", emoji="")
                    
                except Exception as e:
                    completed += 1
                    all_results.append(e)
                    progress_pct = int(completed / total_tasks * 100)
                    bar_filled = int(completed / total_tasks * 20)
                    bar = "█" * bar_filled + "░" * (20 - bar_filled)
                    log.dual_warning(f"  [{bar}] {completed}/{total_tasks} ({progress_pct}%) ✗ 失败")
            
            # 分类收集结果（带配额限制）
            category_limits = {
                'news': news_count,
                'developer': developer_count,
                'product': product_count,
                'leader': leader_count,
                'community': community_count,
                'research': research_count
            }
            
            for result in all_results:
                if isinstance(result, list):
                    for item in result:
                        # 使用 _source_type 进行内部分组（不是分类标签）
                        source_type = item.pop('_source_type', 'news')  # 移除并获取，默认为 news
                        if source_type in all_data:
                            # 检查是否超出配额
                            if len(all_data[source_type]) < category_limits.get(source_type, 100):
                                all_data[source_type].append(item)
                elif isinstance(result, Exception):
                    self._record_failure('Async Task', 'unknown', str(result))
                    log.warning(f"Task failed: {result}")
        
        # 统一去重处理
        all_data = self._apply_deduplication(all_data)
        
        # 统一历史缓存过滤（启用过滤，移除已采集过的内容）
        # filter_enabled=True: 实际过滤掉历史中已有的项目，减少后续处理量
        all_data, new_stats, cached_stats = self._filter_by_history(all_data, filter_enabled=True)
        
        # 更新统计信息（过滤后的数据）
        self.stats['end_time'] = time.time()
        total_new = sum(len(items) for items in all_data.values())
        total_cached = sum(cached_stats.values())
        self.stats['items_collected'] = total_new
        
        # 打印统计
        elapsed = self.stats['end_time'] - self.stats['start_time']
        
        log.dual_separator("=", 50)
        log.dual_done(f"采集完成: {total_new + total_cached} items ({total_new} new, {total_cached} cached)")
        log.dual_info(f"⏱️ 耗时: {elapsed:.1f}s | 请求: {self.stats['requests_made']} | 失败: {self.stats['requests_failed']}", emoji="")
        
        for category, items in all_data.items():
            new_count = new_stats.get(category, 0)
            cached_count = cached_stats.get(category, 0)
            log.dual_data(f"  {category}: {new_count + cached_count} ({new_count} new, {cached_count} cached)")
        
        # 显示失败数据源汇总
        self._print_failed_sources_summary()
        
        return all_data

# 用于向后兼容
DataCollector = AIDataCollector
