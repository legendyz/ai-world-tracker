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
- **🌍 双语支持**：完整的中英文界面（i18n 国际化）

### LLM 集成（Main 分支）
- **多提供商支持**：Ollama（免费、本地）、OpenAI、Anthropic
- **本地模型**：通过 Ollama 使用 Qwen3:8b - 完全免费
- **GPU 加速**：自动检测 NVIDIA、AMD、Apple Silicon
- **并发处理**：3-6 线程并行处理提升速度
- **自动降级**：LLM 不可用时优雅降级到规则分类
- **资源管理**：退出时自动卸载模型，释放显存/内存

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
当前分类模式：🤖 LLM模式 (ollama/qwen3:8b)
============================================================
1. 🚀 自动更新数据与报告 (Auto Update & Generate)
2. 🌐 生成并打开 Web 页面 (Generate & Open Web Page)
3. 📝 人工审核分类 (Manual Review)
4. 📚 学习反馈分析 (Learning Feedback)
5. ⚙️  设置与管理 (Settings & Management)
0. 退出程序
============================================================
```

### 设置与管理菜单

```
⚙️  设置与管理

当前模式：🤖 LLM模式 (ollama/qwen3:8b)

📋 分类模式:
  1. 📝 规则模式 (Rule-based) - 快速、免费、无需网络
  2. 🤖 LLM模式 (Ollama本地) - 高精度、语义理解
  3. 🤖 LLM模式 (OpenAI) - 最高精度、需要API密钥
  4. 🤖 LLM模式 (Anthropic) - 高精度、需要API密钥

🧹 数据维护:
  5. 🗑️ 清除LLM分类缓存
  6. 🗑️ 清除采集历史缓存
  7. 🗑️ 清除采集结果历史

  0. ↩️ 返回主菜单
```

### 功能说明

| 选项 | 功能 | 描述 |
|------|------|------|
| 1 | 自动更新 | 执行完整流程：采集 → 分类 → 分析 → 可视化 → 生成网页，完成后询问是否打开浏览器 |
| 2 | 网页生成 | 重新生成 HTML 仪表盘并在浏览器中打开 |
| 3 | 人工审核 | 审核低置信度分类项目 |
| 4 | 学习反馈 | 基于审核历史生成优化建议 |
| 5 | 设置与管理 | 切换分类模式和管理数据/缓存 |

### 数据维护选项

| 选项 | 功能 | 描述 |
|------|------|------|
| 清除LLM分类缓存 | 🗑️ | 删除 `llm_classification_cache.json`，强制使用 LLM 重新分类 |
| 清除采集历史缓存 | 🗑️ | 删除 `collection_history_cache.json`，允许重新采集所有 URL |
| 清除采集结果历史 | 🗑️ | 删除所有 `data/exports/*.json` 和 `*.txt` 文件（需要确认） |

## 📂 项目结构

```
ai-world-tracker/
├── TheWorldOfAI.py          # 主程序入口
├── data_collector.py        # 多源数据采集
├── content_classifier.py    # 规则分类器
├── llm_classifier.py        # LLM 增强分类器
├── config.py                # 统一配置管理
├── logger.py                # 统一日志系统
├── ai_analyzer.py           # 趋势分析引擎
├── visualizer.py            # 数据可视化（Matplotlib）
├── web_publisher.py         # 网页生成器
├── manual_reviewer.py       # 人工审核界面
├── learning_feedback.py     # 学习反馈系统
├── i18n.py                  # 国际化（中/英文）
├── link_validator.py        # URL 验证工具
├── regenerate_web.py        # 快速网页重生成工具
├── requirements.txt         # Python 依赖
├── config.yaml              # 应用配置
├── ai_tracker_config.json   # 用户配置（自动生成）
├── pytest.ini               # 测试配置
├── data/                    # 生成的数据目录
│   ├── exports/             # 导出的数据和报告
│   │   ├── ai_tracker_data_*.json    # 带时间戳的采集数据
│   │   └── ai_tracker_report_*.txt   # 文本报告
│   └── cache/               # 缓存文件
│       ├── collection_history_cache.json  # URL/标题去重缓存
│       └── llm_classification_cache.json  # LLM 分类结果缓存
├── tests/                   # 测试文件目录
│   ├── __init__.py
│   ├── test_classifier_*.py
│   ├── test_llm_*.py
│   └── ...
├── logs/                    # 日志文件目录
├── visualizations/          # 生成的图表
├── web_output/              # 生成的网页（备份）
│   └── index.html
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

### 配置文件

应用支持多种配置源，优先级如下：

1. **环境变量** - 最高优先级
2. **.env 文件** - 本地开发使用
3. **config.yaml** - 项目默认配置
4. **ai_tracker_config.json** - 用户偏好（自动保存）
5. **代码默认值** - 后备值

### config.yaml 示例

```yaml
collector:
  product_count: 15
  community_count: 10
  leader_count: 15
  research_count: 15
  developer_count: 20
  news_count: 25
  max_total: 100

classification:
  mode: llm        # 可选: llm, rule
  provider: ollama
  model: Qwen3:8B
  batch_size: 10
  max_workers: 4

visualization:
  theme: default

output:
  report_dir: ./
  web_dir: ./web_output/

# 数据目录配置
data:
  exports_dir: data/exports    # 导出的数据和报告
  cache_dir: data/cache        # 缓存文件

# 日志配置
logging:
  level: INFO                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  dir: logs                    # 日志文件目录
  console: true                # 输出到控制台
  file: true                   # 输出到文件
  max_size_mb: 10              # 单个日志文件最大大小 (MB)
  backup_count: 2              # 备份文件数量
  retention_days: 3            # 日志保留天数
  format: standard             # standard 或 json
```

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

## 📊 内容分类

分类器将内容划分为六个维度：

| 类别 | 描述 | 示例 |
|------|------|------|
| `research` | 学术论文和研究 | arXiv 论文、基准测试结果 |
| `product` | 产品发布和更新 | GPT-4o 发布、新功能 |
| `market` | 商业和市场新闻 | 融资轮次、收购 |
| `developer` | 开发者工具和资源 | SDK、API、教程 |
| `leader` | 行业领袖观点 | CEO 访谈、主题演讲 |
| `community` | 社区讨论 | 热门话题、争论 |

## 🔧 版本对比

| 功能 | v1.0 (ai-world-tracker-v1) | v2.0 (main) |
|------|----------------------------|-------------|
| 分类方式 | 规则分类 | LLM + 规则降级 |
| LLM 支持 | ❌ | ✅ Ollama/OpenAI/Anthropic |
| 本地模型 | ❌ | ✅ Qwen3:8b |
| 并发处理 | ❌ | ✅ 多线程（3-6） |
| 智能缓存 | ❌ | ✅ MD5 缓存 |
| GPU 加速 | ❌ | ✅ 自动检测 |
| 统一日志 | ❌ | ✅ logger.py (带 emoji 去重) |
| 结构化数据目录 | ❌ | ✅ data/exports, data/cache |
| 日志自动清理 | ❌ | ✅ 可配置保留天数 |
| JSON 日志格式 | ❌ | ✅ 可选 |
| 测试组织 | 分散 | ✅ tests/ 目录 |
| 双语界面 | ❌ | ✅ 中/英文 |
| 资源清理 | ❌ | ✅ 退出时自动卸载 LLM |
| 缓存管理 | ❌ | ✅ 菜单清理缓存 |
| 准确率 | ~70% | ~95% |
| 适用场景 | 学习、自定义开发 | 生产环境 |

## 🧪 测试

测试文件组织在 `tests/` 目录中：

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_classifier_advanced.py -v

# 运行带覆盖率的测试
pytest tests/ --cov=. --cov-report=html
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🤝 参与贡献

我们欢迎各种形式的贡献！以下是参与方式：

1. **报告问题**：发现 Bug？[提交 Issue](https://github.com/legendyz/ai-world-tracker/issues)
2. **功能建议**：有好的想法？告诉我们！
3. **提交代码**：
   - Fork 仓库
   - 从 `feature/data-collection-v2` 创建功能分支
   - 提交 PR

### 开发工作流

```bash
# 克隆和设置
git clone https://github.com/legendyz/ai-world-tracker.git
cd ai-world-tracker
git checkout feature/data-collection-v2

# 创建功能分支
git checkout -b feature/your-feature

# 修改并测试
pytest tests/ -v

# 提交并推送
git commit -m "feat: add your feature"
git push origin feature/your-feature
```

## 📧 联系方式

- GitHub: [@legendyz](https://github.com/legendyz)
- 项目地址: [ai-world-tracker](https://github.com/legendyz/ai-world-tracker)

---

**⭐ 如果这个项目对你有帮助，请给它一个 Star！**
