# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-06 (Main Branch)

### Added
- **LLM-Enhanced Classification System**
  - Multi-provider support: Ollama, OpenAI, Anthropic
  - Local model support with Ollama (Qwen3:8b) - completely free
  - Semantic understanding for 95%+ classification accuracy
  - MD5-based intelligent caching system
  - Automatic fallback to rule-based classification
  
- **Performance Optimizations**
  - Concurrent processing with ThreadPoolExecutor (3 workers)
  - Smart content skipping for pre-classified items
  - Optimized prompts (50% token reduction)
  - Ollama parameter tuning (6-9x speed improvement)
  - Processing time: 28 minutes → 3-5 minutes for 60 items

- **GPU Auto-Detection**
  - NVIDIA CUDA support
  - AMD ROCm support (Linux)
  - Apple Metal support (macOS)
  - Automatic configuration optimization

- **Configuration Management** (`config.py`)
  - Unified configuration interface
  - Multi-source priority: ENV > .env > defaults
  - Secure API key management
  - Provider-agnostic design

- **Enhanced User Interface**
  - Hierarchical menu structure
  - Manual workflow sub-menu
  - Real-time classification mode display
  - Context-aware menu items (LLM vs Rule mode)
  - Auto-open web page after generation
  - Internationalization support (EN/CN)

- **New Modules**
  - `llm_classifier.py`: Core LLM classification engine
  - `config.py`: Configuration management
  - `i18n.py`: Internationalization support
  - `config_manager.py`: YAML configuration loader

### Changed
- Menu structure reorganized with settings sub-menu
- Manual review and learning feedback now rule-mode only
- Data collection limited to 10 items per category (60 total)
- Classification mode displayed in main menu
- Web page automatically opens after generation

### Technical Details
- LLM timeout: 45s
- Ollama config: num_predict=300, num_ctx=2048
- Concurrent workers: 3 threads
- Cache storage: JSON with MD5 keys

---

## [1.0.0] - 2025-12-05 (ai-world-tracker-v1 Branch)

### Features
This is the first complete release of AI World Tracker.

- **Rule-Based Classification System**
  - Keyword matching and pattern recognition
  - Six content categories: research, product, market, developer, leader, community
  - Confidence score calculation based on keyword weights
  - Learnable through manual review feedback

- **Multi-Source Data Collection**
  - arXiv papers (cs.AI, cs.LG, cs.CV, cs.CL)
  - GitHub trending repositories
  - Tech news RSS feeds (TechCrunch, The Verge, Wired, etc.)
  - AI company blogs (OpenAI, Google AI, Hugging Face)
  - Chinese tech media support

- **Data Visualization**
  - Technology hotspots chart
  - Content distribution pie chart
  - Regional distribution chart
  - Daily trend line chart

- **Web Dashboard Generation**
  - Responsive HTML dashboard
  - Mobile-friendly design
  - Category-based news organization
  - GitHub Pages integration

- **Manual Review System**
  - Review low-confidence classifications
  - Provide corrections for classifier improvement
  - Review history tracking

- **Learning Feedback System**
  - Analyze review history patterns
  - Generate classifier improvement suggestions
  - Continuous learning support

### Notes
This version is ideal for:
- Hobbyists who want to understand the codebase
- Developers looking to customize the classification system
- Those who prefer a simpler, dependency-free solution
- Learning purposes and educational projects

---

## [Unreleased] - feature/data-collection-v2 Branch

### In Development
- Enhanced data collection capabilities
- Improved RSS feed parsing
- Better error handling for network requests
- Extended data source support
- Collection rate optimization

### Status
- **Beta**: Not recommended for production use
- Active development in progress
- Contributors welcome

---

## Version Guidelines

### Semantic Versioning
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

### Branch Strategy
- `main`: Stable releases only
- `ai-world-tracker-v1`: Legacy support (bug fixes only)
- `feature/*`: Development branches
