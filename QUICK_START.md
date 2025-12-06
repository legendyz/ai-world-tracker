# 🚀 AI World Tracker - 快速开始指南

## 📌 快速决策

### 我应该使用哪个版本？

| 使用场景 | 推荐版本 | 原因 |
|---------|---------|------|
| 🏢 生产环境 | **Main分支 (v1.2)** | 稳定、测试充分、零依赖 |
| 🧪 测试/开发 | **Feature分支 (v2.0-beta)** | 最新功能、更高准确率 |
| 💰 成本敏感 | **Feature + Ollama** | 完全免费、本地运行 |
| 🎯 追求准确率 | **Feature + OpenAI/Anthropic** | 95%+ 准确率 |
| 📶 离线环境 | **Main或Feature + Ollama** | 无需网络连接 |

---

## ⚡ 30秒快速启动

### Main分支 (简单模式)
```bash
git clone https://github.com/legendyz/ai-world-tracker.git
cd ai-world-tracker
pip install -r requirements.txt
python TheWorldOfAI.py
# 选择 1 → 自动更新数据与报告
```

### Feature分支 (LLM模式)
```bash
cd ai-world-tracker
git checkout feature/ai-enhancements

# 安装Ollama
ollama pull qwen3:8b
ollama serve

pip install -r requirements.txt
python TheWorldOfAI.py
# 选择 1 → 自动更新数据并生成Web
```

---

## 📖 详细步骤

### 1️⃣ Main分支部署 (稳定版)

#### 安装
```bash
# 1. 克隆仓库
git clone https://github.com/legendyz/ai-world-tracker.git
cd ai-world-tracker

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python TheWorldOfAI.py
```

#### 使用
```
📋 主菜单
1. 🚀 自动更新数据与报告
   - 一键完成：采集 → 分类 → 分析 → 可视化 → Web生成
   - 自动打开浏览器查看结果

2. 🌐 生成并打开 Web 页面
   - 基于现有数据重新生成网页

3. 📝 人工审核分类
   - 查看低置信度分类结果
   - 手动修正错误分类

4. 🎓 学习反馈分析
   - 分析审核历史
   - 生成改进建议
```

---

### 2️⃣ Feature分支部署 (LLM增强版)

#### 方式A: Ollama (推荐 - 免费)

**Step 1: 安装Ollama**
```bash
# Windows
# 下载: https://ollama.com/download/windows

# Mac
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

**Step 2: 下载模型**
```bash
ollama pull qwen3:8b
# 大小: ~5 GB
# 首次下载需要时间，之后可离线使用
```

**Step 3: 启动服务**
```bash
ollama serve
# 保持此终端窗口打开
# 服务运行在 http://localhost:11434
```

**Step 4: 运行应用**
```bash
# 新开一个终端
cd ai-world-tracker
git checkout feature/ai-enhancements
pip install -r requirements.txt
python TheWorldOfAI.py
```

#### 方式B: OpenAI (需API密钥)

**Step 1: 设置API密钥**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY='sk-your-openai-key-here'

# Linux/Mac
export OPENAI_API_KEY='sk-your-openai-key-here'

# 或创建 .env 文件
cp .env.example .env
# 编辑 .env 文件添加:
# OPENAI_API_KEY=sk-your-openai-key-here
```

**Step 2: 运行应用**
```bash
git checkout feature/ai-enhancements
pip install -r requirements.txt
python TheWorldOfAI.py
# 选择 5 → 切换分类模式 → 2 (OpenAI)
```

#### 方式C: Anthropic (需API密钥)

**Step 1: 设置API密钥**
```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY='sk-ant-your-key-here'

# Linux/Mac
export ANTHROPIC_API_KEY='sk-ant-your-key-here'

# 或在 .env 文件中添加:
# ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Step 2: 运行应用**
```bash
python TheWorldOfAI.py
# 选择 5 → 切换分类模式 → 3 (Anthropic)
```

---

### 3️⃣ Feature分支使用

#### LLM模式菜单
```
当前分类模式: 🤖 LLM增强 - Ollama (Qwen3:8b)

1. 🚀 自动更新数据并生成 Web 页面
   - 智能采集 60条 AI资讯
   - LLM语义分类 (95%+ 准确率)
   - 自动生成可视化报告
   - 浏览器打开结果

2. 🛠️  手动更新及生成 Web 页面
   ├─ 1. 📥 仅更新数据
   │    - 采集并分类，保存JSON
   ├─ 2. 🏷️  分类数据
   │    - 对已有JSON重新分类
   └─ 3. 🌐 生成 Web 页面
        - 基于现有数据生成网页

5. ⚙️  切换分类模式
   - 切换到 OpenAI/Anthropic/规则分类
```

#### 规则模式菜单
```
当前分类模式: 📝 规则分类

1-2. 同上
3. 📝 人工审核分类 (仅规则模式)
4. 🎓 学习反馈分析 (仅规则模式)
5. ⚙️  切换分类模式
```

---

## 🔧 故障排除

### Main分支常见问题

**Q: 分类准确率不高？**
```
A: 使用人工审核功能 (选项3)
   - 修正错误分类
   - 系统会学习你的反馈
   - 定期运行学习反馈 (选项4)
```

**Q: 网页没有自动打开？**
```
A: 手动打开文件:
   - index.html (根目录)
   - web_output/index.html (备份)
```

### Feature分支常见问题

**Q: Ollama启动失败？**
```bash
# 检查服务状态
ollama list

# 重启服务
ollama serve
```

**Q: 模型响应很慢？**
```
首次推理: 约28秒 (正常)
后续: 缓存加速，约10-15秒
优化: 使用并发处理 (自动启用)
```

**Q: OpenAI API报错？**
```bash
# 检查密钥
echo $env:OPENAI_API_KEY  # Windows
echo $OPENAI_API_KEY      # Linux/Mac

# 确认格式
sk-proj-xxxxxxxxxxxx (新格式)
sk-xxxxxxxxxxxx     (旧格式)
```

**Q: 切换模式后缓存混乱？**
```bash
# 清理缓存
rm cache/llm_classification_cache.json

# 或删除整个缓存目录
rm -rf cache/
```

---

## 📊 性能对比

### 准确率
| 模式 | 准确率 | 适用场景 |
|-----|-------|---------|
| 规则分类 | 70-80% | 快速测试、离线环境 |
| Ollama | 95%+ | 本地部署、隐私要求 |
| OpenAI | 97%+ | 高准确率要求 |
| Anthropic | 96%+ | 平衡成本和准确率 |

### 速度对比 (60条数据)
| 模式 | 耗时 | 成本 |
|-----|-----|------|
| 规则分类 | ~10秒 | 免费 |
| Ollama (优化后) | ~3-5分钟 | 免费 |
| Ollama (未优化) | ~28分钟 | 免费 |
| OpenAI | ~2-3分钟 | ~$0.05 |
| Anthropic | ~2-3分钟 | ~$0.04 |

---

## 💡 最佳实践

### 日常使用
```bash
# 1. 每日自动采集
python TheWorldOfAI.py
# 选择 1 → 自动更新

# 2. 查看结果
# 浏览器自动打开 index.html

# 3. 定期清理 (可选)
rm ai_tracker_data_*.json  # 删除旧数据
rm -rf cache/              # 清理缓存
```

### 开发测试
```bash
# 1. 先测试小规模
# 修改 data_collector.py
# 每类采集5条 (当前10条)

# 2. 测试Ollama连接
python test_ollama.py

# 3. 测试LLM分类
python demo_llm_classifier.py

# 4. 完整测试
python TheWorldOfAI.py
```

### 成本优化
```
1. 优先使用 Ollama (零成本)
2. 充分利用缓存机制
3. 限制数据采集量
4. 监控API使用量
```

---

## 📚 进阶阅读

- [PROJECT_STATUS.md](PROJECT_STATUS.md) - 完整项目状态
- [LLM_CLASSIFICATION_GUIDE.md](LLM_CLASSIFICATION_GUIDE.md) - LLM使用指南
- [OLLAMA_SETUP_COMPLETE.md](OLLAMA_SETUP_COMPLETE.md) - Ollama详细设置

---

## 🆘 获取帮助

- **GitHub Issues**: https://github.com/legendyz/ai-world-tracker/issues
- **Discussions**: https://github.com/legendyz/ai-world-tracker/discussions
- **文档**: 查看 docs/ 目录

---

**最后更新**: 2025-12-05  
**版本**: Main v1.2 / Feature v2.0-beta
