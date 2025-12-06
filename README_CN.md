# 🌍 AI World Tracker

[🇺🇸 English Version](README.md)

**AI World Tracker** 是一个全面的人工智能动态追踪和分析平台。它自动从多个权威来源采集数据，使用智能算法对内容进行分类，并生成可视化趋势分析报告和网页仪表盘。

## ✨ 核心功能

- **🤖 多源数据采集**: 自动从 arXiv（最新论文）、GitHub（热门项目）、科技媒体（TechCrunch、The Verge、Wired）以及 AI 博客（OpenAI、Google AI、Hugging Face）采集数据
- **📊 智能分类**: 基于规则的内容分类系统，支持关键词匹配和模式识别
- **📈 数据可视化**: 生成技术热点、内容分布、地区分布和每日趋势图表
- **🌐 网页报告生成**: 创建带有分类新闻和移动端支持的静态 HTML 仪表盘
- **📝 人工审核系统**: 审核低置信度分类结果并提供修正
- **🎓 学习反馈**: 分析审核历史并生成改进分类器的建议

## 🛠️ 安装指南

### 环境要求

- Python 3.8+
- Windows / macOS / Linux

### 快速开始

1. **克隆仓库**
   ```bash
   git clone https://github.com/legendyz/ai-world-tracker.git
   cd ai-world-tracker
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行程序**
   ```bash
   python TheWorldOfAI.py
   ```

## 🚀 使用方法

运行主程序启动交互式菜单：

```bash
python TheWorldOfAI.py
```

### 主菜单

```
📋 主菜单
============================================================
1. 🚀 自动更新数据与报告 (完整流程)
2. 🌐 生成并打开 Web 页面
3. 📝 人工审核分类 (审核低置信度项目)
4. 🎓 学习反馈分析 (分析审核历史)
0. 退出程序
============================================================
```

### 功能说明

| 选项 | 功能 | 描述 |
|------|------|------|
| 1 | 自动更新 | 执行完整流程：采集 → 分类 → 分析 → 可视化 → 生成网页 |
| 2 | 网页生成 | 重新生成 HTML 仪表盘并在浏览器中打开 |
| 3 | 人工审核 | 审核低分类置信度的内容项 |
| 4 | 学习反馈 | 根据审核历史生成优化建议 |

## 📂 项目结构

```
ai-world-tracker/
├── TheWorldOfAI.py          # 主程序入口
├── data_collector.py        # 数据采集模块 (arXiv, RSS, GitHub)
├── content_classifier.py    # 基于规则的内容分类器
├── ai_analyzer.py           # 趋势分析引擎
├── visualizer.py            # 数据可视化 (Matplotlib)
├── web_publisher.py         # 网页生成器
├── manual_reviewer.py       # 人工审核界面
├── learning_feedback.py     # 学习反馈系统
├── link_validator.py        # URL 验证工具
├── requirements.txt         # Python 依赖
├── visualizations/          # 生成的图表
└── web_output/              # 生成的网页
    └── index.html           # 主仪表盘
```

## 📰 数据来源

### 研究论文
- arXiv (cs.AI, cs.LG, cs.CV, cs.CL)

### 新闻媒体
- TechCrunch AI
- The Verge AI
- Wired AI
- MIT Technology Review
- IEEE Spectrum AI
- 36氪
- 机器之心
- 量子位

### 开发者与官方博客
- GitHub Blog
- OpenAI Blog
- Google AI Blog
- Hugging Face Blog

### 社区
- Product Hunt AI
- Hacker News

## 🔧 配置

程序使用智能默认设置，基本使用无需任何配置。

### 可选环境变量

```bash
# 用于未来 LLM 集成（当前版本不需要）
OPENAI_API_KEY=sk-your-api-key
```

## 📊 内容分类

分类器将内容分为六个维度：

| 类别 | 描述 | 示例 |
|------|------|------|
| `research` | 学术论文和研究 | arXiv 论文、基准测试结果 |
| `product` | 产品发布和更新 | GPT-4o 发布、新功能上线 |
| `market` | 商业和市场新闻 | 融资轮次、收购事件 |
| `developer` | 开发者工具和资源 | SDK、API、教程 |
| `leader` | 行业领袖观点 | CEO 访谈、主题演讲 |
| `community` | 社区讨论 | 热门话题、技术辩论 |

## 🌿 分支信息

| 分支 | 描述 | 状态 |
|------|------|------|
| `main` | 稳定生产版本 | ✅ 推荐使用 |
| `feature/ai-enhancements-v2` | LLM 增强分类 (Qwen3:8b) | 🧪 测试版 |

### 功能分支 (v2.0-beta)

`feature/ai-enhancements-v2` 分支包含实验性的 LLM 增强分类功能：

- **LLM 提供商**: Ollama（本地）、OpenAI、Anthropic
- **推荐模型**: Qwen3:8b（使用 Chat API + think=false 优化）
- **特性**: GPU 自动检测、MD5 缓存、自动降级

试用测试版：
```bash
git checkout feature/ai-enhancements-v2
pip install -r requirements.txt
# 安装 Ollama 并拉取 qwen3:8b 模型
ollama pull qwen3:8b
python TheWorldOfAI.py
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献指南

欢迎贡献！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📧 联系方式

- GitHub: [@legendyz](https://github.com/legendyz)
- 项目地址: [ai-world-tracker](https://github.com/legendyz/ai-world-tracker)

---

**⭐ 如果这个项目对您有帮助，请给它一个 Star！**
