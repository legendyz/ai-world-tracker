# 🌍 AI World Tracker

[🇺🇸 English Version](README.md)

**AI World Tracker** 是一个全面的人工智能动态追踪和分析平台。它自动从多个权威来源采集数据，使用智能算法（LLM 或规则分类）对内容进行分类，并生成可视化趋势分析报告和网页仪表盘。

## 🌟 分支概览

| 分支 | 版本 | 描述 | 目标用户 |
|------|------|------|----------|
| `main` | v2.0 | **最新稳定版本**，集成完整 LLM 功能 | 生产环境使用 |
| `ai-world-tracker-v1` | v1.0 | 第一个完整版本，采用规则分类 | 爱好者和开发者自定义开发 |
| `feature/data-collection-v2` | Beta | 增强数据采集能力（开发中） | 贡献者和测试者 |

### 选择合适的分支

- **生产环境使用**：使用 `main` 分支 - 经过完整测试，集成 LLM 增强分类
- **学习/自定义开发**：使用 `ai-world-tracker-v1` - 架构简单，规则分类，易于修改
- **参与贡献**：使用 `feature/data-collection-v2` - 帮助我们改进数据采集功能

## ✨ 核心功能

### 基础能力
- **🤖 多源数据采集**：自动从 arXiv（最新论文）、GitHub（热门项目）、科技媒体（TechCrunch、The Verge、Wired）以及 AI 博客（OpenAI、Google AI、Hugging Face）采集数据
- **🧠 智能分类**：双模式分类系统
  - **LLM 模式**：通过 Ollama/OpenAI/Anthropic 进行语义理解（95%+ 准确率）
  - **规则模式**：基于关键词的模式识别（快速，无依赖）
- **📊 数据可视化**：生成技术热点、内容分布、地区分布和每日趋势图表
- **🌐 网页仪表盘**：创建带有分类新闻的响应式 HTML 仪表盘
- **🔄 智能缓存**：基于 MD5 的缓存机制，避免重复 API 调用

### LLM 集成（Main 分支）
- **多提供商支持**：Ollama（免费、本地）、OpenAI、Anthropic
- **本地模型**：通过 Ollama 使用 Qwen3:8b - 完全免费
- **GPU 加速**：自动检测 NVIDIA、AMD、Apple Silicon
- **并发处理**：3 线程并行处理提升速度
- **自动降级**：LLM 不可用时优雅降级到规则分类

## 🛠️ 安装指南

### 环境要求

- Python 3.8+
- Windows / macOS / Linux
- （可选）Ollama 用于本地 LLM

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

3. **（可选）配置 Ollama 进行 LLM 分类**
   ```bash
   # 从 https://ollama.com/download 安装 Ollama
   ollama pull qwen3:8b
   ollama serve
   ```

4. **运行程序**
   ```bash
   python TheWorldOfAI.py
   ```

## 🚀 使用方法

### 主菜单

```
📋 主菜单
============================================================
当前模式：[LLM: Ollama/qwen3:8b] 或 [规则分类]
============================================================
1. 🚀 自动更新数据与报告（完整流程）
2. 🌐 生成并打开 Web 页面
3. ⚙️ 设置（分类模式、语言）
4. 📝 手动工作流（审核、反馈）
0. 退出程序
============================================================
```

### 功能说明

| 选项 | 功能 | 描述 |
|------|------|------|
| 1 | 自动更新 | 执行完整流程：采集 → 分类 → 分析 → 可视化 → 生成网页 |
| 2 | 网页生成 | 重新生成 HTML 仪表盘并在浏览器中打开 |
| 3 | 设置 | 切换 LLM/规则分类模式，更改语言 |
| 4 | 手动工作流 | 审核低置信度项目，学习反馈（仅规则模式） |

## 📂 项目结构

```
ai-world-tracker/
├── TheWorldOfAI.py          # 主程序入口
├── data_collector.py        # 多源数据采集
├── content_classifier.py    # 规则分类器
├── llm_classifier.py        # LLM 增强分类器
├── config.py                # 配置管理
├── ai_analyzer.py           # 趋势分析引擎
├── visualizer.py            # 数据可视化（Matplotlib）
├── web_publisher.py         # 网页生成器
├── manual_reviewer.py       # 人工审核界面
├── learning_feedback.py     # 学习反馈系统
├── i18n.py                  # 国际化（中/英文）
├── config_manager.py        # YAML 配置加载器
├── link_validator.py        # URL 验证工具
├── requirements.txt         # Python 依赖
├── config.yaml              # 应用配置
├── visualizations/          # 生成的图表
├── web_output/              # 生成的网页
│   └── index.html           # 备份仪表盘
└── index.html               # 主仪表盘（GitHub Pages）
```

## 📰 数据来源

### 研究论文
- arXiv (cs.AI, cs.LG, cs.CV, cs.CL)

### 科技新闻媒体
- TechCrunch AI
- The Verge AI
- Wired AI
- MIT Technology Review
- IEEE Spectrum AI
- AI News
- Synced Review

### 中国科技媒体
- 36氪
- IT之家
- 机器之心
- 量子位
- InfoQ 中国

### 开发者资源
- GitHub Blog
- Hugging Face Blog
- OpenAI Blog
- Google AI Blog

### 社区与领袖
- Product Hunt AI
- Hacker News AI
- Sam Altman 博客
- Andrej Karpathy 博客
- Lex Fridman 播客

## ⚙️ 配置

### LLM 提供商

| 提供商 | 模型 | 费用 | 配置方式 |
|--------|------|------|----------|
| Ollama | qwen3:8b | 免费 | `ollama pull qwen3:8b` |
| OpenAI | gpt-4o-mini | 付费 | 设置 `OPENAI_API_KEY` |
| Anthropic | claude-3-haiku | 付费 | 设置 `ANTHROPIC_API_KEY` |

### 环境变量

```bash
# 可选：云端 LLM 提供商
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# 可选：Ollama 自定义 URL
export OLLAMA_BASE_URL="http://localhost:11434"
```

## 🔧 版本对比

| 功能 | v1.0 (ai-world-tracker-v1) | v2.0 (main) |
|------|----------------------------|-------------|
| 分类方式 | 规则分类 | LLM + 规则降级 |
| LLM 支持 | ❌ | ✅ Ollama/OpenAI/Anthropic |
| 本地模型 | ❌ | ✅ Qwen3:8b |
| 并发处理 | ❌ | ✅ 多线程 |
| 智能缓存 | ❌ | ✅ MD5 缓存 |
| GPU 加速 | ❌ | ✅ 自动检测 |
| 准确率 | ~70% | ~95% |
| 适用场景 | 学习、自定义开发 | 生产环境 |

## 🤝 参与贡献

我们欢迎各种形式的贡献！以下是参与方式：

1. **报告问题**：发现 Bug？[提交 Issue](https://github.com/legendyz/ai-world-tracker/issues)
2. **功能建议**：有好的想法？告诉我们！
3. **提交代码**：
   - Fork 仓库
   - 从 `feature/data-collection-v2` 创建功能分支
   - 提交 PR

### 开发分支
- `main`：稳定的生产代码
- `feature/data-collection-v2`：数据采集改进的活跃开发
- `ai-world-tracker-v1`：旧版本（仅修复 Bug）

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Ollama](https://ollama.com/) 提供本地 LLM 支持
- [arXiv](https://arxiv.org/) 提供研究论文访问
- 所有让这个项目成为可能的科技博客和新闻来源

---

**由 AI World Tracker 团队用 ❤️ 制作**
