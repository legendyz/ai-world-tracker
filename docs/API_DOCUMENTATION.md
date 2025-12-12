# AI World Tracker - API文档

**版本**: 2.1.0-beta  
**最后更新**: 2025-12-12  
**状态**: 正式版

---

## 目录

1. [数据收集器 (DataCollector)](#数据收集器-datacollector)
2. [LLM分类器 (LLMClassifier)](#llm分类器-llmclassifier)
3. [规则分类器 (ContentClassifier)](#规则分类器-contentclassifier)
4. [重要性评估器 (ImportanceEvaluator)](#重要性评估器-importanceevaluator)
5. [AI分析器 (AIAnalyzer)](#ai分析器-aianalyzer)
6. [可视化器 (DataVisualizer)](#可视化器-datavisualizer)
7. [Web发布器 (WebPublisher)](#web发布器-webpublisher)
8. [主程序 (AIWorldTracker)](#主程序-aiworldtracker)

---

## 数据收集器 (DataCollector)

### 类名
```python
AIDataCollector  # 主类
DataCollector = AIDataCollector  # 向后兼容别名
```

### 初始化
```python
from data_collector import DataCollector

collector = DataCollector()
```

### 主要方法

#### `collect_all()` - 收集所有数据源
```python
async def collect_all(
    self,
    research_count: int = 30,
    developer_count: int = 20,
    news_count: int = 15,
    product_count: int = 15,
    leader_count: int = 10,
    community_count: int = 10
) -> Dict[str, List[Dict]]
```

**参数**:
- `research_count`: 研究类内容数量限制
- `developer_count`: 开发者类内容数量限制
- `news_count`: 新闻类内容数量限制
- `product_count`: 产品类内容数量限制
- `leader_count`: 领袖观点类内容数量限制
- `community_count`: 社区讨论类内容数量限制

**返回**:
```python
{
    'research': [{'title': '...', 'summary': '...', 'link': '...', 'source': '...'}],
    'developer': [...],
    'news': [...],
    'product': [...],
    'leader': [...],
    'community': [...]
}
```

**使用示例**:
```python
async with collector:
    data = await collector.collect_all(research_count=50)
    
for category, items in data.items():
    print(f"{category}: {len(items)} items")
```

### 统计信息

#### `stats` - 采集统计
```python
collector.stats = {
    'requests_made': int,      # 发出的请求数
    'requests_failed': int,    # 失败的请求数
    'items_collected': int,    # 收集的条目数
    'failed_sources': List[Dict],  # 失败的数据源列表
    'start_time': float,       # 开始时间
    'end_time': float          # 结束时间
}
```

### 配置属性

```python
collector.async_config  # 异步采集配置（ConfigManager实例）
collector.history_cache  # 历史缓存字典
collector.rss_feeds  # RSS源配置（dict）
```

### 上下文管理器

```python
async with collector:
    # 自动管理session生命周期
    data = await collector.collect_all()
# session自动清理
```

---

## LLM分类器 (LLMClassifier)

### 初始化
```python
from llm_classifier import LLMClassifier

classifier = LLMClassifier(
    provider='ollama',        # 'ollama' | 'openai' | 'azure'
    model='qwen3:8b',
    enable_cache=True,
    max_workers=3,
    batch_size=10
)
```

**参数**:
- `provider`: LLM提供商
- `model`: 模型名称
- `enable_cache`: 是否启用缓存
- `max_workers`: 并发worker数量
- `batch_size`: 批处理大小

### 主要方法

#### `classify_batch()` - 批量分类（推荐）
```python
def classify_batch(
    self,
    items: List[Dict],
    show_progress: bool = True,
    use_cache: bool = True
) -> List[Dict]
```

**参数**:
- `items`: 要分类的条目列表
- `show_progress`: 是否显示进度条
- `use_cache`: 是否使用缓存

**返回**:
```python
[
    {
        'title': '...',
        'summary': '...',
        'content_type': 'research',  # research | product | developer | market | news | leader | community
        'tech_categories': ['Generative AI', 'NLP'],
        'reasoning': '分类原因说明',
        'cached': False
    },
    ...
]
```

**使用示例**:
```python
items = [
    {'title': 'GPT-4 Released', 'summary': 'New model...'},
    {'title': 'TensorFlow Update', 'summary': 'Bug fixes...'}
]

results = classifier.classify_batch(items)
for result in results:
    print(f"{result['title']}: {result['content_type']}")
```

#### `classify_item()` - 单条分类
```python
def classify_item(
    self,
    item: Dict,
    use_cache: bool = True
) -> Dict
```

**参数**:
- `item`: 单个条目
- `use_cache`: 是否使用缓存

**返回**: 与classify_batch相同的结构

### GPU信息

```python
classifier.gpu_info: Optional[GPUInfo]  # GPU检测信息

# GPUInfo结构
{
    'available': bool,
    'gpu_type': 'nvidia' | 'amd' | 'apple',
    'gpu_name': str,
    'vram_mb': int,
    'cuda_available': bool,
    'rocm_available': bool,
    'metal_available': bool,
    'ollama_gpu_supported': bool
}
```

### 降级策略

```python
classifier.fallback_strategy: FallbackStrategy

# 方法
fallback_strategy.record_error(reason: FallbackReason)
fallback_strategy.record_success()
fallback_strategy.should_use_llm() -> bool
```

### 统计信息

```python
classifier.stats = {
    'total_classified': int,
    'cache_hits': int,
    'llm_calls': int,
    'fallback_used': int
}
```

---

## 规则分类器 (ContentClassifier)

### 初始化
```python
from content_classifier import ContentClassifier

classifier = ContentClassifier()
```

### 主要方法

#### `classify_batch()` - 批量分类
```python
def classify_batch(
    self,
    items: List[Dict],
    show_progress: bool = False
) -> List[Dict]
```

**返回**: 与LLMClassifier相同的结构

#### `classify_item()` - 单条分类
```python
def classify_item(self, item: Dict) -> Dict
```

**使用示例**:
```python
items = [
    {'title': 'Research Paper', 'summary': 'Academic study...'},
    {'title': 'Product Launch', 'summary': 'New tool released...'}
]

results = classifier.classify_batch(items)
```

### 辅助方法

```python
# 过滤方法
get_filtered_items(
    items: List[Dict],
    content_type: Optional[str] = None,
    tech_category: Optional[str] = None,
    region: Optional[str] = None
) -> List[Dict]
```

---

## 重要性评估器 (ImportanceEvaluator)

### 初始化
```python
from importance_evaluator import ImportanceEvaluator

evaluator = ImportanceEvaluator()
```

### 主要方法

#### `calculate_importance()` - 计算重要性分数
```python
def calculate_importance(self, item: Dict) -> float
```

**参数**:
- `item`: 包含以下字段的字典
  - `source`: 数据来源
  - `content_type`: 内容类型
  - `tech_categories`: 技术分类列表
  - `published`: 发布时间（可选）

**返回**: `0.0 - 1.0` 之间的分数

**评分维度**:
1. **来源权威性** (25%): 基于数据源权威度
2. **内容新鲜度** (25%): 基于发布时间
3. **相关性** (20%): 基于技术分类
4. **置信度** (20%): 基于分类置信度
5. **互动度** (10%): 基于用户反馈

**使用示例**:
```python
item = {
    'title': 'GPT-4 Released',
    'source': 'OpenAI',
    'content_type': 'product',
    'tech_categories': ['Generative AI'],
    'published': '2025-12-12T10:00:00'
}

score = evaluator.calculate_importance(item)
print(f"Importance: {score:.2f}")  # 0.85
```

---

## AI分析器 (AIAnalyzer)

### 初始化
```python
from ai_analyzer import AIAnalyzer

analyzer = AIAnalyzer(
    api_key=None,  # OpenAI API密钥（可选）
    verbose=False
)
```

### 主要方法

#### `analyze_trends()` - 分析趋势
```python
def analyze_trends(self, items: List[Dict]) -> Dict
```

**返回**:
```python
{
    'content_types': {
        'research': 45,
        'product': 30,
        ...
    },
    'tech_categories': {
        'Generative AI': 67,
        'Computer Vision': 23,
        ...
    },
    'top_items': [...]  # 按重要性排序的top条目
}
```

#### `generate_summary()` - 生成摘要
```python
def generate_summary(self, item: Dict) -> str
```

**使用示例**:
```python
# 分析趋势
trends = analyzer.analyze_trends(classified_items)

# 按类型统计
for ctype, count in trends['content_types'].items():
    print(f"{ctype}: {count}")
```

---

## 可视化器 (DataVisualizer)

### 初始化
```python
from visualizer import DataVisualizer

visualizer = DataVisualizer()
visualizer.output_dir = 'visualizations'
```

### 主要方法

#### `visualize_all()` - 生成所有图表
```python
def visualize_all(self, trends: Dict) -> Dict[str, str]
```

**参数**:
- `trends`: analyze_trends()的返回值

**返回**:
```python
{
    'content_type_pie': 'path/to/content_types.png',
    'tech_category_bar': 'path/to/tech_categories.png',
    'timeline': 'path/to/timeline.png',
    ...
}
```

**使用示例**:
```python
trends = analyzer.analyze_trends(items)
chart_files = visualizer.visualize_all(trends)

for chart_name, filepath in chart_files.items():
    print(f"Generated: {chart_name} -> {filepath}")
```

---

## Web发布器 (WebPublisher)

### 初始化
```python
from web_publisher import WebPublisher

publisher = WebPublisher()
publisher.output_dir = 'web_output'
```

### 主要方法

#### `generate_html_page()` - 生成HTML页面
```python
def generate_html_page(
    self,
    items: List[Dict],
    trends: Dict,
    chart_files: Dict[str, str]
) -> str
```

**参数**:
- `items`: 分类和评分后的数据列表
- `trends`: 趋势分析结果
- `chart_files`: 图表文件路径字典

**返回**: 生成的HTML文件路径

**使用示例**:
```python
html_file = publisher.generate_html_page(
    items=classified_items,
    trends=trends,
    chart_files=chart_files
)
print(f"HTML生成: {html_file}")
```

---

## 主程序 (AIWorldTracker)

### 初始化
```python
from TheWorldOfAI import AIWorldTracker

# 自动模式（无交互）
tracker = AIWorldTracker(auto_mode=True)

# 交互模式
tracker = AIWorldTracker(auto_mode=False)
```

### 组件属性

```python
tracker.collector        # AIDataCollector实例
tracker.classifier       # ContentClassifier实例
tracker.llm_classifier   # LLMClassifier实例（如果已初始化）
tracker.analyzer         # AIAnalyzer实例
tracker.visualizer       # DataVisualizer实例
tracker.web_publisher    # WebPublisher实例
tracker.reviewer         # ManualReviewer实例
tracker.learner          # LearningFeedback实例
```

### 数据属性

```python
tracker.data            # List[Dict] - 收集的数据
tracker.trends          # Dict - 趋势分析结果
tracker.chart_files     # Dict[str, str] - 图表文件路径
```

### 配置属性

```python
tracker.classification_mode  # 'rule' | 'llm'
tracker.llm_provider        # 'ollama' | 'openai' | 'azure'
tracker.llm_model           # 模型名称
```

---

## API变更历史

### v2.1.0-beta (2025-12-10)
- **BREAKING**: `DataCollector.collect_all_sources()` → `collect_all()`
- **BREAKING**: `collector.config` → `collector.async_config`
- **BREAKING**: `collector.stats['total']` → `stats['requests_made']`
- **BREAKING**: `collector.stats['success']` → `stats['items_collected']`
- **BREAKING**: `collector.stats['failed']` → `stats['requests_failed']`
- **NEW**: 异步数据收集（78%性能提升）
- **NEW**: URL预过滤优化

### v2.0.3 (2025-12-08)
- **BREAKING**: `LLMClassifier.classify()` → `classify_batch()` (主要API)
- **NEW**: 添加`classify_item()`用于单条分类
- **BREAKING**: `gpu_available: bool` → `gpu_info: GPUInfo`
- **BREAKING**: `circuit_breaker` → `fallback_strategy`
- **NEW**: 智能降级策略系统

### v2.0.2 (2025-12-07)
- **NEW**: GPU自动检测
- **NEW**: 并发分类支持

### v2.0.0 (2025-12-06)
- **NEW**: LLM分类器
- **NEW**: 多提供商支持
- **NEW**: 缓存系统

---

## 常见使用模式

### 完整工作流示例

```python
import asyncio
from TheWorldOfAI import AIWorldTracker

async def main():
    # 1. 初始化
    tracker = AIWorldTracker(auto_mode=True)
    
    # 2. 数据收集
    async with tracker.collector:
        data_dict = await tracker.collector.collect_all(research_count=50)
    
    # 展平数据
    all_items = []
    for items in data_dict.values():
        all_items.extend(items)
    
    # 3. 分类
    classified = tracker.classifier.classify_batch(all_items)
    
    # 4. 重要性评估
    from importance_evaluator import ImportanceEvaluator
    evaluator = ImportanceEvaluator()
    for item in classified:
        item['importance'] = evaluator.calculate_importance(item)
    
    # 5. 趋势分析
    trends = tracker.analyzer.analyze_trends(classified)
    
    # 6. 可视化
    chart_files = tracker.visualizer.visualize_all(trends)
    
    # 7. 生成Web页面
    html_file = tracker.web_publisher.generate_html_page(
        classified, trends, chart_files
    )
    
    print(f"✅ 完成！HTML: {html_file}")

if __name__ == '__main__':
    asyncio.run(main())
```

---

## 错误处理

### 数据收集错误
```python
try:
    async with collector:
        data = await collector.collect_all()
except Exception as e:
    print(f"收集失败: {e}")
    # 检查failed_sources获取详情
    for failure in collector.stats['failed_sources']:
        print(f"  - {failure['source']}: {failure['error']}")
```

### LLM分类错误
```python
# LLM自动降级到规则分类
results = classifier.classify_batch(items)

# 检查是否使用了降级
for result in results:
    if result.get('fallback_used'):
        print(f"使用降级: {result['title']}")
```

---

## 性能优化建议

1. **批量处理**: 始终使用`classify_batch()`而非循环调用`classify_item()`
2. **启用缓存**: 设置`enable_cache=True`减少重复API调用
3. **合理配额**: 根据需求设置各类别的数量限制
4. **异步采集**: 使用async/await获得最佳性能
5. **GPU加速**: 确保Ollama检测到GPU以提升速度

---

**文档版本**: 1.0  
**最后更新**: 2025-12-12  
**维护者**: AI World Tracker Team
