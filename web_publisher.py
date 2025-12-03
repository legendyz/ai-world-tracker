"""
Web发布模块 - Web Publisher (重构版)
将AI资讯数据生成为现代化的静态HTML网页
"""

import os
import json
from datetime import datetime
from typing import Dict, List
import base64


import re

class WebPublisher:
    """Web网页发布器 - 专业版"""
    
    def __init__(self, output_dir: str = "."):  # 修改默认输出目录为根目录
        self.output_dir = output_dir
        # 不再创建web_output目录，直接输出到根目录
        if not os.path.exists(output_dir) and output_dir != ".":
            os.makedirs(output_dir)
            
        # 定义颜色主题
        self.colors = {
            'primary': '#2563eb',    # 商务蓝
            'secondary': '#475569',  # 深灰
            'background': '#f8fafc', # 浅灰背景
            'card_bg': '#ffffff',    # 卡片白
            'text_main': '#1e293b',  # 主要文字
            'text_light': '#64748b', # 次要文字
            'border': '#e2e8f0',     # 边框
            
            # 分类颜色
            'research': '#059669',   # 绿色
            'product': '#2563eb',    # 蓝色
            'market': '#d97706',     # 橙色
            'developer': '#7c3aed',  # 紫色
            'leader': '#dc2626',     # 红色
            'community': '#0891b2'   # 青色
        }

    def _sanitize_html(self, text: str) -> str:
        """清理HTML标签，防止破坏页面布局"""
        if not text:
            return ""
        # 1. 移除HTML标签 (替换为空格以防单词粘连)
        clean = re.sub(r'<[^>]+>', ' ', str(text))
        # 2. 移除多余空白
        clean = re.sub(r'\s+', ' ', clean).strip()
        # 3. 转义特殊字符 (顺序很重要)
        clean = clean.replace('&', '&amp;')
        clean = clean.replace('<', '&lt;')
        clean = clean.replace('>', '&gt;')
        clean = clean.replace('"', '&quot;')
        clean = clean.replace("'", '&#39;')
        return clean
    
    def generate_html_page(self, data: List[Dict], trends: Dict, chart_files: Dict[str, str] = None) -> str:
        """生成完整的HTML页面"""
        print("🌐 Generating new Web page...")
        
        timestamp = trends.get('analysis_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 1. 准备数据
        # 按重要性和时间排序
        sorted_data = sorted(data, key=lambda x: (x.get('importance', 0), x.get('published', '')), reverse=True)
        
        # 分类数据
        categorized_data = {
            'leader': [],
            'community': [],
            'product': [],
            'market': [],
            'research': [],
            'developer': []
        }
        
        for item in sorted_data:
            ctype = item.get('content_type', 'market')
            if ctype in categorized_data:
                categorized_data[ctype].append(item)
            else:
                categorized_data['market'].append(item) # 默认归类
                
        # 2. 生成HTML内容
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI World Tracker - Global AI Radar</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <!-- 顶部导航 -->
    <nav class="navbar">
        <div class="container nav-content">
            <div class="brand">
                <span class="logo-icon">🌍</span>
                <span class="logo-text">AI World Tracker</span>
            </div>
            <div class="nav-meta">
                <span class="update-time">Updated: {timestamp}</span>
                <span class="data-count">Items: {len(data)}</span>
            </div>
        </div>
    </nav>

    <div class="container main-content">
        
        <!-- 1. 核心指标看板 -->
        {self._render_dashboard(trends)}
        
        <!-- 2. 可视化图表区 -->
        {self._render_charts(chart_files)}
        
        <!-- 3. 领袖言论 (置顶) -->
        {self._render_section('🗣️ Global Leaders', 'leader', categorized_data['leader'], is_grid=True)}
        
        <!-- 4. 社区热点 (高价值) -->
        {self._render_section('🔥 Geek Community', 'community', categorized_data['community'], is_grid=True)}
        
        <!-- 5. 产品与市场 (商业核心) -->
        {self._render_section('🚀 Product Launches', 'product', categorized_data['product'], is_grid=True)}
        {self._render_section('💼 Market Dynamics', 'market', categorized_data['market'], is_grid=True)}
        
        <!-- 6. 技术前沿 -->
        {self._render_section('🔬 Frontier Research', 'research', categorized_data['research'], is_grid=True)}
        {self._render_section('🛠️ Developer Resources', 'developer', categorized_data['developer'], is_grid=True)}
        
        <!-- 7. 完整数据表 -->
        {self._render_data_table(sorted_data)}
        
    </div>

    <!-- 页脚 -->
    <footer class="footer">
        <div class="container">
            <p>AI World Tracker &copy; 2025</p>
            <p class="sources">Data Sources: arXiv, GitHub, Product Hunt, Hacker News, Google/Bing News, Official Blogs</p>
        </div>
    </footer>

    <script>
        {self._get_js()}
    </script>
</body>
</html>
"""
        
        # 保存文件到根目录 (用于GitHub Pages)
        root_html_file = os.path.join(".", 'index.html')
        with open(root_html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 同时保存到web_output目录 (保持兼容性)
        web_output_dir = "web_output"
        if not os.path.exists(web_output_dir):
            os.makedirs(web_output_dir)
        web_html_file = os.path.join(web_output_dir, 'index.html')
        with open(web_html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✅ Web page generated:")
        print(f"   📄 Root: {root_html_file} (GitHub Pages)")
        print(f"   📄 Web: {web_html_file} (Backup)")
        return root_html_file

    def _render_dashboard(self, trends: Dict) -> str:
        """渲染顶部仪表盘"""
        dist = trends.get('content_distribution', {})
        
        cards = [
            ('Products', dist.get('product', 0), 'product', '🚀'),
            ('Market', dist.get('market', 0), 'market', '💼'),
            ('Community', dist.get('community', 0), 'community', '🔥'),
            ('Research', dist.get('research', 0), 'research', '🔬'),
        ]
        
        html = '<div class="dashboard-grid">'
        for label, count, type_key, icon in cards:
            color = self.colors.get(type_key, '#333')
            html += f"""
            <div class="stat-card" style="border-top-color: {color}">
                <div class="stat-icon">{icon}</div>
                <div class="stat-info">
                    <div class="stat-value" style="color: {color}">{count}</div>
                    <div class="stat-label">{label}</div>
                </div>
            </div>
            """
        html += '</div>'
        return html

    def _render_charts(self, chart_files: Dict) -> str:
        """渲染图表区域"""
        if not chart_files:
            return ""
            
        # 过滤掉不需要显示的图表
        valid_charts = {}
        for name, path in chart_files.items():
            if name not in ['dashboard', 'region_distribution', 'daily_trends'] and os.path.exists(path):
                valid_charts[name] = path
                
        if not valid_charts:
            return ""
            
        html = '<div class="section charts-section"><h2>📈 Trend Analysis</h2><div class="charts-container">'
        for name, path in valid_charts.items():
            try:
                with open(path, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode('utf-8')
                    title = name.replace('_', ' ').title()
                    html += f"""
                    <div class="chart-wrapper">
                        <img src="data:image/png;base64,{b64}" alt="{title}">
                    </div>
                    """
            except Exception:
                continue
        html += '</div></div>'
        return html

    def _render_section(self, title: str, type_key: str, items: List[Dict], is_grid: bool = False, is_compact: bool = False) -> str:
        """渲染内容板块"""
        if not items:
            return ""
            
        # 限制显示数量
        limit = 6
        has_more = len(items) > limit
        
        css_class = "news-grid" if is_grid else "news-list"
        if is_compact: css_class += " compact"
        
        section_id = f"sec-{type_key}"
        
        btn_html = ""
        if has_more:
            btn_html = f"""<button class="btn-expand" onclick="toggleSection('{section_id}', this)">Show All ({len(items)})</button>"""
        
        html = f"""
        <div class="section {type_key}-section" id="{section_id}" data-count="{len(items)}">
            <div class="section-header">
                <div class="header-title-group">
                    <h2 style="color: {self.colors.get(type_key)}">{title}</h2>
                    <span class="badge" style="background: {self.colors.get(type_key)}">{len(items)}</span>
                </div>
                {btn_html}
            </div>
            <div class="{css_class}">
        """
        
        for i, item in enumerate(items):
            is_hidden = i >= limit
            html += self._render_card(item, type_key, is_compact, hidden=is_hidden)
            
        html += "</div></div>"
        return html

    def _render_card(self, item: Dict, type_key: str, is_compact: bool, hidden: bool = False) -> str:
        """渲染单个卡片"""
        title = self._sanitize_html(item.get('title', 'No Title'))
        raw_summary = item.get('summary', '')
        summary = self._sanitize_html(raw_summary)[:150] + '...' if len(raw_summary) > 150 else self._sanitize_html(raw_summary)
        source = self._sanitize_html(item.get('source', 'Unknown'))
        date = item.get('published', '')[:10]
        url = item.get('url', '#')
        
        hidden_class = " hidden-item" if hidden else ""
        
        # 领袖特殊样式
        if type_key == 'leader':
            author = self._sanitize_html(item.get('author', 'Unknown'))
            title_text = self._sanitize_html(item.get('author_title', ''))
            return f"""
            <div class="card leader-card{hidden_class}">
                <div class="leader-header">
                    <div class="leader-avatar">{author[0] if author else '?'}</div>
                    <div>
                        <div class="leader-name">{author}</div>
                        <div class="leader-title">{title_text}</div>
                    </div>
                </div>
                <div class="leader-content">
                    <a href="{url}" target="_blank">{summary}</a>
                </div>
                <div class="card-meta">
                    <span>{source}</span>
                    <span>{date}</span>
                </div>
            </div>
            """
            
        # 普通卡片样式
        tags_html = ""
        for tag in item.get('tech_categories', [])[:2]:
            tags_html += f'<span class="tag">{self._sanitize_html(tag)}</span>'
            
        return f"""
        <div class="card {type_key}-card{hidden_class}">
            <a href="{url}" target="_blank" class="card-title">{title}</a>
            <div class="card-summary">{summary}</div>
            <div class="card-footer">
                <div class="card-tags">{tags_html}</div>
                <div class="card-meta">
                    <span>{source}</span>
                    <span>{date}</span>
                </div>
            </div>
        </div>
        """

    def _render_data_table(self, data: List[Dict]) -> str:
        """渲染完整数据表"""
        html = """
        <div class="section">
            <div class="section-header">
                <h2>📋 Full Data Index</h2>
                <button onclick="toggleTable()" class="btn-toggle">Expand/Collapse</button>
            </div>
            <div id="dataTable" class="table-wrapper hidden">
                <table>
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>Title</th>
                            <th>Source</th>
                            <th>Region</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for item in data[:200]: # 限制200条
            ctype = item.get('content_type', 'market')
            color = self.colors.get(ctype, '#333')
            html += f"""
            <tr>
                <td><span class="status-dot" style="background: {color}"></span>{ctype}</td>
                <td><a href="{item.get('url', '#')}" target="_blank">{item.get('title')}</a></td>
                <td>{item.get('source')}</td>
                <td>{item.get('region')}</td>
                <td>{item.get('published', '')[:10]}</td>
            </tr>
            """
            
        html += "</tbody></table></div></div>"
        return html

    def _get_css(self) -> str:
        return """
        :root {
            --primary: #2563eb;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --border: #e2e8f0;
        }
        
        body {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            line-height: 1.5;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        .main-content { flex: 1; width: 100%; box-sizing: border-box; }
        
        /* Navbar */
        .navbar { background: var(--card); border-bottom: 1px solid var(--border); padding: 1rem 0; position: sticky; top: 0; z-index: 100; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .nav-content { display: flex; justify-content: space-between; align-items: center; }
        .brand { font-size: 1.25rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem; }
        .nav-meta { font-size: 0.875rem; color: var(--text-light); }
        
        /* Dashboard */
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin: 2rem 0; }
        .stat-card { background: var(--card); padding: 1.5rem; border-radius: 0.75rem; border: 1px solid var(--border); border-top-width: 4px; display: flex; align-items: center; gap: 1rem; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .stat-icon { font-size: 2rem; }
        .stat-value { font-size: 1.5rem; font-weight: 700; line-height: 1; }
        .stat-label { font-size: 0.875rem; color: var(--text-light); margin-top: 0.25rem; }
        
        /* Sections */
        .section { margin-bottom: 3rem; }
        .section-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; border-bottom: 2px solid var(--border); padding-bottom: 0.5rem; }
        .section-header h2 { margin: 0; font-size: 1.25rem; }
        .badge { color: white; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
        
        /* Grids */
        .news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
        .news-list { display: flex; flex-direction: column; gap: 1rem; }
        .two-column-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; align-items: start; }
        .two-column-grid > :only-child { grid-column: 1 / -1; }
        @media (max-width: 768px) { .two-column-grid { grid-template-columns: 1fr; } }
        
        /* Cards */
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 0.5rem; padding: 1.25rem; transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; height: 100%; overflow: hidden; }
        .news-list.compact .card { padding: 1rem; }
        .card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
        .card-title { font-weight: 600; color: var(--text); text-decoration: none; margin-bottom: 0.75rem; display: block; font-size: 1.05rem; word-break: break-word; line-height: 1.4; }
        .card-title:hover { color: var(--primary); }
        .card-summary { font-size: 0.875rem; color: var(--text-light); margin-bottom: 1rem; flex-grow: 1; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; word-break: break-word; overflow-wrap: anywhere; line-height: 1.5; }
        .news-list.compact .card-summary { -webkit-line-clamp: 2; margin-bottom: 0.5rem; }
        .card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: auto; pt: 1rem; border-top: 1px solid var(--bg); }
        .card-meta { font-size: 0.75rem; color: #94a3b8; display: flex; gap: 0.75rem; }
        
        /* Leader Card Specifics */
        .leader-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
        .leader-avatar { width: 40px; height: 40px; background: #fee2e2; color: #dc2626; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; }
        .leader-name { font-weight: 600; font-size: 0.9rem; }
        .leader-title { font-size: 0.75rem; color: var(--text-light); }
        .leader-content a { color: var(--text); font-style: italic; text-decoration: none; font-size: 0.95rem; line-height: 1.6; display: block; margin-bottom: 1rem; }
        .leader-content a:hover { color: #dc2626; }
        
        /* Tags */
        .tag { background: #f1f5f9; color: #475569; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-right: 0.5rem; }
        
        /* Charts */
        .charts-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 2rem; }
        .chart-wrapper { background: var(--card); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border); }
        .chart-wrapper img { width: 100%; height: auto; }
        
        /* Table */
        .table-wrapper { overflow-x: auto; background: var(--card); border-radius: 0.5rem; border: 1px solid var(--border); }
        table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
        th { background: #f8fafc; text-align: left; padding: 0.75rem 1rem; font-weight: 600; color: var(--text-light); }
        td { padding: 0.75rem 1rem; border-top: 1px solid var(--border); }
        tr:hover { background: #f8fafc; }
        .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 0.5rem; }
        .hidden { display: none; }
        .btn-toggle { background: var(--primary); color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.25rem; cursor: pointer; font-size: 0.875rem; }
        
        /* Footer */
        .footer { background: #1e293b; color: #94a3b8; padding: 3rem 0; margin-top: 4rem; text-align: center; font-size: 0.875rem; width: 100%; }
        
        /* Expand/Collapse */
        .hidden-item { display: none !important; }
        .section.expanded .hidden-item { display: flex !important; }
        .btn-expand { background: transparent; border: 1px solid var(--primary); color: var(--primary); padding: 0.25rem 0.75rem; border-radius: 4px; cursor: pointer; font-size: 0.875rem; transition: all 0.2s; }
        .btn-expand:hover { background: var(--primary); color: white; }
        .header-title-group { display: flex; align-items: center; gap: 1rem; }
        .section-header { justify-content: space-between; }
        """

    def _get_js(self) -> str:
        return """
        function toggleTable() {
            const table = document.getElementById('dataTable');
            table.classList.toggle('hidden');
        }
        
        function toggleSection(id, btn) {
            const section = document.getElementById(id);
            section.classList.toggle('expanded');
            const isExpanded = section.classList.contains('expanded');
            const count = section.dataset.count;
            btn.textContent = isExpanded ? 'Show Less' : 'Show All (' + count + ')';
        }
        """
