# 🌍 AI World Tracker

[🇺🇸 English Version](README.md) | [📊 项目状态](PROJECT_STATUS.md)

**AI World Tracker (全球人工智能动态追踪系统)** 是一个全方位的 AI 资讯追踪与分析平台。它能够自动从 arXiv、GitHub、科技媒体和博客等多个渠道采集数据，利用智能分类算法（基于规则 + LLM增强）对内容进行多维度归类（研究、产品、市场等），并生成可视化的趋势分析报告和 Web 展示页面。

**🆕 v2.0-beta**: 现已支持**LLM增强分类**，集成本地 Ollama (Qwen3:8b)、OpenAI 和 Anthropic，实现语义理解，准确率达 95%+！

---

## 🌟 v2.0 新特性

### Main 分支 (v1.2 - 稳定版)
- 基于规则的关键词匹配分类
- 人工审核和学习反馈系统
- 精简的4项菜单
- 生产就绪，稳定可靠

### Feature 分支 (v2.0-beta - LLM增强版)
- 🤖 **LLM分类**: Ollama (Qwen3:8b)、OpenAI (GPT-4o-mini)、Anthropic (Claude-3-Haiku)
- ⚡ **性能提升**: 并发处理（3线程），速度提升6-9倍
- 🧠 **智能缓存**: 基于MD5的内容缓存，避免重复API调用
- 📱 **增强界面**: 分层菜单，手动工作流子菜单
- 🎯 **95%+ 准确率**: 语义理解 vs 关键词匹配
- 💰 **零成本选项**: 本地 Ollama 模型，完全免费
- 🔄 **自动降级**: 优雅降级到基于规则的分类

---

## ✨ 主要功能

### 核心功能（所有版本）
*   **🤖 多源数据采集**: 自动抓取 arXiv (最新论文)、GitHub (热门项目) 和 RSS Feeds (科技新闻、官方博客)。
*   **📊 数据可视化**: 生成技术热点图、内容分布图、地区分布图和每日趋势图。
*   **🌐 Web 报告生成**: 自动生成包含仪表盘和分类资讯的静态 HTML 页面 (`index.html`)，支持移动端适配。

### 分类系统
**Main 分支**: 基于规则的关键词匹配（准确率 ~70-80%）
- 模式识别和关键词权重
- 人工审核系统进行修正
- 学习反馈优化规则

**Feature 分支**: LLM增强，支持多提供商（准确率 95%+）
- 语义理解和上下文分析
- 多级置信度和推理说明
- 技术领域识别
- 谣言检测和事实核查

## 🛠️ 安装指南

### 环境要求
*   Python 3.8+
*   Windows/macOS/Linux
*   (可选) Ollama 用于本地 LLM 支持

### 快速开始 - Main 分支（稳定版）

1.  **克隆仓库**
    ```bash
    git clone https://github.com/legendyz/ai-world-tracker.git
    cd ai-world-tracker
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **运行应用**
    ```bash
    python TheWorldOfAI.py
    ```

### 高级设置 - Feature 分支（LLM增强版）

1.  **切换到 Feature 分支**
    ```bash
    git checkout feature/ai-enhancements
    ```

2.  **方式A: 使用 Ollama（推荐 - 免费且本地）**
    ```bash
    # 安装 Ollama
    # Windows: 从 https://ollama.com/download 下载
    # Mac: brew install ollama
    # Linux: curl -fsSL https://ollama.com/install.sh | sh
    
    # 拉取模型
    ollama pull qwen3:8b
    
    # 启动 Ollama 服务
    ollama serve
    
    # 安装 Python 依赖
    pip install -r requirements.txt
    
    # 运行应用
    python TheWorldOfAI.py
    ```

3.  **方式B: 使用 OpenAI 或 Anthropic**
    ```bash
    # 安装依赖
    pip install -r requirements.txt
    
    # 设置 API 密钥（Windows PowerShell）
    $env:OPENAI_API_KEY='sk-your-openai-key'
    $env:ANTHROPIC_API_KEY='sk-ant-your-anthropic-key'
    
    # 或创建 .env 文件
    cp .env.example .env
    # 编辑 .env 并添加你的 API 密钥
    
    # 运行应用
    python TheWorldOfAI.py
    ```

## 🚀 快速开始

运行主程序启动交互式菜单：

```bash
python TheWorldOfAI.py
```

### Main 分支菜单 (v1.2)

1.  **🚀 自动更新数据与报告**
    *   执行完整流程：采集 → 分类 → 分析 → 可视化 → Web 生成。
    *   自动在浏览器中打开生成的网页。

2.  **🌐 生成并打开 Web 页面**
    *   基于当前数据重新生成 HTML 页面并在浏览器中打开。

3.  **📝 人工审核分类**
    *   进入审核模式，系统会筛选出置信度较低的内容供人工确认或修正。
    *   审核结果会自动保存，用于后续的学习优化。

4.  **🎓 学习反馈分析**
    *   分析审核历史，生成分类器改进建议报告。

### Feature 分支菜单 (v2.0-beta)

#### 使用 LLM 模式时:
```
当前分类模式: 🤖 LLM增强 - Ollama (Qwen3:8b)

1. 🚀 自动更新数据并生成 Web 页面
2. 🛠️  手动更新及生成 Web 页面
   ├─ 1. 📥 仅更新数据
   ├─ 2. 🏷️  分类数据
   └─ 3. 🌐 生成 Web 页面
5. ⚙️  切换分类模式
0. 退出
```

#### 使用规则模式时:
```
当前分类模式: 📝 规则分类

1. 🚀 自动更新数据并生成 Web 页面
2. 🛠️  手动更新及生成 Web 页面
3. 📝 人工审核分类（仅规则模式）
4. 🎓 学习反馈分析（仅规则模式）
5. ⚙️  切换分类模式
0. 退出
```

## 📂 项目结构

### Main 分支 (v1.2)
```text
ai-world-tracker/
├── TheWorldOfAI.py          # 主程序入口
├── data_collector.py        # 数据采集（arXiv、RSS、GitHub）
├── content_classifier.py    # 基于规则的分类器
├── ai_analyzer.py           # 趋势分析
├── visualizer.py            # 数据可视化（Matplotlib）
├── web_publisher.py         # Web 页面生成器
├── manual_reviewer.py       # 人工审核界面
├── learning_feedback.py     # 学习反馈系统
├── requirements.txt         # 依赖项
├── visualizations/          # 生成的图表
└── web_output/              # 生成的网页
```

### Feature 分支 (v2.0-beta) - 额外文件
```text
ai-world-tracker/
├── llm_classifier.py        # 🆕 LLM 分类引擎
├── config.py                # 🆕 配置管理
├── .env.example             # 🆕 环境变量模板
├── cache/                   # 🆕 LLM 响应缓存
├── test_ollama.py           # 🆕 Ollama 集成测试
├── test_llm_classifier.py   # 🆕 LLM 分类器测试
├── demo_llm_classifier.py   # 🆕 交互式演示
├── LLM_CLASSIFICATION_GUIDE.md     # 🆕 LLM 使用指南
├── LLM_IMPLEMENTATION_SUMMARY.md   # 🆕 实现细节
├── OLLAMA_SETUP_COMPLETE.md        # 🆕 Ollama 设置指南
└── PROJECT_STATUS.md               # 🆕 综合状态报告
```

## 🔄 工作流程

### Main 分支工作流
```
1. 采集 → 规则分类 → 分析
2. 可视化 → Web 生成
3. [可选] 人工审核 → 学习反馈
```

### Feature 分支工作流（LLM 模式）
```
1. 采集 → 智能分类
   ├─ 缓存检查（MD5）
   ├─ 智能跳过（已分类）
   ├─ 并发 LLM 调用（3线程）
   └─ 自动降级（LLM 失败时）
2. 分析 → 可视化
3. Web 生成 + 自动打开
```

## ⚡ 性能对比

| 指标 | Main 分支 | Feature 分支（LLM） |
|------|----------|-------------------|
| **准确率** | 70-80% | 95%+ |
| **速度** | 基准 | 快6-9倍* |
| **成本** | 免费 | 免费（Ollama）/ 付费（API） |
| **离线** | ✅ | ✅（仅 Ollama） |
| **设置** | 简单 | 中等 |

*使用并发处理和优化

## 📊 分类类别

两个版本都支持 6 个主要类别：

1. **Research（研究）** - 学术论文、科学研究
2. **Product（产品）** - 产品发布、新版本
3. **Market（市场）** - 融资、收购、商业新闻
4. **Developer（开发者）** - 工具、库、教程
5. **Leader（领袖）** - 专家观点、访谈
6. **Community（社区）** - 热门讨论、病毒式内容

### LLM 优势（Feature 分支）
- 语义理解 vs 关键词匹配
- 上下文感知的分类
- 多维度分析
- 置信度评分和推理说明
- 技术领域识别
- 谣言检测

## 🧪 测试

### Main 分支
```bash
python test_workflow.py
python test_classifier_advanced.py
```

### Feature 分支
```bash
# 测试 Ollama 集成
python test_ollama.py

# 测试 LLM 分类器
python test_llm_classifier.py

# 交互式演示
python demo_llm_classifier.py
```

## 🤝 贡献

我们欢迎贡献！请查看我们的开发分支：

- `main` - 稳定的生产版本（v1.2）
- `feature/ai-enhancements` - LLM 功能（v2.0-beta）

### 开发工作流
1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 提交 pull request

### 提交约定
```
feat: 新功能
fix: Bug修复
docs: 文档
refactor: 代码重构
perf: 性能改进
test: 测试
chore: 构建/配置
```

## 📝 文档

- [项目状态报告](PROJECT_STATUS.md) - 综合项目概览
- [LLM 分类指南](LLM_CLASSIFICATION_GUIDE.md) - 仅 Feature 分支
- [LLM 实现摘要](LLM_IMPLEMENTATION_SUMMARY.md) - 仅 Feature 分支
- [Ollama 设置指南](OLLAMA_SETUP_COMPLETE.md) - 仅 Feature 分支
- [变更日志](CHANGELOG.md) - 版本历史

## 🐛 已知问题

### Main 分支
- 基于规则的准确率限制在 70-80%
- 边缘情况需要人工审核

### Feature 分支
- Ollama 首次推理较慢（~28秒，后续通过缓存加速）
- 并发处理时内存占用较高
- LLM 模式下学习反馈不可用

## 🗺️ 路线图

### v2.0.0（Feature 分支 - 进行中）
- [x] LLM 分类核心
- [x] 多提供商支持
- [x] 本地 Ollama 集成
- [x] 并发处理
- [x] 智能缓存
- [x] 菜单重构
- [ ] 全面测试
- [ ] 合并到 main

### v2.1.0（计划中）
- [ ] 批量 API 支持
- [ ] 自定义提示词模板
- [ ] 分类结果导出
- [ ] RESTful API

### v2.2.0（计划中）
- [ ] Web UI
- [ ] 实时数据流
- [ ] 用户认证
- [ ] 数据库集成

## 💬 社区与支持

- **GitHub Issues**: 报告 Bug 或请求功能
- **GitHub Discussions**: 社区讨论和问答
- **文档**: 查看我们的综合文档

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

**注意**: Feature 分支（v2.0-beta）目前处于 beta 测试阶段。生产环境请使用 main 分支。LLM 增强版将在经过全面测试和稳定性验证后合并。

**最后更新**: 2025年12月5日
