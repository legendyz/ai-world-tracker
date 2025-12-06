"""
智能分析模块 - AI Analyzer
使用AI进行内容摘要和趋势分析
"""

from typing import List, Dict
from collections import Counter
from datetime import datetime
import os


class AIAnalyzer:
    """AI内容智能分析器"""
    
    def __init__(self, api_key: str = None):
        """
        初始化分析器
        
        Args:
            api_key: OpenAI API密钥（可选）
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.use_ai = bool(self.api_key)
        
        if not self.use_ai:
            print("⚠️ 未提供OpenAI API密钥，将使用规则基础的分析方法")
    
    def generate_summary(self, item: Dict) -> str:
        """
        生成内容摘要
        
        Args:
            item: 内容项
            
        Returns:
            摘要文本
        """
        if self.use_ai:
            return self._generate_ai_summary(item)
        else:
            return self._generate_rule_based_summary(item)
    
    def _generate_ai_summary(self, item: Dict) -> str:
        """使用AI生成摘要（需要API密钥）"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            title = item.get('title', '')
            summary = item.get('summary', item.get('description', ''))
            content = f"标题: {title}\n内容: {summary}"
            prompt = f"请总结以下内容（不超过100字）：\n{content}"
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个AI资讯分析助手，请用简洁的中文总结AI相关内容的要点。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ AI摘要生成失败: {e}，使用规则方法")
            return self._generate_rule_based_summary(item)
    
    def _generate_rule_based_summary(self, item: Dict) -> str:
        """使用规则生成摘要"""
        summary = item.get('summary', item.get('description', ''))
        if len(summary) > 150:
            summary = summary[:150] + '...'
        return summary
    
    def analyze_trends(self, items: List[Dict]) -> Dict:
        """
        分析内容趋势
        
        Args:
            items: 分类后的内容列表
            
        Returns:
            趋势分析结果
        """
        print("\n📊 正在分析AI趋势...")
        
        # 技术热点统计
        tech_counter = Counter()
        for item in items:
            for category in item.get('tech_categories', []):
                tech_counter[category] += 1
        
        # 内容类型分布
        type_counter = Counter(item.get('content_type', 'market') for item in items)
        
        # 地区分布
        region_counter = Counter(item.get('region', 'Global') for item in items)
        
        # 来源统计
        source_counter = Counter(item.get('source', 'Unknown') for item in items)
        
        # 时间趋势（按日期）
        date_counter = Counter()
        for item in items:
            date = item.get('published', item.get('updated', ''))
            if date:
                date_key = date[:10] if len(date) >= 10 else date
                date_counter[date_key] += 1
        
        trends = {
            'tech_hotspots': dict(tech_counter.most_common(10)),
            'content_distribution': dict(type_counter),
            'region_distribution': dict(region_counter),
            'source_distribution': dict(source_counter),
            'daily_trends': dict(sorted(date_counter.items())[-7:]),  # 最近7天
            'total_items': len(items),
            'analysis_time': datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
        }
        
        self._print_trends(trends)
        
        return trends
    
    def _print_trends(self, trends: Dict):
        """打印趋势分析结果"""
        print("\n✨ 趋势分析完成！\n")
        
        print("🔥 技术热点 TOP 5:")
        for tech, count in list(trends['tech_hotspots'].items())[:5]:
            bar = '█' * (count * 2)
            print(f"   {tech:20s} {bar} {count}")
        
        print("\n📈 内容类型分布:")
        for ctype, count in trends['content_distribution'].items():
            print(f"   {ctype:15s}: {count} 条")
        
        print("\n🌍 地区分布:")
        for region, count in trends['region_distribution'].items():
            print(f"   {region:15s}: {count} 条")
    
    def get_top_items(self, items: List[Dict], category: str = 'tech_categories', top_n: int = 5) -> List[Dict]:
        """
        获取热门内容
        
        Args:
            items: 内容列表
            category: 分类维度
            top_n: 返回数量
            
        Returns:
            热门内容列表
        """
        # 简单按来源和类型排序
        sorted_items = sorted(items, 
                            key=lambda x: (x.get('source', ''), x.get('published', '')), 
                            reverse=True)
        return sorted_items[:top_n]
    
    def generate_report(self, items: List[Dict], trends: Dict) -> str:
        """
        生成分析报告
        
        Args:
            items: 内容列表
            trends: 趋势数据
            
        Returns:
            报告文本
        """
        report = []
        report.append("="*60)
        report.append("AI World Tracker - 分析报告")
        report.append("="*60)
        report.append(f"\n生成时间: {trends['analysis_time']}")
        report.append(f"数据总量: {trends['total_items']} 条\n")
        
        report.append("\n【技术热点】")
        for tech, count in list(trends['tech_hotspots'].items())[:5]:
            report.append(f"  • {tech}: {count} 条")
        
        report.append("\n【内容分布】")
        for ctype, count in trends['content_distribution'].items():
            percentage = (count / trends['total_items'] * 100) if trends['total_items'] > 0 else 0
            report.append(f"  • {ctype}: {count} 条 ({percentage:.1f}%)")
        
        report.append("\n【地区分布】")
        for region, count in trends['region_distribution'].items():
            report.append(f"  • {region}: {count} 条")
        
        report.append("\n【热门内容】")
        top_items = self.get_top_items(items, top_n=3)
        for i, item in enumerate(top_items, 1):
            report.append(f"\n  {i}. {item.get('title', 'No title')}")
            report.append(f"     来源: {item.get('source', 'Unknown')} | 类型: {item.get('content_type', 'N/A')}")
        
        report.append("\n" + "="*60)
        
        return "\n".join(report)


if __name__ == "__main__":
    # 测试示例
    analyzer = AIAnalyzer()
    
    test_items = [
        {
            'title': 'GPT-5 Released',
            'summary': 'OpenAI releases GPT-5 with multimodal capabilities',
            'content_type': 'product',
            'tech_categories': ['NLP', 'Generative AI'],
            'region': 'USA',
            'source': 'TechCrunch',
            'published': '2025-11-30'
        },
        {
            'title': 'Transformer Research Breakthrough',
            'summary': 'New paper on efficient attention mechanisms',
            'content_type': 'research',
            'tech_categories': ['NLP'],
            'region': 'Global',
            'source': 'arXiv',
            'published': '2025-11-29'
        },
        {
            'title': '百度AI获融资',
            'summary': '百度完成新一轮AI投资',
            'content_type': 'market',
            'tech_categories': ['General AI'],
            'region': 'China',
            'source': '中国科技',
            'published': '2025-11-28'
        }
    ]
    
    trends = analyzer.analyze_trends(test_items)
    report = analyzer.generate_report(test_items, trends)
    print("\n" + report)
