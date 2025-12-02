# Contributing to AI World Tracker

我们热烈欢迎您为AI World Tracker项目做出贡献！🎉

## 🤝 贡献方式

### 🐛 报告Bug
1. 检查现有的[Issues](https://github.com/yourusername/ai-world-tracker/issues)确保没有重复
2. 使用Bug Report模板创建新的Issue
3. 提供详细的复现步骤和环境信息

### 💡 提出功能建议  
1. 使用Feature Request模板创建Issue
2. 详细描述功能需求和使用场景
3. 与社区讨论可行性和实现方案

### 📝 代码贡献

#### 开发环境设置
```bash
# 1. Fork项目并克隆
git clone https://github.com/yourusername/ai-world-tracker.git
cd ai-world-tracker

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate.bat  # Windows

# 3. 安装依赖
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

## 📂 项目结构说明

```
ai-world-tracker/
├── TheWorldOfAI.py         # 主程序入口
├── data_collector.py       # 数据采集模块（新数据源在这里添加）
├── content_classifier.py   # 内容分类（新分类规则在这里修改）
├── ai_analyzer.py          # 趋势分析引擎
├── visualizer.py           # 图表生成器
├── web_publisher.py        # Web界面生成
├── link_validator.py       # 工具：链接验证
├── diagnose_feeds.py       # 工具：数据源诊断
└── requirements.txt        # 依赖管理
```

## 🎯 贡献重点领域

### 🔥 高优先级
- **新数据源集成**: 添加更多高质量AI资讯源
- **性能优化**: 提高数据采集和处理效率
- **错误处理**: 增强网络异常和API限制的处理
- **国际化**: 支持英文界面和多语言内容

### 📈 中优先级
- **数据质量**: 改进内容过滤和去重算法
- **可视化增强**: 新的图表类型和交互功能
- **配置选项**: 更灵活的用户配置选项
- **文档完善**: API文档和使用示例

### 💡 创新方向
- **AI集成**: 使用LLM进行内容摘要和分析
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