# 🌍 AI World Tracker

[🇺🇸 English Version](README.md)

**全球人工智能动态追踪系统 (AI World Tracker)** 是一个全方位的 AI 资讯追踪与分析平台。它能够自动从 arXiv、GitHub、科技媒体和博客等多个渠道采集数据，利用智能分类算法对内容进行多维度归类（研究、产品、市场等），并生成可视化的趋势分析报告和 Web 展示页面。

本项目还包含独特的**人工审核与学习反馈机制**，能够通过用户的反馈不断优化分类算法的准确性。

---

## ✨ 主要功能

*   **🤖 多源数据采集**: 自动抓取 arXiv (最新论文), GitHub (热门项目), RSS Feeds (科技新闻, 官方博客) 等源头数据。
*   **🏷️ 智能内容分类**: 自动将资讯分类为 `Research` (研究), `Product` (产品), `Market` (市场), `Developer` (开发), `Leader` (观点) 等类别。
*   **📊 数据可视化**: 生成技术热点图、内容分布图、地区分布图和每日趋势图。
*   **🌐 Web 报告生成**: 自动生成包含仪表盘和分类资讯的静态 HTML 页面 (`index.html`)，支持移动端适配。
*   **📝 人工审核系统**: 提供交互式命令行界面，允许用户对低置信度的分类结果进行人工修正。
*   **🎓 自学习反馈循环**: 系统会分析人工审核的历史记录，自动生成改进建议并优化分类规则。

## 🛠️ 安装指南

### 环境要求
*   Python 3.8+
*   Windows/macOS/Linux

### 安装步骤

1.  **克隆仓库**
    ```bash
    git clone https://github.com/legendyz/ai-world-tracker.git
    cd ai-world-tracker
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```
    *主要依赖包括: `requests`, `beautifulsoup4`, `feedparser`, `arxiv`, `matplotlib`*

3.  **快速安装 (Windows)**
    如果使用 PowerShell，可以直接运行安装脚本：
    ```powershell
    .\install.ps1
    ```

## 🚀 快速开始

运行主程序启动交互式菜单：

```bash
python TheWorldOfAI.py
```

### 主菜单功能说明

1.  **🚀 一键更新数据与报告 (Update & Generate All)**
    *   执行完整流程：采集 -> 分类 -> 分析 -> 可视化 -> 生成 Web 页面。
    *   适合每日定时运行。

2.  **📄 查看分析报告 (View Report)**
    *   在终端直接查看最新的文本分析报告。

3.  **🔍 搜索与筛选 (Search & Filter)**
    *   按关键词、类别或地区筛选已采集的数据。

4.  **🌐 生成并打开 Web 页面 (Generate & Open Web Page)**
    *   基于当前数据重新生成 HTML 页面并在浏览器中打开。

5.  **📝 人工审核分类 (Manual Review)**
    *   进入审核模式，系统会筛选出置信度较低的内容供人工确认或修正。
    *   审核结果会自动保存，用于后续的学习优化。

6.  **🎓 学习反馈分析 (Learning Feedback)**
    *   分析审核历史，生成分类器改进建议报告。

## 📂 项目结构

```text
ai-world-tracker/
├── TheWorldOfAI.py          # 主程序入口
├── data_collector.py        # 数据采集模块 (arXiv, RSS, etc.)
├── content_classifier.py    # 内容分类器 (基于规则与关键词)
├── ai_analyzer.py           # 趋势分析模块
├── visualizer.py            # 数据可视化模块 (Matplotlib)
├── web_publisher.py         # Web 页面生成器
├── manual_reviewer.py       # 人工审核模块
├── learning_feedback.py     # 学习反馈模块
├── requirements.txt         # 项目依赖
├── visualizations/          # 生成的图表存放目录
└── web_output/              # 生成的 Web 页面存放目录
```

## 🔄 工作流示例

1.  **采集与初筛**: 运行功能 `1`，系统自动采集并生成初始报告。
2.  **人工介入**: 运行功能 `5`，检查系统标记为"低置信度"的内容，修正分类错误。
3.  **更新展示**: 审核完成后，选择重新生成 Web 页面，获得更准确的展示结果。
4.  **系统进化**: 定期运行功能 `6`，查看系统根据你的审核操作提出的改进建议，优化 `content_classifier.py`。

## 📄 许可证

MIT License
