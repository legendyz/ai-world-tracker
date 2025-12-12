# 🌍 AI World Tracker

[🇺🇸 English Version](README.md)

**AI World Tracker** 是一个全面的人工智能动态追踪和分析平台。它自动从多个权威来源采集数据，使用智能算法（LLM 或规则分类）对内容进行分类，并生成可视化趋势分析报告和网页仪表盘。

## 🌟 分支概览

| 分支 | 版本 | 描述 | 目标用户 |
|------|------|------|----------|
| `main` | v2.0 | **最新稳定版本**，集成完整 LLM 功能 + 异步数据采集 | 生产环境使用 |
| `ai-world-tracker-v2` | v2.0 | 稳定的 v2 版本，包含异步采集（性能提升 78%） | 生产环境使用 |
| `ai-world-tracker-v1` | v1.0 | 第一个完整版本，采用规则分类 | 学习和自定义开发 |
| `ai-world-tracker-v3-developing` | v3.0-dev | **下一代开发中** | 贡献者和测试者 |

### 选择合适的分支

- **生产环境使用**：使用 `main` 分支 - 经过完整测试，集成 LLM 增强分类和异步采集
- **稳定 v2 版本**：使用 `ai-world-tracker-v2` - 稳定的 v2 发布版，包含所有异步改进
- **学习/自定义开发**：使用 `ai-world-tracker-v1` - 架构简单，规则分类，易于修改
- **参与贡献**：使用 `ai-world-tracker-v3-developing` - 下一代功能开发中

## ✨ 核心功能

### 基础能力
- **🤖 多源数据采集**：自动从 arXiv（最新论文）、GitHub（热门项目）、科技媒体（TechCrunch、The Verge、Wired）以及 AI 博客（OpenAI、Google AI、Hugging Face）采集数据
- **⚡ 高性能纯异步采集**：基于 asyncio + aiohttp 的纯异步架构
  - 20+ 并发请求，智能限速（每主机最多 3 个）
  - URL 预过滤，使用规范化 URL 去重
  - 三层去重：MD5 指纹 + 语义相似度 + 字符串相似度
  - 7 天历史缓存，自动过期清理
- **🧠 智能分类**：双模式分类系统
  - **LLM 模式**：通过 Ollama/Azure OpenAI 进行语义理解（95%+ 准确率）
  - **规则模式**：基于关键词的模式识别（快速，无依赖）
- **📊 数据可视化**：生成技术热点、内容分布、地区分布和每日趋势图表
- **🌐 网页仪表盘**：创建带有分类新闻的响应式 HTML 仪表盘
- **🔄 智能缓存**：多模型缓存 + 断路器模式，确保 LLM 调用弹性
- **🌍 双语支持**：完整的中英文界面（i18n 国际化）

### LLM 集成
- **多提供商支持**：Ollama（免费、本地）、Azure OpenAI
- **本地模型**：通过 Ollama 使用 Qwen3:8b - 完全免费
- **GPU 加速**：自动检测 NVIDIA (CUDA)、AMD (ROCm)、Apple Silicon (Metal)
- **并发处理**：3-6 线程并行处理提升速度
- **自动降级**：LLM 不可用时优雅降级到规则分类
- **资源管理**：退出时自动卸载模型，释放显存/内存

### 数据采集性能 (v2.0)
| 指标 | 同步模式 | 异步模式 | 提升 |
|------|----------|----------|------|
| 采集耗时 | ~147秒 | ~32秒 | **快 78%** |
| 并发请求 | 6 线程 | 20+ 异步 | **3 倍** |
| 请求效率 | 0.14 req/s | 3.0 req/s | **21 倍** |

## 🛠️ 安装指南

### 环境要求

- Python 3.8+（Python 3.13+ 需要安装 `legacy-cgi` 包）
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
   
   # Python 3.13+ 还需要安装：
   pip install legacy-cgi
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
   
   # 或使用自动模式运行（非交互式）
   python TheWorldOfAI.py --auto
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
  3. 🤖 LLM模式 (Azure OpenAI) - 最高精度、需要API密钥

🧹 数据维护:
  4. 🗑️ 清除LLM分类缓存
  5. 🗑️ 清除采集历史缓存
  6. 🗑️ 清除采集结果历史
  7. 🗑️ 清除人工审核记录
  8. ⚠️ 清除所有数据（需要输入 YES 确认）

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
| 清除人工审核记录 | 🗑️ | 删除 `review_history_*.json` 和 `learning_report_*.json` 文件 |
| 清除所有数据 | ⚠️ | 清除所有缓存和数据文件（需要输入 YES 确认） |

## 📂 项目结构

```
ai-world-tracker/
├── TheWorldOfAI.py          # 主程序入口 (AIWorldTracker 类)
├── data_collector.py        # 多源数据采集（异步模式）
├── content_classifier.py    # 规则分类器
├── importance_evaluator.py  # 多维度重要性评估（5 个维度）
├── llm_classifier.py        # LLM 增强分类器 (Ollama/Azure OpenAI)
├── ai_analyzer.py           # 趋势分析引擎 (AIAnalyzer)
├── visualizer.py            # 数据可视化 - Matplotlib (DataVisualizer)
├── web_publisher.py         # 网页生成器 (WebPublisher)
├── manual_reviewer.py       # 人工审核界面 (ManualReviewer)
├── learning_feedback.py     # 学习反馈系统 (LearningFeedback)
├── config.py                # 统一配置管理
├── logger.py                # 统一日志系统（彩色控制台 + 文件）
├── i18n.py                  # 国际化（中/英文）
├── regenerate_web.py        # 快速网页重生成工具
├── requirements.txt         # Python 依赖
├── config.yaml              # 应用配置
├── pytest.ini               # 测试配置
├── data/                    # 生成的数据目录
│   ├── exports/             # 导出的数据和报告
│   │   ├── ai_tracker_data_*.json    # 带时间戳的采集数据
│   │   ├── ai_tracker_report_*.txt   # 文本报告
│   │   ├── review_history_*.json     # 人工审核记录
│   │   └── learning_report_*.json    # 学习反馈报告
│   └── cache/               # 缓存文件
│       ├── collection_history_cache.json  # URL/标题去重缓存（7天过期）
│       └── llm_classification_cache.json  # LLM 分类缓存（多模型支持）
├── tests/                   # 测试文件目录
│   ├── __init__.py
│   ├── test_classifier_*.py
│   ├── test_llm_*.py
│   ├── test_async_performance.py
│   └── ...
├── docs/                    # 技术文档
│   ├── ASYNC_OPTIMIZATION.md
│   ├── DATA_COLLECTOR_ARCHITECTURE.md
│   ├── IMPORTANCE_EVALUATOR_ANALYSIS.md
│   └── URL_PREFILTER_OPTIMIZATION.md
├── logs/                    # 日志文件目录（自动清理）
├── visualizations/          # 生成的图表 (PNG)
│   ├── tech_hotspots.png
│   ├── content_distribution.png
│   ├── region_distribution.png
│   ├── daily_trends.png
│   └── dashboard.png
├── web_output/              # 生成的网页（备份）
│   └── index.html
└── index.html               # 主仪表盘（GitHub Pages）
```

## 🏛️ 系统架构

### 模块依赖关系图

```
                              ┌─────────────────────┐
                              │   TheWorldOfAI.py   │
                              │    （主程序入口）    │
                              │   AIWorldTracker    │
                              └─────────┬───────────┘
                                        │
        ┌───────────────┬───────────────┼───────────────┬───────────────┐
        │               │               │               │               │
        ▼               ▼               ▼               ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│data_collector │ │content_       │ │ai_analyzer    │ │visualizer     │ │web_publisher  │
│   .py         │ │classifier.py  │ │   .py         │ │   .py         │ │   .py         │
│   数据采集     │ │   内容分类     │ │   趋势分析    │ │   数据可视化   │ │   网页生成    │
│               │ │               │ │               │ │               │ │               │
│• DataCollector│ │• Importance   │ │• AIAnalyzer   │ │• DataVisualizer│ │• WebPublisher │
│• collect_all()│ │  Evaluator    │ │• analyze_     │ │• visualize_   │ │• generate_    │
│               │ │• Content      │ │  trends()     │ │  all()        │ │  html_page()  │
│               │ │  Classifier   │ │               │ │               │ │               │
└───────┬───────┘ └───────┬───────┘ └───────────────┘ └───────────────┘ └───────────────┘
        │                 │
        │                 │         ┌───────────────┐
        │                 ├────────▶│llm_classifier │ (可选模块)
        │                 │         │   .py         │
        │                 │         │• LLMClassifier│
        │                 │         │• GPU自动检测  │
        │                 │         │• 多Provider   │
        │                 │         └───────────────┘
        │                 │
        │                 │         ┌───────────────┐
        │                 └────────▶│importance_    │
        │                           │evaluator.py   │
        │                           │• 5维度评分    │
        │                           └───────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              基础设施层                                      │
├───────────────┬───────────────┬───────────────┬─────────────────────────────┤
│  config.py    │  logger.py    │   i18n.py     │ manual_reviewer.py          │
│   配置管理     │   日志系统     │   国际化      │ learning_feedback.py        │
│               │               │               │   人工反馈闭环               │
│• OllamaConfig │• get_log_     │• t() 翻译函数 │• ManualReviewer 人工审核    │
│• AzureOpenAI  │  helper()     │• LANG_PACKS   │• LearningFeedback 学习优化  │
│  Config       │• dual_* 方法  │• 中/英语言包  │                             │
│• Classifier   │• 彩色输出     │               │                             │
│  Config       │• 自动清理     │               │                             │
└───────────────┴───────────────┴───────────────┴─────────────────────────────┘
```

### 主菜单功能映射

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              主菜单功能                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. 🚀 自动更新数据与报告                                                    │
│     └── run_full_pipeline()                                                  │
│         → 数据采集 → 内容分类 → 智能分析 → 可视化 → Web生成                   │
│                                                                              │
│  2. 🌐 生成并打开 Web 页面                                                   │
│     └── _generate_web_page()                                                 │
│         → 基于现有数据重新生成网页                                             │
│                                                                              │
│  3. 📝 人工审核分类                                                          │
│     └── _manual_review()                                                     │
│         → 筛选低置信度 → 交互审核 → 保存历史 → 可选重新生成                     │
│                                                                              │
│  4. 🎓 学习反馈分析                                                          │
│     └── _learning_feedback()                                                 │
│         → 分析审核历史 → 提取模式 → 生成改进建议                               │
│                                                                              │
│  5. ⚙️ 设置与管理                                                            │
│     └── _switch_classification_mode()                                        │
│         ├── 分类模式: Rule / Ollama / Azure OpenAI                           │
│         └── 数据维护: 清除缓存 / 历史 / 审核记录                               │
│                                                                              │
│  0. 退出程序                                                                 │
│     └── cleanup() + 保存配置                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📰 数据来源

### 研究论文
- arXiv API (cs.AI, cs.LG, cs.CV, cs.CL, cs.NE, stat.ML)

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
- GitHub Trending（AI/ML 热门仓库）
- Hugging Face（模型与论文）
- GitHub 博客
- Hugging Face 博客
- OpenAI 博客
- Google AI 博客
- Anthropic 博客
- DeepMind 博客

### 社区与领袖
- Product Hunt AI
- Hacker News AI（使用官方 API）
- **AI 领袖跟踪**：
  - Sam Altman（OpenAI CEO）
  - Satya Nadella（微软 CEO）
  - Sundar Pichai（谷歌 CEO）
  - Jensen Huang/黄仁勋（NVIDIA CEO）
  - Mark Zuckerberg（Meta CEO）
  - Elon Musk/马斯克（xAI/特斯拉 CEO）
  - Demis Hassabis（Google DeepMind CEO）
  - Yann LeCun/杨立昌（Meta 首席 AI 科学家）
  - Geoffrey Hinton/辛顿（AI 先驱）
  - Andrew Ng/吴恩达（AI Fund 管理合伙人）
  - Kai-Fu Lee/李开复（01.AI CEO）
  - Robin Li/李彦宏（百度 CEO）

## 🔄 数据处理流程

### 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI World Tracker 数据流程                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ 数据采集模块 │ →  │ 内容分类模块 │ →  │ 重要性评估  │              │
│  │DataCollector │    │  Classifier  │    │  Evaluator   │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         ↓                   ↓                   ↓                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ 去重与过滤  │    │   MD5缓存   │    │  多维评分   │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         ↓                   ↓                   ↓                       │
│  ┌───────────────────────────────────────────────────────┐             │
│  │                    趋势分析与可视化                    │             │
│  │                     (AIAnalyzer)                      │             │
│  └───────────────────────────────────────────────────────┘             │
│         ↓                                                               │
│  ┌──────────────┐    ┌──────────────┐                                  │
│  │  网页生成   │    │  报告导出   │                                  │
│  │WebPublisher │    │   Export    │                                  │
│  └──────────────┘    └──────────────┘                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 数据采集模块 (DataCollector)

采集器使用**纯异步架构**以实现最佳性能：

**异步模式 (asyncio + aiohttp)**
- 使用 `asyncio` + `aiohttp` 实现真正的异步 I/O
- 全局 20 个并发请求，每主机最多 3 个（智能限速）
- 使用 `asyncio.as_completed()` 实时进度跟踪
- 自动重试，指数退避策略

**三层去重系统**
- **MD5 指纹**：基于哈希的精确重复检测
- **语义相似度**：基于规范化词元的 Jaccard 相似度（阈值：0.6）
- **字符串相似度**：difflib SequenceMatcher 模糊匹配（阈值：0.85）

| 数据类型 | 来源 | 采集方式 | 默认数量 |
|----------|------|----------|----------|
| 研究论文 | arXiv API | API 调用 | 15 条 |
| 开发者内容 | GitHub Blog, HuggingFace | RSS + API | 20 条 |
| 产品发布 | 官方博客 | RSS | 15 条 |
| 领袖言论 | 个人博客/播客 | RSS | 15 条 |
| 社区热点 | HN (API) + Product Hunt | API + RSS | 10 条 |
| 行业新闻 | 中外科技媒体 | RSS | 25 条 |

**特点**：
- **纯异步架构**：所有采集任务并发执行
- **URL 预过滤**：发送请求前进行规范化 URL 检查
- **多层去重**：MD5 + 语义 + 字符串相似度
- **历史缓存**：URL、标题和规范化标题，7 天过期
- **AI 相关性过滤**：提前过滤非 AI 内容
- **可配置配额**：按类别限制数量，确保均衡采集

### 内容分类模块

#### LLM 分类器运行逻辑

```
输入内容
    ↓
计算 MD5 哈希 → 命中缓存？ → 是 → 返回缓存结果
    ↓ 否
构建分类提示词
    ↓
调用 LLM API（支持批量）
    ↓
解析 JSON 响应 → 失败？ → 降级到规则分类
    ↓ 成功
写入缓存
    ↓
返回分类结果
```

#### 规则分类器运行逻辑

```
输入内容
    ↓
提取标题 + 摘要文本
    ↓
┌─────────────────────────────────────────┐
│ 并行匹配六类关键词词典                   │
│ research / product / market /           │
│ developer / leader / community          │
│ (每类词典含权重：高3分/中2分/低1分)      │
└─────────────────────────────────────────┘
    ↓
计算各类别得分
    ↓
选择最高分类别 + 计算置信度
    ↓
短语模式匹配验证
    ↓
返回分类结果
```

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
  parallel_enabled: true    # 启用并行采集（同步模式）
  parallel_workers: 6       # 同步模式最大线程数
  async_mode: true          # 使用异步模式（推荐）

# 异步采集器配置
async_collector:
  max_concurrent_requests: 20    # 最大并发请求数
  max_concurrent_per_host: 3     # 每主机最大并发数
  request_timeout: 15            # 请求超时（秒）
  total_timeout: 120             # 总采集超时
  max_retries: 2                 # 最大重试次数
  retry_delay: 1.0               # 重试延迟（秒）
  rate_limit_delay: 0.2          # 限速延迟（秒）

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
  retention_days: 3            # 日志保留天数（自动清理）
  format: standard             # standard 或 json
```

### LLM 提供商

| 提供商 | 模型 | 费用 | 配置方式 |
|--------|------|------|----------|
| Ollama | qwen3:8b | 免费 | `ollama pull qwen3:8b` |
| Azure OpenAI | gpt-4o-mini, gpt-4o | 付费 | 通过菜单配置（选项 3） |

### 环境变量

```bash
# 可选：Ollama 自定义 URL
export OLLAMA_BASE_URL="http://localhost:11434"

# Azure OpenAI 通过菜单交互式配置
# 无需设置环境变量
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

## 🏗️ 分类系统架构

### 架构概览

系统采用**双模式分类架构**，支持自动降级：

```
┌─────────────────────────────────────────────────────────────┐
│                      分类处理流水线                           │
├─────────────────────────────────────────────────────────────┤
│  输入数据                                                     │
│      ↓                                                        │
│  ┌─────────────────┐    ┌─────────────────┐                  │
│  │  LLM 分类器     │ 或 │  规则分类器     │                  │
│  │  (主分类器)     │    │  (备用降级)     │                  │
│  └────────┬────────┘    └────────┬────────┘                  │
│           ↓                      ↓                            │
│  ┌─────────────────────────────────────────┐                 │
│  │         重要性评估器                     │                 │
│  │     (多维度权重评分系统)                 │                 │
│  └─────────────────────────────────────────┘                 │
│           ↓                                                   │
│  输出: 分类类别, 重要性分数, 置信度, 评分明细                  │
└─────────────────────────────────────────────────────────────┘
```

### LLM 分类器 (`llm_classifier.py`)

LLM 增强分类器提供语义理解能力：

- **多提供商支持**：Ollama（本地）、Azure OpenAI
- **多模型缓存**：缓存 key 格式 `{内容哈希}:{模型标识}`，不同模型缓存独立共存
- **断路器模式**：连续失败 5 次后自动断开，60 秒后自动恢复
- **智能降级策略**：根据错误类型（超时、连接错误、解析错误等）采取不同降级动作
- **HTTP 连接池复用**：Session 复用 + 重试策略（3 次重试，指数退避）
- **并发处理**：3-6 线程并行分类（GPU 模式 6 线程）
- **GPU 自动检测**：支持 NVIDIA (CUDA)、AMD (ROCm)、Apple Silicon (Metal)
- **模型保活**：5 分钟保活时间，避免冷启动
- **缓存格式校验**：自动检测并清理过时缓存格式

### 规则分类器 (`content_classifier.py`)

基于关键词的规则分类器：

- **关键词匹配**：针对不同类别的关键词词典
- **置信度评分**：基于关键词匹配强度计算
- **快速处理**：无网络依赖，即时返回结果

## ⚖️ 多维度重要性评估

`ImportanceEvaluator` 使用 **5 个加权维度** 计算内容重要性：

### 维度权重配置

| 维度 | 权重 | 说明 |
|------|------|------|
| **来源权威度** (source_authority) | 25% | 内容来源的可信度 |
| **时效性** (recency) | 25% | 内容的新鲜程度 |
| **分类置信度** (confidence) | 20% | 分类结果的置信度（支持置信度上限） |
| **内容相关度** (relevance) | 20% | 与 AI 话题的相关性 |
| **社交热度** (engagement) | 10% | 社交信号（星标、下载量等） |

### 置信度上限机制

在 7 天采集窗口内，系统应用置信度上限来平衡内容排名：

| 内容时效 | 来源权威度 | 置信度上限 |
|----------|-----------|------------|
| 5-7 天 | < 0.70（低权威） | 75% |
| 3-5 天 | < 0.60（极低权威） | 85% |
| ≤ 3 天 | 任意 | 无上限 |

### 计算公式

```
重要性分数 = Σ (维度分数 × 权重)

具体计算:
- source_authority × 0.25
- recency × 0.25
- confidence × 0.20 （可能受置信度上限影响）
- relevance × 0.20
- engagement × 0.10
```

### 来源权威度评分

| 来源类型 | 分数范围 | 示例 |
|----------|----------|------|
| AI 官方公司 | 0.90 - 1.00 | OpenAI、Google AI、Anthropic、Meta AI |
| 中国 AI 公司 | 0.85 - 0.90 | 百度、阿里、腾讯、DeepSeek、智谱、月之暗面 |
| 学术/研究 | 0.90 - 0.95 | arXiv、GitHub、Hugging Face |
| 专业媒体 | 0.70 - 0.85 | TechCrunch、The Verge、机器之心、量子位 |
| 社区 | 0.65 - 0.70 | Hacker News、Reddit、Product Hunt |
| 未知来源 | 0.40 | 默认分数 |

### 时效性衰减曲线（7 天采集窗口）

由于系统只采集**最近 7 天**的内容，时效性评分针对此窗口进行了优化。

系统采用指数衰减公式：`score = (1 - min_score) × e^(-decay_rate × days) + min_score`

| 时间 | 分数 | 说明 |
|------|------|------|
| 今天 | 1.00 | 最新鲜 |
| 1 天前 | ~0.89 | 非常新 |
| 2 天前 | ~0.79 | 新鲜 |
| 3 天前 | ~0.70 | 较新 |
| 5 天前 | ~0.56 | 周中 |
| 7 天前 | ~0.44 | 周边界（最旧采集） |

**参数配置**：
- 衰减率 (decay_rate): 0.12
- 最低分数 (min_score): 0.08
- 采集窗口: 7 天（可通过 `data_retention_days` 配置）

### 内容相关度评估（分层关键词系统）

系统采用四层关键词权重体系：

| 层级 | 权重系数 | 类型 | 示例关键词 |
|------|----------|------|------------|
| 第一层 | 0.12-0.18 | 突破性/里程碑 | breakthrough, SOTA, 突破, 里程碑 |
| 第二层 | 0.08-0.12 | 发布/公告 | release, launch, 发布, 上线 |
| 第三层 | 0.05-0.10 | 技术/模型 | open source, LLM, 开源, 大模型 |
| 第四层 | 0.02-0.05 | 一般性描述 | new, update, 最新, 更新 |

**负面关键词降权**：传闻、未经证实等内容会被降低相关度分数（-0.02 ~ -0.08）

### 社交热度评估（统一归一化）

采用对数归一化公式：`score = log(value + 1) / log(threshold_high + 1) × weight`

| 信号类型 | 低阈值 | 高阈值 | 权重 |
|----------|--------|--------|------|
| GitHub Stars | 100 | 50,000 | 1.0 |
| HuggingFace Downloads | 1,000 | 1,000,000 | 0.9 |
| Reddit Score | 50 | 5,000 | 0.85 |
| HN Points | 30 | 1,000 | 0.85 |
| Likes | 100 | 10,000 | 0.7 |
| Comments | 20 | 500 | 0.6 |

### 重要性等级

| 分数范围 | 等级 | 标识 |
|----------|------|------|
| ≥ 0.85 | 关键 | 🔴 |
| ≥ 0.70 | 高 | 🟠 |
| ≥ 0.55 | 中 | 🟡 |
| ≥ 0.40 | 低 | 🟢 |
| < 0.40 | 最低 | ⚪ |

### 输出示例

```json
{
  "title": "OpenAI 发布 GPT-5",
  "category": "product",
  "importance": 0.892,
  "confidence": 0.95,
  "importance_breakdown": {
    "source_authority": 1.0,
    "recency": 0.95,
    "confidence": 0.95,
    "relevance": 0.85,
    "engagement": 0.5
  }
}
```

## 🔧 版本对比

| 功能 | v1.0 (ai-world-tracker-v1) | v2.0 (main / ai-world-tracker-v2) | v3.0-dev (开发中) |
|------|----------------------------|-----------------------------------|------------------|
| 分类方式 | 规则分类 | LLM + 规则降级 | 待定 |
| LLM 支持 | ❌ | ✅ Ollama/Azure OpenAI | ✅ |
| 本地模型 | ❌ | ✅ Qwen3:8b | ✅ |
| 数据采集 | 仅同步 | ✅ **异步优先（快 78%）** | ✅ |
| URL 预过滤 | ❌ | ✅ 跳过已缓存 URL | ✅ |
| 并发处理 | ❌ | ✅ 20+ 异步请求 | ✅ |
| 智能缓存 | ❌ | ✅ MD5 缓存 | ✅ |
| GPU 加速 | ❌ | ✅ 自动检测 | ✅ |
| 统一日志 | ❌ | ✅ logger.py | ✅ |
| 日志自动清理 | ❌ | ✅ 可配置保留天数 | ✅ |
| 结构化数据目录 | ❌ | ✅ data/exports, data/cache | ✅ |
| 测试组织 | 分散 | ✅ tests/ 目录 | ✅ |
| 双语界面 | ❌ | ✅ 中/英文 | ✅ |
| 资源清理 | ❌ | ✅ 退出时自动卸载 LLM | ✅ |
| 置信度上限 | ❌ | ✅ 旧内容置信度限制 | ✅ |
| 重要性评估 | ❌ | ✅ 5 维度评分 | ✅ |
| 准确率 | ~70% | ~95% | 待定 |
| 采集速度 | 基准 | **~32秒（快 78%）** | 待定 |
| 适用场景 | 学习开发 | 生产环境 | 下一代开发 |

## 🧪 测试

测试文件组织在 `tests/` 目录中：

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_classifier_advanced.py -v

# 运行异步性能测试
pytest tests/test_async_performance.py -v

# 运行带覆盖率的测试
pytest tests/ --cov=. --cov-report=html
```

## 📚 技术文档

技术文档位于 `docs/` 目录：

| 文档 | 描述 |
|------|------|
| [ASYNC_OPTIMIZATION.md](docs/ASYNC_OPTIMIZATION.md) | 异步采集架构和 78% 性能提升 |
| [DATA_COLLECTOR_ARCHITECTURE.md](docs/DATA_COLLECTOR_ARCHITECTURE.md) | 双模式（同步/异步）采集器设计 |
| [IMPORTANCE_EVALUATOR_ANALYSIS.md](docs/IMPORTANCE_EVALUATOR_ANALYSIS.md) | 5 维度重要性评分系统 |
| [URL_PREFILTER_OPTIMIZATION.md](docs/URL_PREFILTER_OPTIMIZATION.md) | URL 预过滤跳过已缓存内容 |

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🤝 参与贡献

我们欢迎各种形式的贡献！以下是参与方式：

1. **报告问题**：发现 Bug？[提交 Issue](https://github.com/legendyz/ai-world-tracker/issues)
2. **功能建议**：有好的想法？告诉我们！
3. **提交代码**：
   - Fork 仓库
   - 从 `ai-world-tracker-v3-developing` 创建功能分支
   - 提交 PR

### 开发工作流

```bash
# 克隆和设置
git clone https://github.com/legendyz/ai-world-tracker.git
cd ai-world-tracker
git checkout ai-world-tracker-v3-developing

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
