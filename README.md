# 🌍 AI World Tracker

[🇨🇳 中文版 (Chinese Version)](README_CN.md)

**AI World Tracker** is a comprehensive platform for tracking and analyzing global Artificial Intelligence trends. It automatically collects data from multiple authoritative sources, classifies content using intelligent algorithms (LLM or rule-based), and generates visual trend analysis reports and web dashboards.

## 🌟 Branch Overview

| Branch | Version | Description | Target Users |
|--------|---------|-------------|--------------|
| `main` | v2.0 | **Latest stable version** with full LLM integration | Production use |
| `ai-world-tracker-v1` | v1.0 | First complete release with rule-based classification | Hobbyists & custom development |
| `feature/data-collection-v2` | Beta | Enhanced data collection (in development) | Contributors & testers |

### Choosing the Right Branch

- **Production Use**: Use `main` branch - fully tested with LLM-enhanced classification
- **Learning/Customization**: Use `ai-world-tracker-v1` - simpler architecture, rule-based, easy to modify
- **Contributing**: Use `feature/data-collection-v2` - help us improve data collection

## ✨ Key Features

### Core Capabilities
- **🤖 Multi-Source Data Collection**: Automatically scrapes data from arXiv (latest papers), GitHub (trending projects), tech media (TechCrunch, The Verge, Wired), and AI blogs (OpenAI, Google AI, Hugging Face)
- **🧠 Intelligent Classification**: Dual-mode classification system
  - **LLM Mode**: Semantic understanding via Ollama/OpenAI/Anthropic (95%+ accuracy)
  - **Rule Mode**: Keyword-based pattern recognition (fast, no dependencies)
- **📊 Data Visualization**: Generates charts for technology hotspots, content distribution, regional distribution, and daily trends
- **🌐 Web Dashboard**: Creates responsive HTML dashboard with categorized news
- **🔄 Smart Caching**: MD5-based caching to avoid redundant API calls
- **🌍 Bilingual Support**: Full Chinese/English interface (i18n)

### LLM Integration (Main Branch)
- **Multi-Provider Support**: Ollama (free, local), OpenAI, Anthropic
- **Local Models**: Qwen3:8b via Ollama - completely free
- **GPU Acceleration**: Auto-detects NVIDIA, AMD, Apple Silicon
- **Concurrent Processing**: 3-6 thread parallel processing for speed
- **Auto-Fallback**: Gracefully degrades to rule-based when LLM unavailable
- **Resource Management**: Automatic model unloading on exit to free VRAM/memory

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

3. **(Optional) Set up Ollama for LLM Classification**
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
Current Mode: 🤖 LLM Mode (ollama/qwen3:8b)
============================================================
1. 🚀 Auto Update & Generate (Full pipeline)
2. 🌐 Generate & Open Web Page
3. 📝 Manual Review (Review low-confidence items)
4. 📚 Learning Feedback (Analyze review history)
5. ⚙️  Settings & Management
0. Exit
============================================================
```

### Settings & Management Menu

```
⚙️  Settings & Management

Current Mode: 🤖 LLM Mode (ollama/qwen3:8b)

📋 Classification Mode:
  1. 📝 Rule Mode (Rule-based) - Fast, free, no network required
  2. 🤖 LLM Mode (Ollama Local) - High accuracy, semantic understanding
  3. 🤖 LLM Mode (OpenAI) - Highest accuracy, API key required
  4. 🤖 LLM Mode (Anthropic) - High accuracy, API key required

🧹 Data Maintenance:
  5. 🗑️ Clear LLM classification cache
  6. 🗑️ Clear collection history cache
  7. 🗑️ Clear export data history

  0. ↩️ Back to main menu
```

### Feature Description

| Option | Function | Description |
|--------|----------|-------------|
| 1 | Auto Update | Execute full pipeline: Collection → Classification → Analysis → Visualization → Web Generation, then prompt to open browser |
| 2 | Web Page | Regenerate HTML dashboard and open in browser |
| 3 | Manual Review | Review items with low classification confidence |
| 4 | Learning Feedback | Generate optimization suggestions based on review history |
| 5 | Settings & Management | Switch classification mode and manage data/cache |

### Data Maintenance Options

| Option | Function | Description |
|--------|----------|-------------|
| Clear LLM Cache | 🗑️ | Delete `llm_classification_cache.json`, force re-classification with LLM |
| Clear Collection Cache | 🗑️ | Delete `collection_history_cache.json`, allow re-collection of all URLs |
| Clear Export History | 🗑️ | Delete all `data/exports/*.json` and `*.txt` files (requires confirmation) |

## 📂 Project Structure

```
ai-world-tracker/
├── TheWorldOfAI.py          # Main application entry point
├── data_collector.py        # Multi-source data collection
├── content_classifier.py    # Rule-based content classifier
├── llm_classifier.py        # LLM-enhanced classifier
├── config.py                # Unified configuration management
├── logger.py                # Unified logging system
├── ai_analyzer.py           # Trend analysis engine
├── visualizer.py            # Data visualization (Matplotlib)
├── web_publisher.py         # Web page generator
├── manual_reviewer.py       # Manual review interface
├── learning_feedback.py     # Learning feedback system
├── i18n.py                  # Internationalization (EN/CN)
├── link_validator.py        # URL validation utility
├── regenerate_web.py        # Quick web regeneration utility
├── requirements.txt         # Python dependencies
├── config.yaml              # Application configuration
├── ai_tracker_config.json   # User preferences (auto-generated)
├── pytest.ini               # Test configuration
├── data/                    # Generated data directory
│   ├── exports/             # Exported data and reports
│   │   ├── ai_tracker_data_*.json    # Collected data with timestamps
│   │   └── ai_tracker_report_*.txt   # Text reports
│   └── cache/               # Cache files
│       ├── collection_history_cache.json  # URL/title deduplication
│       └── llm_classification_cache.json  # LLM classification results
├── tests/                   # Test files directory
│   ├── __init__.py
│   ├── test_classifier_*.py
│   ├── test_llm_*.py
│   └── ...
├── logs/                    # Log files directory
├── visualizations/          # Generated charts
├── web_output/              # Generated web pages (backup)
│   └── index.html
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
- 36氪 (36Kr)
- IT之家
- 机器之心
- 量子位 (QbitAI)
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

### Configuration Files

The application supports multiple configuration sources with the following priority:

1. **Environment Variables** - Highest priority
2. **.env File** - For local development
3. **config.yaml** - Project defaults
4. **ai_tracker_config.json** - User preferences (auto-saved)
5. **Code Defaults** - Fallback values

### config.yaml Example

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
  mode: llm        # Options: llm, rule
  provider: ollama
  model: Qwen3:8B
  batch_size: 10
  max_workers: 4

visualization:
  theme: default

output:
  report_dir: ./
  web_dir: ./web_output/

# Data directory configuration
data:
  exports_dir: data/exports    # Exported data and reports
  cache_dir: data/cache        # Cache files

# Logging configuration
logging:
  level: INFO                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  dir: logs                    # Log files directory
  console: true                # Output to console
  file: true                   # Output to file
  max_size_mb: 10              # Max size per log file (MB)
  backup_count: 2              # Number of backup files
  retention_days: 3            # Log retention days
  format: standard             # standard or json
```

### LLM Providers

| Provider | Model | Cost | Setup |
|----------|-------|------|-------|
| Ollama | qwen3:8b | Free | `ollama pull qwen3:8b` |
| OpenAI | gpt-4o-mini | Paid | Set `OPENAI_API_KEY` |
| Anthropic | claude-3-haiku | Paid | Set `ANTHROPIC_API_KEY` |

### Environment Variables

```bash
# Optional: Cloud LLM providers
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# Optional: Custom Ollama URL
export OLLAMA_BASE_URL="http://localhost:11434"
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

## 🔧 Version Comparison

| Feature | v1.0 (ai-world-tracker-v1) | v2.0 (main) |
|---------|----------------------------|-------------|
| Classification | Rule-based | LLM + Rule fallback |
| LLM Support | ❌ | ✅ Ollama/OpenAI/Anthropic |
| Local Models | ❌ | ✅ Qwen3:8b |
| Concurrent Processing | ❌ | ✅ Multi-threaded (3-6) |
| Smart Caching | ❌ | ✅ MD5-based |
| GPU Acceleration | ❌ | ✅ Auto-detection |
| Unified Logging | ❌ | ✅ logger.py (with emoji dedup) |
| Structured Data Dir | ❌ | ✅ data/exports, data/cache |
| Log Auto-Cleanup | ❌ | ✅ Configurable retention |
| JSON Log Format | ❌ | ✅ Optional |
| Test Organization | Scattered | ✅ tests/ directory |
| Bilingual UI | ❌ | ✅ Chinese/English |
| Resource Cleanup | ❌ | ✅ Auto unload LLM on exit |
| Cache Management | ❌ | ✅ Clear cache via menu |
| Accuracy | ~70% | ~95% |
| Use Case | Learning, customization | Production |

## 🧪 Testing

Tests are organized in the `tests/` directory:

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_classifier_advanced.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Here's how to get involved:

1. **Report Issues**: Found a bug? [Open an issue](https://github.com/legendyz/ai-world-tracker/issues)
2. **Feature Requests**: Have an idea? Let us know!
3. **Submit Code**:
   - Fork the repository
   - Create a feature branch from `feature/data-collection-v2`
   - Submit a PR

### Development Workflow

```bash
# Clone and setup
git clone https://github.com/legendyz/ai-world-tracker.git
cd ai-world-tracker
git checkout feature/data-collection-v2

# Create feature branch
git checkout -b feature/your-feature

# Make changes and test
pytest tests/ -v

# Commit and push
git commit -m "feat: add your feature"
git push origin feature/your-feature
```

## 📧 Contact

- GitHub: [@legendyz](https://github.com/legendyz)
- Project: [ai-world-tracker](https://github.com/legendyz/ai-world-tracker)

---

**⭐ Star this repository if you find it helpful!**
