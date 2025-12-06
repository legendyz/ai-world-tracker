# 🌍 AI World Tracker

[🇨🇳 中文版 (Chinese Version)](README_CN.md)

**AI World Tracker** is a comprehensive platform for tracking and analyzing global Artificial Intelligence trends. It automatically collects data from multiple authoritative sources, classifies content using intelligent algorithms (LLM or rule-based), and generates visual trend analysis reports and web dashboards.

## 🌟 Branch Overview

| Branch | Version | Description | Target Users |
|--------|---------|-------------|--------------|
| `main` | v2.0 | **Latest stable version** with full LLM integration | Production use |
| `ai-world-tracker-v1` | v1.0 | First complete release with rule-based classification | Hobbyists & developers for customization |
| `feature/data-collection-v2` | Beta | Enhanced data collection capabilities (in development) | Contributors & testers |

### Choosing the Right Branch

- **For Production Use**: Use `main` branch - fully tested with LLM-enhanced classification
- **For Learning/Customization**: Use `ai-world-tracker-v1` - simpler architecture, rule-based classification, easy to modify
- **For Contributing**: Use `feature/data-collection-v2` - help us improve data collection features

## ✨ Key Features

### Core Capabilities
- **🤖 Multi-Source Data Collection**: Automatically scrapes data from arXiv (latest papers), GitHub (trending projects), tech media (TechCrunch, The Verge, Wired), and AI blogs (OpenAI, Google AI, Hugging Face)
- **🧠 Intelligent Classification**: Dual-mode classification system
  - **LLM Mode**: Semantic understanding via Ollama/OpenAI/Anthropic (95%+ accuracy)
  - **Rule Mode**: Keyword-based pattern recognition (fast, no dependencies)
- **📊 Data Visualization**: Generates charts for technology hotspots, content distribution, regional distribution, and daily trends
- **🌐 Web Dashboard**: Creates a responsive HTML dashboard with categorized news
- **🔄 Smart Caching**: MD5-based caching to avoid redundant API calls

### LLM Integration (Main Branch)
- **Multi-provider Support**: Ollama (free, local), OpenAI, Anthropic
- **Local Model**: Qwen3:8b via Ollama - completely free
- **GPU Acceleration**: Auto-detection for NVIDIA, AMD, Apple Silicon
- **Concurrent Processing**: 3-thread parallel processing for speed
- **Automatic Fallback**: Graceful degradation to rule-based when LLM unavailable

## 🛠️ Installation

### Requirements

- Python 3.8+
- Windows / macOS / Linux
- (Optional) Ollama for local LLM

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

3. **(Optional) Setup Ollama for LLM Classification**
   ```bash
   # Install Ollama from https://ollama.com/download
   ollama pull qwen3:8b
   ollama serve
   ```

4. **Run the Application**
   ```bash
   python TheWorldOfAI.py
   ```

## 🚀 Usage

### Main Menu

```
📋 Main Menu
============================================================
Current Mode: [LLM: Ollama/qwen3:8b] or [Rule-based]
============================================================
1. 🚀 Auto Update & Generate (Full pipeline)
2. 🌐 Generate & Open Web Page
3. ⚙️ Settings (Classification mode, Language)
4. 📝 Manual Workflow (Review, Feedback)
0. Exit
============================================================
```

### Feature Description

| Option | Function | Description |
|--------|----------|-------------|
| 1 | Auto Update | Execute full pipeline: Collection → Classification → Analysis → Visualization → Web Generation |
| 2 | Web Page | Regenerate HTML dashboard and open in browser |
| 3 | Settings | Switch between LLM/Rule classification, change language |
| 4 | Manual Workflow | Review low-confidence items, learning feedback (Rule mode only) |

## 📂 Project Structure

```
ai-world-tracker/
├── TheWorldOfAI.py          # Main application entry point
├── data_collector.py        # Multi-source data collection
├── content_classifier.py    # Rule-based content classifier
├── llm_classifier.py        # LLM-enhanced classifier
├── config.py                # Configuration management
├── ai_analyzer.py           # Trend analysis engine
├── visualizer.py            # Data visualization (Matplotlib)
├── web_publisher.py         # Web page generator
├── manual_reviewer.py       # Manual review interface
├── learning_feedback.py     # Learning feedback system
├── i18n.py                  # Internationalization (EN/CN)
├── config_manager.py        # YAML configuration loader
├── link_validator.py        # URL validation utility
├── requirements.txt         # Python dependencies
├── config.yaml              # Application configuration
├── visualizations/          # Generated charts
├── web_output/              # Generated web pages
│   └── index.html           # Backup dashboard
└── index.html               # Main dashboard (GitHub Pages)
```

## 📰 Data Sources

### Research Papers
- arXiv (cs.AI, cs.LG, cs.CV, cs.CL)

### Tech News Media
- TechCrunch AI
- The Verge AI
- Wired AI
- MIT Technology Review
- IEEE Spectrum AI
- AI News
- Synced Review

### Chinese Tech Media
- 36Kr (36氪)
- IT Home (IT之家)
- Jiqizhixin (机器之心)
- QbitAI (量子位)
- InfoQ China

### Developer Resources
- GitHub Blog
- Hugging Face Blog
- OpenAI Blog
- Google AI Blog

### Community & Leaders
- Product Hunt AI
- Hacker News AI
- Sam Altman's Blog
- Andrej Karpathy's Blog
- Lex Fridman Podcast

## ⚙️ Configuration

### LLM Providers

| Provider | Model | Cost | Setup |
|----------|-------|------|-------|
| Ollama | qwen3:8b | Free | `ollama pull qwen3:8b` |
| OpenAI | gpt-4o-mini | Paid | Set `OPENAI_API_KEY` |
| Anthropic | claude-3-haiku | Paid | Set `ANTHROPIC_API_KEY` |

### Environment Variables

```bash
# Optional: For cloud LLM providers
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# Optional: Ollama custom URL
export OLLAMA_BASE_URL="http://localhost:11434"
```

## 🔧 Version Comparison

| Feature | v1.0 (ai-world-tracker-v1) | v2.0 (main) |
|---------|----------------------------|-------------|
| Classification | Rule-based | LLM + Rule fallback |
| LLM Support | ❌ | ✅ Ollama/OpenAI/Anthropic |
| Local Models | ❌ | ✅ Qwen3:8b |
| Concurrent Processing | ❌ | ✅ Multi-threaded |
| Smart Caching | ❌ | ✅ MD5-based |
| GPU Acceleration | ❌ | ✅ Auto-detection |
| Accuracy | ~70% | ~95% |
| Best For | Learning, Customization | Production |

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report Issues**: Found a bug? [Open an issue](https://github.com/legendyz/ai-world-tracker/issues)
2. **Feature Requests**: Have an idea? Let us know!
3. **Pull Requests**: 
   - Fork the repository
   - Create a feature branch from `feature/data-collection-v2`
   - Submit a PR

### Development Branches
- `main`: Stable production code
- `feature/data-collection-v2`: Active development for data collection improvements
- `ai-world-tracker-v1`: Legacy version (bug fixes only)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.com/) for local LLM support
- [arXiv](https://arxiv.org/) for research paper access
- All the tech blogs and news sources that make this possible

---

**Made with ❤️ by the AI World Tracker Team**
