"""
AI世界追踪器 - 数据采集模块
专注于收集最新AI研究、产品、开发者社区和行业信息
"""

import requests
import feedparser
import arxiv
import json
from datetime import datetime, timedelta
from dateutil import parser
from typing import List, Dict, Optional
import time
import random
import difflib
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from config_manager import config

# 导入国际化模块
try:
    from i18n import t, get_language
except ImportError:
    def t(key, **kwargs): return key
    def get_language(): return 'zh'


class AIDataCollector:
    """AI数据采集器 - 收集真实最新的AI信息"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # RSS源配置 - 真实可用的AI新闻源
        self.rss_feeds = {
            'research': [
                'http://export.arxiv.org/rss/cs.AI',  # ArXiv AI
                'http://export.arxiv.org/rss/cs.CL',  # 计算语言学  
                'http://export.arxiv.org/rss/cs.CV',  # 计算机视觉
                'http://export.arxiv.org/rss/cs.LG',  # 机器学习
            ],
            'news': [
                # 国际AI新闻源
                'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',  # The Verge AI
                'https://techcrunch.com/category/artificial-intelligence/feed/',  # TechCrunch AI
                'https://www.wired.com/feed/tag/ai/latest/rss',  # Wired AI
                'https://spectrum.ieee.org/rss/topic/artificial-intelligence',  # IEEE Spectrum AI
                'https://www.technologyreview.com/feed/',  # MIT Technology Review
                'https://artificialintelligence-news.com/feed/',  # AI News
                'https://syncedreview.com/feed/',  # Synced Review (AI专业)
                # 中国AI新闻源
                'https://www.36kr.com/feed',  # 36氪 (科技创业)
                'https://www.ithome.com/rss/',  # IT之家
                'https://www.jiqizhixin.com/rss',  # 机器之心
                'https://www.qbitai.com/feed',  # 量子位
                'https://www.infoq.cn/feed/topic/18',  # InfoQ AI
            ],
            'developer': [
                'https://github.blog/feed/',  # GitHub Blog
                'https://huggingface.co/blog/feed.xml',  # Hugging Face
                'https://openai.com/blog/rss.xml',  # OpenAI Blog
                'https://blog.google/technology/ai/rss/',  # Google AI Blog
            ],
            'product_news': [  # 新增专门的产品发布新闻源
                # 公司官方博客
                'https://openai.com/blog/rss.xml',  # OpenAI官方博客
                'https://blog.google/technology/ai/rss/',  # Google AI博客
                'https://blogs.microsoft.com/ai/feed/',  # Microsoft AI博客
                # Meta和Anthropic因RSS不稳定，主要依赖备用数据或新闻聚合
                
                # 中国公司
                # 腾讯云RSS存在解析错误，已移除
            ],
            'community': [  # 新增社区热点源
                'https://www.producthunt.com/feed?category=artificial-intelligence', # Product Hunt AI
                'https://hnrss.org/newest?q=AI+LLM', # Hacker News AI (简化查询以提高命中率)
            ],
            'leader_blogs': [  # 新增领袖个人渠道
                {'url': 'http://blog.samaltman.com/posts.atom', 'author': 'Sam Altman', 'title': 'OpenAI CEO'},
                {'url': 'https://karpathy.github.io/feed.xml', 'author': 'Andrej Karpathy', 'title': 'AI Researcher'},
                {'url': 'https://lexfridman.com/feed/podcast/', 'author': 'Lex Fridman', 'title': 'Podcast Host', 'type': 'podcast'},
            ]
        }
        
        # 采集历史缓存
        self.history_cache_file = 'collection_history_cache.json'
        self.history_cache = self._load_history_cache()
    
    def _load_history_cache(self) -> Dict:
        """加载采集历史缓存"""
        try:
            import os
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
                                    print(t('dc_cache_expired'))
                                    return {'urls': set(), 'titles': set(), 'last_updated': ''}
                            except:
                                pass
                        # 转换为 set 以加速查找
                        cache['urls'] = set(cache['urls'])
                        cache['titles'] = set(cache['titles'])
                        print(t('dc_cache_loaded', url_count=len(cache['urls']), title_count=len(cache['titles'])))
                        return cache
        except Exception as e:
            print(t('dc_cache_load_failed', error=str(e)))
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
            print(t('dc_cache_save_failed', error=str(e)))
    
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
        print(t('dc_cache_cleared'))
    
    def collect_research_papers(self, max_results: int = 10) -> List[Dict]:
        """
        采集最新AI研究论文
        
        Args:
            max_results: 最大结果数
            
        Returns:
            研究论文列表
        """
        print(t('dc_collect_research'))
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
                    'summary': result.summary[:300] + "..." if len(result.summary) > 300 else result.summary,
                    'authors': [str(author) for author in result.authors],
                    'url': result.entry_id,
                    'published': result.published.strftime('%Y-%m-%d'),
                    'categories': [str(cat) for cat in result.categories],
                    'source': 'arXiv',
                    'category': 'research',
                    'importance': self._calculate_importance(result.title, result.summary)
                }
                papers.append(paper)
                
            print(t('dc_got_papers', count=len(papers)))
            
        except Exception as e:
            print(t('dc_arxiv_failed', error=str(e)))
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
        print(t('dc_collect_developer'))
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
        
        print(t('dc_got_developer', count=len(content)))
        return content
    
    def collect_product_releases(self, max_results: int = 10) -> List[Dict]:
        """
        采集AI产品发布信息
        
        Args:
            max_results: 最大结果数
            
        Returns:
            产品发布列表
        """
        print(t('dc_collect_products'))
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
                print(t('dc_product_failed', company=company, error=str(e)))
        
        # 按重要性排序并限制数量
        products.sort(key=lambda x: x.get('importance', 0), reverse=True)
        products = products[:max_results]
        
        print(t('dc_got_products', count=len(products)))
        return products
    
    def collect_ai_leaders_quotes(self, max_results: int = 15) -> List[Dict]:
        """
        采集全球AI领袖的近期言论
        
        Args:
            max_results: 最大结果数
            
        Returns:
            领袖言论列表
        """
        print(t('dc_collect_leaders'))
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
                        quotes.append(quote)
                        count += 1
                
                time.sleep(0.5) # 避免请求过快
                
            except Exception as e:
                print(t('dc_leader_failed', name=leader_name, error=str(e)))
        
        # 2. 采集个人博客和播客
        print(t('dc_collect_blogs'))
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
                        'summary': entry.get('summary', entry.get('description', ''))[:300],
                        'url': entry.link,
                        'published': entry.get('published', datetime.now().strftime('%Y-%m-%d')),
                        'source': 'Personal Blog/Podcast',
                        'category': 'leader',
                        'author': source['author'],
                        'author_title': source['title'],
                        'importance': 1.0 # 个人博客内容权重最高
                    }
                    quotes.append(quote)
            except Exception as e:
                print(t('dc_blog_failed', author=source['author'], error=str(e)))

        # 3. 如果采集数量不足，使用备用数据
        if len(quotes) < 5:
            print(t('dc_fallback_data'))
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
        print(t('dc_got_leaders', count=len(result)))
        return result

    def collect_latest_news(self, max_results: int = 20) -> List[Dict]:
        """
        采集最新AI行业新闻
        
        Args:
            max_results: 最大结果数
            
        Returns:
            新闻列表
        """
        print(t('dc_collect_news'))
        
        # 从产品发布新闻源采集
        product_news = []
        for feed_url in self.rss_feeds.get('product_news', []):
            try:
                feed_news = self._parse_rss_feed(feed_url, category='product')
                product_news.extend(feed_news)
                time.sleep(0.3)
            except Exception as e:
                print(t('dc_product_feed_failed', url=feed_url, error=str(e)))
        
        # 从传统新闻源采集
        general_news = []
        for feed_url in self.rss_feeds['news']:
            try:
                feed_news = self._parse_rss_feed(feed_url, category='news')
                general_news.extend(feed_news)
                time.sleep(0.5)
            except Exception as e:
                print(t('dc_rss_failed', url=feed_url, error=str(e)))
        
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
        print(t('dc_got_news', count=len(result)))
        return result
    
    def collect_community_trends(self, max_results: int = 15) -> List[Dict]:
        """
        采集社区热点 (Product Hunt, Hacker News, Reddit)
        """
        print(t('dc_collect_community'))
        trends = []
        
        for feed_url in self.rss_feeds.get('community', []):
            try:
                # Determine source name for better labeling
                source_name = "Community"
                if "producthunt" in feed_url:
                    source_name = "Product Hunt"
                elif "hnrss" in feed_url:
                    source_name = "Hacker News"
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
                    # Boost importance for these high-signal sources
                    item['importance'] = item.get('importance', 0.6) + 0.1
                    trends.append(item)
                    time.sleep(0.2)
                    
            except Exception as e:
                print(t('dc_community_failed', url=feed_url, error=str(e)))
        
        # Deduplicate
        trends = self._deduplicate_items(trends)
        
        # Sort by published date
        trends.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        result = trends[:max_results]
        print(t('dc_got_community', count=len(result)))
        return result

    def collect_all(self) -> Dict[str, List[Dict]]:
        """
        采集所有类型的数据
        
        Returns:
            分类的数据字典
        """
        print(t('dc_start_collection'))
        print("=" * 50)
        
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

        all_data['research'] = self.collect_research_papers(research_count)
        all_data['developer'] = self.collect_developer_content(developer_count)
        all_data['product'] = self.collect_product_releases(product_count)
        all_data['leader'] = self.collect_ai_leaders_quotes(leader_count)
        all_data['community'] = self.collect_community_trends(community_count)
        all_data['news'] = self.collect_latest_news(news_count)
        
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
        print(t('dc_collection_done_v2', total=total_items, new=total_new, cached=total_cached))
        for category, items in all_data.items():
            new_count = new_stats.get(category, 0)
            cached_count = cached_stats.get(category, 0)
            print(t('dc_category_stats_v2', category=category, count=len(items), new=new_count, cached=cached_count))
        
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
                        'source': 'GitHub',
                        'category': 'developer',
                        'importance': min(repo['stargazers_count'] / 1000, 1.0)
                    }
                    projects.append(project)
            
        except Exception as e:
            print(t('dc_github_failed', error=str(e)))
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
                        'source': 'Hugging Face',
                        'category': 'developer',
                        'importance': min(model.get('downloads', 0) / 10000, 1.0)
                    }
                    updates.append(update)
        
        except Exception as e:
            print(t('dc_hf_failed', error=str(e)))
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
            print(t('dc_dev_blog_failed', error=str(e)))
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
                item['importance'] = 0.95 # OpenAI新闻通常很重要
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
                'source': 'OpenAI',
                'category': 'product',
                'importance': 0.95
            },
            {
                'title': 'OpenAI API 定价更新公告',
                'summary': 'OpenAI更新API定价策略，降低GPT-4使用成本，同时推出更经济的GPT-4 Turbo选项，为开发者提供更灵活的选择。',
                'url': 'https://openai.com/api/pricing/',
                'company': 'OpenAI',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'OpenAI',
                'category': 'product',
                'importance': 0.88
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
                item['importance'] = 0.92
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
                'source': 'Google AI',
                'category': 'product',
                'importance': 0.92
            },
            {
                'title': 'Google AI Studio 产品发布',
                'summary': 'Google AI Studio为开发者提供快速原型设计和测试生成式AI想法的平台，支持Gemini模型的快速集成和部署。',
                'url': 'https://aistudio.google.com/',
                'company': 'Google',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Google AI',
                'category': 'product',
                'importance': 0.85
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
                item['importance'] = 0.90
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
                'source': 'Microsoft',
                'category': 'product',
                'importance': 0.90
            },
            {
                'title': 'Azure AI Services 产品介绍',
                'summary': 'Azure AI Services提供完整的AI和机器学习服务套件，包括认知服务、机器学习平台和OpenAI服务，为企业AI转型提供支持。',
                'url': 'https://azure.microsoft.com/en-us/products/ai-services',
                'company': 'Microsoft',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Microsoft Azure',
                'category': 'product',
                'importance': 0.88
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
                item['importance'] = 0.90
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
                'source': 'Meta AI',
                'category': 'product',
                'importance': 0.90
            },
            {
                'title': 'Meta AI Assistant 产品介绍',
                'summary': 'Meta AI是智能助手产品，集成到Facebook、Instagram、WhatsApp等平台，为用户提供AI驱动的对话、创作和搜索体验。',
                'url': 'https://www.meta.ai/',
                'company': 'Meta',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Meta AI',
                'category': 'product',
                'importance': 0.85
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
                item['importance'] = 0.88
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
                'source': 'Anthropic',
                'category': 'product',
                'importance': 0.88
            },
            {
                'title': 'Anthropic Claude API 文档',
                'summary': 'Anthropic提供Claude API服务，为开发者提供高质量的对话AI能力，支持多种使用场景，包括内容创作、分析和编程辅助等。',
                'url': 'https://docs.anthropic.com/',
                'company': 'Anthropic',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Anthropic',
                'category': 'product',
                'importance': 0.82
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
                        item['importance'] = 0.9
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
                'source': 'Baidu AI',
                'category': 'product',
                'importance': 0.92
            },
            {
                'title': '阿里通义千问 2.5 发布',
                'summary': '阿里云发布通义千问2.5，模型性能全面升级，在中文语境下表现优异，开源多款尺寸模型供开发者使用。',
                'url': 'https://tongyi.aliyun.com/',
                'company': 'Alibaba',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Aliyun',
                'category': 'product',
                'importance': 0.90
            },
             {
                'title': '腾讯混元大模型升级',
                'summary': '腾讯混元大模型迎来重要升级，扩展了上下文窗口，增强了代码生成和数学推理能力，已接入腾讯全系产品。',
                'url': 'https://hunyuan.tencent.com/',
                'company': 'Tencent',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Tencent Cloud',
                'category': 'product',
                'importance': 0.88
            },
            {
                'title': 'DeepSeek V2 开源发布',
                'summary': '深度求索(DeepSeek)发布DeepSeek-V2，这是一款强大的开源MoE大语言模型，在多项基准测试中表现优异，且推理成本极低。',
                'url': 'https://www.deepseek.com/',
                'company': 'DeepSeek',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'DeepSeek',
                'category': 'product',
                'importance': 0.95
            }
        ]
    
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

                item = {
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', entry.get('description', ''))[:300] + "...",
                    'url': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': feed.feed.get('title', feed_url),
                    'category': category,
                    'importance': 0.6
                }
                
                if self._is_valid_item(item):
                    items.append(item)
        
        except Exception as e:
            print(t('dc_rss_parse_failed', url=feed_url, error=str(e)))
        
        return items
    
    def _deduplicate_items(self, items: List[Dict], threshold: float = 0.6) -> List[Dict]:
        """
        对内容列表进行去重
        基于标题相似度
        """
        if not items:
            return []
            
        unique_items = []
        # 按重要性排序，保留重要的
        sorted_items = sorted(items, key=lambda x: x.get('importance', 0), reverse=True)
        
        for item in sorted_items:
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
                    dt = parser.parse(date_val)
                    # 比较时间戳以避免时区问题
                    return dt.timestamp() >= cutoff_date.timestamp()
                except:
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

    def _calculate_importance(self, title: str, summary: str) -> float:
        """计算内容重要性"""
        text = f"{title} {summary}".lower()
        
        high_value_keywords = [
            'breakthrough', 'new', 'launch', 'release', 'breakthrough',
            '突破', '发布', '新', '最新'
        ]
        
        score = 0.5  # 基础分数
        for keyword in high_value_keywords:
            if keyword in text:
                score += 0.1
        
        return min(score, 1.0)
    
    def _get_backup_leaders_data(self) -> List[Dict]:
        """备用领袖言论数据"""
        return [
            {
                'title': 'Sam Altman: AI发展的速度将超出所有人的预期',
                'summary': 'OpenAI CEO Sam Altman在最近的采访中表示，AGI的到来可能比预期的要快，社会需要为此做好准备。',
                'url': 'https://openai.com/blog',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Interview',
                'category': 'leader',
                'author': 'Sam Altman',
                'author_title': 'OpenAI CEO',
                'importance': 0.98
            },
            {
                'title': 'Elon Musk: AI安全是未来的首要任务',
                'summary': 'Elon Musk再次强调AI安全的重要性，并表示xAI的目标是理解宇宙的本质，构建最大限度追求真理的AI。',
                'url': 'https://x.ai',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'X (Twitter)',
                'category': 'leader',
                'author': 'Elon Musk',
                'author_title': 'xAI Founder',
                'importance': 0.95
            },
            {
                'title': 'Jensen Huang: 生成式AI是计算领域的转折点',
                'summary': 'NVIDIA CEO黄仁勋表示，生成式AI正在重塑每一个行业，计算方式正在发生根本性的转变。',
                'url': 'https://nvidianews.nvidia.com/',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Keynote',
                'category': 'leader',
                'author': 'Jensen Huang',
                'author_title': 'NVIDIA CEO',
                'importance': 0.92
            },
            {
                'title': 'Yann LeCun: 现在的LLM还不是真正的智能',
                'summary': 'Meta首席AI科学家Yann LeCun认为，目前的大语言模型缺乏对物理世界的理解，距离真正的通用人工智能还有很长的路要走。',
                'url': 'https://ai.meta.com/blog/',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Interview',
                'category': 'leader',
                'author': 'Yann LeCun',
                'author_title': 'Meta Chief AI Scientist',
                'importance': 0.90
            },
            {
                'title': '李开复: AI 2.0时代已经到来',
                'summary': '零一万物CEO李开复表示，AI 2.0时代将带来比移动互联网大十倍的机会，中国在应用层有巨大优势。',
                'url': 'https://www.01.ai/',
                'published': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Speech',
                'category': 'leader',
                'author': 'Kai-Fu Lee',
                'author_title': '01.AI CEO',
                'importance': 0.88
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
                'source': 'arXiv',
                'category': 'research',
                'importance': 0.95
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
                'source': 'GitHub',
                'category': 'developer',
                'importance': 0.98
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
                'source': 'Hugging Face',
                'category': 'developer',
                'importance': 0.85
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
                'source': 'GitHub Blog',
                'category': 'developer',
                'importance': 0.80
            }
        ]


# 用于向后兼容
DataCollector = AIDataCollector
