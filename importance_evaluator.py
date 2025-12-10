"""
重要性评估器 - Importance Evaluator
独立的多维度重要性评估模块

评估维度:
1. 来源权威度 (source_authority) - 25%
2. 时效性 (recency) - 25%
3. 分类置信度 (confidence) - 20%
4. 内容相关度 (relevance) - 20%
5. 社交热度 (engagement) - 10%

AI相关性调整:
- ai_relevance 作为乘数调整最终得分
- 高相关(>0.8): 轻微加成 (1.0-1.05)
- 中等相关(0.5-0.8): 轻微惩罚 (0.85-1.0)
- 低相关(0.3-0.5): 中等惩罚 (0.6-0.85)
- 极低相关(<0.3): 大幅惩罚 (0.3-0.6)

该模块独立于分类器，可被规则分类器和LLM分类器共同使用。
"""

from typing import Dict, Tuple, Optional
from datetime import datetime
from dateutil import parser as date_parser
import math
import json
import os
from collections import defaultdict
from logger import get_log_helper

# 模块日志器
log = get_log_helper('importance_evaluator')

# 动态学习配置文件
LEARNING_CONFIG_FILE = 'data/cache/importance_learning.json'


class ImportanceEvaluator:
    """
    多维度重要性评估器
    
    评估维度:
    1. 来源权威度 (source_authority) - 25%
    2. 时效性 (recency) - 25%
    3. 分类置信度 (confidence) - 20% (对低价值内容设上限)
    4. 内容相关度 (relevance) - 20%
    5. 社交热度 (engagement) - 10%
    
    AI相关性调整 (ai_relevance):
    - 作为乘数因子调整最终得分
    - 低AI相关性内容会被降权
    """
    
    def __init__(self):
        # 维度权重配置 (支持动态调整)
        self.weights = {
            'source_authority': 0.25,
            'recency': 0.25,
            'confidence': 0.20,
            'relevance': 0.20,
            'engagement': 0.10
        }
        
        # 动态学习数据
        self.source_performance = defaultdict(lambda: {'scores': [], 'count': 0, 'avg': 0.5})
        self.user_feedback_count = 0
        
        # 加载历史学习数据
        self._load_learning_data()
        
        # 来源权威度评分
        self.source_authority_scores = {
            # 官方一手来源 (0.9-1.0)
            'openai.com': 1.0,
            'openai': 1.0,
            'blog.google': 1.0,
            'google ai': 0.95,
            'ai.meta.com': 1.0,
            'meta ai': 0.95,
            'anthropic.com': 1.0,
            'anthropic': 0.95,
            'microsoft.com': 0.95,
            'blogs.microsoft': 0.95,
            'nvidia': 0.90,
            'arxiv.org': 0.95,
            'arxiv': 0.95,
            'github.com': 0.90,
            'github': 0.90,
            'huggingface.co': 0.90,
            'hugging face': 0.90,
            
            # 中国AI公司官方
            'baidu': 0.90,
            '百度': 0.90,
            'alibaba': 0.90,
            '阿里': 0.90,
            'tencent': 0.90,
            '腾讯': 0.90,
            'deepseek': 0.90,
            '智谱': 0.85,
            '月之暗面': 0.85,
            'kimi': 0.85,
            
            # 专业媒体 (0.7-0.85)
            'techcrunch': 0.85,
            'theverge': 0.80,
            'the verge': 0.80,
            'wired': 0.80,
            'technologyreview': 0.85,
            'mit technology review': 0.85,
            'ieee spectrum': 0.85,
            'artificialintelligence-news': 0.80,
            'syncedreview': 0.80,
            '机器之心': 0.85,
            'jiqizhixin': 0.85,
            '量子位': 0.80,
            'qbitai': 0.80,
            'infoq': 0.75,
            '36kr': 0.70,
            '36氪': 0.70,
            'ithome': 0.70,
            'it之家': 0.70,
            
            # 社区/聚合 (0.5-0.7)
            'reddit': 0.65,
            'producthunt': 0.70,
            'product hunt': 0.70,
            'hacker news': 0.70,
            'hnrss': 0.70,
            
            # 通用新闻 (0.4-0.6)
            'news.google': 0.50,
            'bing.com/news': 0.50,
            'reuters': 0.75,
            'bloomberg': 0.75,
            
            # 个人博客/播客
            'sam altman': 0.90,
            'karpathy': 0.90,
            'andrej karpathy': 0.90,
            'lex fridman': 0.80,
        }
        
        # 高价值关键词 (用于相关度计算) - 分层权重系统
        # 第一层：突破性/里程碑事件 (0.12-0.18)
        self.breakthrough_keywords = {
            'breakthrough': 0.18, 'sota': 0.15, 'state-of-the-art': 0.15,
            'world record': 0.15, 'revolutionary': 0.14, 'game-changer': 0.14,
            'milestone': 0.12, 'paradigm shift': 0.15, 'first-ever': 0.14,
            # 中文
            '突破': 0.18, '里程碑': 0.14, '革命性': 0.14, '颠覆': 0.12,
            '史上首次': 0.15, '重大突破': 0.16,
        }
        
        # 第二层：发布/公告事件 (0.08-0.12)
        self.release_keywords = {
            'release': 0.10, 'launch': 0.10, 'announce': 0.10, 'unveil': 0.12,
            'introduce': 0.08, 'available': 0.08, 'official': 0.10,
            'beta': 0.06, 'preview': 0.06, 'alpha': 0.05,
            'general availability': 0.10, 'ga': 0.08, 'v1.0': 0.08,
            # 中文
            '发布': 0.10, '推出': 0.10, '上线': 0.10, '正式版': 0.10,
            '官宣': 0.10, '官方': 0.08, '公测': 0.06, '内测': 0.05,
        }
        
        # 第三层：技术/模型相关 (0.05-0.10)
        self.tech_keywords = {
            'open source': 0.10, 'open-source': 0.10, 'opensource': 0.10,
            'benchmark': 0.08, 'evaluation': 0.06, 'paper': 0.06,
            'gpt': 0.06, 'llm': 0.06, 'transformer': 0.05, 'diffusion': 0.06,
            'multimodal': 0.08, 'reasoning': 0.08, 'chain-of-thought': 0.08,
            'agent': 0.08, 'agi': 0.10, 'agentic': 0.08,
            'fine-tune': 0.06, 'finetune': 0.06, 'rlhf': 0.07,
            'inference': 0.05, 'training': 0.05, 'dataset': 0.06,
            # 中文
            '开源': 0.10, '模型': 0.05, '大模型': 0.07, '多模态': 0.08,
            '推理': 0.06, '训练': 0.05, '微调': 0.06, '数据集': 0.06,
        }
        
        # 第四层：一般性描述 (0.02-0.05)
        self.general_keywords = {
            'new': 0.03, 'update': 0.04, 'improve': 0.04, 'enhance': 0.04,
            'feature': 0.03, 'support': 0.03, 'capability': 0.04,
            'performance': 0.05, 'faster': 0.04, 'better': 0.03,
            # 中文
            '最新': 0.04, '更新': 0.04, '升级': 0.05, '优化': 0.04,
            '新增': 0.04, '支持': 0.03, '功能': 0.03,
        }
        
        # 负面/降权关键词
        self.negative_relevance_keywords = {
            'rumor': -0.08, 'speculation': -0.06, 'might': -0.03, 'may': -0.02,
            'could': -0.02, 'possibly': -0.04, 'unconfirmed': -0.08,
            'alleged': -0.06, 'reportedly': -0.04,
            # 中文
            '传闻': -0.08, '据悉': -0.04, '或将': -0.04, '可能': -0.03,
            '疑似': -0.06, '未经证实': -0.08,
        }
        
        # 内容类型相关度系数
        self.type_relevance_multipliers = {
            'research': 1.15,   # 研究类通常相关度高
            'product': 1.12,    # 产品发布重要
            'leader': 1.08,     # 领袖言论
            'developer': 1.05,  # 开发者内容
            'tutorial': 1.0,    # 教程内容
            'news': 0.95,       # 新闻可能泛泛而谈
            'market': 0.88,     # 市场分析
            'community': 0.85,  # 社区讨论
            'opinion': 0.80,    # 观点评论
            'other': 0.75,      # 其他内容
        }
        
        # 时效性衰减参数（支持按内容类型调整）
        self.recency_decay_rate = 0.12  # 衰减率，值越大衰减越快
        self.recency_min_score = 0.08   # 最低时效分数
        
        # 不同内容类型的时效性衰减率
        self.type_decay_rates = {
            'product': 0.15,   # 产品发布衰减快（时效性更重要）
            'news': 0.14,      # 新闻衰减快
            'market': 0.10,    # 市场分析衰减慢一些
            'research': 0.08,  # 研究论文衰减最慢（持久价值）
            'tutorial': 0.06,  # 教程更持久
            'leader': 0.10,    # 领袖言论
        }
        
        # 社交热度统一配置
        self.engagement_config = {
            'github_stars': {'threshold_low': 100, 'threshold_high': 50000, 'weight': 1.0},
            'huggingface_downloads': {'threshold_low': 1000, 'threshold_high': 1000000, 'weight': 0.9},
            'reddit_score': {'threshold_low': 50, 'threshold_high': 5000, 'weight': 0.85},
            'hn_points': {'threshold_low': 30, 'threshold_high': 1000, 'weight': 0.85},
            'likes': {'threshold_low': 100, 'threshold_high': 10000, 'weight': 0.7},
            'comments': {'threshold_low': 20, 'threshold_high': 500, 'weight': 0.6},
        }
    
    def calculate_importance(self, item: Dict, 
                            classification_result: Optional[Dict] = None) -> Tuple[float, Dict]:
        """
        计算多维度重要性分数
        
        Args:
            item: 原始数据项
            classification_result: 分类结果，包含 content_type, confidence, ai_relevance 等
            
        Returns:
            (importance_score, score_breakdown)
        """
        if classification_result is None:
            classification_result = {}
        
        breakdown = {}
        
        # 获取内容类型（用于自适应评分）
        content_type = classification_result.get('content_type', 'news')
        
        # 1. 来源权威度 (0-1)
        source_score = self._calculate_source_authority(item)
        breakdown['source_authority'] = round(source_score, 3)
        
        # 2. 时效性 (0-1) - 根据内容类型自适应衰减
        recency_score = self._calculate_recency(item, content_type)
        breakdown['recency'] = round(recency_score, 3)
        
        # 3. 分类置信度 (0-1) - 对低价值内容设置上限
        confidence = classification_result.get('confidence', 0.5)
        # 低时效内容（>14天）限制置信度贡献
        if recency_score <= 0.50:  # 14天以上的内容
            if source_score < 0.80:  # 非官方高权威来源
                confidence = min(confidence, 0.60)  # 置信度上限60%
            else:
                confidence = min(confidence, 0.75)  # 官方来源上限75%
        elif recency_score <= 0.70:  # 7-14天的内容
            if source_score < 0.70:
                confidence = min(confidence, 0.75)  # 普通来源上限75%
        breakdown['confidence'] = round(confidence, 3)
        
        # 4. 内容相关度 (0-1)
        relevance_score = self._calculate_relevance(item, content_type)
        breakdown['relevance'] = round(relevance_score, 3)
        
        # 5. 社交热度 (0-1)
        engagement_score = self._calculate_engagement(item)
        breakdown['engagement'] = round(engagement_score, 3)
        
        # 6. AI相关性调整 (新增)
        # ai_relevance 用于惩罚非AI相关内容
        ai_relevance = classification_result.get('ai_relevance', 0.7)  # 默认0.7（假设大部分采集内容AI相关）
        breakdown['ai_relevance'] = round(ai_relevance, 3)
        
        # 加权求和
        total_score = (
            source_score * self.weights['source_authority'] +
            recency_score * self.weights['recency'] +
            confidence * self.weights['confidence'] +
            relevance_score * self.weights['relevance'] +
            engagement_score * self.weights['engagement']
        )
        
        # 应用AI相关性调整
        # 高相关(>0.7): 不调整或略微加成
        # 中等相关(0.5-0.7): 轻微惩罚
        # 低相关(<0.5): 较大惩罚
        # 极低相关(<0.3): 大幅惩罚
        if ai_relevance >= 0.8:
            ai_multiplier = 1.0 + (ai_relevance - 0.8) * 0.25  # 0.8-1.0 轻微加成 (1.0-1.05)
        elif ai_relevance >= 0.5:
            ai_multiplier = 0.85 + (ai_relevance - 0.5) * 0.5  # 0.5-0.8 轻微惩罚 (0.85-1.0)
        elif ai_relevance >= 0.3:
            ai_multiplier = 0.6 + (ai_relevance - 0.3) * 1.25  # 0.3-0.5 中等惩罚 (0.6-0.85)
        else:
            ai_multiplier = 0.3 + ai_relevance  # <0.3 大幅惩罚 (0.3-0.6)
        
        total_score *= ai_multiplier
        breakdown['ai_multiplier'] = round(ai_multiplier, 3)
        
        # 确保在 0-1 范围内
        importance = round(min(max(total_score, 0.0), 1.0), 3)
        
        return importance, breakdown
    
    def _calculate_source_authority(self, item: Dict) -> float:
        """
        计算来源权威度 - 结合静态评分和动态学习
        
        Args:
            item: 数据项
            
        Returns:
            权威度分数 0-1
        """
        source = item.get('source', '').lower()
        url = item.get('url', '').lower()
        author = item.get('author', '').lower()
        
        # 合并检查文本
        check_text = f"{source} {url} {author}"
        
        # 静态评分：查找匹配的来源
        static_score = 0.40  # 默认值
        matched_source = None
        
        for known_source, score in self.source_authority_scores.items():
            if known_source.lower() in check_text:
                if score > static_score:
                    static_score = score
                    matched_source = known_source
        
        # 动态评分：从历史表现学习
        dynamic_score = None
        if matched_source and matched_source in self.source_performance:
            perf = self.source_performance[matched_source]
            if perf['count'] >= 5:  # 至少5个样本才启用动态评分
                dynamic_score = perf['avg']
        
        # 结合静态和动态评分
        if dynamic_score is not None:
            # 动态评分权重随样本数增加：20% -> 40%
            sample_count = self.source_performance[matched_source]['count']
            dynamic_weight = min(0.20 + sample_count * 0.02, 0.40)
            final_score = static_score * (1 - dynamic_weight) + dynamic_score * dynamic_weight
            return round(final_score, 3)
        
        return static_score
    
    def _calculate_recency(self, item: Dict, content_type: str = 'news') -> float:
        """
        计算时效性分数 - 自适应指数衰减曲线
        
        使用指数衰减公式: score = max_score * e^(-decay_rate * days) + min_score
        衰减率根据内容类型自适应调整
        
        Args:
            item: 数据项
            content_type: 内容类型（影响衰减率）
            
        Returns:
            时效性分数 0-1
        """
        published = item.get('published', '')
        
        if not published:
            # 无日期信息，给中等分数
            return 0.5
        
        try:
            # 解析日期
            if isinstance(published, datetime):
                pub_date = published
            elif isinstance(published, str):
                # 尝试多种格式解析
                try:
                    pub_date = date_parser.parse(published)
                except (ValueError, TypeError):
                    # 尝试简单格式
                    if len(published) >= 10:
                        pub_date = datetime.strptime(published[:10], '%Y-%m-%d')
                    else:
                        return 0.5
            else:
                return 0.5
            
            # 计算天数差
            now = datetime.now()
            # 处理时区
            if pub_date.tzinfo is not None and now.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=None)
            
            days_ago = (now - pub_date).days
            
            # 未来日期或今天
            if days_ago <= 0:
                return 1.0
            
            # 根据内容类型选择衰减率
            decay_rate = self.type_decay_rates.get(content_type, self.recency_decay_rate)
            min_score = self.recency_min_score
            
            # 指数衰减
            score = (1.0 - min_score) * math.exp(-decay_rate * days_ago) + min_score
            
            return round(max(min(score, 1.0), min_score), 3)
                
        except Exception:
            return 0.5
    
    def _calculate_relevance(self, item: Dict, content_type: str) -> float:
        """
        计算内容相关度 - 分层关键词系统
        
        使用分层关键词系统:
        1. 突破性/里程碑事件 (最高权重)
        2. 发布/公告事件 (高权重)
        3. 技术/模型相关 (中权重)
        4. 一般性描述 (低权重)
        并考虑负面关键词降权
        
        Args:
            item: 数据项
            content_type: 分类类型
            
        Returns:
            相关度分数 0-1
        """
        title = item.get('title', '').lower()
        summary = item.get('summary', '').lower()
        text = f"{title} {summary}"
        
        # 基础分
        score = 0.25
        
        # 分层关键词匹配 - 使用集合避免重复计分
        matched_keywords = set()
        layer_scores = {'breakthrough': 0, 'release': 0, 'tech': 0, 'general': 0}
        
        # 第一层: 突破性关键词 (最高价值)
        for keyword, boost in self.breakthrough_keywords.items():
            if keyword in text and keyword not in matched_keywords:
                layer_scores['breakthrough'] += boost
                matched_keywords.add(keyword)
        
        # 第二层: 发布关键词
        for keyword, boost in self.release_keywords.items():
            if keyword in text and keyword not in matched_keywords:
                layer_scores['release'] += boost
                matched_keywords.add(keyword)
        
        # 第三层: 技术关键词
        for keyword, boost in self.tech_keywords.items():
            if keyword in text and keyword not in matched_keywords:
                layer_scores['tech'] += boost
                matched_keywords.add(keyword)
        
        # 第四层: 一般关键词
        for keyword, boost in self.general_keywords.items():
            if keyword in text and keyword not in matched_keywords:
                layer_scores['general'] += boost
                matched_keywords.add(keyword)
        
        # 分层加分，高层次关键词有更大影响
        # 突破层全额计分，其他层有衰减
        score += layer_scores['breakthrough']  # 100% 权重
        score += layer_scores['release'] * 0.9  # 90% 权重
        score += layer_scores['tech'] * 0.8     # 80% 权重
        score += layer_scores['general'] * 0.6  # 60% 权重
        
        # 负面关键词降权
        for keyword, penalty in self.negative_relevance_keywords.items():
            if keyword in text:
                score += penalty  # penalty 是负数
        
        # 标题中的关键词额外加分 (标题通常更重要)
        title_bonus = 0
        for keyword in matched_keywords:
            if keyword in title:
                title_bonus += 0.02  # 每个标题中的关键词额外+0.02
        score += min(title_bonus, 0.10)  # 上限 0.10
        
        # 根据内容类型调整
        multiplier = self.type_relevance_multipliers.get(content_type, 0.9)
        score *= multiplier
        
        # 确保分数在合理范围
        return round(max(min(score, 1.0), 0.1), 3)
    
    def _calculate_engagement(self, item: Dict) -> float:
        """
        计算社交热度 - 统一归一化算法
        
        使用统一的对数归一化公式:
        score = log(value + 1) / log(threshold_high + 1) * weight
        
        支持多个社交信号的加权组合
        
        Args:
            item: 数据项
            
        Returns:
            热度分数 0-1
        """
        signals = []
        
        # 统一的归一化函数
        def normalize_signal(value: int, config: dict) -> float:
            """统一的对数归一化"""
            if not value or value <= 0:
                return None
            
            threshold_low = config['threshold_low']
            threshold_high = config['threshold_high']
            weight = config['weight']
            
            # 对数归一化，并应用权重
            # 低于阈值的给予较低分
            if value < threshold_low:
                score = math.log(value + 1) / math.log(threshold_low + 1) * 0.4
            else:
                # 在阈值范围内的正常计分
                score = 0.4 + 0.6 * math.log(value / threshold_low + 1) / math.log(threshold_high / threshold_low + 1)
            
            return min(score * weight, 1.0)
        
        # GitHub stars
        stars = item.get('stars', 0)
        if stars:
            score = normalize_signal(stars, self.engagement_config['github_stars'])
            if score is not None:
                signals.append(('stars', score, self.engagement_config['github_stars']['weight']))
        
        # HuggingFace downloads
        downloads = item.get('downloads', 0)
        if downloads:
            score = normalize_signal(downloads, self.engagement_config['huggingface_downloads'])
            if score is not None:
                signals.append(('downloads', score, self.engagement_config['huggingface_downloads']['weight']))
        
        # Reddit score
        reddit_score = item.get('score', 0)
        if reddit_score and 'reddit' in item.get('source', '').lower():
            score = normalize_signal(reddit_score, self.engagement_config['reddit_score'])
            if score is not None:
                signals.append(('reddit', score, self.engagement_config['reddit_score']['weight']))
        
        # Hacker News points
        hn_points = item.get('points', 0)
        if hn_points:
            score = normalize_signal(hn_points, self.engagement_config['hn_points'])
            if score is not None:
                signals.append(('hn', score, self.engagement_config['hn_points']['weight']))
        
        # 通用likes
        likes = item.get('likes', item.get('favorites', 0))
        if likes:
            score = normalize_signal(likes, self.engagement_config['likes'])
            if score is not None:
                signals.append(('likes', score, self.engagement_config['likes']['weight']))
        
        # 评论数
        comments = item.get('comments', item.get('num_comments', 0))
        if comments:
            score = normalize_signal(comments, self.engagement_config['comments'])
            if score is not None:
                signals.append(('comments', score, self.engagement_config['comments']['weight']))
        
        # 无社交数据，给中等分
        if not signals:
            return 0.5
        
        # 加权平均
        total_weight = sum(s[2] for s in signals)
        weighted_sum = sum(s[1] for s in signals)
        
        # 组合多个信号时给予小幅加分 (多维度验证)
        multi_signal_bonus = min(len(signals) - 1, 3) * 0.03
        
        final_score = weighted_sum / total_weight + multi_signal_bonus
        
        return round(min(max(final_score, 0.0), 1.0), 3)
    
    def get_importance_level(self, score: float) -> Tuple[str, str]:
        """
        获取重要性等级和标签
        
        Args:
            score: 重要性分数
            
        Returns:
            (等级, emoji标签)
        """
        if score >= 0.85:
            return 'critical', '🔴'
        elif score >= 0.70:
            return 'high', '🟠'
        elif score >= 0.55:
            return 'medium', '🟡'
        elif score >= 0.40:
            return 'low', '🟢'
        else:
            return 'minimal', '⚪'
    
    def update_source_performance(self, source: str, final_importance: float):
        """
        更新来源的历史表现（用于动态学习）
        
        Args:
            source: 来源名称
            final_importance: 最终重要性评分
        """
        if not source:
            return
        
        source_key = source.lower()
        perf = self.source_performance[source_key]
        
        # 滚动窗口：只保留最近50个评分
        perf['scores'].append(final_importance)
        if len(perf['scores']) > 50:
            perf['scores'] = perf['scores'][-50:]
        
        # 更新统计
        perf['count'] = len(perf['scores'])
        perf['avg'] = sum(perf['scores']) / perf['count']
        
        # 定期保存（每10次更新保存一次）
        self.user_feedback_count += 1
        if self.user_feedback_count % 10 == 0:
            self._save_learning_data()
    
    def _load_learning_data(self):
        """
        加载历史学习数据
        """
        try:
            if os.path.exists(LEARNING_CONFIG_FILE):
                with open(LEARNING_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 恢复来源表现数据
                if 'source_performance' in data:
                    for source, perf in data['source_performance'].items():
                        self.source_performance[source] = perf
                
                log.info(f"📚 Loaded learning data: {len(self.source_performance)} sources")
        except Exception as e:
            log.warning(f"Failed to load learning data: {e}")
    
    def _save_learning_data(self):
        """
        保存学习数据到文件
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(LEARNING_CONFIG_FILE), exist_ok=True)
            
            data = {
                'source_performance': dict(self.source_performance),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(LEARNING_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            log.info(f"💾 Saved learning data: {len(self.source_performance)} sources")
        except Exception as e:
            log.warning(f"Failed to save learning data: {e}")
    
    def get_learning_stats(self) -> Dict:
        """
        获取学习统计信息
        
        Returns:
            统计信息字典
        """
        learned_sources = sum(1 for perf in self.source_performance.values() if perf['count'] >= 5)
        
        return {
            'total_sources_tracked': len(self.source_performance),
            'learned_sources': learned_sources,
            'total_samples': sum(perf['count'] for perf in self.source_performance.values()),
            'learning_enabled': learned_sources > 0
        }
