"""
内容分类系统 - Content Classifier
基于关键词和规则对AI内容进行多维度分类
"""

from typing import Dict, List, Set, Tuple, Optional
import re
from datetime import datetime
import math
from collections import Counter


class ContentClassifier:
    """AI内容智能分类器 - 增强版"""
    
    def __init__(self):
        # 否定词和不确定性词汇（扩展版）
        self.negative_words = {
            # 强否定
            'not', 'no', 'never', 'fake', 'false', 'denied', 'debunk', 'refute',
            '不是', '非', '否认', '虚假', '辟谣',
            
            # 传闻/猜测
            'rumor', 'speculation', 'allegedly', 'unconfirmed', 'unverified',
            'might', 'could', 'possibly', 'potentially', 'reportedly',
            '传闻', '谣言', '未经证实', '据称', '可能', '或许', '猜测',
            
            # 延期/取消
            'delayed', 'postponed', 'cancelled', 'canceled', 'suspended',
            '延期', '推迟', '取消', '暂停'
        }
        
        # 高可信度来源（用于提升置信度）
        self.trusted_sources = {
            'official', 'blog', 'press release', 'announcement', 'techcrunch',
            'reuters', 'bloomberg', 'the verge', 'wired',
            '官方', '官网', '新闻稿', '公告'
        }
        
        # 研究类关键词（带权重）
        self.research_keywords = {
            # 高权重（3分）- 强研究指标
            'arxiv': 3, 'conference': 3, 'journal': 3, 'paper': 3, 'publication': 3,
            'peer-reviewed': 3, 'proceedings': 3, 'academic': 3,
            '论文': 3, '学术': 3, '期刊': 3, '会议': 3,
            
            # 中权重（2分）- 研究相关
            'research': 2, 'study': 2, 'experiment': 2, 'methodology': 2,
            'findings': 2, 'analysis': 2, 'survey': 2,
            '研究': 2, '实验': 2, '分析': 2,
            
            # 低权重（1分）- 技术术语
            'algorithm': 1, 'model': 1, 'neural network': 1, 'deep learning': 1, 
            'machine learning': 1, 'architecture': 1,
            '算法': 1, '模型': 1, '神经网络': 1, '学习': 1
        }
        
        # 开发者类关键词（带权重）
        self.developer_keywords = {
            # 高权重（3分）- 强开发指标
            'github': 3, 'repository': 3, 'open source': 3, 'commit': 3, 
            'pull request': 3, 'sdk': 3, 'api documentation': 3,
            '开源': 3, '仓库': 3, '代码库': 3,
            
            # 中权重（2分）- 开发相关
            'library': 2, 'framework': 2, 'implementation': 2, 'tutorial': 2,
            'guide': 2, 'documentation': 2, 'developer': 2, 'programming': 2,
            '开发': 2, '库': 2, '框架': 2, '教程': 2, '文档': 2, '指南': 2,
            
            # 低权重（1分）- 技术词汇
            'code': 1, 'api': 1, 'package': 1, 'tool': 1,
            '代码': 1, '工具': 1
        }
        
        # 产品类关键词（带权重）
        self.product_keywords = {
            # 高权重（3分）- 强发布指标
            'official release': 3, 'officially launched': 3, 'announces launch': 3,
            'unveil': 3, 'debut': 3, 'available now': 3, 'now available': 3,
            '正式发布': 3, '正式推出': 3, '正式上线': 3, '官方发布': 3,
            
            # 中权重（2分）- 发布相关
            'release': 2, 'launch': 2, 'announce': 2, 'introduce': 2,
            'version': 2, 'update': 2, 'available': 2,
            '发布': 2, '推出': 2, '宣布': 2, '上线': 2, '版本': 2,
            
            # 低权重（1分）- 产品术语
            'official': 1, 'commercial': 1, 'enterprise': 1, 'product': 1,
            'platform': 1, 'service': 1, 'solution': 1, 'beta': 1, 'preview': 1,
            '官方': 1, '商业': 1, '企业': 1, '产品': 1, '平台': 1, '服务': 1, '公测': 1
        }
        
        # 市场类关键词（带权重）
        self.market_keywords = {
            # 高权重（3分）- 强市场指标
            'funding round': 3, 'investment': 3, 'acquisition': 3, 'ipo': 3,
            'valuation': 3, 'revenue': 3, 'raises': 3, 'secures funding': 3,
            '融资': 3, '投资': 3, '收购': 3, '上市': 3, '估值': 3,
            
            # 中权重（2分）- 市场相关
            'market': 2, 'business': 2, 'startup': 2, 'company': 2,
            'policy': 2, 'regulation': 2, 'industry': 2,
            '市场': 2, '企业': 2, '公司': 2, '政策': 2, '监管': 2, '行业': 2,
            
            # 低权重（1分）- 商业术语
            'funding': 1, 'partnership': 1, 'collaboration': 1,
            '合作': 1, '伙伴': 1
        }
        
        # 领袖言论关键词（带权重）
        self.leader_keywords = {
            # 高权重（3分）- 强言论指标
            'interview': 3, 'speech': 3, 'keynote': 3, 'statement': 3,
            'exclusive interview': 3, 'in an interview': 3,
            '采访': 3, '演讲': 3, '主题演讲': 3, '声明': 3,
            
            # 中权重（2分）- 言论相关
            'said': 2, 'stated': 2, 'believes': 2, 'warns': 2, 'predicts': 2,
            'opinion': 2, 'commented': 2,
            '表示': 2, '认为': 2, '警告': 2, '预测': 2, '评论': 2, '观点': 2,
            
            # 低权重（1分）- 社交媒体
            'tweeted': 1, 'posted': 1, 'quote': 1,
            '说': 1, '发文': 1
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
    
    def classify_content_type(self, item: Dict) -> Tuple[str, float, List[str]]:
        """
        分类内容类型：研究/开发者/产品/市场/领袖/社区
        
        Args:
            item: 内容项（包含title, summary等字段）
            
        Returns:
            (主分类, 置信度分数 0-1, 次要标签列表)
        """
        # 如果采集时已经指定了类型，直接使用（高置信度）
        category = item.get('category')
        if category in ['research', 'developer', 'product', 'market', 'leader', 'community']:
            return str(category), 1.0, []

        text = f"{item.get('title', '')} {item.get('summary', '')} {item.get('description', '')}".lower()
        source = item.get('source', '').lower()
        
        # 检测否定词和可信度
        negative_score = self._detect_negative_context(text)
        source_trust = self._calculate_source_trust(source, text)
        
        # 绝对优先规则：GitHub来源必须归类为开发者（维持不变）
        if 'github' in source or 'github.com' in text:
            secondary = self._get_secondary_labels(text, exclude='developer')
            return 'developer', 0.95, secondary
        
        # arXiv来源必须归类为研究（维持不变）
        if 'arxiv' in source or 'arxiv.org' in text:
            secondary = self._get_secondary_labels(text, exclude='research')
            return 'research', 0.95, secondary
        
        # 产品类严格规则：必须同时包含公司名称和产品发布关键词
        company_indicators = ['google', 'microsoft', 'openai', 'anthropic', 'meta', 'apple', 'amazon', 
                             'baidu', 'alibaba', 'tencent', 'bytedance', 'huawei', 'xiaomi',
                             '百度', '阿里', '腾讯', '字节', '华为', '小米',
                             'deepseek', 'mistral', 'cohere', 'stability', 'midjourney', 'runway',
                             '智谱', '月之暗面', '零一万物', '百川', '科大讯飞']
        
        has_company = any(company in text or company in source for company in company_indicators)
        
        # 使用新的加权评分系统
        scores = {
            'research': self._calculate_weighted_score(text, self.research_keywords),
            'developer': self._calculate_weighted_score(text, self.developer_keywords),
            'product': self._calculate_weighted_score(text, self.product_keywords),
            'market': self._calculate_weighted_score(text, self.market_keywords),
            'leader': self._calculate_weighted_score(text, self.leader_keywords)
        }
        
        # 产品类加成规则（保持原有逻辑）
        if has_company and scores['product'] > 0:
            scores['product'] *= 2.5
        elif scores['product'] > 0:
            scores['product'] *= 1.3
        
        # 否定词影响（改进版：根据否定强度调整）
        if negative_score > 0:
            # 强否定（分数高）= 更大幅度降低
            negative_factor = max(0.2, 1 - (negative_score * 0.15))
            scores['product'] *= negative_factor
            scores['market'] *= (negative_factor + 0.2)  # 市场类受影响较小
        
        # 来源可信度加成
        if source_trust > 0:
            # 可信来源提升产品和研究类分数
            scores['product'] *= (1 + source_trust * 0.3)
            scores['research'] *= (1 + source_trust * 0.2)
        
        # 获取主分类和次要标签
        max_category = max(scores.items(), key=lambda x: x[1])
        confidence = self._calculate_confidence(scores, max_category[0])
        secondary_labels = self._get_secondary_labels_from_scores(scores, max_category[0])
        
        return max_category[0], confidence, secondary_labels
    
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
        
        content_type, confidence, secondary_labels = self.classify_content_type(item)
        classified['content_type'] = content_type
        classified['confidence'] = round(confidence, 3)
        
        # 添加次要标签（如果存在）
        if secondary_labels:
            classified['secondary_labels'] = secondary_labels
        
        classified['tech_categories'] = self.classify_tech_category(item)
        classified['region'] = self.classify_region(item)
        classified['classified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 如果置信度低于0.6，标记为需要人工审核
        if confidence < 0.6:
            classified['needs_review'] = True
        
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
        low_confidence = sum(1 for item in classified_items if item.get('confidence', 1) < 0.6)
        avg_confidence = sum(item.get('confidence', 0) for item in classified_items) / len(classified_items) if classified_items else 0
        
        print(f"分类完成！")
        print(f"   - 研究: {stats['research']} | 开发者: {stats['developer']} | 产品: {stats['product']} | 市场: {stats['market']} | 领袖: {stats['leader']}")
        print(f"   - 平均置信度: {avg_confidence:.2%} | 低置信度(<60%): {low_confidence} 条")
        
        return classified_items
    
    def _calculate_keyword_score(self, text: str, keywords) -> int:
        """计算关键词匹配分数（旧版本，保留兼容性）"""
        score = 0
        # 支持Set和List
        keyword_list = list(keywords) if not isinstance(keywords, list) else keywords
        for keyword in keyword_list:
            if keyword in text:
                score += 1
        return score
    
    def _calculate_weighted_score(self, text: str, keywords: Dict[str, int]) -> float:
        """
        计算加权关键词分数
        
        Args:
            text: 文本内容
            keywords: 关键词及其权重字典
            
        Returns:
            加权分数
        """
        score = 0.0
        matched_keywords = []
        
        for keyword, weight in keywords.items():
            if keyword in text:
                # 计算词频
                count = text.count(keyword)
                # TF-IDF 简化版：词频 * 权重 * log衰减
                keyword_score = weight * (1 + math.log(count)) if count > 0 else 0
                score += keyword_score
                matched_keywords.append(keyword)
        
        # 考虑关键词多样性：匹配不同关键词的数量也很重要
        diversity_bonus = len(matched_keywords) * 0.5
        
        return score + diversity_bonus
    
    def _detect_negative_context(self, text: str) -> float:
        """
        检测文本中否定或不确定性表达的强度
        
        Args:
            text: 文本内容
            
        Returns:
            否定强度分数 (0-5)，0表示无否定
        """
        negative_score = 0.0
        
        # 强否定词权重字典
        negative_weights = {
            'fake': 3, 'false': 3, 'denied': 3, 'debunk': 2.5, 'not': 2,
            '虚假': 3, '否认': 3, '辟谣': 2.5, '不是': 2,
            'rumor': 2, 'speculation': 2, 'unconfirmed': 2, 'allegedly': 1.5,
            '传闻': 2, '谣言': 2, '未经证实': 2, '据称': 1.5,
            'delayed': 1.5, 'cancelled': 2, 'suspended': 1.5,
            '延期': 1.5, '取消': 2, '暂停': 1.5,
            'might': 1, 'could': 1, 'possibly': 1,
            '可能': 1, '或许': 1
        }
        
        # 关键动作词（用于判断否定词是否与核心动作相关）
        action_words = ['release', 'launch', 'announce', 'unveil', 'publish',
                       '发布', '推出', '宣布', '公布', '上线']
        
        # 检查否定词及其上下文
        for neg_word, weight in negative_weights.items():
            if neg_word in text:
                # 查找所有出现位置
                pos = 0
                while pos < len(text):
                    pos = text.find(neg_word, pos)
                    if pos == -1:
                        break
                    
                    # 提取上下文（前后40字符）
                    context_start = max(0, pos - 40)
                    context_end = min(len(text), pos + 40)
                    context = text[context_start:context_end]
                    
                    # 如果否定词附近有核心动作词，增加权重
                    if any(action in context for action in action_words):
                        negative_score += weight
                    else:
                        # 否定词存在但不直接影响核心动作，权重减半
                        negative_score += weight * 0.5
                    
                    pos += len(neg_word)
        
        return min(5.0, negative_score)  # 最大值限制为5
    
    def _calculate_source_trust(self, source: str, text: str) -> float:
        """
        计算来源可信度
        
        Args:
            source: 来源字符串
            text: 文本内容
            
        Returns:
            可信度分数 (0-1)
        """
        trust_score = 0.0
        
        # 检查可信来源标识
        for trusted in self.trusted_sources:
            if trusted in source or trusted in text:
                trust_score += 0.2
        
        return min(1.0, trust_score)
    
    def _get_secondary_labels(self, text: str, exclude: Optional[str] = None) -> List[str]:
        """
        获取次要分类标签（用于强制规则后的补充）
        
        Args:
            text: 文本内容
            exclude: 要排除的主分类
            
        Returns:
            次要标签列表
        """
        scores = {
            'research': self._calculate_weighted_score(text, self.research_keywords),
            'developer': self._calculate_weighted_score(text, self.developer_keywords),
            'product': self._calculate_weighted_score(text, self.product_keywords),
            'market': self._calculate_weighted_score(text, self.market_keywords),
            'leader': self._calculate_weighted_score(text, self.leader_keywords)
        }
        
        if exclude:
            scores.pop(exclude, None)
        
        # 只返回分数 > 5 的次要标签
        secondary = [cat for cat, score in scores.items() if score > 5]
        return secondary[:2]  # 最多返回2个次要标签
    
    def _get_secondary_labels_from_scores(self, scores: Dict[str, float], primary: str) -> List[str]:
        """
        从分数字典中提取次要标签
        
        Args:
            scores: 分数字典
            primary: 主分类
            
        Returns:
            次要标签列表
        """
        # 排除主分类
        secondary_scores = {k: v for k, v in scores.items() if k != primary}
        
        # 获取最高分和次高分
        sorted_scores = sorted(secondary_scores.items(), key=lambda x: x[1], reverse=True)
        
        secondary = []
        primary_score = scores[primary]
        
        # 只有当次要分类的分数 >= 主分类分数的50%时才添加
        for cat, score in sorted_scores:
            if score >= primary_score * 0.5 and score > 3:
                secondary.append(cat)
                if len(secondary) >= 2:  # 最多2个次要标签
                    break
        
        return secondary
    
    def _calculate_confidence(self, scores: Dict[str, float], winner: str) -> float:
        """
        计算分类置信度
        
        Args:
            scores: 各类别分数字典
            winner: 最高分类别
            
        Returns:
            置信度 (0-1)
        """
        if not scores or winner not in scores:
            return 0.0
        
        winner_score = scores[winner]
        
        # 如果分数为0，置信度极低
        if winner_score == 0:
            return 0.1
        
        # 计算与第二名的差距
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) < 2:
            return 0.8
        
        first_score = sorted_scores[0]
        second_score = sorted_scores[1]
        
        # 避免除零错误
        if first_score == 0:
            return 0.1
        
        # 置信度 = 第一名分数 / (第一名 + 第二名) * 与第二名的差距比例
        score_ratio = first_score / (first_score + second_score)
        gap_ratio = (first_score - second_score) / first_score if first_score > 0 else 0
        
        # 综合置信度：结合分数比例和差距
        confidence = (score_ratio * 0.6 + gap_ratio * 0.4)
        
        # 如果第一名分数很高（>15），适当提升置信度
        if first_score > 15:
            confidence = min(0.95, confidence * 1.1)
        
        # 如果第一名和第二名非常接近，降低置信度
        if second_score > 0 and first_score / second_score < 1.5:
            confidence *= 0.8
        
        return min(0.99, max(0.1, confidence))
    
    def _calculate_statistics(self, items: List[Dict]) -> Dict:
        """计算分类统计"""
        stats = {'research': 0, 'developer': 0, 'product': 0, 'market': 0, 'leader': 0}
        
        for item in items:
            content_type = item.get('content_type', 'market')
            if content_type in stats:
                stats[content_type] += 1
        
        return stats
    
    def get_filtered_items(self, items: List[Dict], 
                          content_type: Optional[str] = None,
                          tech_category: Optional[str] = None,
                          region: Optional[str] = None) -> List[Dict]:
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
        print(f"  类型: {item['content_type']} (置信度: {item['confidence']:.1%})")
        if item.get('secondary_labels'):
            secondary_str = ', '.join(item['secondary_labels'])
            print(f"  次要: {secondary_str}")
        tech_str = ', '.join(item['tech_categories'])
        print(f"  领域: {tech_str}")
        print(f"  地区: {item['region']}")
        if item.get('needs_review'):
            print(f"  ⚠️  需要人工审核")
