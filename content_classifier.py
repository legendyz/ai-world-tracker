"""
内容分类系统 - Content Classifier
基于关键词和规则对AI内容进行多维度分类

包含:
- ImportanceEvaluator: 多维度重要性评估器
- ContentClassifier: 基于规则的内容分类器
"""

from typing import Dict, List, Set, Tuple, Optional
import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import math
from collections import Counter
from logger import get_log_helper

# 模块日志器
log = get_log_helper('classifier')


class ImportanceEvaluator:
    """
    多维度重要性评估器
    
    评估维度:
    1. 来源权威度 (source_authority) - 25%
    2. 时效性 (recency) - 25%
    3. 分类置信度 (confidence) - 20% (对低价值内容设上限)
    4. 内容相关度 (relevance) - 20%
    5. 社交热度 (engagement) - 10%
    """
    
    def __init__(self):
        # 维度权重配置
        self.weights = {
            'source_authority': 0.25,
            'recency': 0.25,
            'confidence': 0.20,
            'relevance': 0.20,
            'engagement': 0.10
        }
        
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
        
        # 时效性衰减参数
        self.recency_decay_rate = 0.12  # 衰减率，值越大衰减越快
        self.recency_min_score = 0.08   # 最低时效分数
        
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
            classification_result: 分类结果，包含 content_type, confidence 等
            
        Returns:
            (importance_score, score_breakdown)
        """
        if classification_result is None:
            classification_result = {}
        
        breakdown = {}
        
        # 1. 来源权威度 (0-1)
        source_score = self._calculate_source_authority(item)
        breakdown['source_authority'] = round(source_score, 3)
        
        # 2. 时效性 (0-1)
        recency_score = self._calculate_recency(item)
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
        content_type = classification_result.get('content_type', 'news')
        relevance_score = self._calculate_relevance(item, content_type)
        breakdown['relevance'] = round(relevance_score, 3)
        
        # 5. 社交热度 (0-1)
        engagement_score = self._calculate_engagement(item)
        breakdown['engagement'] = round(engagement_score, 3)
        
        # 加权求和
        total_score = (
            source_score * self.weights['source_authority'] +
            recency_score * self.weights['recency'] +
            confidence * self.weights['confidence'] +
            relevance_score * self.weights['relevance'] +
            engagement_score * self.weights['engagement']
        )
        
        # 确保在 0-1 范围内
        importance = round(min(max(total_score, 0.0), 1.0), 3)
        
        return importance, breakdown
    
    def _calculate_source_authority(self, item: Dict) -> float:
        """
        计算来源权威度
        
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
        
        # 查找匹配的来源
        best_score = 0.40  # 默认值
        
        for known_source, score in self.source_authority_scores.items():
            if known_source.lower() in check_text:
                best_score = max(best_score, score)
        
        return best_score
    
    def _calculate_recency(self, item: Dict) -> float:
        """
        计算时效性分数 - 平滑指数衰减曲线
        
        使用指数衰减公式: score = max_score * e^(-decay_rate * days) + min_score
        
        衰减曲线参考值:
        - 今天: 1.0
        - 1天前: ~0.89
        - 3天前: ~0.70
        - 7天前: ~0.44
        - 14天前: ~0.22
        - 30天前: ~0.10
        
        Args:
            item: 数据项
            
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
            
            # 平滑指数衰减
            # score = (1 - min_score) * e^(-decay_rate * days) + min_score
            decay_rate = self.recency_decay_rate
            min_score = self.recency_min_score
            
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


class ContentClassifier:
    """AI内容智能分类器 - 增强版"""
    
    def __init__(self):
        # 初始化重要性评估器
        self.importance_evaluator = ImportanceEvaluator()
        
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
        
        # 研究类关键词（带权重）- 2025年更新版
        self.research_keywords = {
            # 高权重（3分）- 强研究指标
            'arxiv': 3, 'conference': 3, 'journal': 3, 'paper': 3, 'publication': 3,
            'peer-reviewed': 3, 'proceedings': 3, 'academic': 3, 'neurips': 3, 'icml': 3,
            'iclr': 3, 'cvpr': 3, 'acl': 3, 'emnlp': 3, 'aaai': 3,
            '论文': 3, '学术': 3, '期刊': 3, '会议': 3,
            
            # 中权重（2分）- 研究相关 + 2024-2025新研究方向
            'research': 2, 'study': 2, 'experiment': 2, 'methodology': 2,
            'findings': 2, 'analysis': 2, 'survey': 2, 'benchmark': 2,
            'state-of-the-art': 2, 'sota': 2, 'baseline': 2, 'ablation': 2,
            'reasoning': 2, 'chain-of-thought': 2, 'cot': 2, 'in-context learning': 2,
            'multimodal': 2, 'moe': 2, 'mixture of experts': 2, 'sparse': 2,
            'distillation': 2, 'quantization': 2, 'pruning': 2, 'efficient': 2,
            'scaling law': 2, 'emergent': 2, 'alignment': 2, 'rlhf': 2, 'dpo': 2,
            '研究': 2, '实验': 2, '分析': 2, '基准': 2, '消融': 2,
            
            # 低权重（1分）- 技术术语
            'algorithm': 1, 'model': 1, 'neural network': 1, 'deep learning': 1, 
            'machine learning': 1, 'architecture': 1, 'attention': 1, 'transformer': 1,
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
        
        # 产品类关键词（带权重）- 2025年更新版
        self.product_keywords = {
            # 高权重（3分）- 强发布指标 + 2024-2025新产品名
            'official release': 3, 'officially launched': 3, 'announces launch': 3,
            'unveil': 3, 'debut': 3, 'available now': 3, 'now available': 3,
            'rolls out': 3, 'ships': 3, 'goes live': 3, 'general availability': 3,
            'gpt-4o': 3, 'gpt-4-turbo': 3, 'o1': 3, 'o1-preview': 3, 'o1-mini': 3, 'o3': 3,
            'claude-3': 3, 'claude-3.5': 3, 'claude-3-opus': 3, 'claude-3-sonnet': 3,
            'gemini': 3, 'gemini-pro': 3, 'gemini-ultra': 3, 'gemini 2.0': 3,
            'sora': 3, 'veo': 3, 'imagen 3': 3, 'firefly': 3,
            'llama-3': 3, 'llama-3.1': 3, 'llama-3.2': 3,
            'copilot': 3, 'github copilot': 3, 'cursor': 3,
            '正式发布': 3, '正式推出': 3, '正式上线': 3, '官方发布': 3, '全面开放': 3,
            '豆包': 3, 'doubao': 3, 'kimi': 3, '通义千问': 3, 'qwen': 3,
            '文心一言': 3, 'ernie': 3, '星火': 3, 'spark': 3,
            
            # 中权重（2分）- 发布相关
            'release': 2, 'launch': 2, 'announce': 2, 'introduce': 2,
            'version': 2, 'update': 2, 'available': 2, 'upgrade': 2,
            'new feature': 2, 'new model': 2, 'latest version': 2,
            '发布': 2, '推出': 2, '宣布': 2, '上线': 2, '版本': 2, '升级': 2, '更新': 2,
            
            # 低权重（1分）- 产品术语
            'official': 1, 'commercial': 1, 'enterprise': 1, 'product': 1,
            'platform': 1, 'service': 1, 'solution': 1, 'beta': 1, 'preview': 1,
            'pro': 1, 'plus': 1, 'premium': 1, 'subscription': 1,
            '官方': 1, '商业': 1, '企业': 1, '产品': 1, '平台': 1, '服务': 1, '公测': 1, '订阅': 1
        }
        
        # 市场类关键词（带权重）- 2025年更新版
        self.market_keywords = {
            # 高权重（3分）- 强市场指标
            'funding round': 3, 'investment': 3, 'acquisition': 3, 'ipo': 3,
            'valuation': 3, 'revenue': 3, 'raises': 3, 'secures funding': 3,
            'series a': 3, 'series b': 3, 'series c': 3, 'series d': 3,
            'unicorn': 3, 'billion': 3, 'million': 3,
            '融资': 3, '投资': 3, '收购': 3, '上市': 3, '估值': 3,
            '轮融资': 3, '独角兽': 3, '亿美元': 3, '亿元': 3,
            
            # 中权重（2分）- 市场相关 + 政策法规
            'market': 2, 'business': 2, 'startup': 2, 'company': 2,
            'policy': 2, 'regulation': 2, 'industry': 2, 'layoff': 2, 'layoffs': 2,
            'antitrust': 2, 'lawsuit': 2, 'copyright': 2, 'license': 2,
            'ai act': 2, 'executive order': 2, 'ban': 2, 'restrict': 2,
            '市场': 2, '企业': 2, '公司': 2, '政策': 2, '监管': 2, '行业': 2,
            '裁员': 2, '反垄断': 2, '版权': 2, '合规': 2, '法案': 2,
            
            # 低权重（1分）- 商业术语
            'funding': 1, 'partnership': 1, 'collaboration': 1, 'deal': 1,
            'contract': 1, 'profit': 1, 'loss': 1, 'growth': 1,
            '合作': 1, '伙伴': 1, '交易': 1, '合同': 1, '营收': 1, '增长': 1
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
        
        # ============ 新增：上下文短语匹配模式 ============
        self.phrase_patterns = {
            'product': [
                r'officially\s+(launched|released|announced)',
                r'now\s+available\s+(for|to|in)',
                r'rolling\s+out\s+to',
                r'is\s+now\s+(live|available|open)',
                r'has\s+(launched|released|unveiled)',
                r'introduces?\s+new',
                r'正式(发布|上线|推出|开放)',
                r'全面(开放|上线|推出)',
                r'(开始|开启)(内测|公测|商用)',
            ],
            'research': [
                r'we\s+propose',
                r'we\s+present',
                r'we\s+introduce\s+a\s+(new|novel)',
                r'our\s+(method|approach|model)\s+(achieves?|outperforms?)',
                r'state-of-the-art\s+(results?|performance)',
                r'benchmark\s+results?',
                r'experiments?\s+(show|demonstrate)',
                r'(本文|我们)(提出|介绍|研究)',
                r'(实验|结果)(表明|显示|证明)',
            ],
            'market': [
                r'raises?\s+\$?\d+\s*(m|million|b|billion)',
                r'valued\s+at\s+\$',
                r'acquisition\s+of',
                r'acquires?\s+',
                r'ipo\s+(filing|plans?)',
                r'layoffs?\s+at',
                r'(获得|完成).{0,10}(融资|投资)',
                r'估值.{0,5}(亿|万)',
                r'(收购|并购)',
            ],
            'leader': [
                r'(ceo|cto|founder|chief).{0,20}(said|says|stated|believes)',
                r'in\s+(an\s+)?interview',
                r'(sam altman|elon musk|jensen huang|sundar pichai).{0,30}(said|says|warns|predicts)',
                r'(表示|认为|指出|警告|预测).{0,10}(说|称)',
            ]
        }
        
        # ============ 新增：来源先验概率 ============
        self.source_priors = {
            # 研究源
            'arxiv': {'research': 0.95, 'developer': 0.02, 'product': 0.01, 'market': 0.01, 'leader': 0.01},
            'arxiv.org': {'research': 0.95, 'developer': 0.02, 'product': 0.01, 'market': 0.01, 'leader': 0.01},
            
            # 开发者源
            'github': {'developer': 0.90, 'research': 0.05, 'product': 0.03, 'market': 0.01, 'leader': 0.01},
            'github.com': {'developer': 0.90, 'research': 0.05, 'product': 0.03, 'market': 0.01, 'leader': 0.01},
            'huggingface': {'developer': 0.70, 'research': 0.20, 'product': 0.05, 'market': 0.03, 'leader': 0.02},
            'hugging face': {'developer': 0.70, 'research': 0.20, 'product': 0.05, 'market': 0.03, 'leader': 0.02},
            
            # 科技新闻源
            'techcrunch': {'product': 0.40, 'market': 0.35, 'developer': 0.10, 'research': 0.05, 'leader': 0.10},
            'the verge': {'product': 0.45, 'market': 0.25, 'developer': 0.10, 'research': 0.05, 'leader': 0.15},
            'wired': {'product': 0.35, 'market': 0.25, 'research': 0.15, 'developer': 0.10, 'leader': 0.15},
            'mit technology review': {'research': 0.40, 'product': 0.25, 'market': 0.15, 'developer': 0.10, 'leader': 0.10},
            
            # 社区源
            'product hunt': {'product': 0.70, 'developer': 0.20, 'market': 0.05, 'research': 0.03, 'leader': 0.02},
            'hacker news': {'developer': 0.40, 'product': 0.25, 'research': 0.15, 'market': 0.10, 'leader': 0.10},
            
            # 官方博客
            'openai': {'product': 0.50, 'research': 0.30, 'developer': 0.10, 'leader': 0.08, 'market': 0.02},
            'google ai': {'product': 0.45, 'research': 0.35, 'developer': 0.10, 'leader': 0.05, 'market': 0.05},
            'microsoft': {'product': 0.50, 'developer': 0.25, 'market': 0.15, 'research': 0.05, 'leader': 0.05},
            'anthropic': {'product': 0.45, 'research': 0.35, 'developer': 0.10, 'leader': 0.05, 'market': 0.05},
            
            # 中文源
            '36氪': {'market': 0.50, 'product': 0.35, 'leader': 0.08, 'developer': 0.05, 'research': 0.02},
            '36kr': {'market': 0.50, 'product': 0.35, 'leader': 0.08, 'developer': 0.05, 'research': 0.02},
            '机器之心': {'research': 0.35, 'product': 0.30, 'developer': 0.15, 'market': 0.10, 'leader': 0.10},
            '量子位': {'product': 0.35, 'research': 0.30, 'market': 0.15, 'developer': 0.10, 'leader': 0.10},
            'it之家': {'product': 0.50, 'market': 0.25, 'developer': 0.10, 'research': 0.05, 'leader': 0.10},
        }
        
        # 编译正则表达式（提高性能）
        self._compiled_patterns = {}
        for category, patterns in self.phrase_patterns.items():
            self._compiled_patterns[category] = [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def classify_content_type(self, item: Dict) -> Tuple[str, float, List[str]]:
        """
        分类内容类型：研究/开发者/产品/市场/领袖/社区
        
        增强版特性：
        - 标题/内容权重分离（标题权重 x1.5）
        - 上下文短语匹配
        - 来源先验概率
        
        Args:
            item: 内容项（包含title, summary等字段）
            
        Returns:
            (主分类, 置信度分数 0-1, 次要标签列表)
        """
        # 如果采集时已经指定了类型，直接使用（高置信度）
        category = item.get('category')
        if category in ['research', 'developer', 'product', 'market', 'leader', 'community']:
            return str(category), 1.0, []

        # ============ 分离标题和内容 ============
        title = item.get('title', '').lower()
        summary = f"{item.get('summary', '')} {item.get('description', '')}".lower()
        full_text = f"{title} {summary}"
        source = item.get('source', '').lower()
        
        # 检测否定词和可信度
        negative_score = self._detect_negative_context(full_text)
        source_trust = self._calculate_source_trust(source, full_text)
        
        # 绝对优先规则：GitHub来源必须归类为开发者（维持不变）
        if 'github' in source or 'github.com' in full_text:
            secondary = self._get_secondary_labels(full_text, exclude='developer')
            return 'developer', 0.95, secondary
        
        # arXiv来源必须归类为研究（维持不变）
        if 'arxiv' in source or 'arxiv.org' in full_text:
            secondary = self._get_secondary_labels(full_text, exclude='research')
            return 'research', 0.95, secondary
        
        # 产品类严格规则：必须同时包含公司名称和产品发布关键词
        company_indicators = ['google', 'microsoft', 'openai', 'anthropic', 'meta', 'apple', 'amazon', 
                             'baidu', 'alibaba', 'tencent', 'bytedance', 'huawei', 'xiaomi',
                             '百度', '阿里', '腾讯', '字节', '华为', '小米',
                             'deepseek', 'mistral', 'cohere', 'stability', 'midjourney', 'runway',
                             '智谱', '月之暗面', '零一万物', '百川', '科大讯飞']
        
        has_company = any(company in full_text or company in source for company in company_indicators)
        
        # ============ 新增：标题/内容分离加权评分 ============
        all_keywords = {
            'research': self.research_keywords,
            'developer': self.developer_keywords,
            'product': self.product_keywords,
            'market': self.market_keywords,
            'leader': self.leader_keywords
        }
        
        scores = {}
        for cat, kw in all_keywords.items():
            # 标题权重 x1.5，内容权重 x1.0
            title_score = self._calculate_weighted_score(title, kw) * 1.5
            summary_score = self._calculate_weighted_score(summary, kw)
            scores[cat] = title_score + summary_score
        
        # ============ 新增：上下文短语匹配加分 ============
        phrase_scores = self._calculate_phrase_scores(full_text)
        for cat, phrase_score in phrase_scores.items():
            if cat in scores:
                # 短语匹配给予额外加分（每个匹配 +3 分）
                scores[cat] += phrase_score * 3.0
        
        # ============ 新增：来源先验概率加成 ============
        scores = self._apply_source_prior(scores, source)
        
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
    
    def _calculate_phrase_scores(self, text: str) -> Dict[str, int]:
        """
        计算短语匹配分数
        
        Args:
            text: 文本内容
            
        Returns:
            各分类的短语匹配数量
        """
        scores = {}
        for category, patterns in self._compiled_patterns.items():
            match_count = 0
            for pattern in patterns:
                if pattern.search(text):
                    match_count += 1
            scores[category] = match_count
        return scores
    
    def _apply_source_prior(self, scores: Dict[str, float], source: str) -> Dict[str, float]:
        """
        应用来源先验概率
        
        Args:
            scores: 当前各分类分数
            source: 来源字符串
            
        Returns:
            调整后的分数
        """
        # 查找匹配的来源
        matched_prior = None
        for source_key, priors in self.source_priors.items():
            if source_key in source:
                matched_prior = priors
                break
        
        if matched_prior:
            # 应用先验概率加成（先验概率 * 权重系数）
            for cat, prior in matched_prior.items():
                if cat in scores:
                    # 高先验概率的分类获得更多加成
                    boost = 1 + (prior * 0.5)  # 最高加成 50%
                    scores[cat] *= boost
        
        return scores
    
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
            添加了分类信息的内容项，包含:
            - content_type: 内容类型
            - confidence: 分类置信度
            - importance: 多维度重要性分数
            - importance_breakdown: 重要性分数明细
            - importance_level: 重要性等级
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
        classified['classified_by'] = 'rule'
        
        # 计算多维度重要性分数
        importance, importance_breakdown = self.importance_evaluator.calculate_importance(
            item,
            {'content_type': content_type, 'confidence': confidence}
        )
        classified['importance'] = importance
        classified['importance_breakdown'] = importance_breakdown
        
        # 添加重要性等级
        level, emoji = self.importance_evaluator.get_importance_level(importance)
        classified['importance_level'] = level
        
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
        log.dual_rule(f"正在对 {len(items)} 条内容进行规则分类...")
        
        classified_items = []
        for item in items:
            classified_items.append(self.classify_item(item))
        
        # 统计
        stats = self._calculate_statistics(classified_items)
        low_confidence = sum(1 for item in classified_items if item.get('confidence', 1) < 0.6)
        avg_confidence = sum(item.get('confidence', 0) for item in classified_items) / len(classified_items) if classified_items else 0
        
        # 重要性统计
        avg_importance = sum(item.get('importance', 0) for item in classified_items) / len(classified_items) if classified_items else 0
        high_importance = sum(1 for item in classified_items if item.get('importance', 0) >= 0.70)
        
        log.dual_success("规则分类完成！")
        log.dual_data(f"研究: {stats['research']} | 开发者: {stats['developer']} | 产品: {stats['product']} | 市场: {stats['market']} | 领袖: {stats['leader']}")
        log.dual_data(f"平均置信度: {avg_confidence:.2%} | 低置信度(<60%): {low_confidence} 条")
        log.dual_data(f"平均重要性: {avg_importance:.2%} | 高重要性(≥70%): {high_importance} 条")
        
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
    
    log.info("📋 分类结果:")
    for item in results:
        log.menu(f"\n  标题: {item['title']}")
        log.menu(f"  类型: {item['content_type']} (置信度: {item['confidence']:.1%})")
        if item.get('secondary_labels'):
            secondary_str = ', '.join(item['secondary_labels'])
            log.menu(f"  次要: {secondary_str}")
        tech_str = ', '.join(item['tech_categories'])
        log.menu(f"  领域: {tech_str}")
        log.menu(f"  地区: {item['region']}")
        if item.get('needs_review'):
            log.warning("需要人工审核")
