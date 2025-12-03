# Contributing to AI World Tracker

We warmly welcome your contributions to the AI World Tracker project! 🎉

## 🤝 How to Contribute

### 🐛 Report Bugs
1. Check existing [Issues](https://github.com/legendyz/ai-world-tracker/issues) to avoid duplicates
2. Use the Bug Report template to create a new Issue
3. Provide detailed reproduction steps and environment information

### 💡 Suggest Features  
1. Use the Feature Request template to create an Issue
2. Describe feature requirements and use cases in detail
3. Discuss feasibility and implementation approaches with the community

### 📝 Code Contributions

#### Development Environment Setup
```bash
# 1. Fork and clone the project
git clone https://github.com/legendyz/ai-world-tracker.git
cd ai-world-tracker

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate.bat  # Windows

# 3. Install dependencies
pip install -r requirements.txt
pip install pytest black flake8

# 4. 创建功能分支
git checkout -b feature/your-feature-name
```

#### 代码规范
- **Python风格**: 遵循PEP 8规范
- **注释**: 使用中文注释，重要函数添加docstring
- **变量命名**: 使用有意义的变量名
- **函数长度**: 单个函数不超过50行

#### 提交流程
1. **运行测试**:
   ```bash
   python -m pytest tests/
   python data_collector.py  # 测试数据采集
   python TheWorldOfAI.py --auto  # 完整测试
   ```

2. **代码格式化**:
   ```bash
   black . --line-length 100
   flake8 . --max-line-length 100
   ```

3. **提交代码**:
   ```bash
   git add .
   git commit -m "feat: 添加新的数据源支持"
   git push origin feature/your-feature-name
   ```

4. **创建Pull Request**:
   - 使用清晰的标题和描述
   - 关联相关的Issue
   - 添加测试用例（如适用）

## 📂 Project Structure

```
ai-world-tracker/
├── TheWorldOfAI.py         # Main program entry point
├── data_collector.py       # Data collection module (add new data sources here)
├── content_classifier.py   # Content classification (modify classification rules here)
├── ai_analyzer.py          # Trend analysis engine
├── visualizer.py           # Chart generator
├── web_publisher.py        # Web interface generator (outputs to root directory)
├── index.html              # Generated web dashboard (GitHub Pages ready)
├── web_output/             # Backup web files
├── link_validator.py       # Tool: Link validation
├── install.ps1             # Windows installation script
├── requirements.txt        # Dependency management
├── README.md               # Project documentation (English)
├── CHANGELOG.md            # Version history
├── USAGE_GUIDE.md          # Detailed usage instructions
└── CONTRIBUTING.md         # This file
```

## 🎯 Key Contribution Areas

### 🔥 High Priority
- **New Data Source Integration**: Add more high-quality AI news sources
- **Performance Optimization**: Improve data collection and processing efficiency  
- **Error Handling**: Enhance network exception and API rate limit handling
- **GitHub Pages**: Improve web dashboard automation and deployment

### 📈 Medium Priority
- **Data Quality**: Improve content filtering and deduplication algorithms
- **Visualization Enhancement**: New chart types and interactive features
- **Configuration Options**: More flexible user configuration options
- **Documentation**: API documentation and usage examples

### 💡 Innovation Directions
- **AI Integration**: Use LLMs for content summarization and analysis
- **实时推送**: 重要AI动态的实时通知
- **移动应用**: 开发移动端应用
- **社区功能**: 用户评论和分享功能

## 🧪 测试指南

### 单元测试
```bash
# 运行所有测试
python -m pytest tests/ -v

# 测试特定模块
python -m pytest tests/test_data_collector.py -v
```

### 集成测试
```bash
# 测试完整流程
python TheWorldOfAI.py --auto

# 测试数据源连接
python diagnose_feeds.py

# 验证输出文件
ls -la visualizations/ web_output/
```

### 性能测试
```bash
# 测量执行时间
time python TheWorldOfAI.py --auto

# 内存使用监控
python -m memory_profiler TheWorldOfAI.py
```

## 📋 Code Review清单

提交PR时，请确保：
- [ ] 代码遵循项目风格指南
- [ ] 添加了必要的测试用例
- [ ] 更新了相关文档
- [ ] 处理了潜在的错误情况
- [ ] 性能没有明显下降
- [ ] 与现有功能兼容

## 🏆 贡献者认可

- 所有贡献者将在README中列出
- 重大贡献者会获得Collaborator权限
- 优秀PR会获得特别标记和推荐

## 📞 获取帮助

- **技术问题**: 在Issues中提问或讨论
- **设计讨论**: 加入GitHub Discussions
- **实时沟通**: [添加您的沟通渠道]

---

**感谢您的贡献！让我们一起打造最好的AI资讯追踪工具！** 🚀