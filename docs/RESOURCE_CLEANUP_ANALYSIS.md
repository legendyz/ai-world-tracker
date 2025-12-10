# 资源释放机制分析报告 (Resource Cleanup Analysis)

## 📋 执行概要 (Executive Summary)

本报告全面分析了 AI World Tracker 应用程序退出时的资源释放机制，识别了现有的清理流程、潜在的资源泄露风险，并提供了详细的优化建议。

**核心发现**:
- ✅ **主入口清理机制**: 存在 try-finally 结构确保基本清理
- ⚠️ **部分清理不完整**: LLM 缓存、ImportanceEvaluator 学习数据、HTTP 客户端等需要改进
- ❌ **缺失清理**: matplotlib 图表句柄、事件循环、线程池等无显式清理
- 🔧 **优化空间**: 需要添加统一的资源管理器和上下文管理器

---

## 🔍 资源类型清单 (Resource Inventory)

### 1. 网络资源 (Network Resources)

#### 1.1 HTTP 客户端
**位置**: `llm_classifier.py`

```python
# 问题代码 - 无资源清理
response = requests.post(
    'http://localhost:11434/api/generate',
    json={...},
    timeout=self.timeout
)
```

**问题**: 
- 使用 `requests` 库直接发送请求，未使用会话管理
- 每次请求创建新的连接，无连接池复用
- 未显式关闭连接，依赖 Python GC

**风险等级**: 🟡 **中等**
- 短期影响: TCP 连接可能延迟关闭，占用系统资源
- 长期影响: 在频繁调用场景下可能导致端口耗尽

#### 1.2 异步 HTTP 会话
**位置**: `data_collector.py` (lines 2298-2330)

```python
async def _collect_all_async(self) -> Dict[str, List[Dict]]:
    connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
    timeout = aiohttp.ClientTimeout(total=60, connect=10)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # ... 异步采集逻辑
```

**状态**: ✅ **正确使用上下文管理器**
- 使用 `async with` 确保会话自动关闭
- 连接器会在会话关闭时正确清理

**风险等级**: 🟢 **低**

#### 1.3 事件循环清理
**位置**: `data_collector.py` (lines 795-810)

```python
def _collect_all(self) -> Dict[str, List[Dict]]:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._collect_all_async())
        finally:
            loop.close()  # ✅ 正确清理
    except Exception as e:
        log.error(f"Async collection failed: {e}")
        return self._collect_all_sync(True, 6)
```

**状态**: ✅ **正确清理**
- 使用 finally 块确保 loop.close() 被调用

**风险等级**: 🟢 **低**

### 2. 文件资源 (File Resources)

#### 2.1 缓存文件 - LLM 分类缓存
**位置**: `llm_classifier.py` (lines 644-653)

```python
def _save_cache(self):
    """保存缓存"""
    if not self.enable_cache:
        return
    try:
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(t('llm_cache_save_failed', error=str(e)))
```

**当前调用时机**: ❌ **仅在特定场景调用**
- 分类任务完成后可能保存
- 应用退出时 **未调用**

**问题**:
- `cleanup()` 方法中未调用 `_save_cache()`
- 未保存的缓存在异常退出时会丢失

**风险等级**: 🔴 **高**

#### 2.2 学习数据 - Importance Evaluator
**位置**: `importance_evaluator.py` (lines 668-690)

```python
def _save_learning_data(self):
    """保存学习数据到文件"""
    try:
        os.makedirs(os.path.dirname(LEARNING_CONFIG_FILE), exist_ok=True)
        
        data = {
            'source_performance': dict(self.source_performance),
            'last_updated': datetime.now().isoformat()
        }
        
        with open(LEARNING_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        log.info(f"💾 Saved learning data: {len(self.source_performance)} sources")
    except Exception as e:
        log.warning(f"Failed to save learning data: {e}")
```

**当前调用时机**: ⚠️ **定期自动保存**
- 每 10 次更新自动保存 (line 648)
- 应用退出时 **未显式调用**

**问题**:
- 如果更新次数不是 10 的倍数，最后几次更新会丢失
- cleanup() 未调用该方法确保最终保存

**风险等级**: 🟡 **中等**

#### 2.3 采集历史缓存
**位置**: `data_collector.py` (lines 283-296)

```python
def _save_history_cache(self):
    """保存采集历史缓存"""
    try:
        cache_to_save = {
            'urls': list(self.history_cache['urls']),
            'titles': list(self.history_cache['titles']),
            'last_updated': datetime.now().isoformat()
        }
        with open(self.history_cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(t('dc_cache_save_failed', error=str(e)))
```

**当前调用**: ✅ **在 cleanup() 中调用**
```python
# TheWorldOfAI.py, line 186-189
try:
    self.collector._save_history_cache()
except Exception:
    pass
```

**风险等级**: 🟢 **低**

#### 2.4 文件句柄使用
**通用模式**: ✅ **正确使用上下文管理器**
```python
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

所有文件操作均使用 `with` 语句，确保自动关闭。

**风险等级**: 🟢 **低**

### 3. 图形资源 (Graphics Resources)

#### 3.1 Matplotlib 图表
**位置**: `visualizer.py`

```python
def plot_tech_hotspots(self, tech_data: Dict, save: bool = True) -> str:
    # ... 创建图表
    fig, ax = plt.subplots(figsize=(12, 6))
    # ... 绘制逻辑
    
    if save:
        filepath = os.path.join(self.output_dir, 'tech_hotspots.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
    
    plt.close()  # ✅ 正确清理
    return filepath
```

**状态**: ✅ **每个绘图方法末尾调用 `plt.close()`**
- 发现 5 处正确使用 (lines 197, 259, 312, 368, 470)

**风险等级**: 🟢 **低**

### 4. 内存资源 (Memory Resources)

#### 4.1 LLM 模型显存/内存
**位置**: `llm_classifier.py` (lines 555-575)

```python
def unload_model(self):
    """立即卸载模型（释放显存/内存）"""
    if self.provider != LLMProvider.OLLAMA:
        return
    
    try:
        import requests
        
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': self.model,
                'prompt': '',
                'stream': False,
                'keep_alive': '0s'  # 立即卸载
            },
            timeout=10
        )
        
        if response.status_code == 200:
            self.is_warmed_up = False
```

**当前调用**: ✅ **在 cleanup() 中调用**
```python
# TheWorldOfAI.py, lines 179-185
def cleanup(self):
    if self.llm_classifier is not None:
        try:
            self.llm_classifier.unload_model()
        except Exception as e:
            log.warning(t('cleanup_error', error=str(e)))
```

**风险等级**: 🟢 **低**

#### 4.2 缓存字典
**位置**: 多处
- `llm_classifier.py`: `self.cache: Dict[str, Dict] = {}` (line 410)
- `data_collector.py`: `self.history_cache` (sets)
- `importance_evaluator.py`: `self.source_performance` (defaultdict)

**问题**:
- 内存中的字典在应用退出时会自动释放
- 但未保存的数据会丢失（见文件资源章节）

**风险等级**: 🟡 **中等** (数据丢失风险)

### 5. 线程/进程资源 (Threading Resources)

#### 5.1 ThreadPoolExecutor
**位置**: `data_collector.py` 多处使用

```python
# 示例使用 (未找到显式清理)
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = {executor.submit(func, *args): name for ...}
    # ...
```

**状态**: ✅ **使用上下文管理器**
- `with` 语句确保线程池在退出时关闭

**风险等级**: 🟢 **低**

---

## 🏗️ 当前清理流程 (Current Cleanup Flow)

### 主入口点 (Main Entry Point)
**文件**: `TheWorldOfAI.py` (lines 1522-1571)

```python
def main():
    tracker = None
    try:
        # 解析命令行参数
        auto_mode = '--auto' in sys.argv
        
        # 初始化追踪器
        tracker = AIWorldTracker(auto_mode=auto_mode)
        
        # ... 应用逻辑
        
    except KeyboardInterrupt:
        log.warning(t('user_interrupted'))
        
    finally:
        # 清理资源
        if tracker is not None:
            tracker.cleanup()  # ✅ 确保清理被调用
        
        log.dual_section(t('exit_message'))
```

**优点**:
- ✅ 使用 try-finally 确保清理
- ✅ 处理 KeyboardInterrupt
- ✅ 空指针检查

**缺点**:
- ⚠️ 只处理了 KeyboardInterrupt，其他信号 (SIGTERM, SIGINT) 未处理
- ⚠️ cleanup() 方法功能不完整

### 清理方法 (Cleanup Method)
**文件**: `TheWorldOfAI.py` (lines 178-191)

```python
def cleanup(self):
    """清理资源，释放内存/显存"""
    # 1. 卸载LLM模型（如果已加载）
    if self.llm_classifier is not None:
        try:
            self.llm_classifier.unload_model()
        except Exception as e:
            log.warning(t('cleanup_error', error=str(e)))
    
    # 2. 保存采集历史缓存
    try:
        self.collector._save_history_cache()
    except Exception:
        pass
```

**当前覆盖**:
- ✅ LLM 模型卸载
- ✅ 采集历史缓存保存

**缺失清理**:
- ❌ LLM 分类缓存 (`llm_classifier._save_cache()`)
- ❌ Importance Evaluator 学习数据 (`importance_evaluator._save_learning_data()`)
- ❌ 其他模块的清理方法 (visualizer, web_publisher, etc.)

---

## ⚠️ 已识别问题 (Identified Issues)

### 🔴 高优先级

#### 问题 1: LLM 分类缓存未保存
**影响**: 未保存的分类结果会丢失，下次启动需要重新分类

**当前行为**:
```python
# llm_classifier.py 中存在 _save_cache() 方法
# 但 cleanup() 未调用
```

**建议修复**:
```python
def cleanup(self):
    # ... 现有代码
    
    # 新增: 保存 LLM 分类缓存
    if self.llm_classifier is not None:
        try:
            self.llm_classifier._save_cache()
            log.info("💾 LLM classification cache saved")
        except Exception as e:
            log.warning(f"Failed to save LLM cache: {e}")
```

#### 问题 2: ImportanceEvaluator 学习数据可能丢失
**影响**: 如果更新次数不是 10 的倍数，最后几次更新会丢失

**当前行为**:
```python
# importance_evaluator.py
# 每 10 次更新自动保存 (line 648)
if self.user_feedback_count % 10 == 0:
    self._save_learning_data()

# cleanup() 未调用
```

**建议修复**:
```python
def cleanup(self):
    # ... 现有代码
    
    # 新增: 保存 ImportanceEvaluator 学习数据
    if self.llm_classifier is not None and hasattr(self.llm_classifier, 'evaluator'):
        try:
            self.llm_classifier.evaluator._save_learning_data()
            log.info("💾 Importance learning data saved")
        except Exception as e:
            log.warning(f"Failed to save learning data: {e}")
```

### 🟡 中优先级

#### 问题 3: HTTP 客户端连接未复用
**影响**: 性能损失，频繁创建/销毁 TCP 连接

**当前行为**:
```python
# llm_classifier.py - 每次请求创建新连接
response = requests.post(url, json=data, timeout=timeout)
```

**建议修复**:
```python
class LLMClassifier:
    def __init__(self, ...):
        # 创建会话以复用连接
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def _call_ollama(self, ...):
        # 使用会话
        response = self.session.post(url, json=data, timeout=timeout)
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'session'):
            self.session.close()
```

#### 问题 4: 信号处理不完整
**影响**: Docker 容器、systemd 服务等可能无法正常退出

**当前行为**: 只处理 KeyboardInterrupt (Ctrl+C)

**建议修复**:
```python
import signal

def signal_handler(signum, frame):
    """处理系统信号"""
    log.warning(f"Received signal {signum}, cleaning up...")
    if tracker is not None:
        tracker.cleanup()
    sys.exit(0)

def main():
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill
    
    # ... 应用逻辑
```

### 🟢 低优先级

#### 问题 5: 缺少统一的资源管理器
**影响**: 清理逻辑分散，难以维护

**建议**: 实现上下文管理器协议
```python
class AIWorldTracker:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False  # 不抑制异常

# 使用示例
with AIWorldTracker(auto_mode=False) as tracker:
    tracker.run()
# 自动调用 cleanup()
```

---

## 🎯 优化建议 (Optimization Recommendations)

### 建议 1: 完善 cleanup() 方法

**优先级**: 🔴 **高**

**实现代码**:
```python
def cleanup(self):
    """清理资源，释放内存/显存"""
    log.dual_info("🧹 Starting resource cleanup...")
    
    # 1. 卸载 LLM 模型
    if self.llm_classifier is not None:
        try:
            log.dual_info("  ↳ Unloading LLM model...")
            self.llm_classifier.unload_model()
        except Exception as e:
            log.warning(f"Failed to unload model: {e}")
    
    # 2. 保存 LLM 分类缓存 (新增)
    if self.llm_classifier is not None:
        try:
            log.dual_info("  ↳ Saving LLM classification cache...")
            self.llm_classifier._save_cache()
        except Exception as e:
            log.warning(f"Failed to save LLM cache: {e}")
    
    # 3. 保存 ImportanceEvaluator 学习数据 (新增)
    if self.llm_classifier is not None and hasattr(self.llm_classifier, 'evaluator'):
        try:
            log.dual_info("  ↳ Saving importance learning data...")
            self.llm_classifier.evaluator._save_learning_data()
        except Exception as e:
            log.warning(f"Failed to save learning data: {e}")
    
    # 4. 保存采集历史缓存
    try:
        log.dual_info("  ↳ Saving collection history cache...")
        self.collector._save_history_cache()
    except Exception as e:
        log.warning(f"Failed to save history cache: {e}")
    
    # 5. 清理 HTTP 会话 (如果使用)
    if hasattr(self, 'llm_classifier') and self.llm_classifier is not None:
        if hasattr(self.llm_classifier, 'session'):
            try:
                log.dual_info("  ↳ Closing HTTP sessions...")
                self.llm_classifier.session.close()
            except Exception as e:
                log.warning(f"Failed to close session: {e}")
    
    log.dual_success("✅ Resource cleanup completed")
```

### 建议 2: 为 LLMClassifier 添加 cleanup() 方法

**优先级**: 🟡 **中**

**实现代码**:
```python
# llm_classifier.py
class LLMClassifier:
    def cleanup(self):
        """清理 LLM 分类器资源"""
        # 1. 保存缓存
        try:
            self._save_cache()
            log.info("💾 LLM cache saved")
        except Exception as e:
            log.warning(f"Failed to save cache: {e}")
        
        # 2. 保存学习数据
        try:
            self.evaluator._save_learning_data()
            log.info("💾 Learning data saved")
        except Exception as e:
            log.warning(f"Failed to save learning data: {e}")
        
        # 3. 关闭 HTTP 会话
        if hasattr(self, 'session'):
            try:
                self.session.close()
                log.info("🔌 HTTP session closed")
            except Exception as e:
                log.warning(f"Failed to close session: {e}")
```

### 建议 3: 实现 HTTP 会话复用

**优先级**: 🟡 **中**

**实现代码**:
```python
# llm_classifier.py
class LLMClassifier:
    def __init__(self, ...):
        # ... 现有初始化代码
        
        # 创建复用会话
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # 配置连接池
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def _call_ollama(self, messages: List[Dict], stream: bool = False) -> Tuple[Optional[Dict], Optional[FallbackReason]]:
        # 使用会话而非直接 requests.post
        try:
            response = self.session.post(
                'http://localhost:11434/api/chat',
                json={'model': self.model, 'messages': messages, 'stream': stream},
                timeout=self.timeout
            )
            # ... 处理响应
        except requests.exceptions.RequestException as e:
            # ... 错误处理
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'session'):
            self.session.close()
```

### 建议 4: 添加信号处理

**优先级**: 🟡 **中**

**实现代码**:
```python
# TheWorldOfAI.py
import signal
import sys

# 全局追踪器引用
_tracker_instance = None

def signal_handler(signum, frame):
    """优雅处理系统信号"""
    signal_names = {
        signal.SIGINT: 'SIGINT (Ctrl+C)',
        signal.SIGTERM: 'SIGTERM (kill)'
    }
    signal_name = signal_names.get(signum, f'Signal {signum}')
    
    log.warning(f"⚠️ Received {signal_name}, initiating graceful shutdown...")
    
    if _tracker_instance is not None:
        _tracker_instance.cleanup()
    
    log.dual_section("👋 Goodbye!")
    sys.exit(0)

def main():
    global _tracker_instance
    
    # 注册信号处理器 (Windows 只支持 SIGINT)
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):  # Unix/Linux
        signal.signal(signal.SIGTERM, signal_handler)
    
    tracker = None
    try:
        # ... 现有代码
        tracker = AIWorldTracker(auto_mode=auto_mode)
        _tracker_instance = tracker
        
        # ... 应用逻辑
        
    except KeyboardInterrupt:
        log.warning(t('user_interrupted'))
        
    finally:
        if tracker is not None:
            tracker.cleanup()
        
        _tracker_instance = None
        log.dual_section(t('exit_message'))
```

### 建议 5: 实现上下文管理器

**优先级**: 🟢 **低** (代码优雅性提升)

**实现代码**:
```python
# TheWorldOfAI.py
class AIWorldTracker:
    def __enter__(self):
        """进入上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器，确保清理"""
        self.cleanup()
        
        # 不抑制异常
        return False

# 使用示例 1: 自动模式
def main_with_context():
    with AIWorldTracker(auto_mode=False) as tracker:
        tracker.run()
    # 自动调用 cleanup()

# 使用示例 2: 手动模式
def main():
    try:
        with AIWorldTracker(auto_mode=False) as tracker:
            while True:
                # ... 交互逻辑
                pass
    except KeyboardInterrupt:
        log.warning("User interrupted")
    # cleanup() 已在 __exit__ 中调用
```

---

## 📊 风险评估矩阵 (Risk Assessment Matrix)

| 资源类型 | 当前状态 | 泄露风险 | 数据丢失风险 | 优先级 |
|---------|---------|---------|------------|--------|
| LLM 分类缓存 | ❌ 未保存 | 🟢 低 | 🔴 高 | 🔴 高 |
| ImportanceEvaluator 学习数据 | ⚠️ 定期保存 | 🟢 低 | 🟡 中 | 🟡 中 |
| 采集历史缓存 | ✅ 已保存 | 🟢 低 | 🟢 低 | 🟢 低 |
| HTTP 连接 | ⚠️ 未复用 | 🟡 中 | 🟢 低 | 🟡 中 |
| LLM 模型内存 | ✅ 已卸载 | 🟢 低 | 🟢 低 | 🟢 低 |
| 异步事件循环 | ✅ 已关闭 | 🟢 低 | 🟢 低 | 🟢 低 |
| 文件句柄 | ✅ with 语句 | 🟢 低 | 🟢 低 | 🟢 低 |
| Matplotlib 图表 | ✅ plt.close() | 🟢 低 | 🟢 低 | 🟢 低 |
| 线程池 | ✅ with 语句 | 🟢 低 | 🟢 低 | 🟢 低 |

---

## 🚀 实施路线图 (Implementation Roadmap)

### 阶段 1: 紧急修复 (1-2 小时)
1. ✅ **完善 cleanup() 方法**
   - 添加 LLM 缓存保存
   - 添加学习数据保存
   - 添加详细日志

2. ✅ **为 LLMClassifier 添加 cleanup()**
   - 集中清理逻辑
   - 便于维护

### 阶段 2: 性能优化 (2-3 小时)
3. ✅ **实现 HTTP 会话复用**
   - 创建 requests.Session
   - 配置连接池
   - 在 cleanup() 中关闭

4. ✅ **添加信号处理**
   - SIGINT (Ctrl+C)
   - SIGTERM (kill)

### 阶段 3: 代码优雅性 (1-2 小时)
5. ✅ **实现上下文管理器**
   - `__enter__` 和 `__exit__`
   - 简化主函数逻辑

6. ✅ **添加资源清理测试**
   - 单元测试验证清理逻辑
   - 集成测试模拟异常退出

---

## 📝 最佳实践建议 (Best Practices)

### 1. 统一清理模式
**原则**: 所有模块应实现 `cleanup()` 方法

```python
class BaseModule:
    def cleanup(self):
        """清理资源 - 子类应重写此方法"""
        raise NotImplementedError

class DataCollector(BaseModule):
    def cleanup(self):
        self._save_history_cache()

class LLMClassifier(BaseModule):
    def cleanup(self):
        self._save_cache()
        self.evaluator._save_learning_data()
        if hasattr(self, 'session'):
            self.session.close()
```

### 2. 资源获取即初始化 (RAII)
**原则**: 使用上下文管理器自动清理

```python
# ✅ 推荐
with requests.Session() as session:
    response = session.get(url)

# ❌ 不推荐
session = requests.Session()
response = session.get(url)
session.close()  # 可能被遗忘或异常跳过
```

### 3. 防御性编程
**原则**: 清理逻辑应容错

```python
def cleanup(self):
    # ✅ 每个清理步骤都有独立的 try-except
    try:
        self._save_cache()
    except Exception as e:
        log.warning(f"Cache save failed: {e}")
    
    try:
        self._close_connections()
    except Exception as e:
        log.warning(f"Connection close failed: {e}")
```

### 4. 清理日志
**原则**: 记录清理过程以便调试

```python
def cleanup(self):
    log.dual_info("🧹 Starting cleanup...")
    
    log.dual_info("  ↳ Saving cache...")
    self._save_cache()
    
    log.dual_info("  ↳ Closing connections...")
    self._close_connections()
    
    log.dual_success("✅ Cleanup completed")
```

---

## 🧪 测试建议 (Testing Recommendations)

### 单元测试: 清理逻辑验证
```python
# tests/test_cleanup.py
import unittest
from unittest.mock import Mock, patch
from TheWorldOfAI import AIWorldTracker

class TestCleanup(unittest.TestCase):
    def test_cleanup_saves_llm_cache(self):
        """测试清理时保存 LLM 缓存"""
        tracker = AIWorldTracker(auto_mode=True)
        tracker.llm_classifier = Mock()
        
        tracker.cleanup()
        
        tracker.llm_classifier._save_cache.assert_called_once()
    
    def test_cleanup_handles_exceptions(self):
        """测试清理时的异常处理"""
        tracker = AIWorldTracker(auto_mode=True)
        tracker.llm_classifier = Mock()
        tracker.llm_classifier._save_cache.side_effect = Exception("Test error")
        
        # 不应抛出异常
        tracker.cleanup()
```

### 集成测试: 模拟异常退出
```python
# tests/test_graceful_shutdown.py
import signal
import subprocess
import time

def test_sigterm_handling():
    """测试 SIGTERM 信号处理"""
    # 启动应用
    proc = subprocess.Popen(['python', 'TheWorldOfAI.py', '--auto'])
    time.sleep(2)
    
    # 发送 SIGTERM
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=10)
    
    # 验证缓存文件已保存
    assert os.path.exists('data/cache/llm_classification_cache.json')
    assert os.path.exists('data/cache/importance_learning.json')
```

---

## 📚 参考资源 (References)

### Python 资源管理
- [Context Managers (PEP 343)](https://peps.python.org/pep-0343/)
- [requests.Session 文档](https://requests.readthedocs.io/en/latest/user/advanced/#session-objects)
- [signal 模块文档](https://docs.python.org/3/library/signal.html)

### 最佳实践
- [Python Best Practices: Resource Management](https://realpython.com/python-with-statement/)
- [Graceful Shutdown in Python](https://medium.com/@ageitgey/graceful-shutdown-in-python-60e4a9b3c4e3)

---

## 📅 文档版本 (Document Version)

- **版本**: 1.0
- **创建日期**: 2024-12-10
- **最后更新**: 2024-12-10
- **作者**: GitHub Copilot
- **审核状态**: 待审核

---

## 📧 反馈与问题 (Feedback)

如有任何问题或建议，请通过以下方式反馈：
- 代码审查: 创建 Pull Request
- 问题报告: 创建 GitHub Issue
- 优化建议: 联系开发团队
