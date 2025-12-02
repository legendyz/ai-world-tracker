"""
内容分类系统 - Content Classifier
基于关键词和规则对AI内容进行多维度分类
"""

from typing import Dict, List, Set
import re
from datetime import datetime


class ContentClassifier:
    """AI内容智能分类器"""
    
    def __init__(self):
        # 研究类关键词
        self.research_keywords = {
            'paper', 'research', 'study', 'arxiv', 'conference', 'journal',
            'algorithm', 'model', 'neural network', 'deep learning', 'machine learning',
            '论文', '研究', '算法', '模型', '神经网络', '学习'
        }
        
        # 开发者类关键词
        self.developer_keywords = {
            'github', 'code', 'library', 'framework', 'sdk', 'api', 'open source',
            'repository', 'commit', 'pull request', 'developer', 'programming',
            'implementation', 'tutorial', 'documentation', 'guide',
            '开发', '代码', '库', '框架', '开源', '仓库', '教程', '文档', '指南'
        }
        
        # 产品类关键词（专注于公司正式发布的AI产品）
        self.product_keywords = {
            'release', 'launch', 'announce', 'unveil', 'debut', 'introduce',
            'official', 'commercial', 'enterprise', 'product', 'version', 'update',
            'platform', 'service', 'solution', 'system', 'assistant', 'api',
            'available', 'beta', 'preview', 'early access', 'public',
            '发布', '推出', '宣布', '官方', '商业', '企业', '产品', '版本', '平台', 
            '服务', '解决方案', '助手', '上线', '正式', '公测'
        }
        
        # 市场类关键词
        self.market_keywords = {
            'funding', 'investment', 'market', 'business', 'startup', 'company',
            'acquisition', 'ipo', 'valuation', 'revenue', 'policy', 'regulation',
            '融资', '投资', '市场', '企业', '公司', '政策', '监管', '行业'
        }
        
        # 领袖言论关键词
        self.leader_keywords = {
            'said', 'stated', 'believes', 'warns', 'predicts', 'interview', 'speech',
            'tweeted', 'posted', 'commented', 'opinion', 'quote',
            '说', '表示', '认为', '警告', '预测', '采访', '演讲', '发文', '评论', '观点'
        }
        
        # 技术领域关键词
        self.tech_categories = {
            'NLP': [
                'nlp', 'natural language', 'text mining', 'embedding', 'bert', 'transformer', 
                'sentiment analysis', 'translation', 'linguistics', 'tokenization',
                '自然语言', '文本挖掘', '语义', '翻译', '词向量'
            ],
            'Computer Vision': [
                'vision', 'image', 'video', 'detection', 'recognition', 'segmentation', 'ocr',
                'yolo', 'resnet', 'vit', '视觉', '图像', '视频', '识别', '检测'
            ],
            'Reinforcement Learning': [
                'reinforcement', 'rl', 'agent', 'policy', 'reward', 'q-learning', 'ppo',
                '强化学习', '智能体', '奖励'
            ],
            'Generative AI': [
                'generative', 'generation', 'aigc', 'llm', 'large language model', 'foundation model',
                'gpt', 'chatgpt', 'claude', 'llama', 'mistral', 'gemini', 'copilot', 'grok',
                'sora', 'midjourney', 'dalle', 'stable diffusion', 'runway', 'pika', 'flux',
                'text-to-image', 'text-to-video', '生成式', '大模型', '语言模型', '文生图', '文生视频'
            ],
            'MLOps': ['mlops', 'deployment', 'production', 'monitoring', 'pipeline', '部署', '运维'],
            'AI Ethics': ['ethics', 'bias', 'fairness', 'privacy', 'safety', 'alignment', '伦理', '偏见', '隐私', '安全', '对齐']
        }
        
        # 区域关键词
        self.region_keywords = {
            'China': ['china', 'chinese', 'beijing', 'shanghai', 'baidu', 'alibaba', 'tencent', '中国', '百度', '阿里', '腾讯'],
            'USA': ['usa', 'us', 'silicon valley', 'openai', 'google', 'microsoft', 'meta', '美国'],
            'Europe': ['europe', 'eu', 'european', 'mistral', 'deepmind', '欧洲'],
            'Global': ['global', 'international', 'worldwide', '全球', '国际']
        }
    
    def classify_content_type(self, item: Dict) -> str:
        """
        分类内容类型：研究/开发者/产品/市场/领袖/社区
        
        Args:
            item: 内容项（包含title, summary等字段）
            
        Returns:
            分类结果
        """
        # 如果采集时已经指定了类型，直接使用
        if item.get('category') in ['research', 'developer', 'product', 'market', 'leader', 'community']:
            return item.get('category')

        text = f"{item.get('title', '')} {item.get('summary', '')} {item.get('description', '')}".lower()
        source = item.get('source', '').lower()
        
        # 绝对优先规则：GitHub来源必须归类为开发者
        if 'github' in source or 'github' in text:
            return 'developer'
        
        # arXiv来源必须归类为研究
        if 'arxiv' in source:
            return 'research'
        
        # 产品类严格规则：必须同时包含公司名称和产品发布关键词
        company_indicators = ['google', 'microsoft', 'openai', 'anthropic', 'meta', 'apple', 'amazon', 
                             'baidu', 'alibaba', 'tencent', 'bytedance', 'huawei', 'xiaomi',
                             '百度', '阿里', '腾讯', '字节', '华为', '小米',
                             'deepseek', 'mistral', 'cohere', 'stability', 'midjourney', 'runway',
                             '智谱', '月之暗面', '零一万物', '百川', '科大讯飞']
        
        has_company = any(company in text or company in source for company in company_indicators)
        product_score = self._calculate_keyword_score(text, self.product_keywords)
        
        # 优化规则：
        # 1. 如果有明确的公司名 + 发布词，权重极大提升
        # 2. 如果没有公司名，但有强烈的发布词（如 launch, release），也保留分数
        if has_company and product_score > 0:
            product_score *= 3.0
        elif product_score > 0:
            product_score *= 1.5 # 即使没有匹配到大公司，只要有发布动作，也给予一定权重
        
        scores = {
            'research': self._calculate_keyword_score(text, self.research_keywords),
            'developer': self._calculate_keyword_score(text, self.developer_keywords),
            'product': product_score,
            'market': self._calculate_keyword_score(text, self.market_keywords),
            'leader': self._calculate_keyword_score(text, self.leader_keywords)
        }
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def classify_tech_category(self, item: Dict) -> List[str]:
        """
        分类技术领域（可多标签）
        
        Args:
            item: 内容项
            
        Returns:
            技术领域列表
        """
        text = f"{item.get('title', '')} {item.get('summary', '')} {item.get('description', '')}".lower()
        categories = []
        
        for category, keywords in self.tech_categories.items():
            score = self._calculate_keyword_score(text, keywords)
            if score > 0:
                categories.append(category)
        
        return categories if categories else ['General AI']
    
    def classify_region(self, item: Dict) -> str:
        """
        分类地区
        
        Args:
            item: 内容项
            
        Returns:
            地区分类
        """
        # 如果已有region字段
        if 'region' in item and item['region']:
            return item['region']
        
        text = f"{item.get('title', '')} {item.get('summary', '')} {item.get('description', '')} {item.get('source', '')}".lower()
        
        scores = {}
        for region, keywords in self.region_keywords.items():
            scores[region] = self._calculate_keyword_score(text, keywords)
        
        max_region = max(scores.items(), key=lambda x: x[1])[0]
        return max_region if scores[max_region] > 0 else 'Global'
    
    def classify_item(self, item: Dict) -> Dict:
        """
        对单个内容项进行完整分类
        
        Args:
            item: 原始内容项
            
        Returns:
            添加了分类信息的内容项
        """
        classified = item.copy()
        
        classified['content_type'] = self.classify_content_type(item)
        classified['tech_categories'] = self.classify_tech_category(item)
        classified['region'] = self.classify_region(item)
        classified['classified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return classified
    
    def classify_batch(self, items: List[Dict]) -> List[Dict]:
        """
        批量分类
        
        Args:
            items: 内容项列表
            
        Returns:
            分类后的内容项列表
        """
        print(f"正在对 {len(items)} 条内容进行分类...")
        
        classified_items = []
        for item in items:
            classified_items.append(self.classify_item(item))
        
        # 统计
        stats = self._calculate_statistics(classified_items)
        print(f"分类完成！")
        print(f"   - 研究: {stats['research']} | 开发者: {stats['developer']} | 产品: {stats['product']} | 市场: {stats['market']} | 领袖: {stats['leader']}")
        
        return classified_items
    
    def _calculate_keyword_score(self, text: str, keywords: Set[str]) -> int:
        """计算关键词匹配分数"""
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        return score
    
    def _calculate_statistics(self, items: List[Dict]) -> Dict:
        """计算分类统计"""
        stats = {'research': 0, 'developer': 0, 'product': 0, 'market': 0, 'leader': 0}
        
        for item in items:
            content_type = item.get('content_type', 'market')
            if content_type in stats:
                stats[content_type] += 1
        
        return stats
    
    def get_filtered_items(self, items: List[Dict], 
                          content_type: str = None,
                          tech_category: str = None,
                          region: str = None) -> List[Dict]:
        """
        根据条件过滤内容
        
        Args:
            items: 分类后的内容列表
            content_type: 内容类型过滤
            tech_category: 技术领域过滤
            region: 地区过滤
            
        Returns:
            过滤后的内容列表
        """
        filtered = items
        
        if content_type:
            filtered = [item for item in filtered if item.get('content_type') == content_type]
        
        if tech_category:
            filtered = [item for item in filtered if tech_category in item.get('tech_categories', [])]
        
        if region:
            filtered = [item for item in filtered if item.get('region') == region]
        
        return filtered


if __name__ == "__main__":
    # 测试示例
    classifier = ContentClassifier()
    
    test_items = [
        {
            'title': 'GPT-5 Released by OpenAI',
            'summary': 'OpenAI announces the release of GPT-5 with improved capabilities',
            'source': 'TechNews'
        },
        {
            'title': 'New Research on Transformer Architecture',
            'summary': 'A breakthrough paper on attention mechanisms in neural networks',
            'source': 'arXiv'
        },
        {
            'title': '百度获得10亿美元AI投资',
            'summary': '中国科技巨头百度宣布完成新一轮融资，用于AI研发',
            'source': '中国科技'
        }
    ]
    
    results = classifier.classify_batch(test_items)
    
    print("\n📋 分类结果:")
    for item in results:
        print(f"\n  标题: {item['title']}")
        print(f"  类型: {item['content_type']}")
        print(f"  领域: {', '.join(item['tech_categories'])}")
        print(f"  地区: {item['region']}")
