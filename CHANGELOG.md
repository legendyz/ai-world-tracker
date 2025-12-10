# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0-beta] - 2025-12-10 (feature/data-collection-v2 Branch)

### Added
- **High-Performance Async Data Collection**
  - True async architecture with `asyncio` + `aiohttp` (78% faster than sync mode)
  - 20+ concurrent requests with smart rate limiting
  - Per-host connection limits (max 3 per host) to avoid rate limiting
  - Configurable timeouts: request (15s), total (120s)
  - Automatic retry mechanism (2 retries with 1s delay)

- **URL Pre-filtering Optimization**
  - Check URL cache BEFORE making HTTP requests (not after)
  - Skip already-cached content to reduce network overhead
  - Filter at RSS/API list level, not after content parsing
  - Estimated 14%+ additional time savings when cache is populated

- **Async Collector Configuration**
  - New `async_collector` section in `config.yaml`
  - Configurable: max_concurrent_requests, max_concurrent_per_host
  - Configurable: request_timeout, total_timeout, max_retries
  - Configurable: retry_delay, rate_limit_delay

- **Technical Documentation**
  - `docs/ASYNC_OPTIMIZATION.md`: Performance analysis and architecture
  - `docs/DATA_COLLECTOR_ARCHITECTURE.md`: Dual-mode design documentation
  - `docs/URL_PREFILTER_OPTIMIZATION.md`: URL pre-filtering details
  - `docs/IMPORTANCE_EVALUATOR_ANALYSIS.md`: 5-dimension scoring analysis

### Changed
- **Data Collector Architecture**
  - Async mode is now the default (configurable via `config.yaml`)
  - Sync mode available as fallback for environments without async support
  - Automatic mode selection based on `asyncio`/`aiohttp` availability

- **Performance Metrics**
  | Metric | Sync Mode | Async Mode | Improvement |
  |--------|-----------|------------|-------------|
  | Collection Time | ~147s | ~32s | **78% faster** |
  | Requests Made | 21 | 96 | **357% increase** |
  | Request Rate | 0.14 req/s | 3.0 req/s | **21x faster** |

### Fixed
- All async methods now properly use semaphore for rate limiting
- Parameter order consistency in `_fetch_json_async()`
- Proper exception handling with `return_exceptions=True`

---

## [2.0.3] - 2025-12-08 (Main Branch)

### Added
- **New Data Maintenance Options**
  - "Clear manual review records" (option 7): Clears `review_history_*.json` and `learning_report_*.json` files
  - "Clear all data" (option 8): Comprehensive data reset with YES confirmation required
  - Both functions support dual output mode (console + log file)

- **Confidence Cap Mechanism**
  - Prevents older low-authority content from ranking too high
  - For content older than 14 days (recency ≤ 0.50):
    - Low authority sources (< 0.80): confidence capped at 60%
    - High authority sources (≥ 0.80): confidence capped at 75%

- **Ollama Local Models**
  - Added DeepSeek-R1:14b as additional local model option

### Changed
- **Importance Weight Adjustment**
  - Recency weight: 20% → 25% (increased to favor fresh content)
  - Confidence weight: 25% → 20% (reduced to prevent overconfidence)
  - Other weights unchanged: source_authority 25%, relevance 20%, engagement 10%

- **Menu Restructuring**
  - Classification modes: Options 1-3 (Rule, Ollama, OpenAI)
  - Data maintenance: Options 4-8 (LLM cache, collection cache, export history, review history, all data)
  - Settings menu now shows 8 options plus back option

### Removed
- **Anthropic Provider**
  - Removed Anthropic from classification mode options
  - Simplified to two cloud providers: Ollama (local) and OpenAI

### Fixed
- Review history and learning report files now correctly saved to `data/exports/` directory
- Consistent dual output mode for all data maintenance functions

---

## [2.0.2] - 2025-12-07 (Main Branch)

### Added
- **Project Directory Restructuring**
  - New `data/exports/` directory for exported data and reports
  - New `data/cache/` directory for cache files
  - Cleaner project root directory structure

- **Enhanced Logging System**
  - Smart emoji deduplication (avoids double emojis like `📦 📦`)
  - Auto-cleanup of old log files based on retention days
  - Support for loading configuration from `config.yaml`
  - New `exception()` method for stack trace logging
  - JSON format logging support (optional)
  - Configurable via `config.yaml`:
    - Log level, directory, console/file output
    - Max file size, backup count, retention days

- **New Configuration Options**
  - `data.exports_dir`: Directory for exported data and reports
  - `data.cache_dir`: Directory for cache files
  - `logging.*`: Full logging configuration support

### Changed
- Data files now saved to `data/exports/` instead of project root
- Cache files now saved to `data/cache/` instead of project root
- Updated `.gitignore` to ignore `data/exports/` and `data/cache/`
- All modules updated to use new directory paths

### Fixed
- Emoji duplication issue in log messages (e.g., `✅ ✅` → `✅`)
- Step logging duplication (e.g., `【步骤 1/5】【步骤 1/5】` → `【步骤 1/5】`)

---

## [2.0.1] - 2025-12-06 (Main Branch)

### Added
- **Unified Logging System** (`logger.py`)
  - Colored console output with ANSI codes
  - Rotating file handler (10MB max, 5 backups)
  - LogHelper class with emoji support methods
  - Singleton pattern for global logger management
  - Configurable log levels and output destinations

- **Test Organization**
  - Created `tests/` directory structure
  - Added `pytest.ini` configuration file
  - Moved all 18 test files to `tests/`
  - Added `__init__.py` with path setup

- **Unified Configuration Management**
  - Merged `config_manager.py` into `config.py`
  - Support for YAML configuration file (`config.yaml`)
  - Support for `.env` file and environment variables
  - Priority: ENV > .env > YAML > defaults
  - Added `CollectorConfig` dataclass for data collection settings
  - Added `reload()` method for runtime configuration refresh

### Changed
- Configuration access unified through `from config import config`
- Test files organized under `tests/` directory
- Removed deprecated `config_manager.py`
- Removed outdated `PROJECT_STATUS.md` and `QUICK_START.md`

### Fixed
- Configuration module import consistency across all modules

---

## [2.0.0] - 2025-12-06 (Main Branch)

### Added
- **LLM-Enhanced Classification System**
  - Multi-provider support: Ollama, Azure OpenAI
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
  - Multi-source priority: ENV > .env > YAML > defaults
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
  - `logger.py`: Unified logging system
  - `i18n.py`: Internationalization support

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

### Synced with Main
- All v2.0.2 features merged from main branch
- Project directory restructuring
- Enhanced logging system
- New configuration options

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
