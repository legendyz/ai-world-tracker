"""
学习反馈系统 - Learning Feedback System
从人工审核结果中学习，优化分类模型

功能:
1. 分析人工审核模式
2. 提取关键特征
3. 动态调整分类权重
4. 生成改进建议
"""

import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import Counter, defaultdict
import re


class LearningFeedback:
    """学习反馈系统"""
    
    def __init__(self):
        self.review_patterns = defaultdict(list)
        self.correction_stats = {
            'total_corrections': 0,
            'by_original_category': defaultdict(int),
            'by_new_category': defaultdict(int),
            'category_transitions': defaultdict(int)
        }
        self.keyword_adjustments = defaultdict(float)
        self.improvement_suggestions = []
    
    def analyze_review_history(self, review_history: List[Dict]) -> Dict:
        """
        分析审核历史，提取学习模式
        
        Args:
            review_history: 审核历史记录列表
            
        Returns:
            分析结果字典
        """
        print("\n📊 正在分析审核历史...")
        
        for record in review_history:
            action = record.get('action', '')
            
            # 提取分类变更
            if '修改分类:' in action or '→' in action:
                self._extract_category_change(record)
            
            # 统计其他操作
            if '标记为垃圾' in action:
                self.correction_stats['spam_count'] = \
                    self.correction_stats.get('spam_count', 0) + 1
            elif '保持分类' in action:
                self.correction_stats['confirmed_count'] = \
                    self.correction_stats.get('confirmed_count', 0) + 1
        
        return self._generate_analysis_report()
    
    def _extract_category_change(self, record: Dict):
        """提取分类变更信息"""
        action = record.get('action', '')
        title = record.get('title', '')
        
        # 解析 "修改分类: old → new" 格式
        if '→' in action:
            parts = action.split('→')
            if len(parts) == 2:
                old_cat = parts[0].split(':')[-1].strip()
                new_cat = parts[1].strip()
                
                self.correction_stats['total_corrections'] += 1
                self.correction_stats['by_original_category'][old_cat] += 1
                self.correction_stats['by_new_category'][new_cat] += 1
                
                transition = f"{old_cat} → {new_cat}"
                self.correction_stats['category_transitions'][transition] += 1
                
                # 记录标题模式
                self.review_patterns[transition].append(title)
    
    def _generate_analysis_report(self) -> Dict:
        """生成分析报告"""
        return {
            'total_reviews': self.correction_stats.get('total_corrections', 0) + \
                           self.correction_stats.get('confirmed_count', 0) + \
                           self.correction_stats.get('spam_count', 0),
            'corrections': self.correction_stats['total_corrections'],
            'confirmations': self.correction_stats.get('confirmed_count', 0),
            'spam_removed': self.correction_stats.get('spam_count', 0),
            'most_corrected_from': self._get_top_items(self.correction_stats['by_original_category']),
            'most_corrected_to': self._get_top_items(self.correction_stats['by_new_category']),
            'common_transitions': self._get_top_items(self.correction_stats['category_transitions'])
        }
    
    def _get_top_items(self, counter_dict: Dict, top_n: int = 3) -> List[Tuple[str, int]]:
        """获取前N个最常见的项"""
        return sorted(counter_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def extract_keyword_patterns(self, reviewed_items: List[Dict]) -> Dict[str, List[str]]:
        """
        从审核后的数据中提取关键词模式
        
        Args:
            reviewed_items: 审核后的内容列表
            
        Returns:
            各分类的特征关键词
        """
        print("\n🔍 正在提取关键词模式...")
        
        category_keywords = defaultdict(lambda: defaultdict(int))
        
        for item in reviewed_items:
            if not item.get('manually_reviewed'):
                continue
            
            category = item.get('content_type')
            text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
            
            # 提取关键词（简单的词频统计）
            words = re.findall(r'\b\w{3,}\b', text)  # 至少3个字符的单词
            
            for word in words:
                if word not in ['the', 'and', 'for', 'with', 'from', 'that', 'this']:
                    category_keywords[category][word] += 1
        
        # 为每个分类找出最具代表性的关键词
        representative_keywords = {}
        for category, words in category_keywords.items():
            # 选择频率最高的前10个词
            top_words = sorted(words.items(), key=lambda x: x[1], reverse=True)[:10]
            representative_keywords[category] = [word for word, count in top_words]
        
        return representative_keywords
    
    def generate_weight_adjustments(self, analysis: Dict) -> Dict[str, Dict[str, float]]:
        """
        根据分析结果生成权重调整建议
        
        Args:
            analysis: 分析报告
            
        Returns:
            权重调整建议
        """
        print("\n⚙️ 生成权重调整建议...")
        
        adjustments = {
            'category_thresholds': {},
            'keyword_boosts': {},
            'confidence_adjustments': {}
        }
        
        # 分析常见错误转换
        common_transitions = analysis.get('common_transitions', [])
        
        for transition, count in common_transitions:
            if ' → ' in transition:
                old_cat, new_cat = transition.split(' → ')
                
                # 如果某个分类经常被改为另一个，说明分类阈值可能需要调整
                if count >= 3:
                    adjustments['category_thresholds'][old_cat] = {
                        'issue': f'经常被修改为 {new_cat}',
                        'suggestion': '考虑降低该分类的权重或提高阈值',
                        'frequency': count
                    }
        
        # 分析最常被纠正的分类
        most_corrected = analysis.get('most_corrected_from', [])
        for category, count in most_corrected:
            if count >= 5:
                adjustments['confidence_adjustments'][category] = {
                    'issue': f'该分类有 {count} 次被修正',
                    'suggestion': '该分类可能需要更严格的判定条件',
                    'recommended_action': '增加关键词权重或添加更多特征'
                }
        
        return adjustments
    
    def apply_learning(self, classifier, reviewed_items: List[Dict], 
                      auto_apply: bool = False) -> Dict:
        """
        将学习成果应用到分类器
        
        Args:
            classifier: ContentClassifier实例
            reviewed_items: 审核后的数据
            auto_apply: 是否自动应用（否则只生成建议）
            
        Returns:
            应用结果报告
        """
        print("\n🎓 正在应用学习成果...")
        
        # 提取关键词模式
        patterns = self.extract_keyword_patterns(reviewed_items)
        
        # 生成改进建议
        suggestions = []
        
        for category, keywords in patterns.items():
            # 找出当前分类器中没有的高频关键词
            current_keywords = self._get_classifier_keywords(classifier, category)
            new_keywords = [kw for kw in keywords if kw not in current_keywords]
            
            if new_keywords:
                suggestions.append({
                    'category': category,
                    'type': 'add_keywords',
                    'keywords': new_keywords[:5],  # 建议添加前5个
                    'reason': f'在人工审核的 {category} 类内容中高频出现'
                })
        
        # 分析错误模式
        error_patterns = self._analyze_error_patterns(reviewed_items)
        suggestions.extend(error_patterns)
        
        self.improvement_suggestions = suggestions
        
        if auto_apply:
            print("⚠️  自动应用功能需要重启程序才能生效")
            print("当前版本将建议保存到文件中，供手动审查")
        
        return {
            'suggestions_count': len(suggestions),
            'suggestions': suggestions,
            'patterns': patterns
        }
    
    def _get_classifier_keywords(self, classifier, category: str) -> set:
        """获取分类器当前使用的关键词"""
        keyword_map = {
            'research': classifier.research_keywords,
            'developer': classifier.developer_keywords,
            'product': classifier.product_keywords,
            'market': classifier.market_keywords,
            'leader': classifier.leader_keywords
        }
        
        keywords_dict = keyword_map.get(category, {})
        return set(keywords_dict.keys()) if isinstance(keywords_dict, dict) else set(keywords_dict)
    
    def _analyze_error_patterns(self, reviewed_items: List[Dict]) -> List[Dict]:
        """分析常见错误模式"""
        patterns = []
        
        # 统计低置信度但被确认的情况
        low_conf_confirmed = [
            item for item in reviewed_items
            if item.get('manually_reviewed') and 
               item.get('confidence', 1.0) < 0.6 and
               not ('修改分类' in str(item.get('reviewed_action', '')))
        ]
        
        if len(low_conf_confirmed) >= 3:
            patterns.append({
                'type': 'threshold_adjustment',
                'issue': f'{len(low_conf_confirmed)} 条低置信度内容被确认为正确分类',
                'suggestion': '考虑降低置信度阈值要求或调整关键词权重',
                'affected_items': len(low_conf_confirmed)
            })
        
        # 统计高置信度但被修改的情况
        high_conf_corrected = [
            item for item in reviewed_items
            if item.get('manually_reviewed') and 
               item.get('original_confidence', 1.0) > 0.7 and
               '修改分类' in str(item.get('reviewed_action', ''))
        ]
        
        if len(high_conf_corrected) >= 2:
            patterns.append({
                'type': 'false_positive',
                'issue': f'{len(high_conf_corrected)} 条高置信度内容被修正',
                'suggestion': '存在系统性误判，需要检查分类规则',
                'severity': 'high',
                'affected_items': len(high_conf_corrected)
            })
        
        return patterns
    
    def save_learning_report(self, filename: str = None):
        """保存学习报告"""
        if not filename:
            filename = f"learning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'correction_stats': dict(self.correction_stats),
            'improvement_suggestions': self.improvement_suggestions,
            'summary': {
                'total_suggestions': len(self.improvement_suggestions),
                'high_priority': len([s for s in self.improvement_suggestions 
                                     if s.get('severity') == 'high']),
                'keyword_additions': len([s for s in self.improvement_suggestions 
                                         if s.get('type') == 'add_keywords'])
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 学习报告已保存到: {filename}")
        return filename
    
    def print_learning_summary(self, analysis: Dict, learning_result: Dict):
        """打印学习摘要"""
        print("\n" + "="*70)
        print("🎓 学习反馈摘要")
        print("="*70)
        
        print(f"\n📊 审核统计:")
        print(f"   总审核数: {analysis.get('total_reviews', 0)}")
        print(f"   修正次数: {analysis.get('corrections', 0)}")
        print(f"   确认次数: {analysis.get('confirmations', 0)}")
        print(f"   删除垃圾: {analysis.get('spam_removed', 0)}")
        
        print(f"\n🔄 常见修正:")
        for transition, count in analysis.get('common_transitions', [])[:3]:
            print(f"   {transition}: {count} 次")
        
        print(f"\n💡 改进建议: {learning_result.get('suggestions_count', 0)} 条")
        
        for i, suggestion in enumerate(learning_result.get('suggestions', [])[:5], 1):
            print(f"\n   建议 {i}:")
            print(f"   - 类型: {suggestion.get('type')}")
            if suggestion.get('category'):
                print(f"   - 分类: {suggestion.get('category')}")
            print(f"   - 建议: {suggestion.get('suggestion', suggestion.get('reason'))}")
            if suggestion.get('keywords'):
                print(f"   - 关键词: {', '.join(suggestion['keywords'][:3])}...")
        
        if learning_result.get('suggestions_count', 0) > 5:
            print(f"\n   ... 还有 {learning_result['suggestions_count'] - 5} 条建议（详见报告文件）")
        
        print("\n" + "="*70)


def create_feedback_loop(review_history_file: str, 
                        reviewed_data_file: str,
                        classifier) -> str:
    """
    完整的反馈学习流程
    
    Args:
        review_history_file: 审核历史文件路径
        reviewed_data_file: 审核后数据文件路径
        classifier: ContentClassifier实例
        
    Returns:
        学习报告文件路径
    """
    print("\n🔄 启动学习反馈循环...")
    
    # 加载审核历史
    with open(review_history_file, 'r', encoding='utf-8') as f:
        review_history = json.load(f)
    
    # 加载审核后的数据
    with open(reviewed_data_file, 'r', encoding='utf-8') as f:
        reviewed_data = json.load(f)
        reviewed_items = reviewed_data.get('data', [])
    
    # 创建学习系统
    learner = LearningFeedback()
    
    # 分析审核历史
    analysis = learner.analyze_review_history(review_history)
    
    # 应用学习
    learning_result = learner.apply_learning(classifier, reviewed_items)
    
    # 生成权重调整建议
    adjustments = learner.generate_weight_adjustments(analysis)
    learning_result['weight_adjustments'] = adjustments
    
    # 保存报告
    report_file = learner.save_learning_report()
    
    # 打印摘要
    learner.print_learning_summary(analysis, learning_result)
    
    return report_file


if __name__ == "__main__":
    print("🎓 学习反馈系统")
    print("="*70)
    print("\n该模块从人工审核结果中学习，优化分类模型。")
    print("\n使用方法:")
    print("  1. 完成人工审核（会生成审核历史文件）")
    print("  2. 调用 create_feedback_loop() 分析学习")
    print("  3. 查看生成的学习报告")
    print("  4. 根据建议优化分类器配置")
    print("\n示例:")
    print("  from learning_feedback import create_feedback_loop")
    print("  from content_classifier import ContentClassifier")
    print("  ")
    print("  classifier = ContentClassifier()")
    print("  report = create_feedback_loop(")
    print("      'review_history_xxx.json',")
    print("      'ai_tracker_data_reviewed_xxx.json',")
    print("      classifier")
    print("  )")
