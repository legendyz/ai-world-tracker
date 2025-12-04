"""
AI World Tracker - MVP版本
全球AI研究、产品、市场动态追踪应用

主要功能:
1. 数据采集模块 - 从arXiv、GitHub、RSS等源采集AI资讯
2. 内容分类系统 - 自动分类为研究/产品/市场维度
3. 智能分析功能 - 生成趋势分析和洞察报告
4. 数据可视化 - 生成各类图表展示数据

作者: AI World Tracker Team
日期: 2025-12-01
"""

import sys
import json
import os
from datetime import datetime
from typing import Optional

# 导入自定义模块
from data_collector import DataCollector
from content_classifier import ContentClassifier
from ai_analyzer import AIAnalyzer
from visualizer import DataVisualizer
from web_publisher import WebPublisher
from manual_reviewer import ManualReviewer
from learning_feedback import LearningFeedback, create_feedback_loop


class AIWorldTracker:
    """AI世界追踪器主应用"""
    
    def __init__(self):
        print("\n" + "="*60)
        print("     🌍 AI World Tracker - MVP 版本")
        print("     全球人工智能动态追踪系统")
        print("="*60 + "\n")
        
        self.collector = DataCollector()
        self.classifier = ContentClassifier()
        self.analyzer = AIAnalyzer()
        self.visualizer = DataVisualizer()
        self.web_publisher = WebPublisher()
        self.reviewer = ManualReviewer()
        self.learner = LearningFeedback()
        
        self.data = []
        self.trends = {}
        self.chart_files = {}
        
        # 尝试加载最新数据
        self._load_latest_data()
    
    def _load_latest_data(self):
        """尝试加载最新的数据文件"""
        try:
            files = [f for f in os.listdir('.') if f.startswith('ai_tracker_data_') and f.endswith('.json')]
            if not files:
                return
            
            latest_file = max(files)
            print(f"📥 发现历史数据，正在加载: {latest_file}...")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                
            self.data = saved_data.get('data', [])
            self.trends = saved_data.get('trends', {})
            
            # 尝试加载图表文件
            if os.path.exists('visualizations'):
                self.chart_files = {
                    'tech_hotspots': os.path.join('visualizations', 'tech_hotspots.png'),
                    'content_distribution': os.path.join('visualizations', 'content_distribution.png'),
                    'region_distribution': os.path.join('visualizations', 'region_distribution.png'),
                    'daily_trends': os.path.join('visualizations', 'daily_trends.png'),
                    'dashboard': os.path.join('visualizations', 'dashboard.png')
                }
                # 验证文件是否存在
                self.chart_files = {k: v for k, v in self.chart_files.items() if os.path.exists(v)}
            
            print(f"✅ 已加载 {len(self.data)} 条历史数据")
        except Exception as e:
            print(f"⚠️ 加载历史数据失败: {e}")
    
    def run_full_pipeline(self):
        """运行完整数据处理流程"""
        print("🚀 启动完整数据处理流程...\n")
        
        # 步骤1: 数据采集
        print("【步骤 1/4】数据采集")
        raw_data = self.collector.collect_all()
        
        # 合并所有数据
        all_items = []
        for category, items in raw_data.items():
            all_items.extend(items)
        
        print(f"\n📦 共采集 {len(all_items)} 条原始数据\n")
        
        # 步骤2: 内容分类
        print("【步骤 2/4】内容分类")
        self.data = self.classifier.classify_batch(all_items)
        
        # 步骤3: 智能分析
        print("\n【步骤 3/4】智能分析")
        self.trends = self.analyzer.analyze_trends(self.data)
        
        # 步骤4: 数据可视化
        print("\n【步骤 4/4】数据可视化")
        self.chart_files = self.visualizer.visualize_all(self.trends)
        
        # 步骤5: 生成Web页面
        print("\n【步骤 5/5】生成Web页面")
        web_file = self.web_publisher.generate_html_page(self.data, self.trends, self.chart_files)
        
        # 生成报告
        report = self.analyzer.generate_report(self.data, self.trends)
        
        # 保存数据和报告
        self._save_results(report, web_file)
        
        print("\n" + "="*60)
        print("✨ 处理完成！")
        print("="*60)
        print(f"\n📊 已生成 {len([f for f in self.chart_files.values() if f])} 个可视化图表")
        print(f"📄 分析报告已保存")
        print(f"💾 数据已保存到 JSON 文件")
        print(f"🌐 Web页面已生成\n")
        
        return report
    
    def show_menu(self):
        """显示交互菜单"""
        while True:
            print("\n" + "="*60)
            print("📋 主菜单")
            print("="*60)
            print("1. 🚀 一键更新数据与报告 (Update & Generate All)")
            print("2. 📄 查看分析报告 (View Report)")
            print("3. 🔍 搜索与筛选 (Search & Filter)")
            print("4. 🌐 生成并打开 Web 页面 (Generate & Open Web Page)")
            print("5. 📝 人工审核分类 (Manual Review) ⭐ 新功能")
            print("6. 🎓 学习反馈分析 (Learning Feedback) ⭐ 新功能")
            print("0. 退出程序")
            print("="*60)
            
            choice = input("\n请选择功能 (0-6): ").strip()
            
            if choice == '1':
                self.run_full_pipeline()
            elif choice == '2':
                self._show_report()
            elif choice == '3':
                self._filter_data()
            elif choice == '4':
                self._generate_web_page()
            elif choice == '5':
                self._manual_review()
            elif choice == '6':
                self._learning_feedback()
            elif choice == '0':
                print("\n👋 感谢使用 AI World Tracker！再见！\n")
                break
            else:
                print("\n❌ 无效选择，请重试")
    
    def _collect_only(self):
        """仅采集数据"""
        print("\n🔄 开始数据采集...\n")
        raw_data = self.collector.collect_all()
        
        all_items = []
        for items in raw_data.values():
            all_items.extend(items)
        
        self.data = self.classifier.classify_batch(all_items)
        print(f"\n✅ 采集并分类完成！共 {len(self.data)} 条数据")
    
    def _show_statistics(self):
        """显示数据统计"""
        if not self.data:
            print("\n⚠️ 暂无数据，请先运行数据采集")
            return
        
        print("\n📊 数据统计概览:")
        print(f"   总数据量: {len(self.data)} 条")
        
        # 内容类型统计
        type_count = {}
        for item in self.data:
            ct = item.get('content_type', 'unknown')
            type_count[ct] = type_count.get(ct, 0) + 1
        
        print("\n   内容类型:")
        for ctype, count in type_count.items():
            print(f"   - {ctype}: {count} 条")
        
        # 地区统计
        region_count = {}
        for item in self.data:
            region = item.get('region', 'unknown')
            region_count[region] = region_count.get(region, 0) + 1
        
        print("\n   地区分布:")
        for region, count in region_count.items():
            print(f"   - {region}: {count} 条")
    
    def _generate_visualizations(self):
        """生成可视化图表"""
        if not self.data:
            print("\n⚠️ 暂无数据，请先运行数据采集")
            return
        
        if not self.trends:
            print("\n🔄 正在分析数据...")
            self.trends = self.analyzer.analyze_trends(self.data)
        
        print("\n🎨 正在生成可视化图表...")
        self.chart_files = self.visualizer.visualize_all(self.trends)
    
    def _show_report(self):
        """显示分析报告"""
        if not self.data:
            print("\n⚠️ 暂无数据，请先运行数据采集")
            return
        
        if not self.trends:
            print("\n🔄 正在生成分析...")
            self.trends = self.analyzer.analyze_trends(self.data)
        
        report = self.analyzer.generate_report(self.data, self.trends)
        print("\n" + report)
    
    def _filter_data(self):
        """按条件筛选数据"""
        if not self.data:
            print("\n⚠️ 暂无数据，请先运行数据采集")
            return
        
        print("\n🔍 数据筛选:")
        print("1. 按内容类型 (research/product/market)")
        print("2. 按地区 (China/USA/Europe/Global)")
        print("3. 按技术领域")
        
        filter_choice = input("\n选择筛选方式 (1-3): ").strip()
        
        if filter_choice == '1':
            ctype = input("输入内容类型 (research/product/market): ").strip()
            filtered = self.classifier.get_filtered_items(self.data, content_type=ctype)
        elif filter_choice == '2':
            region = input("输入地区 (China/USA/Europe/Global): ").strip()
            filtered = self.classifier.get_filtered_items(self.data, region=region)
        elif filter_choice == '3':
            tech = input("输入技术领域 (如: NLP, Computer Vision): ").strip()
            filtered = self.classifier.get_filtered_items(self.data, tech_category=tech)
        else:
            print("❌ 无效选择")
            return
        
        print(f"\n✅ 筛选结果: {len(filtered)} 条数据\n")
        
        # 显示前5条
        for i, item in enumerate(filtered[:5], 1):
            print(f"{i}. {item.get('title', 'No title')}")
            print(f"   类型: {item.get('content_type')} | 地区: {item.get('region')}")
            print(f"   来源: {item.get('source')} | 日期: {item.get('published', 'N/A')}\n")
        
        if len(filtered) > 5:
            print(f"   ... 还有 {len(filtered) - 5} 条结果")
    
    def _generate_web_page(self):
        """生成Web页面"""
        if not self.data:
            print("\n⚠️ 暂无数据，请先运行数据采集")
            return
        
        if not self.trends:
            print("\n🔄 正在生成分析...")
            self.trends = self.analyzer.analyze_trends(self.data)
        
        if not self.chart_files:
            print("\n🎨 正在生成图表...")
            self.chart_files = self.visualizer.visualize_all(self.trends)
        
        print("\n🌐 正在生成Web页面...")
        web_file = self.web_publisher.generate_html_page(self.data, self.trends, self.chart_files)
        
        # 询问是否在浏览器中打开
        try:
            import webbrowser
            choice = input("\n是否在浏览器中打开Web页面? (Y/N): ").strip().lower()
            if choice in ['y', 'yes', '是']:
                webbrowser.open(f'file://{os.path.abspath(web_file)}')
                print("🚀 已在浏览器中打开Web页面")
        except Exception as e:
            print(f"⚠️ 无法自动打开浏览器: {e}")
            print(f"请手动打开文件: {os.path.abspath(web_file)}")
    
    def _manual_review(self):
        """人工审核分类"""
        if not self.data:
            print("\n⚠️ 暂无数据，请先运行数据采集")
            return
        
        print("\n" + "="*60)
        print("📝 人工审核模式")
        print("="*60)
        
        # 检查需要审核的内容
        review_items = self.reviewer.get_items_for_review(self.data, min_confidence=0.6)
        
        print(f"\n📊 数据统计:")
        print(f"   总内容数: {len(self.data)} 条")
        print(f"   需要审核: {len(review_items)} 条 ({len(review_items)/len(self.data):.1%})")
        
        if not review_items:
            print("\n✅ 所有内容分类置信度都很高，无需审核！")
            return
        
        # 显示需要审核的内容概览
        print("\n需要审核的内容:")
        for i, item in enumerate(review_items[:5], 1):
            print(f"   {i}. {item.get('title', 'N/A')[:50]}... (置信度: {item.get('confidence', 0):.1%})")
        
        if len(review_items) > 5:
            print(f"   ... 还有 {len(review_items)-5} 条")
        
        print("\n审核选项:")
        print("   1. 批量审核所有低置信度内容")
        print("   2. 设置自定义置信度阈值")
        print("   3. 仅查看需要审核的内容列表")
        print("   0. 返回主菜单")
        
        choice = input("\n请选择 (0-3): ").strip()
        
        if choice == '1':
            # 批量审核
            self.data = self.reviewer.batch_review(self.data, min_confidence=0.6)
            
            # 保存审核后的数据
            save = input("\n是否保存审核后的数据? (Y/N): ").strip().lower()
            if save == 'y':
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'ai_tracker_data_reviewed_{timestamp}.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        'metadata': {
                            'timestamp': timestamp,
                            'total_items': len(self.data),
                            'reviewed': True
                        },
                        'data': self.data,
                        'trends': self.trends
                    }, f, ensure_ascii=False, indent=2)
                print(f"✅ 已保存到: {filename}")
            
            # 保存审核历史
            self.reviewer.save_review_history()
            
            # 显示审核摘要
            summary = self.reviewer.get_review_summary()
            print(f"\n📊 审核摘要:")
            print(f"   总审核数: {summary['total']} 条")
            for action, count in summary['actions'].items():
                print(f"   - {action}: {count} 次")
            
            # 询问是否重新生成分析和Web页面
            print("\n" + "="*60)
            regenerate = input("\n是否基于审核后的数据重新生成报告和Web页面? (Y/N): ").strip().lower()
            if regenerate == 'y':
                self._regenerate_after_review()
        
        elif choice == '2':
            # 自定义阈值
            try:
                threshold = float(input("\n请输入置信度阈值 (0.0-1.0, 如 0.7): ").strip())
                if 0 <= threshold <= 1:
                    self.data = self.reviewer.batch_review(self.data, min_confidence=threshold)
                else:
                    print("❌ 阈值必须在 0.0-1.0 之间")
            except ValueError:
                print("❌ 无效输入")
        
        elif choice == '3':
            # 仅查看列表
            print("\n" + "="*70)
            print("需要审核的内容列表:")
            print("="*70)
            for i, item in enumerate(review_items, 1):
                print(f"\n[{i}] {item.get('title', 'N/A')}")
                print(f"    分类: {item.get('content_type')} | 置信度: {item.get('confidence', 0):.1%}")
                print(f"    来源: {item.get('source', 'N/A')}")
        
        elif choice == '0':
            return
        else:
            print("❌ 无效选择")
    
    def _regenerate_after_review(self):
        """审核后重新生成分析和Web页面"""
        print("\n" + "="*60)
        print("🔄 重新生成报告和可视化")
        print("="*60)
        
        try:
            # 步骤1: 重新分析
            print("\n【1/3】重新分析趋势...")
            self.trends = self.analyzer.analyze_trends(self.data)
            
            # 步骤2: 重新生成图表
            print("【2/3】重新生成图表...")
            self.chart_files = self.visualizer.visualize_all(self.trends)
            
            # 步骤3: 重新生成Web页面
            print("【3/3】重新生成Web页面...")
            web_file = self.web_publisher.generate_html_page(self.data, self.trends, self.chart_files)
            
            # 生成报告
            report = self.analyzer.generate_report(self.data, self.trends)
            
            # 保存（使用reviewed标记）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            data_file = f'ai_tracker_data_reviewed_{timestamp}.json'
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'timestamp': timestamp,
                        'total_items': len(self.data),
                        'reviewed': True
                    },
                    'data': self.data,
                    'trends': self.trends
                }, f, ensure_ascii=False, indent=2)
            
            report_file = f'ai_tracker_report_reviewed_{timestamp}.txt'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print("\n✅ 重新生成完成！")
            print(f"   数据文件: {data_file}")
            print(f"   报告文件: {report_file}")
            print(f"   Web页面: {web_file}")
            
            # 询问是否打开
            import webbrowser
            choice = input("\n是否在浏览器中打开更新后的Web页面? (Y/N): ").strip().lower()
            if choice == 'y':
                webbrowser.open(f'file://{os.path.abspath(web_file)}')
                print("🚀 已在浏览器中打开")
        
        except Exception as e:
            print(f"\n❌ 重新生成失败: {e}")
    
    def _learning_feedback(self):
        """学习反馈分析"""
        print("\n" + "="*60)
        print("🎓 学习反馈系统")
        print("="*60)
        
        # 查找审核历史文件和审核后数据文件
        import glob
        
        review_files = sorted(glob.glob('review_history_*.json'), reverse=True)
        data_files = sorted(glob.glob('ai_tracker_data_reviewed_*.json'), reverse=True)
        
        if not review_files:
            print("\n⚠️ 未找到审核历史文件")
            print("请先完成人工审核（菜单选项5）")
            return
        
        if not data_files:
            print("\n⚠️ 未找到审核后的数据文件")
            print("请先完成人工审核并保存数据")
            return
        
        print(f"\n📁 找到审核记录:")
        print(f"   审核历史: {len(review_files)} 个文件")
        print(f"   审核数据: {len(data_files)} 个文件")
        
        # 显示最近的文件
        print(f"\n最近的审核:")
        for i, (review_file, data_file) in enumerate(zip(review_files[:3], data_files[:3]), 1):
            print(f"   {i}. {review_file}")
        
        print("\n选项:")
        print("   1. 分析最近一次审核")
        print("   2. 选择特定审核文件")
        print("   0. 返回")
        
        choice = input("\n请选择 (0-2): ").strip()
        
        if choice == '1':
            # 分析最近一次
            review_file = review_files[0]
            data_file = data_files[0]
            
            print(f"\n📊 正在分析: {review_file}")
            
            try:
                report_file = create_feedback_loop(
                    review_file,
                    data_file,
                    self.classifier
                )
                
                print(f"\n✅ 学习分析完成！")
                print(f"详细报告已保存到: {report_file}")
                
                # 询问是否查看建议
                view = input("\n是否查看改进建议? (Y/N): ").strip().lower()
                if view == 'y':
                    self._show_improvement_suggestions(report_file)
                
            except Exception as e:
                print(f"\n❌ 分析失败: {e}")
        
        elif choice == '2':
            # 选择特定文件
            print("\n可用的审核历史文件:")
            for i, file in enumerate(review_files, 1):
                print(f"   {i}. {file}")
            
            try:
                idx = int(input("\n选择文件编号: ").strip()) - 1
                if 0 <= idx < len(review_files):
                    review_file = review_files[idx]
                    data_file = data_files[idx] if idx < len(data_files) else data_files[0]
                    
                    report_file = create_feedback_loop(
                        review_file,
                        data_file,
                        self.classifier
                    )
                    
                    print(f"\n✅ 学习分析完成！报告: {report_file}")
                else:
                    print("❌ 无效选择")
            except (ValueError, IndexError) as e:
                print(f"❌ 输入错误: {e}")
        
        elif choice == '0':
            return
        else:
            print("❌ 无效选择")
    
    def _show_improvement_suggestions(self, report_file: str):
        """显示改进建议"""
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            suggestions = report.get('improvement_suggestions', [])
            
            if not suggestions:
                print("\n✅ 当前分类器表现良好，暂无改进建议")
                return
            
            print("\n" + "="*70)
            print("💡 改进建议详情")
            print("="*70)
            
            for i, sug in enumerate(suggestions, 1):
                print(f"\n建议 {i}:")
                print(f"   类型: {sug.get('type')}")
                
                if sug.get('category'):
                    print(f"   分类: {sug.get('category')}")
                
                if sug.get('issue'):
                    print(f"   问题: {sug.get('issue')}")
                
                if sug.get('suggestion'):
                    print(f"   建议: {sug.get('suggestion')}")
                
                if sug.get('keywords'):
                    print(f"   建议添加关键词: {', '.join(sug['keywords'])}")
                
                if sug.get('severity'):
                    print(f"   严重程度: {sug.get('severity')}")
            
            print("\n" + "="*70)
            print("📝 说明:")
            print("   这些建议基于人工审核结果自动生成")
            print("   可以手动编辑 content_classifier.py 应用这些改进")
            print("="*70)
            
        except Exception as e:
            print(f"❌ 读取报告失败: {e}")
    
    def _save_results(self, report: str, web_file: Optional[str] = None):
        """保存结果到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON数据
        data_file = f'ai_tracker_data_{timestamp}.json'
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': timestamp,
                    'total_items': len(self.data)
                },
                'data': self.data,
                'trends': self.trends
            }, f, ensure_ascii=False, indent=2)
        
        print(f"💾 数据已保存: {data_file}")
        
        # 保存文本报告
        report_file = f'ai_tracker_report_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 报告已保存: {report_file}")
        
        if web_file:
            print(f"🌐 Web页面已生成: {web_file}")


def main():
    """主函数"""
    tracker = AIWorldTracker()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--auto':
            # 自动运行完整流程
            tracker.run_full_pipeline()
        elif sys.argv[1] == '--help':
            print("\nAI World Tracker - 使用说明")
            print("\n参数:")
            print("  --auto    自动运行完整流程")
            print("  --help    显示帮助信息")
            print("\n无参数:     进入交互式菜单\n")
    else:
        # 交互式菜单
        tracker.show_menu()


if __name__ == "__main__":
    main()
