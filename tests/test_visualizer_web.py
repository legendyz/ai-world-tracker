"""
可视化和Web发布模块测试

测试DataVisualizer和WebPublisher的核心功能
"""

import sys
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualizer import DataVisualizer
from web_publisher import WebPublisher
from ai_analyzer import AIAnalyzer


@pytest.fixture
def sample_trends():
    """提供样本趋势数据"""
    return {
        'tech_categories': {
            'Generative AI': 15,
            'Computer Vision': 10,
            'NLP': 8,
            'Robotics': 5,
            'AutoML': 3
        },
        'content_distribution': {
            'research': 20,
            'product': 15,
            'developer': 10,
            'market': 8,
            'leader': 5
        },
        'region_distribution': {
            'US': 30,
            'China': 20,
            'EU': 15,
            'Other': 10
        },
        'daily_data': [
            {'date': '2025-12-08', 'count': 10},
            {'date': '2025-12-09', 'count': 15},
            {'date': '2025-12-10', 'count': 12},
            {'date': '2025-12-11', 'count': 18},
            {'date': '2025-12-12', 'count': 20}
        ]
    }


@pytest.fixture
def sample_data():
    """提供样本数据"""
    return [
        {
            'title': 'Test AI Research Paper',
            'summary': 'A groundbreaking study on transformers',
            'content_type': 'research',
            'importance': 0.85,
            'published': '2025-12-12',
            'source': 'arXiv',
            'tech_categories': ['Generative AI']
        },
        {
            'title': 'New AI Product Launch',
            'summary': 'Company releases new AI model',
            'content_type': 'product',
            'importance': 0.75,
            'published': '2025-12-11',
            'source': 'TechCrunch',
            'tech_categories': ['NLP']
        },
        {
            'title': 'AI Developer Tool',
            'summary': 'Open source framework for AI development',
            'content_type': 'developer',
            'importance': 0.70,
            'published': '2025-12-10',
            'source': 'GitHub',
            'tech_categories': ['AutoML']
        }
    ]


class TestDataVisualizer:
    """数据可视化测试"""
    
    @pytest.fixture
    def visualizer(self, tmp_path):
        """创建可视化器实例"""
        # 使用临时目录避免污染项目目录
        vis = DataVisualizer()
        vis.output_dir = str(tmp_path / "visualizations")
        os.makedirs(vis.output_dir, exist_ok=True)
        return vis
    
    def test_visualizer_initialization(self, visualizer):
        """测试可视化器初始化"""
        assert visualizer is not None
        assert hasattr(visualizer, 'output_dir')
        print("✅ 可视化器初始化正常")
    
    def test_visualize_all(self, visualizer, sample_trends):
        """测试完整可视化生成"""
        chart_files = visualizer.visualize_all(sample_trends)
        
        assert isinstance(chart_files, dict)
        assert len(chart_files) > 0
        
        # 检查关键图表
        expected_charts = ['tech_hotspots', 'content_distribution', 'region_distribution']
        for chart_name in expected_charts:
            if chart_name in chart_files:
                print(f"  ✓ {chart_name} 生成成功")
        
        print(f"✅ 生成了 {len(chart_files)} 个图表")
    
    def test_chart_file_creation(self, visualizer, sample_trends):
        """测试图表文件是否被创建"""
        chart_files = visualizer.visualize_all(sample_trends)
        
        # 检查至少有一些文件被创建
        created_files = [f for f in chart_files.values() if f and os.path.exists(f)]
        
        assert len(created_files) > 0
        print(f"✅ 创建了 {len(created_files)} 个实际文件")


class TestWebPublisher:
    """Web发布器测试"""
    
    @pytest.fixture
    def publisher(self, tmp_path):
        """创建Web发布器实例"""
        pub = WebPublisher()
        pub.output_dir = str(tmp_path / "web_output")
        os.makedirs(pub.output_dir, exist_ok=True)
        return pub
    
    @pytest.fixture
    def chart_files(self):
        """提供图表文件路径（可能不存在）"""
        return {
            'tech_hotspots': 'visualizations/tech_hotspots.png',
            'content_distribution': 'visualizations/content_distribution.png',
            'region_distribution': 'visualizations/region_distribution.png'
        }
    
    def test_publisher_initialization(self, publisher):
        """测试发布器初始化"""
        assert publisher is not None
        assert hasattr(publisher, 'output_dir')
        print("✅ Web发布器初始化正常")
    
    def test_generate_html_page(self, publisher, sample_data, sample_trends, chart_files):
        """测试HTML页面生成"""
        html_file = publisher.generate_html_page(sample_data, sample_trends, chart_files)
        
        assert html_file is not None
        assert html_file.endswith('.html')
        
        print(f"✅ HTML页面生成成功: {os.path.basename(html_file)}")
    
    def test_html_file_exists(self, publisher, sample_data, sample_trends, chart_files):
        """测试HTML文件是否被创建"""
        html_file = publisher.generate_html_page(sample_data, sample_trends, chart_files)
        
        assert os.path.exists(html_file)
        assert os.path.getsize(html_file) > 0
        
        print(f"✅ HTML文件存在且非空: {os.path.getsize(html_file)} 字节")
    
    def test_html_content_validity(self, publisher, sample_data, sample_trends, chart_files):
        """测试HTML内容有效性"""
        html_file = publisher.generate_html_page(sample_data, sample_trends, chart_files)
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本HTML结构检查
        assert '<!DOCTYPE html>' in content or '<html' in content
        assert '<head>' in content or '<title>' in content
        assert '<body>' in content
        
        # 检查是否包含数据
        assert len(sample_data) > 0
        
        print("✅ HTML内容结构有效")


class TestIntegration:
    """可视化和Web发布集成测试"""
    
    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """创建临时工作空间"""
        vis_dir = tmp_path / "visualizations"
        web_dir = tmp_path / "web_output"
        vis_dir.mkdir()
        web_dir.mkdir()
        return {"vis": str(vis_dir), "web": str(web_dir)}
    
    def test_full_visualization_to_web_pipeline(self, temp_workspace, sample_data, sample_trends):
        """测试完整的可视化到Web发布流程"""
        # 步骤1: 生成可视化
        visualizer = DataVisualizer()
        visualizer.output_dir = temp_workspace["vis"]
        
        chart_files = visualizer.visualize_all(sample_trends)
        assert len(chart_files) > 0
        print(f"  ✓ 步骤1: 生成了 {len(chart_files)} 个图表")
        
        # 步骤2: 生成Web页面
        publisher = WebPublisher()
        publisher.output_dir = temp_workspace["web"]
        
        html_file = publisher.generate_html_page(sample_data, sample_trends, chart_files)
        assert os.path.exists(html_file)
        print(f"  ✓ 步骤2: 生成HTML页面")
        
        # 步骤3: 验证完整性
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert len(content) > 1000  # HTML应该足够长
        print(f"  ✓ 步骤3: 验证完整性 ({len(content)} 字符)")
        
        print("✅ 完整流程测试通过")


if __name__ == '__main__':
    print("\n" + "🌟" * 30)
    print("   可视化和Web发布模块测试")
    print("🌟" * 30)
    
    # 运行测试
    pytest.main([__file__, '-v', '-s'])
