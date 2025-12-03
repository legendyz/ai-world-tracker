# AI World Tracker - User Guide

## 🚀 Quick Start

### 1. One-Click Installation (Windows)

```powershell
# Clone the repository
git clone https://github.com/legendyz/ai-world-tracker.git
cd ai-world-tracker

# Run the installation script
.\install.ps1
```

This script will:
- ✓ Check your Python environment (3.8+ required)
- ✓ Install all dependencies from `requirements.txt`
- ✓ Prompt you to run the application immediately
- ✓ Generate initial web dashboard in root directory

### 2. Manual Installation

```powershell
# Install dependencies
pip install -r requirements.txt

# Run the application
python TheWorldOfAI.py
```

### 3. GitHub Pages Deployment

**NEW**: The web dashboard now automatically generates in the repository root!

```powershell
# Run the tracker to generate web dashboard
python TheWorldOfAI.py

# The index.html is automatically created in root directory
# Perfect for GitHub Pages - no manual copying needed!

# Commit and push to GitHub
git add .
git commit -m "Update AI dashboard"
git push origin main

# Enable GitHub Pages in repository Settings > Pages
# Select Source: "Deploy from a branch" > "main" > "/ (root)"
```

---

## 📖 Usage Scenarios

### Scenario 1: Daily AI Briefing (Full Workflow)

**Goal**: Get a complete update on global AI trends, research, and products.

**Steps**:
1. Run `python TheWorldOfAI.py`.
2. Select **Option 1: Run Full Process**.

**What happens**:
- **Data Collection**: Fetches data from arXiv, GitHub, Hacker News, Product Hunt, etc.
- **Classification**: Categorizes items into Leaders, Community, Product, Market, Research, etc.
- **Visualization**: Generates English charts for content distribution and tech trends.
- **Web Generation**: Creates a responsive HTML dashboard at `web_output/index.html`.

### Scenario 2: Adjusting the Web Layout

**Goal**: You modified the CSS or layout settings in `web_publisher.py` and want to see changes without re-fetching data.

**Steps**:
1. Run `python TheWorldOfAI.py`.
2. Select **Option 4: Generate Web Page**.

**Result**:
- The script reads the most recent local data (`ai_tracker_data_*.json`).
- It regenerates `web_output/index.html` instantly with your new layout settings.

### Scenario 3: Publishing to GitHub Pages

**Goal**: Share your AI Tracker report with the world.

**Steps**:
1. Run the full process to generate the latest report.
2. Ensure `web_output/index.html` exists.
3. Push your code to GitHub.
4. In GitHub Repository Settings -> Pages, set the source to your branch (e.g., `main`) and folder (root or docs).
   - *Tip*: You may need to move `web_output/index.html` to the root folder or configure a specific deployment workflow.

---

## ⚙️ Configuration & Customization

### Modifying Data Sources
Edit `data_collector.py` to add or remove RSS feeds and API endpoints.

### Changing Classification Rules
Edit `content_classifier.py`. You can add new keywords to `self.genai_keywords` or `self.research_keywords` to refine how content is tagged.

### Customizing the Web Report
Edit `web_publisher.py`:
- **Colors**: Modify `self.colors` dictionary.
- **Layout**: Adjust `_render_section` or CSS in `_get_css`.
- **Item Limits**: Change the `limit = 6` variable in `_render_section` to show more or fewer items initially.

---

## 📂 Output Structure

```
MYCODE/
├── ai_tracker_data_YYYYMMDD_HHMMSS.json  # Raw data backup
├── ai_tracker_report_YYYYMMDD_HHMMSS.txt # Text summary
├── visualizations/                        # Generated charts (PNG)
│   ├── content_distribution.png
│   └── tech_trends.png
└── web_output/
    └── index.html                        # The main dashboard file
```
3. 等待处理完成
4. 选择 `6. 按条件筛选数据`
5. 选择 `3. 按技术领域`
6. 输入 `NLP`

**结果**: 显示所有NLP相关的论文、产品和新闻

### 场景3: 对比中美AI发展

**目标**: 分析中美AI生态差异

**步骤**:
1. 运行完整流程采集数据
2. 查看生成的 `region_distribution.png` 图表
3. 分别筛选 China 和 USA 数据
4. 对比技术热点和内容类型

**示例**:
```powershell
python TheWorldOfAI.py
# 选择 1 (运行完整流程)
# 选择 6 (筛选数据)
# 选择 2 (按地区)
# 输入 China 或 USA
```

### 场景4: 追踪特定公司动态

**目标**: 关注OpenAI、百度等公司

**方法**: 在筛选结果中查找关键词

```python
# 手动筛选（可扩展功能）
filtered_items = [
    item for item in tracker.data 
    if 'openai' in item.get('title', '').lower() or 
       'baidu' in item.get('title', '').lower() or
       '百度' in item.get('title', '')
]
```

## 交互菜单详解

### 菜单选项说明

```
1. 运行完整数据处理流程
   - 执行所有4个步骤
   - 生成所有输出文件
   - 适合首次使用或定期更新

2. 仅采集数据
   - 只进行数据采集和分类
   - 不进行分析和可视化
   - 适合快速获取原始数据

3. 查看数据统计
   - 显示当前数据概览
   - 内容类型和地区分布
   - 不生成图表

4. 生成可视化图表
   - 基于现有数据生成图表
   - 需要先采集数据
   - 可重复生成

5. 查看分析报告
   - 显示文本格式报告
   - 包含趋势分析和热点
   - 终端直接输出

6. 按条件筛选数据
   - 支持多维度筛选
   - 显示筛选结果前5条
   - 可导出（扩展功能）

0. 退出程序
   - 安全退出应用
```

## 高级用法

### 1. 定时自动运行

**Windows任务计划**:

```powershell
# 创建每天早上8点运行的任务
$action = New-ScheduledTaskAction -Execute 'python' -Argument 'C:\Users\legendz\OneDrive\Coding\MYCODE\TheWorldOfAI.py --auto'
$trigger = New-ScheduledTaskTrigger -Daily -At 8am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "AI_World_Tracker_Daily" -Description "每日AI资讯采集"
```

### 2. 集成OpenAI API

**启用AI摘要功能**:

```powershell
# 设置环境变量
$env:OPENAI_API_KEY = "sk-your-api-key-here"

# 运行应用
python TheWorldOfAI.py --auto
```

**效果**: 
- 自动生成内容摘要
- 更准确的趋势分析
- 智能关键信息提取

### 3. 批量处理历史数据

**处理多天数据**:

```python
# 创建自定义脚本 batch_process.py
from TheWorldOfAI import AIWorldTracker

tracker = AIWorldTracker()

# 连续采集多次
for day in range(7):
    print(f"\n=== 第 {day+1} 天采集 ===")
    tracker.run_full_pipeline()
    # 可以添加延时避免API限制
```

### 4. 导出特定格式

**导出Excel报告** (需安装 openpyxl):

```python
import pandas as pd
from TheWorldOfAI import AIWorldTracker

tracker = AIWorldTracker()
tracker.run_full_pipeline()

# 转换为DataFrame
df = pd.DataFrame(tracker.data)

# 导出Excel
df.to_excel('ai_tracker_report.xlsx', index=False)
print("✓ Excel报告已生成")
```

### 5. 自定义数据源

**添加微信公众号RSS源**:

编辑 `data_collector.py`:

```python
def collect_wechat_articles(self):
    feed_urls = [
        'https://your-wechat-rss-source.com/feed',
        # 添加更多RSS源
    ]
    return self.collect_rss_feeds(feed_urls)
```

## 输出文件说明

### JSON数据文件

```json
{
  "metadata": {
    "timestamp": "20251201_100530",
    "total_items": 73
  },
  "data": [
    {
      "title": "GPT-5 Released",
      "content_type": "product",
      "tech_categories": ["NLP", "Generative AI"],
      "region": "USA",
      ...
    }
  ],
  "trends": {
    "tech_hotspots": {...},
    "content_distribution": {...}
  }
}
```

### 分析报告示例

```
============================================================
AI World Tracker - 分析报告
============================================================

生成时间: 2025-12-01 10:05:30
数据总量: 73 条

【技术热点】
  • NLP: 25 条
  • Generative AI: 22 条
  • Computer Vision: 18 条

【内容分布】
  • research: 30 条 (41.1%)
  • product: 25 条 (34.2%)
  • market: 18 条 (24.7%)

【地区分布】
  • USA: 30 条
  • China: 20 条
  • Global: 15 条
  • Europe: 8 条
```

## 常见问题

### Q1: 数据采集失败怎么办？

**A**: 应用会自动使用示例数据。检查：
- 网络连接是否正常
- 是否被防火墙拦截
- GitHub API是否超限（等待后重试）

### Q2: 图表显示乱码？

**A**: 中文字体问题
```powershell
# Windows: 确保安装了微软雅黑或SimHei
# 查看代码中的字体设置：
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
```

### Q3: 如何只采集中国AI资讯？

**A**: 使用筛选功能
```
运行程序 -> 选择 1 -> 选择 6 -> 选择 2 -> 输入 China
```

### Q4: 可以添加更多数据源吗？

**A**: 可以！编辑 `data_collector.py`，参考现有方法添加新的采集函数

### Q5: 如何定期自动运行？

**A**: 使用Windows任务计划或Linux cron，参考"高级用法"部分

## 性能优化建议

1. **减少API调用**: 调整 `max_results` 参数
2. **本地缓存**: 保存JSON文件用于离线分析
3. **异步采集**: 使用 `asyncio` 并行采集（高级扩展）
4. **数据库存储**: 使用SQLite持久化历史数据

## 贡献和反馈

发现问题或有改进建议？欢迎：
- 提交Issue
- 贡献代码
- 分享使用经验

---

祝你使用愉快！🚀
