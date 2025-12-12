# 🌍 AI World Tracker

[🇨🇳 中文版 (Chinese Version)](README_CN.md)

**AI World Tracker** is a comprehensive platform for tracking and analyzing global Artificial Intelligence trends. It automatically collects data from multiple authoritative sources, classifies content using intelligent algorithms (LLM or rule-based), and generates visual trend analysis reports and web dashboards.

## 🌟 Branch Overview

| Branch | Version | Description | Target Users |
|--------|---------|-------------|--------------|
| `main` | v2.0 | **Latest stable version** with full LLM integration + async data collection | Production use |
| `ai-world-tracker-v2` | v2.0 | Stable v2 release with async collection (78% faster) | Production use |
| `ai-world-tracker-v1` | v1.0 | First complete release with rule-based classification | Learning & customization |
| `ai-world-tracker-v3-developing` | v3.0-dev | **Next generation development** | Contributors & testers |

### Choosing the Right Branch

- **Production Use**: Use `main` branch - fully tested with LLM-enhanced classification and async collection
- **Stable v2**: Use `ai-world-tracker-v2` - stable v2 release with all async improvements
- **Learning/Customization**: Use `ai-world-tracker-v1` - simpler architecture, rule-based, easy to modify
- **Contributing**: Use `ai-world-tracker-v3-developing` - next generation features in development

## ✨ Key Features

### Core Capabilities
- **🤖 Multi-Source Data Collection**: Automatically scrapes data from arXiv (latest papers), GitHub (trending projects), tech media (TechCrunch, The Verge, Wired), and AI blogs (OpenAI, Google AI, Hugging Face)
- **⚡ High-Performance Pure Async Collection**: True async architecture with asyncio + aiohttp
  - 20+ concurrent requests with smart rate limiting (3 per host)
  - URL pre-filtering with normalized URL deduplication
  - 3-tier deduplication: MD5 fingerprint + Semantic similarity + String similarity
  - 7-day history cache with automatic expiration
- **🧠 Intelligent Classification**: Dual-mode classification system
  - **LLM Mode**: Semantic understanding via Ollama/Azure OpenAI (95%+ accuracy)
  - **Rule Mode**: Keyword-based pattern recognition (fast, no dependencies)
- **📊 Data Visualization**: Generates charts for technology hotspots, content distribution, regional distribution, and daily trends
- **🌐 Web Dashboard**: Creates responsive HTML dashboard with categorized news
- **🔄 Smart Caching**: MD5-based caching to avoid redundant API calls
- **🌍 Bilingual Support**: Full Chinese/English interface (i18n)

### LLM Integration
- **Multi-Provider Support**: Ollama (free, local), Azure OpenAI
- **Local Models**: Qwen3:8b via Ollama - completely free
- **GPU Acceleration**: Auto-detects NVIDIA (CUDA), AMD (ROCm), Apple Silicon (Metal)
- **Concurrent Processing**: 3-6 thread parallel processing for speed
- **Auto-Fallback**: Gracefully degrades to rule-based when LLM unavailable
- **Resource Management**: Automatic model unloading on exit to free VRAM/memory

### Data Collection Performance (v2.0)
| Metric | Sync Mode | Async Mode | Improvement |
|--------|-----------|------------|-------------|
| Collection Time | ~147s | ~32s | **78% faster** |
| Concurrent Requests | 6 threads | 20+ async | **3x more** |
| Request Efficiency | 0.14 req/s | 3.0 req/s | **21x faster** |

## 🛠️ Installation

### Requirements

- Python 3.8+ (Python 3.13+ requires `legacy-cgi` package)
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
   
   # For Python 3.13+, also install:
   pip install legacy-cgi
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
   
   # Or run in auto mode (non-interactive)
   python TheWorldOfAI.py --auto
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
  3. 🤖 LLM Mode (Azure OpenAI) - Highest accuracy, API key required

🧹 Data Maintenance:
  4. 🗑️ Clear LLM classification cache
  5. 🗑️ Clear collection history cache
  6. 🗑️ Clear export data history
  7. 🗑️ Clear manual review records
  8. ⚠️ Clear ALL data (requires typing "YES" to confirm)

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
| Clear Export History | 🗑️ | Delete all `data/exports/ai_tracker_*.json` and `*.txt` files (requires confirmation) |
| Clear Review Records | 🗑️ | Delete all `data/exports/review_history_*.json` and `learning_report_*.json` files |
| Clear ALL Data | ⚠️ | Delete all cache and export files - **requires typing "YES" to confirm** |

## 📂 Project Structure

```
ai-world-tracker/
├── TheWorldOfAI.py          # Main application entry point (AIWorldTracker class)
├── data_collector.py        # Multi-source data collection (sync + async modes)
├── content_classifier.py    # Rule-based classifier
├── importance_evaluator.py  # Multi-dimensional importance scoring (5 dimensions)
├── llm_classifier.py        # LLM-enhanced classifier (Ollama/Azure OpenAI)
├── ai_analyzer.py           # Trend analysis engine (AIAnalyzer)
├── visualizer.py            # Data visualization - Matplotlib (DataVisualizer)
├── web_publisher.py         # Web page generator (WebPublisher)
├── manual_reviewer.py       # Manual review interface (ManualReviewer)
├── learning_feedback.py     # Learning feedback system (LearningFeedback)
├── config.py                # Unified configuration management
├── logger.py                # Unified logging system (colored console + file)
├── i18n.py                  # Internationalization (EN/CN)
├── regenerate_web.py        # Quick web regeneration utility
├── requirements.txt         # Python dependencies
├── config.yaml              # Application configuration
├── pytest.ini               # Test configuration
├── data/                    # Generated data directory
│   ├── exports/             # Exported data and reports
│   │   ├── ai_tracker_data_*.json    # Collected data with timestamps
│   │   ├── ai_tracker_report_*.txt   # Text reports
│   │   ├── review_history_*.json     # Manual review records
│   │   └── learning_report_*.json    # Learning feedback reports
│   └── cache/               # Cache files
│       ├── collection_history_cache.json  # URL/title deduplication (7-day expiry)
│       └── llm_classification_cache.json  # LLM classification results (MD5-based)
├── tests/                   # Test files directory
│   ├── __init__.py
│   ├── test_classifier_*.py
│   ├── test_llm_*.py
│   ├── test_async_performance.py
│   └── ...
├── docs/                    # Technical documentation
│   ├── ASYNC_OPTIMIZATION.md
│   ├── DATA_COLLECTOR_ARCHITECTURE.md
│   ├── IMPORTANCE_EVALUATOR_ANALYSIS.md
│   └── URL_PREFILTER_OPTIMIZATION.md
├── logs/                    # Log files directory (auto-cleanup)
├── visualizations/          # Generated charts (PNG)
│   ├── tech_hotspots.png
│   ├── content_distribution.png
│   ├── region_distribution.png
│   ├── daily_trends.png
│   └── dashboard.png
├── web_output/              # Generated web pages (backup)
│   └── index.html
└── index.html               # Main dashboard (GitHub Pages)
```

## 🏛️ System Architecture

### Module Dependency Diagram

```
                              ┌─────────────────────┐
                              │   TheWorldOfAI.py   │
                              │  (Main Entry Point) │
                              │   AIWorldTracker    │
                              └─────────┬───────────┘
                                        │
        ┌───────────────┬───────────────┼───────────────┬───────────────┐
        │               │               │               │               │
        ▼               ▼               ▼               ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│data_collector │ │content_       │ │ai_analyzer    │ │visualizer     │ │web_publisher  │
│   .py         │ │classifier.py  │ │   .py         │ │   .py         │ │   .py         │
│               │ │               │ │               │ │               │ │               │
│• DataCollector│ │• Importance   │ │• AIAnalyzer   │ │• DataVisualizer│ │• WebPublisher │
│• collect_all()│ │  Evaluator    │ │• analyze_     │ │• visualize_   │ │• generate_    │
│               │ │• Content      │ │  trends()     │ │  all()        │ │  html_page()  │
│               │ │  Classifier   │ │               │ │               │ │               │
└───────┬───────┘ └───────┬───────┘ └───────────────┘ └───────────────┘ └───────────────┘
        │                 │
        │                 │         ┌───────────────┐
        │                 ├────────▶│llm_classifier │ (Optional)
        │                 │         │   .py         │
        │                 │         │• LLMClassifier│
        │                 │         │• GPU Detection│
        │                 │         │• Multi-Provider│
        │                 │         └───────────────┘
        │                 │
        │                 │         ┌───────────────┐
        │                 └────────▶│importance_    │
        │                           │evaluator.py   │
        │                           │• 5-Dimension  │
        │                           │  Scoring      │
        │                           └───────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Infrastructure Layer                              │
├───────────────┬───────────────┬───────────────┬─────────────────────────────┤
│  config.py    │  logger.py    │   i18n.py     │ manual_reviewer.py          │
│               │               │               │ learning_feedback.py        │
│• OllamaConfig │• get_log_     │• t() translate│• ManualReviewer             │
│• AzureOpenAI  │  helper()     │• LANG_PACKS   │• LearningFeedback           │
│  Config       │• dual_* methods│• zh/en       │  (Human-in-the-loop)        │
│• Classifier   │• colored output│              │                             │
│  Config       │• auto-cleanup  │              │                             │
└───────────────┴───────────────┴───────────────┴─────────────────────────────┘
```

### Main Menu Function Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Main Menu Functions                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. 🚀 Auto Update & Generate                                               │
│     └── run_full_pipeline()                                                  │
│         → Data Collection → Classification → Analysis → Visualization → Web │
│                                                                              │
│  2. 🌐 Generate & Open Web Page                                             │
│     └── _generate_web_page()                                                 │
│         → Regenerate HTML based on existing data                            │
│                                                                              │
│  3. 📝 Manual Review                                                        │
│     └── _manual_review()                                                     │
│         → Filter low-confidence → Interactive review → Save history         │
│                                                                              │
│  4. 🎓 Learning Feedback                                                    │
│     └── _learning_feedback()                                                 │
│         → Analyze review history → Extract patterns → Generate suggestions  │
│                                                                              │
│  5. ⚙️ Settings & Management                                                │
│     └── _switch_classification_mode()                                        │
│         ├── Classification: Rule / Ollama / Azure OpenAI                    │
│         └── Data Maintenance: Clear cache / history / review records        │
│                                                                              │
│  0. Exit                                                                     │
│     └── cleanup() + Save config                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📰 Data Sources

### Research Papers
- arXiv API (cs.AI, cs.LG, cs.CV, cs.CL, cs.NE, stat.ML)

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
- GitHub Trending (AI/ML repositories)
- Hugging Face (models & papers)
- GitHub Blog
- Hugging Face Blog
- OpenAI Blog
- Google AI Blog
- Anthropic Blog
- DeepMind Blog

### Community & Leaders
- Product Hunt AI
- Hacker News AI (via Official API)
- **AI Leaders Tracking**:
  - Sam Altman (OpenAI CEO)
  - Satya Nadella (Microsoft CEO)
  - Sundar Pichai (Google CEO)
  - Jensen Huang (NVIDIA CEO)
  - Mark Zuckerberg (Meta CEO)
  - Elon Musk (xAI/Tesla CEO)
  - Demis Hassabis (Google DeepMind CEO)
  - Yann LeCun (Meta Chief AI Scientist)
  - Geoffrey Hinton (AI Pioneer)
  - Andrew Ng (AI Fund Managing General Partner)
  - Kai-Fu Lee (01.AI CEO)
  - Robin Li (Baidu CEO)

## 🔄 Data Processing Pipeline

### Overall Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     AI World Tracker Data Pipeline                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │Data Collector│ →  │  Classifier  │ →  │  Importance  │              │
│  │   Module     │    │    Module    │    │  Evaluator   │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         ↓                   ↓                   ↓                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ Dedup/Filter │    │  MD5 Cache   │    │ Multi-dim    │              │
│  └──────────────┘    └──────────────┘    │   Scoring    │              │
│         ↓                   ↓            └──────────────┘              │
│  ┌───────────────────────────────────────────────────────┐             │
│  │              Trend Analysis & Visualization            │             │
│  │                     (AIAnalyzer)                       │             │
│  └───────────────────────────────────────────────────────┘             │
│         ↓                                                               │
│  ┌──────────────┐    ┌──────────────┐                                  │
│  │ Web Publisher│    │Report Export │                                  │
│  └──────────────┘    └──────────────┘                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Collector Module

The collector uses **pure async architecture** for maximum performance:

**Async Mode (asyncio + aiohttp)**
- True async I/O with `asyncio` + `aiohttp`
- 20 concurrent requests globally, 3 per host (smart rate limiting)
- Real-time progress tracking with `asyncio.as_completed()`
- Automatic retry with exponential backoff

**3-Tier Deduplication System**
- **MD5 Fingerprint**: Hash-based exact duplicate detection
- **Semantic Similarity**: Jaccard similarity on normalized tokens (threshold: 0.6)
- **String Similarity**: difflib SequenceMatcher for fuzzy matching (threshold: 0.85)

| Data Type | Sources | Method | Default Count |
|-----------|---------|--------|---------------|
| Research Papers | arXiv API | API Call | 15 items |
| Developer Content | GitHub Blog, HuggingFace | RSS + API | 20 items |
| Product Releases | Official Blogs | RSS | 15 items |
| Leader Quotes | Personal Blogs/Podcasts | RSS | 15 items |
| Community Trends | HN (API) + Product Hunt | API + RSS | 10 items |
| Industry News | Global Tech Media | RSS | 25 items |

**Features**:
- **Pure async architecture**: All collection tasks run concurrently
- **URL pre-filtering**: Normalized URL check before making requests
- **Multi-tier deduplication**: MD5 + semantic + string similarity
- **History cache**: URLs, titles, and normalized_titles with 7-day expiration
- **AI relevance filtering**: Early filtering of non-AI content
- **Configurable quotas**: Per-category limits for balanced collection

### Content Classification Module

#### LLM Classifier Logic

```
Input Content
    ↓
Calculate MD5 Hash → Cache Hit? → Yes → Return Cached Result
    ↓ No
Build Classification Prompt
    ↓
Call LLM API (supports batching)
    ↓
Parse JSON Response → Failed? → Fallback to Rule Classifier
    ↓ Success
Write to Cache
    ↓
Return Classification Result
```

#### Rule Classifier Logic

```
Input Content
    ↓
Extract Title + Summary Text
    ↓
┌─────────────────────────────────────────┐
│ Parallel Match Against 6 Keyword Dicts  │
│ research / product / market /           │
│ developer / leader / community          │
│ (Each dict has weights: high=3/mid=2/low=1) │
└─────────────────────────────────────────┘
    ↓
Calculate Scores for Each Category
    ↓
Select Highest Category + Calculate Confidence
    ↓
Phrase Pattern Matching Validation
    ↓
Return Classification Result
```

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
  parallel_enabled: true    # Enable parallel collection (sync mode)
  parallel_workers: 6       # Max threads for sync mode
  async_mode: true          # Use async mode (recommended)

# Async collector settings
async_collector:
  max_concurrent_requests: 20    # Max concurrent requests
  max_concurrent_per_host: 3     # Max concurrent per host
  request_timeout: 15            # Request timeout (seconds)
  total_timeout: 120             # Total collection timeout
  max_retries: 2                 # Max retries per request
  retry_delay: 1.0               # Retry delay (seconds)
  rate_limit_delay: 0.2          # Rate limit delay (seconds)

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
  retention_days: 3            # Log retention days (auto-cleanup)
  format: standard             # standard or json
```

### LLM Providers

| Provider | Model | Cost | Setup |
|----------|-------|------|-------|
| Ollama | qwen3:8b | Free | `ollama pull qwen3:8b` |
| Azure OpenAI | gpt-4o-mini, gpt-4o | Paid | Configure via menu (Option 3) |

### Environment Variables

```bash
# Optional: Custom Ollama URL
export OLLAMA_BASE_URL="http://localhost:11434"

# Azure OpenAI is configured interactively via menu
# No environment variables needed
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

## 🏗️ Classification System Architecture

### Overview

The system uses a **dual-mode classification architecture** with automatic fallback:

```
┌─────────────────────────────────────────────────────────────┐
│                    Classification Pipeline                    │
├─────────────────────────────────────────────────────────────┤
│  Input Data                                                   │
│      ↓                                                        │
│  ┌─────────────────┐    ┌─────────────────┐                  │
│  │  LLM Classifier │ OR │ Rule Classifier │                  │
│  │  (Primary)      │    │ (Fallback)      │                  │
│  └────────┬────────┘    └────────┬────────┘                  │
│           ↓                      ↓                            │
│  ┌─────────────────────────────────────────┐                 │
│  │      Importance Evaluator               │                 │
│  │   (Multi-dimensional Weighted Scoring)  │                 │
│  └─────────────────────────────────────────┘                 │
│           ↓                                                   │
│  Output: category, importance, confidence, breakdown          │
└─────────────────────────────────────────────────────────────┘
```

### LLM Classifier (`llm_classifier.py`)

The LLM-enhanced classifier provides semantic understanding:

- **Multi-Provider Support**: Ollama (local), Azure OpenAI
- **MD5-based Caching**: Avoid redundant API calls
- **Concurrent Processing**: 3-6 threads for parallel classification
- **Auto-Fallback**: Gracefully degrades to rule-based when LLM unavailable
- **GPU Auto-Detection**: NVIDIA (CUDA), AMD (ROCm), Apple Silicon (Metal)
- **Model Keep-Alive**: 5-minute keep-alive to avoid cold starts
- **Concurrent Processing**: 3-6 threads for parallel classification
- **Auto-Fallback**: Gracefully degrades to rule-based when LLM unavailable
- **GPU Auto-Detection**: NVIDIA (CUDA), AMD (ROCm), Apple Silicon (Metal)

### Rule Classifier (`content_classifier.py`)

The rule-based classifier uses keyword patterns:

- **Keyword Matching**: Category-specific keyword dictionaries
- **Confidence Scoring**: Based on keyword match strength
- **Fast Processing**: No network dependency, instant results

## ⚖️ Multi-Dimensional Importance Evaluation

The `ImportanceEvaluator` calculates content importance using **5 weighted dimensions**:

### Dimension Weights

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Source Authority** | 25% | Credibility of the content source |
| **Recency** | 25% | How recent the content is |
| **Confidence** | 20% | Classification confidence score (capped for old content) |
| **Relevance** | 20% | Relevance to AI topics |
| **Engagement** | 10% | Social signals (stars, downloads, etc.) |

### Confidence Cap Mechanism

To prevent old, low-value content from ranking too high, the system applies confidence caps:

| Content Age | Source Authority | Confidence Cap |
|-------------|-----------------|----------------|
| > 14 days | < 0.80 (non-official) | 60% |
| > 14 days | ≥ 0.80 (official) | 75% |
| 7-14 days | < 0.70 (low authority) | 75% |
| ≤ 7 days | Any | No cap |

### Calculation Formula

```
Importance = Σ (dimension_score × weight)

Where:
- source_authority × 0.25
- recency × 0.25
- confidence × 0.20  (with cap for old content)
- relevance × 0.20
- engagement × 0.10
```

### Source Authority Scores

| Source Type | Score Range | Examples |
|-------------|-------------|----------|
| Official AI Companies | 0.90 - 1.00 | OpenAI, Google AI, Anthropic, Meta AI |
| Chinese AI Companies | 0.85 - 0.90 | Baidu, Alibaba, Tencent, DeepSeek, Zhipu, Moonshot |
| Academic/Research | 0.90 - 0.95 | arXiv, GitHub, Hugging Face |
| Professional Media | 0.70 - 0.85 | TechCrunch, The Verge, Wired, 机器之心, 量子位 |
| Community | 0.65 - 0.70 | Hacker News, Reddit, Product Hunt |
| Unknown | 0.40 | Default for unrecognized sources |

### Recency Decay Curve (Exponential Decay)

The system uses a smooth exponential decay formula: `score = (1 - min_score) × e^(-decay_rate × days) + min_score`

| Age | Score | Description |
|-----|-------|-------------|
| Today | 1.00 | Most recent |
| 1 day | ~0.89 | Very fresh |
| 3 days | ~0.70 | Recent |
| 7 days | ~0.44 | Within a week |
| 14 days | ~0.22 | Two weeks old |
| 30+ days | ~0.10 | Older content |

**Parameters**:
- Decay rate: 0.12
- Minimum score: 0.08

### Content Relevance Evaluation (Tiered Keyword System)

The system uses a four-tier keyword weighting system:

| Tier | Weight Range | Type | Example Keywords |
|------|--------------|------|------------------|
| Tier 1 | 0.12-0.18 | Breakthrough/Milestone | breakthrough, SOTA, state-of-the-art |
| Tier 2 | 0.08-0.12 | Release/Announcement | release, launch, unveil, available |
| Tier 3 | 0.05-0.10 | Technical/Model | open source, LLM, multimodal |
| Tier 4 | 0.02-0.05 | General Description | new, update, improve |

**Negative Keywords**: Rumors, unconfirmed content receive relevance penalties (-0.02 to -0.08)

### Engagement Evaluation (Unified Normalization)

Uses logarithmic normalization: `score = log(value + 1) / log(threshold_high + 1) × weight`

| Signal Type | Low Threshold | High Threshold | Weight |
|-------------|---------------|----------------|--------|
| GitHub Stars | 100 | 50,000 | 1.0 |
| HuggingFace Downloads | 1,000 | 1,000,000 | 0.9 |
| Reddit Score | 50 | 5,000 | 0.85 |
| HN Points | 30 | 1,000 | 0.85 |
| Likes | 100 | 10,000 | 0.7 |
| Comments | 20 | 500 | 0.6 |

### Importance Levels

| Score Range | Level | Emoji |
|-------------|-------|-------|
| ≥ 0.85 | Critical | 🔴 |
| ≥ 0.70 | High | 🟠 |
| ≥ 0.55 | Medium | 🟡 |
| ≥ 0.40 | Low | 🟢 |
| < 0.40 | Minimal | ⚪ |

### Output Example

```json
{
  "title": "OpenAI releases GPT-5",
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

## 🔧 Version Comparison

| Feature | v1.0 (ai-world-tracker-v1) | v2.0 (main / ai-world-tracker-v2) | v3.0-dev (developing) |
|---------|----------------------------|-----------------------------------|----------------------|
| Classification | Rule-based | LLM + Rule fallback | TBD |
| LLM Support | ❌ | ✅ Ollama/Azure OpenAI | ✅ |
| Local Models | ❌ | ✅ Qwen3:8b | ✅ |
| Data Collection | Sync only | ✅ **Async-first (78% faster)** | ✅ |
| URL Pre-filtering | ❌ | ✅ Skip cached URLs | ✅ |
| Concurrent Processing | ❌ | ✅ 20+ async requests | ✅ |
| Smart Caching | ❌ | ✅ MD5-based | ✅ |
| GPU Acceleration | ❌ | ✅ Auto-detection | ✅ |
| Unified Logging | ❌ | ✅ logger.py | ✅ |
| Log Auto-Cleanup | ❌ | ✅ Configurable retention | ✅ |
| Structured Data Dir | ❌ | ✅ data/exports, data/cache | ✅ |
| Test Organization | Scattered | ✅ tests/ directory | ✅ |
| Bilingual UI | ❌ | ✅ Chinese/English | ✅ |
| Resource Cleanup | ❌ | ✅ Auto unload LLM | ✅ |
| Confidence Cap | ❌ | ✅ Cap for old content | ✅ |
| Importance Evaluator | ❌ | ✅ 5-dimension scoring | ✅ |
| Accuracy | ~70% | ~95% | TBD |
| Collection Speed | Baseline | **~32s (78% faster)** | TBD |
| Use Case | Learning | Production | Next-gen Development |

## 🧪 Testing

Tests are organized in the `tests/` directory:

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_classifier_advanced.py -v

# Run async performance tests
pytest tests/test_async_performance.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## 📚 Documentation

Technical documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [ASYNC_OPTIMIZATION.md](docs/ASYNC_OPTIMIZATION.md) | Async collection architecture and 78% performance improvement |
| [DATA_COLLECTOR_ARCHITECTURE.md](docs/DATA_COLLECTOR_ARCHITECTURE.md) | Dual-mode (sync/async) collector design |
| [IMPORTANCE_EVALUATOR_ANALYSIS.md](docs/IMPORTANCE_EVALUATOR_ANALYSIS.md) | 5-dimension importance scoring system |
| [URL_PREFILTER_OPTIMIZATION.md](docs/URL_PREFILTER_OPTIMIZATION.md) | URL pre-filtering to skip cached content |

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Here's how to get involved:

1. **Report Issues**: Found a bug? [Open an issue](https://github.com/legendyz/ai-world-tracker/issues)
2. **Feature Requests**: Have an idea? Let us know!
3. **Submit Code**:
   - Fork the repository
   - Create a feature branch from `ai-world-tracker-v3-developing`
   - Submit a PR

### Development Workflow

```bash
# Clone and setup
git clone https://github.com/legendyz/ai-world-tracker.git
cd ai-world-tracker
git checkout ai-world-tracker-v3-developing

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
