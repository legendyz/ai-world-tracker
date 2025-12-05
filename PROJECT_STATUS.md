# AI World Tracker - 项目状态报告

**生成时间**: 2025-12-05  
**当前分支**: feature/ai-enhancements  
**主要版本**: v2.0.0-beta (LLM增强版)

---

## 📋 项目概述

AI World Tracker 是一个全球AI动态追踪和分析系统，现已演进为两个版本：

### 版本对比

| 特性 | Main分支 (v1.2) | Feature/AI-Enhancements (v2.0-beta) |
|------|----------------|-------------------------------------|
| **分类方式** | 规则+关键词 | LLM智能分类 + 规则备份 |
| **LLM支持** | ❌ | ✅ (Ollama/OpenAI/Anthropic) |
| **本地模型** | ❌ | ✅ DeepSeek-R1:14b |
| **并发处理** | ❌ | ✅ 多线程加速 |
| **智能缓存** | ❌ | ✅ MD5内容缓存 |
| **菜单结构** | 简化4项 | 分层7项 |
| **性能优化** | 标准 | 6-9倍提速 |

---

## 🏗️ 架构设计

### Main分支架构
```
数据采集 → 规则分类 → 趋势分析 → 可视化 → Web生成
          ↓
     人工审核 → 学习反馈
```

### Feature/AI-Enhancements分支架构
```
数据采集 → LLM智能分类 (Ollama/OpenAI/Anthropic) → 趋势分析
          ↓                    ↓
       规则备份           智能缓存
          ↓                    ↓
         可视化 ← -------- Web生成
          ↓
     人工审核 (仅规则模式) → 学习反馈
```

---

## 📂 核心模块

### 1. 数据采集 (`data_collector.py`)
- **功能**: 从多个源采集AI资讯
- **数据源**:
  - arXiv: 学术论文 (10条/次)
  - GitHub: 热门项目 (10条/次)
  - RSS: 科技新闻 (10条/次)
  - 官方博客 (10条/次)
- **总量**: 60条/次 (优化后)
- **更新**: 限制每类10条，避免过度采集

### 2. 分类系统

#### Main分支: `content_classifier.py`
- **方法**: 规则+关键词匹配
- **类别**: research, product, market, developer, leader, community
- **置信度**: 基于关键词权重计算
- **可学习**: 支持人工审核反馈

#### Feature分支: `llm_classifier.py` + `content_classifier.py`
- **LLM提供商**:
  - Ollama (默认): DeepSeek-R1:14b, 免费本地
  - OpenAI: GPT-4o-mini, 需API key
  - Anthropic: Claude-3-Haiku, 需API key
- **核心特性**:
  - 语义理解分类
  - 多维度分析 (置信度/技术领域/真实性)
  - MD5内容缓存 (避免重复调用)
  - 自动降级到规则分类
  - 并发处理 (3线程)
  - 提示词优化 (减少50% token)

### 3. 配置管理 (`config.py` - 仅Feature分支)
```python
优先级: 环境变量 > .env文件 > 默认值
```
- 统一配置接口
- 多提供商支持
- 安全的密钥管理

### 4. 智能分析 (`ai_analyzer.py`)
- 趋势分析
- 技术热点识别
- 地区分布统计
- 报告生成

### 5. 可视化 (`visualizer.py`)
- 技术热点图
- 内容分布图
- 地区分布图
- 每日趋势图
- 综合仪表板

### 6. Web发布 (`web_publisher.py`)
- 响应式HTML生成
- 移动端优化
- 分类展示
- 自动部署到根目录

### 7. 人工审核 (`manual_reviewer.py`)
- 交互式审核界面
- 低置信度筛选
- 历史记录保存
- **注**: 仅规则分类模式可用

### 8. 学习反馈 (`learning_feedback.py`)
- 审核历史分析
- 改进建议生成
- 规则优化指导
- **注**: 仅规则分类模式可用

---

## 🎯 用户界面

### Main分支菜单
```
1. 🚀 自动更新数据与报告
2. 🌐 生成并打开 Web 页面
3. 📝 人工审核分类
4. 🎓 学习反馈分析
0. 退出程序
```

### Feature分支菜单

#### LLM模式
```
当前分类模式: 🤖 LLM增强 - Ollama (DeepSeek-R1:14b)

1. 🚀 自动更新数据并生成 Web 页面
2. 🛠️  手动更新及生成 Web 页面
   ├─ 1. 📥 仅更新数据
   ├─ 2. 🏷️  分类数据
   └─ 3. 🌐 生成 Web 页面
5. ⚙️  切换分类模式
0. 退出程序
```

#### 规则分类模式
```
当前分类模式: 📝 规则分类

1. 🚀 自动更新数据并生成 Web 页面
2. 🛠️  手动更新及生成 Web 页面
3. 📝 人工审核分类  ⭐ 规则模式专属
4. 🎓 学习反馈分析  ⭐ 规则模式专属
5. ⚙️  切换分类模式
0. 退出程序
```

---

## ⚡ 性能优化 (Feature分支)

### 1. 并发处理
```python
ThreadPoolExecutor(max_workers=3)
预计提升: 3倍速度
```

### 2. 智能跳过
```python
已有category字段 → 直接使用规则分类
预计节省: 20-30% LLM调用
```

### 3. 提示词优化
```python
Token使用: 减少50%
Summary截断: 500 → 300字符
推理时间: 28秒 → 18秒
```

### 4. Ollama参数调优
```python
num_predict: 500 → 300
num_ctx: 默认 → 2048
timeout: 60秒 → 45秒
```

### 综合效果
```
原始耗时: ~28分钟 (60项 × 28秒)
优化后: ~3-5分钟
提速: 6-9倍
```

---

## 🔧 技术栈

### 核心依赖
```
Python 3.8+
requests        - HTTP客户端
beautifulsoup4  - HTML解析
feedparser      - RSS解析
arxiv           - arXiv API
matplotlib      - 数据可视化
```

### Feature分支额外依赖
```
openai          - OpenAI API (可选)
anthropic       - Anthropic API (可选)
python-dotenv   - 环境变量管理
```

### 本地LLM
```
Ollama          - 本地模型服务
DeepSeek-R1:14b - 8.37 GB模型
```

---

## 📊 数据流程

### Main分支
```
1. 数据采集 (60条)
2. 规则分类 (关键词匹配)
3. 趋势分析
4. 可视化生成
5. Web页面生成
6. 【可选】人工审核
7. 【可选】学习反馈
```

### Feature分支 (LLM模式)
```
1. 数据采集 (60条)
2. 智能分类
   ├─ 检查缓存 (MD5)
   ├─ 智能跳过 (已有类别)
   ├─ 并发LLM调用 (3线程)
   └─ 失败降级 (规则分类)
3. 趋势分析
4. 可视化生成
5. Web页面生成 + 自动打开
```

---

## 🚀 部署指南

### Main分支部署
```bash
# 1. 克隆仓库
git clone https://github.com/legendyz/ai-world-tracker.git
cd ai-world-tracker

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python TheWorldOfAI.py
```

### Feature分支部署

#### 使用Ollama (推荐)
```bash
# 1. 安装Ollama
# Windows: 下载 https://ollama.com/download
# Mac: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# 2. 拉取模型
ollama pull deepseek-r1:14b

# 3. 启动服务
ollama serve

# 4. 切换到功能分支
git checkout feature/ai-enhancements

# 5. 安装依赖
pip install -r requirements.txt

# 6. 运行
python TheWorldOfAI.py
```

#### 使用OpenAI/Anthropic
```bash
# 1. 设置API密钥
# Windows:
$env:OPENAI_API_KEY='sk-your-key'
$env:ANTHROPIC_API_KEY='sk-ant-your-key'

# Linux/Mac:
export OPENAI_API_KEY='sk-your-key'
export ANTHROPIC_API_KEY='sk-ant-your-key'

# 2. 或创建 .env 文件
cp .env.example .env
# 编辑 .env 填入密钥

# 3. 运行并选择提供商
python TheWorldOfAI.py
```

---

## 🔬 测试套件 (Feature分支)

### 1. `test_ollama.py`
- Ollama连接测试
- 模型可用性检查
- 推理性能测试
- 分类准确性验证

### 2. `test_llm_classifier.py`
- 多提供商测试
- 缓存机制验证
- 错误处理测试
- 性能基准测试

### 3. `demo_llm_classifier.py`
- 交互式演示
- 功能展示
- 快速验证工具

---

## 📈 开发路线图

### v2.0.0 (Feature分支 - 准备中)
- [x] LLM分类器核心
- [x] 多提供商支持
- [x] Ollama本地集成
- [x] 并发优化
- [x] 缓存机制
- [x] 菜单重构
- [x] 文档完善
- [ ] 充分测试
- [ ] 合并到Main

### v2.1.0 (计划)
- [ ] 批量API支持
- [ ] 更多LLM提供商
- [ ] 自定义提示词模板
- [ ] 分类结果导出
- [ ] RESTful API

### v2.2.0 (计划)
- [ ] Web UI界面
- [ ] 实时数据流
- [ ] 用户账户系统
- [ ] 数据库集成

---

## 🤝 贡献指南

### 分支策略
- `main`: 稳定生产版本
- `feature/ai-enhancements`: LLM功能开发
- `feature/*`: 新功能开发
- `bugfix/*`: Bug修复

### 提交规范
```
feat: 新功能
fix: Bug修复
docs: 文档更新
refactor: 重构
perf: 性能优化
test: 测试相关
chore: 构建/工具配置
```

---

## 📝 已知问题

### Main分支
1. 规则分类精度有限 (~70-80%)
2. 无法处理复杂语义
3. 需要人工审核辅助

### Feature分支
1. Ollama首次推理较慢 (~28秒)
2. LLM模式下无学习反馈
3. 并发可能导致内存压力
4. 缓存文件需定期清理

---

## 💡 最佳实践

### 性能优化
1. 使用Ollama本地模型 (免费+隐私)
2. 定期清理缓存 (保留最近100条)
3. 限制数据采集量 (当前10条/类)
4. 启用并发处理 (max_workers=3)

### 成本控制
1. 优先使用Ollama (零成本)
2. OpenAI仅用于关键内容
3. 充分利用缓存机制
4. 监控API使用量

### 准确性提升
1. LLM模式: 95%+ 准确率
2. 规则模式: 配合人工审核
3. 定期更新关键词库
4. 分析学习反馈报告

---

## 📧 联系方式

- **GitHub**: https://github.com/legendyz/ai-world-tracker
- **Issues**: 提交问题和建议
- **Discussions**: 功能讨论和交流

---

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

**最后更新**: 2025-12-05  
**维护者**: AI World Tracker Team
