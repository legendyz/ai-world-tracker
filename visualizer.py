"""
数据可视化模块 - Visualizer
生成各类图表展示AI趋势和数据
"""

import matplotlib
# 在导入 pyplot 之前设置后端为 Agg（非交互式），避免 CI 环境问题
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from typing import Dict, List
from datetime import datetime
import os
import platform

from i18n import t, get_language

# 配置中文字体支持
def configure_chinese_fonts():
    """配置中文字体支持"""
    import warnings
    # 忽略字体警告
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
    
    system = platform.system()
    
    if system == "Windows":
        # Windows 系统中文字体
        chinese_fonts = [
            'Microsoft YaHei',  # 微软雅黑
            'SimHei',           # 黑体
            'SimSun',           # 宋体
            'KaiTi',            # 楷体
            'FangSong',         # 仿宋
            'Arial Unicode MS'   # 备用字体
        ]
    elif system == "Darwin":  # macOS
        chinese_fonts = [
            'Heiti TC',
            'Arial Unicode MS',
            'PingFang SC',
            'Hiragino Sans GB'
        ]
    else:  # Linux
        chinese_fonts = [
            'DejaVu Sans',
            'WenQuanYi Micro Hei',
            'SimHei'
        ]
    
    # 检查可用字体
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    valid_fonts = []
    
    for font in chinese_fonts:
        if font in available_fonts:
            valid_fonts.append(font)
    
    # 如果没有找到中文字体，使用DejaVu Sans作为后备
    if not valid_fonts:
        valid_fonts = ['DejaVu Sans']
    
    # 设置matplotlib字体参数（多重保险）
    matplotlib.rcParams['font.sans-serif'] = valid_fonts
    matplotlib.rcParams['axes.unicode_minus'] = False
    matplotlib.rcParams['font.family'] = 'sans-serif'
    
    # 同时设置plt的参数
    plt.rcParams['font.sans-serif'] = valid_fonts
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.family'] = 'sans-serif'
    
    # 清除字体缓存（使用正确的API）
    try:
        fm.fontManager._rebuild()
    except (AttributeError, Exception):
        # 如果_rebuild不可用，使用其他方法
        pass
    
    print(t('vis_fonts_configured', fonts=str(valid_fonts)))
    return valid_fonts[0] if valid_fonts else 'DejaVu Sans'

# 初始化字体配置
configure_chinese_fonts()


class DataVisualizer:
    """数据可视化工具"""
    
    def __init__(self, output_dir: str = "visualizations"):
        """
        初始化可视化工具
        
        Args:
            output_dir: 图表输出目录
        """
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 确保字体配置
        self.default_font = configure_chinese_fonts()
        
    def _ensure_chinese_font(self):
        """确保中文字体设置正确"""
        import matplotlib
        import warnings
        # 忽略字体警告
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
        
        # 强制设置中文字体
        chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong']
        
        # 同时设置matplotlib和plt的参数
        matplotlib.rcParams['font.sans-serif'] = chinese_fonts
        matplotlib.rcParams['axes.unicode_minus'] = False
        matplotlib.rcParams['font.family'] = 'sans-serif'
        
        plt.rcParams['font.sans-serif'] = chinese_fonts
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.family'] = 'sans-serif'
        
        # 强制刷新字体缓存（安全方式）
        try:
            import matplotlib.font_manager as fm
            fm.fontManager._rebuild()
        except (AttributeError, Exception):
            pass
        
        # 设置样式
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except OSError:
            plt.style.use('default')
        self.colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']
    
    def plot_tech_hotspots(self, tech_data: Dict, save: bool = True) -> str:
        """
        绘制技术热点柱状图
        
        Args:
            tech_data: 技术领域数据
            save: 是否保存文件
            
        Returns:
            图表文件路径
        """
        self._ensure_chinese_font()  # 确保中文字体
        print(t('vis_gen_tech_chart'))
        
        if not tech_data:
            print(t('vis_no_tech_data'))
            return None
        
        # 准备数据
        techs = list(tech_data.keys())[:10]
        counts = [tech_data[t] for t in techs]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 设置字体属性
        font_family = self.default_font
        font_prop = {'family': font_family, 'size': 12}
        title_font = {'family': font_family, 'size': 14, 'weight': 'bold'}
        
        bars = ax.barh(techs, counts, color=self.colors[:len(techs)])
        
        ax.set_xlabel('Count', fontdict=font_prop)
        ax.set_title('AI Tech Hotspots', fontdict=title_font, pad=20)
        ax.grid(axis='x', alpha=0.3)
        
        # 添加数值标签
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count + 0.1, i, str(count), va='center', fontsize=10)
        
        plt.tight_layout()
        
        filepath = None
        if save:
            filepath = os.path.join(self.output_dir, 'tech_hotspots.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(t('vis_chart_saved', filepath=filepath))
        
        plt.close()
        return filepath
    
    def plot_content_distribution(self, content_data: Dict, save: bool = True) -> str:
        """
        绘制内容类型分布饼图
        
        Args:
            content_data: 内容类型数据
            save: 是否保存文件
            
        Returns:
            图表文件路径
        """
        self._ensure_chinese_font()  # 确保中文字体
        print(t('vis_gen_content_chart'))
        
        if not content_data:
            print(t('vis_no_content_data'))
            return None
        
        # 准备数据
        labels = list(content_data.keys())
        sizes = list(content_data.values())
        
        # 中英文标签映射
        label_map = {'research': 'Research', 'product': 'Product', 'market': 'Market'}
        labels = [label_map.get(l, l) for l in labels]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct='%1.1f%%',
            colors=self.colors[:len(labels)],
            startangle=90,
            textprops={'fontsize': 12}
        )
        
        # 美化百分比文字
        font_family = self.default_font
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontfamily(font_family)
            
        # 设置标签字体
        for text in texts:
            text.set_fontfamily(font_family)
        
        title_font = {'family': font_family, 'size': 14, 'weight': 'bold'}
        ax.set_title('Content Type Distribution', fontdict=title_font, pad=20)
        
        plt.tight_layout()
        
        filepath = None
        if save:
            filepath = os.path.join(self.output_dir, 'content_distribution.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(t('vis_chart_saved', filepath=filepath))
        
        plt.close()
        return filepath
    
    def plot_region_distribution(self, region_data: Dict, save: bool = True) -> str:
        """
        绘制地区分布对比图
        
        Args:
            region_data: 地区数据
            save: 是否保存文件
            
        Returns:
            图表文件路径
        """
        self._ensure_chinese_font()  # 确保中文字体
        print(t('vis_gen_region_chart'))
        
        if not region_data:
            print(t('vis_no_region_data'))
            return None
        
        # 准备数据
        regions = list(region_data.keys())
        counts = list(region_data.values())
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(regions, counts, color=self.colors[:len(regions)])
        
        # 使用中文字体设置
        font_family = self.default_font
        font_prop = {'family': font_family, 'size': 12}
        title_font = {'family': font_family, 'size': 14, 'weight': 'bold'}
        
        ax.set_ylabel('Count', fontdict=font_prop)
        ax.set_title('Regional Distribution', fontdict=title_font, pad=20)
        ax.grid(axis='y', alpha=0.3)
        
        # 添加数值标签
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(count)}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        
        filepath = None
        if save:
            filepath = os.path.join(self.output_dir, 'region_distribution.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(t('vis_chart_saved', filepath=filepath))
        
        plt.close()
        return filepath
    
    def plot_daily_trends(self, daily_data: Dict, save: bool = True) -> str:
        """
        绘制每日趋势折线图
        
        Args:
            daily_data: 每日数据
            save: 是否保存文件
            
        Returns:
            图表文件路径
        """
        self._ensure_chinese_font()  # 确保中文字体
        print(t('vis_gen_trend_chart'))
        
        if not daily_data or len(daily_data) < 2:
            print(t('vis_insufficient_data'))
            return None
        
        # 准备数据并排序
        dates = sorted(daily_data.keys())
        counts = [daily_data[d] for d in dates]
        
        # 简化日期显示
        date_labels = [d[5:] for d in dates]  # 只显示月-日
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(date_labels, counts, marker='o', linewidth=2, 
                markersize=8, color=self.colors[0])
        
        # 使用中文字体设置
        font_family = self.default_font
        font_prop = {'family': font_family, 'size': 12}
        title_font = {'family': font_family, 'size': 14, 'weight': 'bold'}
        
        ax.set_xlabel('Date', fontdict=font_prop)
        ax.set_ylabel('Item Count', fontdict=font_prop)
        ax.set_title('Daily Trends', fontdict=title_font, pad=20)
        ax.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, (label, count) in enumerate(zip(date_labels, counts)):
            ax.text(i, count + 0.5, str(count), ha='center', va='bottom', fontsize=9)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        filepath = None
        if save:
            filepath = os.path.join(self.output_dir, 'daily_trends.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(t('vis_chart_saved', filepath=filepath))
        
        plt.close()
        return filepath
    
    def create_dashboard(self, trends: Dict, save: bool = True) -> str:
        """
        创建综合仪表板
        
        Args:
            trends: 趋势数据
            save: 是否保存文件
            
        Returns:
            仪表板文件路径
        """
        self._ensure_chinese_font()  # 确保中文字体
        print(t('vis_gen_dashboard'))
        
        fig = plt.figure(figsize=(16, 10))
        
        # 1. 技术热点 (左上)
        ax1 = plt.subplot(2, 2, 1)
        if trends.get('tech_hotspots'):
            techs = list(trends['tech_hotspots'].keys())[:6]
            counts = [trends['tech_hotspots'][t] for t in techs]
            ax1.barh(techs, counts, color=self.colors[:len(techs)])
            
            # 使用中文字体设置
            font_family = self.default_font
            title_font = {'family': font_family, 'size': 12, 'weight': 'bold'}
            ax1.set_title('Top 6 Tech Hotspots', fontdict=title_font)
            ax1.grid(axis='x', alpha=0.3)
        
        # 2. 内容分布 (右上)
        ax2 = plt.subplot(2, 2, 2)
        if trends.get('content_distribution'):
            labels = list(trends['content_distribution'].keys())
            sizes = list(trends['content_distribution'].values())
            label_map = {'research': 'Research', 'developer': 'Developer', 'product': 'Product', 'market': 'Market'}
            labels = [label_map.get(l, l) for l in labels]
            
            # 使用中文字体设置
            font_family = self.default_font
            title_font = {'family': font_family, 'size': 12, 'weight': 'bold'}
            
            wedges, texts, autotexts = ax2.pie(sizes, labels=labels, autopct='%1.1f%%', 
                   colors=self.colors[:len(labels)], startangle=90)
            ax2.set_title('Content Distribution', fontdict=title_font)
            
            # 设置标签字体
            for text in texts:
                text.set_fontfamily(font_family)
            for autotext in autotexts:
                autotext.set_fontfamily(font_family)
        
        # 3. 地区分布 (左下)
        ax3 = plt.subplot(2, 2, 3)
        if trends.get('region_distribution'):
            regions = list(trends['region_distribution'].keys())
            counts = list(trends['region_distribution'].values())
            ax3.bar(regions, counts, color=self.colors[:len(regions)])
            
            # 使用中文字体设置
            font_family = self.default_font
            title_font = {'family': font_family, 'size': 12, 'weight': 'bold'}
            ax3.set_title('Regional Distribution', fontdict=title_font)
            ax3.grid(axis='y', alpha=0.3)
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right', fontfamily=font_family)
        
        # 4. 每日趋势 (右下)
        ax4 = plt.subplot(2, 2, 4)
        if trends.get('daily_trends') and len(trends['daily_trends']) > 1:
            dates = sorted(trends['daily_trends'].keys())
            counts = [trends['daily_trends'][d] for d in dates]
            date_labels = [d[5:] for d in dates]
            ax4.plot(date_labels, counts, marker='o', linewidth=2, 
                    markersize=6, color=self.colors[0])
            
            # 使用中文字体设置
            font_family = self.default_font
            title_font = {'family': font_family, 'size': 12, 'weight': 'bold'}
            ax4.set_title('Daily Trends', fontdict=title_font)
            ax4.grid(True, alpha=0.3)
            plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right', fontfamily=font_family)
        
        # 添加总标题
        font_family = self.default_font
        fig.suptitle('AI World Tracker - Dashboard', 
                    fontfamily=font_family, fontsize=16, fontweight='bold', y=0.98)
        
        # 添加时间戳
        timestamp = trends.get('analysis_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        fig.text(0.99, 0.01, f'Generated: {timestamp}', 
                ha='right', va='bottom', fontsize=8, style='italic', fontfamily=font_family)
        
        plt.tight_layout(rect=[0, 0.02, 1, 0.96])
        
        filepath = None
        if save:
            filepath = os.path.join(self.output_dir, 'dashboard.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(t('vis_dashboard_saved', filepath=filepath))
        
        plt.close()
        return filepath
    
    def visualize_all(self, trends: Dict) -> Dict[str, str]:
        """
        生成所有可视化图表
        
        Args:
            trends: 趋势分析数据
            
        Returns:
            图表文件路径字典
        """
        print("\n" + "="*60)
        print(t('vis_start_gen'))
        print("="*60 + "\n")
        
        filepaths = {}
        
        # 生成各类图表
        if trends.get('tech_hotspots'):
            filepaths['tech_hotspots'] = self.plot_tech_hotspots(trends['tech_hotspots'])
        
        if trends.get('content_distribution'):
            filepaths['content_distribution'] = self.plot_content_distribution(trends['content_distribution'])
        
        if trends.get('region_distribution'):
            filepaths['region_distribution'] = self.plot_region_distribution(trends['region_distribution'])
        
        if trends.get('daily_trends'):
            filepaths['daily_trends'] = self.plot_daily_trends(trends['daily_trends'])
        
        # 生成综合仪表板
        filepaths['dashboard'] = self.create_dashboard(trends)
        
        print(t('vis_complete', count=len([f for f in filepaths.values() if f])))
        print(t('vis_output_dir', dir=os.path.abspath(self.output_dir)))
        
        return filepaths


if __name__ == "__main__":
    # 测试示例
    visualizer = DataVisualizer()
    
    test_trends = {
        'tech_hotspots': {
            'NLP': 25,
            'Computer Vision': 18,
            'Generative AI': 22,
            'Reinforcement Learning': 10,
            'MLOps': 8,
            'AI Ethics': 6
        },
        'content_distribution': {
            'research': 30,
            'product': 25,
            'market': 15
        },
        'region_distribution': {
            'China': 20,
            'USA': 30,
            'Europe': 10,
            'Global': 10
        },
        'daily_trends': {
            '2025-11-25': 8,
            '2025-11-26': 12,
            '2025-11-27': 10,
            '2025-11-28': 15,
            '2025-11-29': 18,
            '2025-11-30': 20
        },
        'analysis_time': '2025-12-01 10:00:00'
    }
    
    visualizer.visualize_all(test_trends)
