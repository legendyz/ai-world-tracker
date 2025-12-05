# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - feature/ai-enhancements

### Added - v2.0.0-beta
- **LLM-Enhanced Classification System**
  - Multi-provider support: Ollama, OpenAI, Anthropic
  - Local model support with Ollama (Qwen3:8b)
  - Semantic understanding for 95%+ accuracy
  - MD5-based intelligent caching system
  - Automatic fallback to rule-based classification
  
- **Performance Optimizations**
  - Concurrent processing with ThreadPoolExecutor (3 workers)
  - Smart content skipping for pre-classified items
  - Optimized prompts (50% token reduction)
  - Ollama parameter tuning (6-9x speed improvement)
  - Processing time: 28 minutes → 3-5 minutes for 60 items

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

- **New Modules**
  - `llm_classifier.py`: Core LLM classification engine
  - `config.py`: Configuration management
  - `test_ollama.py`: Ollama integration testing
  - `test_llm_classifier.py`: LLM classifier tests
  - `demo_llm_classifier.py`: Interactive demonstration

- **Documentation**
  - `LLM_CLASSIFICATION_GUIDE.md`: Comprehensive usage guide
  - `LLM_IMPLEMENTATION_SUMMARY.md`: Technical implementation details
  - `OLLAMA_SETUP_COMPLETE.md`: Ollama setup walkthrough
  - `PROJECT_STATUS.md`: Complete project status report
  - `.env.example`: Environment configuration template

### Changed
- Menu structure simplified and reorganized
- Manual review and learning feedback now rule-mode only
- Data collection limited to 10 items per category (60 total)
- Classification mode now displayed in menu
- Web page automatically opens after generation

### Technical Details
- LLM timeout: 60s → 45s
- Ollama config: num_predict=300, num_ctx=2048
- Concurrent workers: 3 threads
- Cache storage: JSON with MD5 keys
- Prompt length: ~50% reduction

## [1.2.0] - 2025-12-05 (Main Branch)

### Changed
- Simplified main menu from 6 to 4 items
- Removed "View Report" option
- Removed "Search & Filter" option
- Renamed menu item to "Auto Update & Generate"

### Fixed
- Menu numbering consistency
- User experience improvements

## [1.2.0] - 2025-12-03

### Added
- Direct GitHub Pages integration: Web publisher now outputs index.html to repository root
- Dual output system: Main output to root directory + backup to web_output/
- Enhanced logging for web generation showing both output locations
- Automatic GitHub Pages compatibility without manual file copying

### Changed
- **BREAKING**: WebPublisher default output directory changed from "web_output" to "." (root)
- Improved web dashboard with latest AI data and trends
- Enhanced responsive design for better mobile experience
- Updated project documentation to reflect current architecture

### Fixed
- GitHub Pages deployment issues resolved
- Web dashboard now automatically syncs with repository root
- Eliminated manual copy step for web deployment

### Technical Details
- WebPublisher.__init__(): Default output_dir parameter changed
- generate_html_page(): Implements dual file output strategy
- Enhanced error handling and user feedback

## [1.1.0] - 2025-12-02

### Added
- Comprehensive English documentation for international developers
- Bilingual project support (Chinese/English)
- Professional README.md in English for global accessibility
- GitHub repository setup for multiple accounts (legendz_microsoft, legendyz)

### Changed
- README.md converted to English as primary language
- Project title updated to emphasize international scope
- Documentation structure improved for open source standards

### Fixed
- Type annotation issues in TheWorldOfAI.py resolved
- Import statements optimized for Optional[str] typing

## [1.0.0] - 2025-12-02
### Added
- 🎉 Initial release of AI World Tracker
- 📊 Complete data collection system with 29 high-quality sources
- 🤖 Intelligent content classification (6 dimensions)
- 📈 Real-time trend analysis and visualization
- 🌐 Responsive web dashboard generation
- 🔄 Automated deduplication mechanism
- ⚙️ Configurable data sources and filtering
- 📱 Multi-device compatible HTML interface
- 🔧 Built-in diagnostic and validation tools
- 📝 Comprehensive documentation and usage guide

### Data Sources
- **Academic**: arXiv (AI/ML/CV/NLP categories)
- **Developer**: GitHub Blog, Hugging Face, OpenAI Blog
- **News**: TechCrunch, Wired, MIT Technology Review, Synced Review
- **Chinese**: 36氪, IT之家, 机器之心, 量子位, InfoQ AI
- **Community**: Hacker News AI, Product Hunt AI
- **Corporate**: Google AI Blog, Microsoft AI Blog

### Features
- **Multi-dimensional Classification**: Research, Product, Market, Developer, Leader, Community
- **Technology Categorization**: Generative AI, Computer Vision, NLP, Reinforcement Learning, MLOps, AI Ethics
- **Regional Analysis**: China, USA, Europe, Global
- **Quality Control**: 30-day freshness filter, AI relevance detection, importance scoring
- **Visualization**: 5 types of charts (tech hotspots, content distribution, regional analysis, daily trends, dashboard)
- **Web Publishing**: Responsive HTML with embedded charts and collapsible tables
- **Export Options**: JSON data, text reports, PNG charts, HTML dashboard

### Technical
- **Python 3.8+ support**
- **Cross-platform compatibility** (Windows/Linux/macOS)
- **Robust error handling** with fallback data
- **Configurable RSS feed management**
- **Link validation and connectivity testing**
- **Automated installation script** (install.ps1)

---

## Release Notes Format

Each release includes:
- 📊 **Data Sources**: Number and types of integrated sources
- 🔧 **Features**: New functionality and improvements
- 🐛 **Bug Fixes**: Resolved issues and stability improvements
- 📈 **Performance**: Speed and efficiency enhancements
- 📚 **Documentation**: Updated guides and examples
- 🔄 **Breaking Changes**: API or configuration changes (if any)

---

## Version History

- **v1.0.0** (2025-12-02): Initial public release
- **v0.9.x**: Development and testing phases
- **v0.1.x**: Proof of concept and MVP development