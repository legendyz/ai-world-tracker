# 🌍 AI World Tracker

[🇨🇳 中文版 (Chinese Version)](README_CN.md)

**AI World Tracker** is a comprehensive platform for tracking and analyzing global Artificial Intelligence trends. It automatically collects data from multiple authoritative sources, classifies content using intelligent algorithms, and generates visual trend analysis reports and web dashboards.

## ✨ Key Features

- **🤖 Multi-Source Data Collection**: Automatically scrapes data from arXiv (latest papers), GitHub (trending projects), tech media (TechCrunch, The Verge, Wired), and AI blogs (OpenAI, Google AI, Hugging Face)
- **📊 Intelligent Classification**: Rule-based content classification with keyword matching and pattern recognition
- **📈 Data Visualization**: Generates charts for technology hotspots, content distribution, regional distribution, and daily trends
- **🌐 Web Report Generation**: Creates a static HTML dashboard with categorized news and mobile support
- **📝 Manual Review System**: Review low-confidence classifications and provide corrections
- **🎓 Learning Feedback**: Analyze review history and generate suggestions for improving the classifier

## 🛠️ Installation

### Requirements

- Python 3.8+
- Windows / macOS / Linux

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/legendyz/ai-world-tracker.git
   cd ai-world-tracker
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python TheWorldOfAI.py
   ```

## 🚀 Usage

Run the main program to launch the interactive menu:

```bash
python TheWorldOfAI.py
```

### Main Menu

```
📋 Main Menu
============================================================
1. 🚀 Auto Update & Generate (Full pipeline)
2. 🌐 Generate & Open Web Page
3. 📝 Manual Review (Review low-confidence items)
4. 🎓 Learning Feedback (Analyze review history)
0. Exit
============================================================
```

### Feature Description

| Option | Function | Description |
|--------|----------|-------------|
| 1 | Auto Update | Execute full pipeline: Collection → Classification → Analysis → Visualization → Web Generation |
| 2 | Web Page | Regenerate HTML dashboard and open in browser |
| 3 | Manual Review | Review items with low classification confidence |
| 4 | Learning Feedback | Generate optimization suggestions based on review history |

## 📂 Project Structure

```
ai-world-tracker/
├── TheWorldOfAI.py          # Main application entry point
├── data_collector.py        # Data collection (arXiv, RSS, GitHub)
├── content_classifier.py    # Rule-based content classifier
├── ai_analyzer.py           # Trend analysis engine
├── visualizer.py            # Data visualization (Matplotlib)
├── web_publisher.py         # Web page generator
├── manual_reviewer.py       # Manual review interface
├── learning_feedback.py     # Learning feedback system
├── link_validator.py        # URL validation utility
├── requirements.txt         # Python dependencies
├── visualizations/          # Generated charts
└── web_output/              # Generated web pages
    └── index.html           # Main dashboard
```

## 📰 Data Sources

### Research
- arXiv (cs.AI, cs.LG, cs.CV, cs.CL)

### News Media
- TechCrunch AI
- The Verge AI
- Wired AI
- MIT Technology Review
- IEEE Spectrum AI
- 36Kr (Chinese)
- 机器之心 / Synced (Chinese)
- 量子位 / QbitAI (Chinese)

### Developer & Official Blogs
- GitHub Blog
- OpenAI Blog
- Google AI Blog
- Hugging Face Blog

### Community
- Product Hunt AI
- Hacker News

## 🔧 Configuration

The application uses intelligent defaults and requires no configuration for basic usage.

### Optional Environment Variables

```bash
# For future LLM integration (not required for current version)
OPENAI_API_KEY=sk-your-api-key
```

## 配置文件：config.yaml

集中管理采集、分类、分析、可视化等参数。

### 示例结构
```yaml
collector:
  product_count: 15
  community_count: 10
  max_total: 100

classification:
  mode: llm   # 可选: llm, rule
  provider: ollama
  model: Qwen3:8B
  batch_size: 10
  max_workers: 4

visualization:
  theme: default

output:
  report_dir: ./
  web_dir: ./web_output/
```

### 如何扩展
- 新增参数直接在 config.yaml 添加即可
- 代码中通过 `from config_manager import config`，然后 `config.get('路径.参数名', 默认值)` 访问

### 依赖
- 需安装 pyyaml

```
pip install pyyaml
```

## 📊 Content Classification

The classifier categorizes content into six dimensions:

| Category | Description | Examples |
|----------|-------------|----------|
| `research` | Academic papers and studies | arXiv papers, benchmark results |
| `product` | Product launches and updates | GPT-4o release, new features |
| `market` | Business and market news | Funding rounds, acquisitions |
| `developer` | Developer tools and resources | SDKs, APIs, tutorials |
| `leader` | Industry leader opinions | CEO interviews, keynotes |
| `community` | Community discussions | Hot topics, debates |

## 🌿 Branch Information

| Branch | Description | Status |
|--------|-------------|--------|
| `main` | Stable production version | ✅ Recommended |
| `feature/ai-enhancements-v2` | LLM-enhanced classification (Qwen3:8b) | 🧪 Beta |

### Feature Branch (v2.0-beta)

The `feature/ai-enhancements-v2` branch includes experimental LLM-enhanced classification:

- **LLM Providers**: Ollama (local), OpenAI, Anthropic
- **Recommended Model**: Qwen3:8b (optimized with Chat API + think=false)
- **Features**: GPU auto-detection, MD5 caching, auto-fallback

To try the beta version:
```bash
git checkout feature/ai-enhancements-v2
pip install -r requirements.txt
# Install Ollama and pull qwen3:8b model
ollama pull qwen3:8b
python TheWorldOfAI.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Contact

- GitHub: [@legendyz](https://github.com/legendyz)
- Project: [ai-world-tracker](https://github.com/legendyz/ai-world-tracker)

---

**⭐ Star this repository if you find it helpful!**
