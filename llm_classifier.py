"""
LLM增强分类器 - LLM Classifier
使用大语言模型进行智能内容分类

支持的提供商:
- Ollama (本地): Qwen3:8b, Llama3.2:3b, Mistral:7b
- Azure OpenAI: GPT-4o-mini, GPT-4o

功能特性:
- 多提供商支持，灵活切换
- MD5内容缓存，避免重复调用
- 自动降级到规则分类
- 并发处理加速
- 详细的分类推理
- GPU自动检测与自适应配置
"""

import os
import json
import hashlib
import time
import subprocess
import platform
import threading
import re
import requests
import yaml
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum

# 导入规则分类器作为备份
from content_classifier import ContentClassifier
from importance_evaluator import ImportanceEvaluator
from logger import get_log_helper

# 导入国际化模块
try:
    from i18n import t, get_language
except ImportError:
    def t(key, **kwargs): return key
    def get_language(): return 'zh'

# 模块日志器
log = get_log_helper('llm_classifier')

# ============== 降级策略配置 ==============

class FallbackReason(Enum):
    """降级原因枚举"""
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    PARSE_ERROR = "parse_error"
    INVALID_RESPONSE = "invalid_response"
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    MODEL_ERROR = "model_error"


class FallbackStrategy:
    """智能降级策略管理器"""
    
    def __init__(self):
        self.error_counts = {}  # 错误计数
        self.last_error_time = {}  # 最后错误时间
        self.circuit_breaker_open = False  # 断路器状态
        self.circuit_breaker_open_time = None
        self.circuit_breaker_threshold = 5  # 连续失败阈值
        self.circuit_breaker_timeout = 60  # 断路器打开时间（秒）
    
    def should_use_llm(self) -> bool:
        """判断是否应该使用 LLM（断路器检查）"""
        if not self.circuit_breaker_open:
            return True
        
        # 检查断路器是否应该关闭
        if self.circuit_breaker_open_time:
            elapsed = time.time() - self.circuit_breaker_open_time
            if elapsed > self.circuit_breaker_timeout:
                log.dual_info("🔄 Circuit breaker closed, retrying LLM")
                self.circuit_breaker_open = False
                self.circuit_breaker_open_time = None
                self.error_counts.clear()
                return True
        
        return False
    
    def record_error(self, reason: FallbackReason):
        """记录错误并更新断路器状态"""
        reason_key = reason.value
        self.error_counts[reason_key] = self.error_counts.get(reason_key, 0) + 1
        self.last_error_time[reason_key] = time.time()
        
        # 检查是否应该打开断路器
        total_errors = sum(self.error_counts.values())
        if total_errors >= self.circuit_breaker_threshold and not self.circuit_breaker_open:
            self.circuit_breaker_open = True
            self.circuit_breaker_open_time = time.time()
            log.dual_warning(f"⚠️ Circuit breaker opened after {total_errors} errors")
    
    def record_success(self):
        """记录成功，重置错误计数"""
        if self.error_counts:
            self.error_counts.clear()
            self.last_error_time.clear()
    
    def get_fallback_action(self, reason: FallbackReason, item: Dict) -> str:
        """根据错误类型决定降级策略
        
        Returns:
            'retry': 重试 LLM
            'quick': 快速降级（简化规则）
            'full_rule': 完整规则分类
        """
        # 超时错误：使用快速降级
        if reason == FallbackReason.TIMEOUT:
            return 'quick'
        
        # 连接错误：断路器打开，使用完整规则
        if reason in [FallbackReason.CONNECTION_ERROR, FallbackReason.API_ERROR]:
            self.record_error(reason)
            return 'full_rule' if self.circuit_breaker_open else 'retry'
        
        # 解析错误：重试一次，失败则降级
        if reason in [FallbackReason.PARSE_ERROR, FallbackReason.INVALID_RESPONSE]:
            error_count = self.error_counts.get(reason.value, 0)
            if error_count < 2:
                return 'retry'
            return 'full_rule'
        
        # 速率限制：等待后重试
        if reason == FallbackReason.RATE_LIMIT:
            time.sleep(2)
            return 'retry'
        
        # 默认：完整规则分类
        return 'full_rule'


# 加载缓存目录配置
def _get_cache_dir():
    """获取缓存目录路径"""
    cache_dir = 'data/cache'
    try:
        if os.path.exists('config.yaml'):
            with open('config.yaml', 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
                cache_dir = cfg.get('data', {}).get('cache_dir', cache_dir)
    except (OSError, yaml.YAMLError, KeyError) as e:
        # 配置加载失败，使用默认值
        pass
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

DATA_CACHE_DIR = _get_cache_dir()

# 模型保活时间（秒）
MODEL_KEEP_ALIVE_SECONDS = 5 * 60  # 5分钟

# Ollama 超时配置
OLLAMA_WARMUP_TIMEOUT = 180  # 预热超时（模型首次加载可能很慢）
OLLAMA_SINGLE_REQUEST_TIMEOUT = 120  # 单条分类超时
OLLAMA_BATCH_REQUEST_TIMEOUT = 150  # 批量分类超时

# 统一的 LLM System Prompt（所有提供商使用相同的系统提示）
LLM_SYSTEM_PROMPT = "你是一个专业的AI内容分类助手，请严格按照JSON格式输出分类结果。"


class LLMProvider(Enum):
    """提供商枚举"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"


@dataclass
class GPUInfo:
    """GPU信息"""
    available: bool = False
    gpu_type: str = "none"  # nvidia, amd, apple, qualcomm, none
    gpu_name: str = ""
    vram_mb: int = 0
    driver_version: str = ""
    cuda_available: bool = False
    rocm_available: bool = False
    metal_available: bool = False
    ollama_gpu_supported: bool = False  # Ollama是否支持该GPU


def detect_gpu() -> GPUInfo:
    """
    检测系统GPU信息
    
    Returns:
        GPUInfo: GPU检测结果
    """
    info = GPUInfo()
    system = platform.system()
    
    # 1. 检测 NVIDIA GPU (CUDA)
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(', ')
            if len(parts) >= 3:
                info.available = True
                info.gpu_type = "nvidia"
                info.gpu_name = parts[0].strip()
                info.vram_mb = int(float(parts[1].strip()))
                info.driver_version = parts[2].strip()
                info.cuda_available = True
                info.ollama_gpu_supported = True
                return info
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    
    # 2. 检测 AMD GPU (ROCm) - 仅Linux
    if system == "Linux":
        try:
            result = subprocess.run(['rocm-smi', '--showproductname'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'GPU' in result.stdout:
                info.available = True
                info.gpu_type = "amd"
                info.gpu_name = "AMD ROCm GPU"
                info.rocm_available = True
                info.ollama_gpu_supported = True
                return info
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
    
    # 3. 检测 Apple Silicon (Metal)
    if system == "Darwin":
        try:
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                cpu_info = result.stdout.strip()
                if 'Apple' in cpu_info:
                    info.available = True
                    info.gpu_type = "apple"
                    info.gpu_name = cpu_info
                    info.metal_available = True
                    info.ollama_gpu_supported = True
                    return info
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
    
    # 4. 检测 Windows 显卡（可能是不支持的GPU）
    if system == "Windows":
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 'Get-WmiObject Win32_VideoController | Select-Object -First 1 Name, AdapterRAM, DriverVersion | ConvertTo-Json'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                gpu_data = json.loads(result.stdout)
                gpu_name = gpu_data.get('Name', '')
                
                info.gpu_name = gpu_name
                info.driver_version = gpu_data.get('DriverVersion', '')
                adapter_ram = gpu_data.get('AdapterRAM', 0)
                if adapter_ram:
                    info.vram_mb = int(adapter_ram / (1024 * 1024))
                
                # 判断GPU类型
                if 'NVIDIA' in gpu_name.upper():
                    info.available = True
                    info.gpu_type = "nvidia"
                    info.cuda_available = True
                    info.ollama_gpu_supported = True
                elif 'AMD' in gpu_name.upper() or 'RADEON' in gpu_name.upper():
                    info.available = True
                    info.gpu_type = "amd"
                    info.ollama_gpu_supported = False  # Windows上AMD不支持
                elif 'QUALCOMM' in gpu_name.upper() or 'ADRENO' in gpu_name.upper():
                    info.available = True
                    info.gpu_type = "qualcomm"
                    info.ollama_gpu_supported = False  # Qualcomm不支持
                elif 'INTEL' in gpu_name.upper():
                    info.available = True
                    info.gpu_type = "intel"
                    info.ollama_gpu_supported = False  # Intel集显不支持
                
                return info
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            pass
    
    return info


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 60
    max_retries: int = 2


@dataclass
class OllamaOptions:
    """Ollama推理选项 - 根据GPU自适应配置"""
    temperature: float = 0.1
    num_predict: int = 200  # 单条分类输出长度
    num_predict_batch: int = 500  # 批量分类输出长度（每条约80 tokens）
    num_ctx: int = 2048
    num_thread: int = 4
    num_gpu: int = 0  # 0表示自动，-1表示禁用GPU
    
    @classmethod
    def auto_configure(cls, gpu_info: GPUInfo) -> 'OllamaOptions':
        """根据GPU信息自动配置推理选项"""
        options = cls()
        
        if gpu_info and gpu_info.ollama_gpu_supported:
            # GPU加速配置 - 优化速度
            options.num_gpu = 999  # 使用所有GPU层
            options.num_ctx = 4096  # GPU可以处理更大上下文（支持批量）
            options.num_predict = 200  # 单条分类
            options.num_predict_batch = 600  # 批量分类（5条*80tokens+余量）
            options.num_thread = 4  # GPU模式下CPU线程不需要太多
        else:
            # CPU模式优化配置
            options.num_gpu = 0  # 禁用GPU
            options.num_ctx = 2048  # 增加上下文以支持批量
            options.num_predict = 150  # 单条分类
            options.num_predict_batch = 500  # 批量分类
            # 根据CPU核心数设置线程
            try:
                import multiprocessing
                cpu_count = multiprocessing.cpu_count()
                options.num_thread = min(cpu_count, 8)  # 最多8线程
            except (NotImplementedError, OSError):
                options.num_thread = 4
        
        return options


# 预定义的模型配置
AVAILABLE_MODELS = {
    LLMProvider.OLLAMA: {
        'qwen3:8b': {'name': 'Qwen3 8B', 'description': '阿里通义千问，中文能力强，推荐使用'},
        'llama3.2:3b': {'name': 'Llama 3.2 3B', 'description': 'Meta轻量模型，速度最快'},
        'mistral:7b': {'name': 'Mistral 7B', 'description': '性能均衡，英文能力强'},
    },
    LLMProvider.OPENAI: {
        'gpt-4o-mini': {'name': 'GPT-4o Mini', 'description': '性价比高，推荐使用'},
        'gpt-4o': {'name': 'GPT-4o', 'description': '最强性能，成本较高'},
        'gpt-3.5-turbo': {'name': 'GPT-3.5 Turbo', 'description': '经济实惠'},
    },
    LLMProvider.AZURE_OPENAI: {
        'gpt-4o-mini': {'name': 'GPT-4o Mini (Azure)', 'description': 'Azure部署，企业级安全'},
        'gpt-4o': {'name': 'GPT-4o (Azure)', 'description': 'Azure部署，最强性能'},
        'gpt-4': {'name': 'GPT-4 (Azure)', 'description': 'Azure部署，稳定可靠'},
        'gpt-35-turbo': {'name': 'GPT-3.5 Turbo (Azure)', 'description': 'Azure部署，经济实惠'},
    }
}


class LLMClassifier:
    """LLM增强分类器"""
    
    def __init__(self, 
                 provider: str = 'ollama',
                 model: str = 'qwen3:8b',
                 api_key: Optional[str] = None,
                 enable_cache: bool = True,
                 max_workers: int = 3,  # 默认并发数
                 auto_detect_gpu: bool = True,
                 batch_size: int = 5,  # 新增批量分类大小
                 azure_endpoint: Optional[str] = None,  # Azure OpenAI 端点
                 azure_api_version: Optional[str] = None):  # Azure API 版本
        """
        初始化LLM分类器
        
        Args:
            provider: 提供商 ('ollama', 'openai', 'azure_openai', 'anthropic')
            model: 模型名称 (对于 Azure OpenAI，这是部署名称)
            api_key: API密钥（Ollama不需要）
            enable_cache: 是否启用缓存
            max_workers: 并发工作线程数 (默认5，GPU模式可更高)
            auto_detect_gpu: 是否自动检测GPU并优化配置
            batch_size: 批量分类时每批的数量 (用于减少LLM调用次数)
            azure_endpoint: Azure OpenAI 端点 URL (如 https://xxx.openai.azure.com/)
            azure_api_version: Azure OpenAI API 版本 (如 2024-02-15-preview)
        """
        self.provider = LLMProvider(provider)
        self.model = model
        self.api_key = api_key or self._get_api_key()
        self.enable_cache = enable_cache
        self.max_workers = max_workers
        self.batch_size = batch_size
        
        # Azure OpenAI 特有配置
        self.azure_endpoint = azure_endpoint or os.getenv('AZURE_OPENAI_ENDPOINT')
        self.azure_api_version = azure_api_version or os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        
        # GPU检测与自适应配置
        self.gpu_info: Optional[GPUInfo] = None
        self.ollama_options: Optional[OllamaOptions] = None
        if auto_detect_gpu and self.provider == LLMProvider.OLLAMA:
            self._setup_gpu_acceleration()
            # GPU模式下可以提高并发数
            if self.gpu_info and self.gpu_info.ollama_gpu_supported:
                self.max_workers = max(max_workers, 6)  # GPU模式提高并发至6
        
        # 缓存
        self.cache: Dict[str, Dict] = {}
        self.cache_file = os.path.join(DATA_CACHE_DIR, 'llm_classification_cache.json')
        self._load_cache()
        
        # 规则分类器（作为备份）
        self.rule_classifier = ContentClassifier()
        
        # 独立的重要性评估器 (解耦后的设计)
        self.importance_evaluator = ImportanceEvaluator()
        
        # 降级策略管理器
        self.fallback_strategy = FallbackStrategy()
        
        # 模型预热状态
        self.is_warmed_up = False
        self._keep_alive_timer: Optional[threading.Timer] = None
        
        # 统计
        self.stats = {
            'total_calls': 0,
            'cache_hits': 0,
            'llm_calls': 0,
            'fallback_calls': 0,
            'errors': 0,
            'fallback_details': []  # 记录每条降级的详细信息
        }
        
        # HTTP 会话复用（新增）
        self.session = self._create_http_session()
        
        # 验证配置
        self._validate_config()
        
        self._print_init_info()
    
    def _create_http_session(self) -> requests.Session:
        """创建配置好的 HTTP 会话（连接池复用）"""
        session = requests.Session()
        
        # 配置请求头
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AI-World-Tracker/1.0'
        })
        
        # 配置连接池和重试策略
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,  # 最多重试3次
            backoff_factor=0.5,  # 重试间隔: 0.5s, 1s, 2s
            status_forcelist=[429, 500, 502, 503, 504],  # 这些状态码触发重试
            allowed_methods=["POST", "GET"]  # 允许重试的方法
        )
        
        adapter = HTTPAdapter(
            pool_connections=10,  # 连接池大小
            pool_maxsize=20,  # 最大连接数
            max_retries=retry_strategy
        )
        
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def _setup_gpu_acceleration(self):
        """设置GPU加速"""
        self.gpu_info = detect_gpu()
        self.ollama_options = OllamaOptions.auto_configure(self.gpu_info)
    
    def _print_init_info(self):
        """打印初始化信息"""
        log.dual_ai(t('llm_init_done'))
        log.dual_ai(t('llm_provider', provider=self.provider.value))
        log.dual_ai(t('llm_model_name', model=self.model))
        cache_status = t('llm_cache_enabled') if self.enable_cache else t('llm_cache_disabled')
        log.dual_config(t('llm_cache_status', status=cache_status))
        
        if self.gpu_info:
            if self.gpu_info.ollama_gpu_supported:
                log.dual_success(t('llm_gpu_enabled', gpu_name=self.gpu_info.gpu_name))
                if self.gpu_info.vram_mb:
                    log.dual_info("💾 " + t('llm_vram', vram=self.gpu_info.vram_mb))
            else:
                gpu_name = self.gpu_info.gpu_name or t('llm_no_gpu_detected')
                log.dual_warning(t('llm_cpu_mode', gpu_name=gpu_name))
                if self.ollama_options:
                    log.dual_info("⚙️ " + t('llm_cpu_threads', threads=self.ollama_options.num_thread))
    
    def get_gpu_info(self) -> Optional[GPUInfo]:
        """获取GPU信息"""
        return self.gpu_info
    
    def warmup_model(self) -> bool:
        """
        预热模型：发送一个简单请求让模型加载到内存/显存
        
        Returns:
            bool: 预热是否成功
        """
        if self.provider != LLMProvider.OLLAMA:
            # 云端API不需要预热
            self.is_warmed_up = True
            return True
        
        if self.is_warmed_up:
            log.dual_info("✅ " + t('llm_model_warmed'))
            return True
        
        log.dual_ai(t('llm_warming_model', model=self.model))
        start_time = time.time()
        
        try:
            # 发送一个简单的请求来加载模型
            # 使用 keep_alive 参数让模型保持活跃
            log.dual_info(f"⏳ 正在加载模型到{'GPU' if self.gpu_info and self.gpu_info.ollama_gpu_supported else 'CPU'}内存，首次加载可能需要1-3分钟...")
            response = self.session.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': self.model,
                    'prompt': 'Hi',  # 最简单的prompt
                    'stream': False,
                    'keep_alive': f'{MODEL_KEEP_ALIVE_SECONDS}s',  # 保活时间
                    'options': {
                        'num_predict': 1,  # 只生成1个token
                        'num_ctx': 512
                    }
                },
                timeout=OLLAMA_WARMUP_TIMEOUT  # 首次加载可能较慢
            )
            
            if response.status_code == 200:
                elapsed = time.time() - start_time
                self.is_warmed_up = True
                log.dual_success(t('llm_warmup_done', time=f'{elapsed:.1f}'))
                log.dual_info("⏰ " + t('llm_keep_alive', minutes=MODEL_KEEP_ALIVE_SECONDS // 60))
                return True
            else:
                log.dual_error(t('llm_warmup_failed_http', code=response.status_code))
                return False
                
        except Exception as e:
            log.dual_error(t('llm_warmup_failed', error=str(e)))
            return False
    
    def set_keep_alive(self, seconds: int = MODEL_KEEP_ALIVE_SECONDS):
        """
        设置模型保活时间
        
        Args:
            seconds: 保活秒数
        """
        if self.provider != LLMProvider.OLLAMA:
            return
        
        try:
            # 发送保活请求
            response = self.session.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': self.model,
                    'prompt': '',  # 空prompt
                    'stream': False,
                    'keep_alive': f'{seconds}s',
                    'options': {'num_predict': 0}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                log.dual_success(t('llm_keepalive_set', minutes=seconds // 60))
                
        except Exception as e:
            log.warning(t('llm_keepalive_failed', error=str(e)))
    
    def unload_model(self):
        """立即卸载模型（释放显存/内存）"""
        if self.provider != LLMProvider.OLLAMA:
            return
        
        try:
            response = self.session.post(
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
                log.dual_success(t('llm_model_unloaded', model=self.model))
                
        except Exception as e:
            log.warning(t('llm_unload_failed', error=str(e)))
    
    def cleanup(self):
        """清理资源（保存缓存、关闭 HTTP 会话）"""
        # 1. 保存缓存
        try:
            self._save_cache()
            log.info("💾 LLM cache saved")
        except Exception as e:
            log.warning(f"Failed to save cache: {e}")
        
        # 2. 保存学习数据
        try:
            if hasattr(self, 'evaluator'):
                self.evaluator._save_learning_data()
                log.info("💾 Learning data saved")
        except Exception as e:
            log.warning(f"Failed to save learning data: {e}")
        
        # 3. 关闭 HTTP 会话
        try:
            if hasattr(self, 'session'):
                self.session.close()
                log.info("🔌 HTTP session closed")
        except Exception as e:
            log.warning(f"Failed to close session: {e}")

    def _get_api_key(self) -> Optional[str]:
        """从环境变量获取API密钥"""
        if self.provider == LLMProvider.OPENAI:
            return os.getenv('OPENAI_API_KEY')
        elif self.provider == LLMProvider.AZURE_OPENAI:
            return os.getenv('AZURE_OPENAI_API_KEY')
        return None
    
    def _validate_config(self):
        """验证配置"""
        if self.provider == LLMProvider.OLLAMA:
            # 检查Ollama服务是否运行
            if not self._check_ollama_service():
                log.error(t('llm_ollama_not_running'))
        elif self.provider == LLMProvider.AZURE_OPENAI:
            if not self.api_key:
                log.error(t('llm_api_key_missing', provider='AZURE_OPENAI'))
            if not self.azure_endpoint:
                log.error(t('llm_azure_endpoint_missing'))
        elif self.provider == LLMProvider.OPENAI:
            if not self.api_key:
                log.error(t('llm_api_key_missing', provider=self.provider.value.upper()))
    
    def _check_ollama_service(self) -> bool:
        """检查Ollama服务是否运行"""
        try:
            response = self.session.get('http://localhost:11434/api/tags', timeout=5)
            return response.status_code == 200
        except (requests.RequestException, ConnectionError, TimeoutError):
            return False
    
    def _load_cache(self):
        """加载缓存"""
        if not self.enable_cache:
            return
        
        # 直接删除旧缓存文件，确保从零开始
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    loaded_cache = json.load(f)
                
                # 检查缓存格式是否正确（必须包含 classified_by 字段）
                if loaded_cache:
                    first_entry = next(iter(loaded_cache.values()), None)
                    if first_entry and 'classified_by' not in first_entry:
                        # 旧格式缓存，删除文件
                        os.remove(self.cache_file)
                        log.warning(t('llm_cache_outdated'))
                        self.cache = {}
                        return
                
                self.cache = loaded_cache
                log.dual_data(t('llm_cache_loaded', count=len(self.cache)))
            except Exception as e:
                print(f"⚠️ Cache load failed: {e}")
                # 删除损坏的缓存文件
                try:
                    os.remove(self.cache_file)
                except (OSError, PermissionError):
                    pass
                self.cache = {}
    
    def _save_cache(self):
        """保存缓存"""
        if not self.enable_cache:
            return
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(t('llm_cache_save_failed', error=str(e)))
    
    def clear_cache(self):
        """清除缓存（文件和内存）"""
        # 清除内存缓存
        self.cache.clear()
        self.stats['cache_hits'] = 0
        
        # 删除缓存文件
        if os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
                log.dual_success("✅ LLM分类缓存已清除（文件+内存）")
            except Exception as e:
                log.error(f"❌ 删除缓存文件失败: {e}")
    
    def _get_content_hash(self, item: Dict) -> str:
        """计算内容的MD5哈希（不含模型信息）"""
        content = f"{item.get('title', '')}|{item.get('summary', '')}|{item.get('source', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_current_model_identifier(self) -> str:
        """获取当前模型的标识符"""
        return f"{self.provider.value}/{self.model}"
    
    def _get_cache_key(self, item: Dict) -> str:
        """
        获取缓存key（复合key：内容哈希 + 模型标识）
        
        多模型缓存共存设计：
        - 同一内容被不同模型分类后，会有多条缓存记录
        - 切换模型时，如果该模型之前分类过同样的内容，可以直接从缓存读取
        - 不会覆盖其他模型的分类结果
        
        Args:
            item: 内容项
            
        Returns:
            格式: "{content_hash}:{model_identifier}"
        """
        content_hash = self._get_content_hash(item)
        model_id = self._get_current_model_identifier()
        return f"{content_hash}:{model_id}"
    
    def _build_classification_prompt(self, item: Dict) -> str:
        """构建分类提示词（与批量分类规则统一）"""
        title = item.get('title', '')[:100]
        summary = item.get('summary', item.get('description', ''))[:300]
        source = item.get('source', '')
        url = item.get('url', '')
        
        # 检测 URL 类型提示（与批量分类统一）
        url_hints = []
        if 'arxiv.org' in url or '/paper/' in url:
            url_hints.append("[PAPER]")
        if '/podcast/' in url or '/podcasts/' in url:
            url_hints.append("[PODCAST]")
        if '/blog/' in url:
            url_hints.append("[BLOG]")
        
        url_hint_text = f" {' '.join(url_hints)}" if url_hints else ""
        
        prompt = f"""Classify this AI news item. Output ONLY valid JSON.

Title: {title}{url_hint_text}
Summary: {summary}
Source: {source}

IMPORTANT: Use ONLY these exact values for content_type:
- research: Academic papers, scientific studies, technical reports from arxiv/conferences
- product: Product launches, new features, version releases, API announcements
- market: Funding news, investments, company analysis, industry competition (NO quote markers)
- developer: Tools, frameworks, models, open source projects, technical tutorials
- leader: Person's statement with quote markers ★★★ HIGHEST PRIORITY ★★★
- community: Forum discussions, social media trends, community events

★★★ LEADER CLASSIFICATION - HIGHEST PRIORITY ★★★
Quote marker words (ANY of these in title = leader):
  English: says, said, warns, predicts, believes, stated, told, claims, according to
  Chinese: 说, 表示, 称, 认为, 指出, 透露, 预测, 警告

Decision flow:
1. Title contains ANY quote marker word → "leader" (even if about company news)
2. Title format "Person Name: ..." or "人名：..." → "leader"
3. About famous person but NO quote marker → "market"

Examples:
- "Elon Musk says AI will change work" → leader ✓ (has "says")
- "Sam Altman predicts AGI timeline" → leader ✓ (has "predicts")
- "OpenAI CEO warns about AI risks" → leader ✓ (has "warns")
- "OpenAI launches new model" → product (no quote marker)
- "OpenAI faces competition from Google" → market (no quote marker)

Other rules:
- Items marked [PAPER] → research
- Items marked [PODCAST] → community

★★★ AI RELEVANCE SCORING (ai_relevance: 0.0-1.0) - BE STRICT ★★★
- 0.9-1.0: Core AI (LLM, deep learning, neural networks, model training, transformers)
- 0.7-0.9: Primary AI (ChatGPT, Claude, Midjourney, AI company core business)
- 0.5-0.7: Partial AI (tech news with explicit AI/ML mention as main topic)
- 0.2-0.5: Weak AI (smart devices without ML, automation without AI)
- 0.0-0.2: Non-AI (completely unrelated to AI)

★★★ NON-AI EXAMPLES (score 0.0-0.3) ★★★
- Car news: EVs, digital keys, smart cockpit (unless ML-based)
- Hardware: CPUs, GPUs, storage, displays, phones (unless AI chips)
- Software: Regular app updates, OS features (unless AI-powered)
- Gaming: Unless AI NPCs, AI content creation
- Finance: Unless AI company funding or AI trading
- Communication tech: NFC, Bluetooth, UWB, 5G = NOT AI

tech_fields options: LLM, Computer Vision, NLP, Robotics, AI Safety, MLOps, Multimodal, Audio/Speech, Healthcare AI, General AI

Output format (strict JSON, no extra text):
{{"content_type": "TYPE", "confidence": 0.8, "ai_relevance": 0.85, "tech_fields": ["FIELD"], "reasoning": "brief reason"}}"""
        
        return prompt
    
    def _build_batch_prompt(self, items: List[Dict]) -> str:
        """构建批量分类提示词（与单条分类规则统一）"""
        items_text = []
        for i, item in enumerate(items, 1):
            title = item.get('title', '')[:80]
            summary = item.get('summary', item.get('description', ''))[:120]
            source = item.get('source', '')[:20]
            url = item.get('url', '')
            
            # 检测 URL 类型提示（与单条分类统一）
            url_type = ""
            if 'arxiv.org' in url or '/paper/' in url:
                url_type = " [PAPER]"
            elif '/podcast/' in url or '/podcasts/' in url:
                url_type = " [PODCAST]"
            elif '/blog/' in url:
                url_type = " [BLOG]"
            
            items_text.append(f"[{i}] {title}{url_type}\n    Summary: {summary}\n    Source: {source}")
        
        all_items = "\n".join(items_text)
        
        prompt = f"""Classify these {len(items)} AI news items. Output ONLY valid JSON, one per line.

Items to classify:
{all_items}

IMPORTANT: Use ONLY these exact values for content_type:
- research: Academic papers, scientific studies, technical reports from arxiv/conferences
- product: Product launches, new features, version releases, API announcements  
- market: Funding news, investments, company analysis, industry competition (NO quote markers)
- developer: Tools, frameworks, models, open source projects, technical tutorials
- leader: Person's statement with quote markers ★★★ HIGHEST PRIORITY ★★★
- community: Forum discussions, social media trends, community events

★★★ LEADER CLASSIFICATION - HIGHEST PRIORITY ★★★
Quote marker words (ANY of these in title = leader):
  English: says, said, warns, predicts, believes, stated, told, claims, according to
  Chinese: 说, 表示, 称, 认为, 指出, 透露, 预测, 警告

Decision flow:
1. Title contains ANY quote marker word → "leader" (even if about company news)
2. Title format "Person Name: ..." or "人名：..." → "leader"
3. About famous person but NO quote marker → "market"

★ LEADER EXAMPLES (classify as leader) ★
- "Elon Musk says AI will make work optional" → leader ✓ (has "says")
- "Sam Altman predicts AGI in 5 years" → leader ✓ (has "predicts")
- "Jensen Huang believes AI approach human intelligence" → leader ✓ (has "believes")
- "OpenAI CEO warns about AI risks" → leader ✓ (has "warns")
- "Bill Gates: AI will transform education" → leader ✓ (has "Name:" format)

★ MARKET EXAMPLES (NO quote markers) ★
- "OpenAI declares code red as Google threatens" → market (no quote marker)
- "Sam Altman eyes rocket company" → market (no quote marker)
- "Elon Musk's Grok AI launches new feature" → product (no quote marker)

Other rules:
- Items marked [PAPER] → research
- Items marked [PODCAST] → community
- Items marked [BLOG] → market or developer (based on content)

★★★ AI RELEVANCE SCORING (ai_relevance: 0.0-1.0) - BE STRICT ★★★
- 0.9-1.0: Core AI (LLM, deep learning, neural networks, model training, transformers, diffusion models)
- 0.7-0.9: Primary AI (ChatGPT, Claude, Midjourney, AI company core business, ML applications)
- 0.5-0.7: Partial AI (tech news with explicit AI/ML mention as main topic)
- 0.2-0.5: Weak AI (smart devices without ML, automation without AI)
- 0.0-0.2: Non-AI (completely unrelated to AI)

★★★ NON-AI EXAMPLES (score 0.0-0.3) ★★★
- Car news: EVs, digital keys, smart cockpit, autonomous driving sensors (unless ML-based)
- Hardware: CPUs, GPUs (unless AI chips like TPU/NPU), storage, displays, phones
- Software: Regular app updates, OS features (unless AI-powered)
- Gaming: Unless AI NPCs, procedural generation, AI content creation
- Finance: Unless AI company funding or AI trading algorithms
- Communication tech: NFC, Bluetooth, UWB, 5G = NOT AI
- IoT/Smart home: Unless using ML for predictions/recommendations

tech_fields options: LLM, Computer Vision, NLP, Robotics, AI Safety, MLOps, Multimodal, Audio/Speech, Healthcare AI, General AI

Output format - EXACTLY {len(items)} lines starting from id=1:
{{"id":1,"content_type":"TYPE","confidence":0.8,"ai_relevance":0.85,"tech_fields":["FIELD"]}}
{{"id":2,"content_type":"TYPE","confidence":0.8,"ai_relevance":0.85,"tech_fields":["FIELD"]}}
...continue until id={len(items)}

START from id=1, classify ALL {len(items)} items:"""
        
        return prompt
    
    def _call_ollama(self, prompt: str, is_batch: bool = False) -> Tuple[Optional[str], Optional[FallbackReason]]:
        """调用Ollama API
        
        支持两种模式:
        1. 对于 Qwen3 等支持 think 参数的模型，使用 Chat API + think=false 获得快速响应
        2. 对于其他模型，使用 Generate API 并解析 thinking 字段（如有）
        
        Args:
            prompt: 提示词
            is_batch: 是否为批量分类模式（需要更多输出tokens）
            
        Returns:
            (response_text, error_reason): 响应文本和错误原因（成功时为None）
        """
        try:
            import requests
            
            # 检测是否为支持 think 参数的模型（如 Qwen3）
            use_chat_api = 'qwen3' in self.model.lower()
            
            # 保活时间设置
            keep_alive = f'{MODEL_KEEP_ALIVE_SECONDS}s'
            
            if use_chat_api:
                # 使用 Chat API + think=false 关闭思考模式，大幅提升速度
                # 根据GPU检测结果自适应配置
                options = self._get_ollama_options(is_batch=is_batch)
                
                response = self.session.post(
                    'http://localhost:11434/api/chat',
                    json={
                        'model': self.model,
                        'messages': [
                            {'role': 'system', 'content': LLM_SYSTEM_PROMPT},
                            {'role': 'user', 'content': prompt}
                        ],
                        'stream': False,
                        'think': False,  # 关闭思考模式（Qwen3专用）
                        'keep_alive': keep_alive,  # 保持模型活跃
                        'options': options
                    },
                    timeout=OLLAMA_BATCH_REQUEST_TIMEOUT if is_batch else OLLAMA_SINGLE_REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message = result.get('message', {})
                    content = message.get('content', '')
                    return (content, None) if content else (None, FallbackReason.INVALID_RESPONSE)
                elif response.status_code == 429:
                    return (None, FallbackReason.RATE_LIMIT)
                else:
                    return (None, FallbackReason.API_ERROR)
            else:
                # 使用 Generate API（适用于其他模型）
                options = self._get_ollama_options()
                
                # Generate API 不支持 system message，将其添加到 prompt 前面
                full_prompt = f"System: {LLM_SYSTEM_PROMPT}\n\nUser: {prompt}"
                
                response = self.session.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': self.model,
                        'prompt': full_prompt,
                        'stream': False,
                        'keep_alive': keep_alive,  # 保持模型活跃
                        'options': options
                    },
                    timeout=OLLAMA_SINGLE_REQUEST_TIMEOUT + 30  # Generate API 通常更慢
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 部分模型使用 thinking 字段存储思考过程
                    response_text = result.get('response', '')
                    thinking_text = result.get('thinking', '')
                    
                    # 如果 response 为空但 thinking 有内容，从 thinking 中提取
                    if not response_text.strip() and thinking_text:
                        return (thinking_text, None)
                    
                    return (response_text, None) if response_text else (None, FallbackReason.INVALID_RESPONSE)
                elif response.status_code == 429:
                    return (None, FallbackReason.RATE_LIMIT)
                else:
                    return (None, FallbackReason.API_ERROR)
            
        except requests.exceptions.Timeout:
            log.dual_warning("⏱️ Ollama请求超时 - 可能原因: 1)模型正在首次加载 2)显存/内存不足 3)批量请求过大")
            return (None, FallbackReason.TIMEOUT)
        except requests.exceptions.ConnectionError:
            log.dual_error("🔌 无法连接Ollama服务 - 请确认 ollama serve 正在运行")
            return (None, FallbackReason.CONNECTION_ERROR)
        except Exception as e:
            log.error(t('llm_ollama_failed', error=str(e)))
            return (None, FallbackReason.MODEL_ERROR)
    
    def _get_ollama_options(self, is_batch: bool = False) -> Dict:
        """获取Ollama推理选项（根据GPU自适应配置）
        
        Args:
            is_batch: 是否为批量分类模式（需要更多输出tokens）
        """
        if self.ollama_options:
            num_predict = self.ollama_options.num_predict_batch if is_batch else self.ollama_options.num_predict
            return {
                'temperature': self.ollama_options.temperature,
                'num_predict': num_predict,
                'num_ctx': self.ollama_options.num_ctx,
                'num_thread': self.ollama_options.num_thread,
                'num_gpu': self.ollama_options.num_gpu
            }
        else:
            # 默认配置
            return {
                'temperature': 0.1,
                'num_predict': 500 if is_batch else 200,
                'num_ctx': 2048,
                'num_thread': 4
            }
    
    def _call_openai(self, prompt: str, is_batch: bool = False) -> Tuple[Optional[str], Optional[FallbackReason]]:
        """调用OpenAI API
        
        Args:
            prompt: 提示词
            is_batch: 是否为批量分类模式（需要更多输出tokens）
            
        Returns:
            (response, error_reason): 响应文本和错误原因
        """
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            # 批量模式需要更多输出 tokens
            max_tokens = 2000 if is_batch else 300
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            return (content, None) if content else (None, FallbackReason.INVALID_RESPONSE)
            
        except Exception as e:
            log.error(t('llm_openai_failed', error=str(e)))
            return (None, FallbackReason.API_ERROR)
    
    def _call_azure_openai(self, prompt: str, is_batch: bool = False) -> Tuple[Optional[str], Optional[FallbackReason]]:
        """调用Azure OpenAI API
        
        Azure OpenAI 使用部署名称而非模型名称，
        需要配置 endpoint 和 api_version
        
        Args:
            prompt: 提示词
            is_batch: 是否为批量分类模式（需要更多输出tokens）
            
        Returns:
            (response, error_reason): 响应文本和错误原因
        """
        try:
            from openai import AzureOpenAI
            
            # 从环境变量或配置获取 Azure 特定参数
            endpoint = self.azure_endpoint or os.getenv('AZURE_OPENAI_ENDPOINT')
            api_version = self.azure_api_version or os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
            
            if not endpoint:
                log.error(t('llm_azure_endpoint_missing'))
                return (None, FallbackReason.API_ERROR)
            
            # 确保 endpoint 以 / 结尾
            if not endpoint.endswith('/'):
                endpoint = endpoint + '/'
            
            client = AzureOpenAI(
                api_key=self.api_key,
                api_version=api_version,
                azure_endpoint=endpoint
            )
            
            # 批量模式需要更多输出 tokens
            max_tokens = 2000 if is_batch else 300
            
            # Azure OpenAI 使用 deployment_name 作为 model 参数
            # 注意: self.model 必须是 Azure 中的部署名称，不是模型名称
            response = client.chat.completions.create(
                model=self.model,  # 这里是 Azure 部署名称，不是模型名如 gpt-4o
                messages=[
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            return (content, None) if content else (None, FallbackReason.INVALID_RESPONSE)
            
        except Exception as e:
            error_msg = str(e)
            # 提供更详细的错误提示
            if '404' in error_msg and 'Resource not found' in error_msg:
                log.error(f"Azure OpenAI 404错误 - 请检查:")
                log.error(f"  1. Deployment Name '{self.model}' 是否正确 (必须是Azure中创建的部署名称)")
                log.error(f"  2. Endpoint '{self.azure_endpoint}' 是否正确")
                log.error(f"  3. API Version '{self.azure_api_version}' 是否支持")
            log.error(t('llm_azure_openai_failed', error=error_msg))
            return (None, FallbackReason.API_ERROR)
    
    def _call_llm(self, prompt: str, is_batch: bool = False) -> Tuple[Optional[str], Optional[FallbackReason]]:
        """调用LLM（根据提供商选择）
        
        Args:
            prompt: 提示词
            is_batch: 是否为批量分类模式
            
        Returns:
            (response, error_reason): 响应文本和错误原因（成功时为None）
        """
        if self.provider == LLMProvider.OLLAMA:
            return self._call_ollama(prompt, is_batch=is_batch)
        elif self.provider == LLMProvider.OPENAI:
            return self._call_openai(prompt, is_batch=is_batch)
        elif self.provider == LLMProvider.AZURE_OPENAI:
            return self._call_azure_openai(prompt, is_batch=is_batch)
        return (None, FallbackReason.MODEL_ERROR)
    
    def _parse_llm_response(self, response: str) -> Optional[Dict]:
        """解析LLM响应
        
        支持两种格式:
        1. JSON格式: {"content_type": "xxx", ...}
        2. 纯文本格式: 直接返回类别名称（用于 thinking 模式的模型）
        """
        if not response:
            log.warning("LLM响应为空")
            return None
        
        try:
            # 尝试提取JSON部分
            response = response.strip()
            
            # 查找JSON开始和结束位置
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                result = json.loads(json_str)
                
                # 验证必要字段
                if 'content_type' in result:
                    # 规范化字段
                    result['content_type'] = result['content_type'].lower()
                    result['confidence'] = float(result.get('confidence', 0.8))
                    result['ai_relevance'] = float(result.get('ai_relevance', 0.7))  # 默认0.7（假设大部分采集内容是AI相关）
                    result['tech_fields'] = result.get('tech_fields', ['General AI'])
                    result['is_verified'] = result.get('is_verified', True)
                    result['reasoning'] = result.get('reasoning', '')
                    
                    return result
                else:
                    log.warning(f"JSON响应缺少content_type字段: {json_str[:100]}")
            
            # JSON解析失败，尝试从文本中提取类别（支持 thinking 模式的模型）
            return self._extract_category_from_text(response)
            
        except json.JSONDecodeError as e:
            log.warning(f"JSON解析错误: {e}, 响应内容: {response[:200] if response else 'None'}")
            # JSON解析失败，尝试从文本中提取类别
            return self._extract_category_from_text(response)
        except Exception as e:
            log.warning(t('llm_parse_failed', error=str(e)))
        
        return None
    
    def _extract_category_from_text(self, text: str) -> Optional[Dict]:
        """从自然语言文本中提取类别
        
        用于处理使用 thinking 模式的模型输出
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        # 定义类别关键词映射
        category_keywords = {
            'llm': ['llm', 'large language model', 'language model', 'gpt', 'chatgpt', 'claude', 'gemini'],
            'product': ['product', 'launch', 'release', 'announce', 'new feature'],
            'research': ['research', 'paper', 'study', 'academic', 'arxiv', 'conference'],
            'industry': ['industry', 'business', 'company', 'enterprise', 'market'],
            'tools': ['tool', 'framework', 'library', 'sdk', 'api'],
            'ethics': ['ethics', 'safety', 'regulation', 'policy', 'bias', 'fairness'],
            'vision': ['vision', 'image', 'video', 'computer vision', 'visual'],
            'robotics': ['robot', 'robotics', 'autonomous', 'embodied'],
        }
        
        # 首先检查文本末尾是否有明确的类别名称（R1模型通常在最后给出答案）
        lines = text.strip().split('\n')
        last_lines = ' '.join(lines[-3:]) if len(lines) >= 3 else text
        
        for category in category_keywords.keys():
            # 检查最后几行是否包含明确的类别名称
            if category in last_lines.lower().split():
                return {
                    'content_type': category,
                    'confidence': 0.85,
                    'ai_relevance': 0.7,  # 默认中等相关性
                    'tech_fields': ['General AI'],
                    'is_verified': True,
                    'reasoning': 'Extracted from LLM thinking output'
                }
        
        # 如果末尾没有明确类别，统计关键词出现次数
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return {
                'content_type': best_category,
                'confidence': min(0.7 + category_scores[best_category] * 0.05, 0.9),
                'ai_relevance': 0.7,  # 默认中等相关性
                'tech_fields': ['General AI'],
                'is_verified': True,
                'reasoning': f'Inferred from text analysis (score: {category_scores[best_category]})'
            }
        
        return None
    
    def classify_item(self, item: Dict, use_cache: bool = True) -> Dict:
        """
        使用LLM分类单个内容项
        
        Args:
            item: 内容项
            use_cache: 是否使用缓存
            
        Returns:
            分类后的内容项，包含:
            - content_type: 内容类型
            - confidence: 分类置信度
            - importance: 多维度重要性分数
            - importance_breakdown: 重要性分数明细
            - importance_level: 重要性等级
        """
        self.stats['total_calls'] += 1
        
        classified = item.copy()
        cache_key = self._get_cache_key(item)  # 复合key：content_hash:model_id
        
        # 检查缓存（多模型共存：key已包含模型信息，无需额外验证）
        if use_cache and self.enable_cache and cache_key in self.cache:
            cached = self.cache[cache_key]
            self.stats['cache_hits'] += 1
            classified.update(cached)
            classified['from_cache'] = True
            
            # 重要性分数始终重新计算（因为时效性会随时间变化）
            importance, breakdown = self.importance_evaluator.calculate_importance(
                item,
                {'content_type': classified.get('content_type', 'news'), 
                 'confidence': classified.get('confidence', 0.5),
                 'ai_relevance': classified.get('ai_relevance', 0.7)}
            )
            classified['importance'] = importance
            classified['importance_breakdown'] = breakdown
            level, _ = self.importance_evaluator.get_importance_level(importance)
            classified['importance_level'] = level
            
            return classified
        
        # 检查断路器
        if not self.fallback_strategy.should_use_llm():
            self.stats['fallback_calls'] += 1
            log.dual_warning("⚠️ Circuit breaker open, using rule classifier")
            classified = self.rule_classifier.classify_item(item)
            classified['classified_by'] = 'rule:circuit_breaker'
            return classified
        
        # 调用LLM（带重试机制）
        prompt = self._build_classification_prompt(item)
        response, error_reason = self._call_llm_with_fallback(prompt, item)
        
        if response:
            result = self._parse_llm_response(response)
            
            if result:
                self.stats['llm_calls'] += 1
                self.fallback_strategy.record_success()  # 记录成功
            
            # 更新分类结果
            classified['content_type'] = result['content_type']
            classified['confidence'] = result['confidence']
            classified['ai_relevance'] = result.get('ai_relevance', 0.7)  # AI相关性评分
            classified['tech_categories'] = result['tech_fields']
            classified['is_verified'] = result['is_verified']
            classified['llm_reasoning'] = result['reasoning']
            classified['classified_by'] = f"llm:{self.provider.value}/{self.model}"
            classified['classified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 使用规则分类器补充地区信息
            classified['region'] = self.rule_classifier.classify_region(item)
            
            # 计算多维度重要性分数（使用统一的评估器）
            importance, importance_breakdown = self.importance_evaluator.calculate_importance(
                item,
                {'content_type': result['content_type'], 'confidence': result['confidence'],
                 'ai_relevance': classified['ai_relevance']}  # 传入AI相关性
            )
            classified['importance'] = importance
            classified['importance_breakdown'] = importance_breakdown
            level, _ = self.importance_evaluator.get_importance_level(importance)
            classified['importance_level'] = level
            
            # 保存到缓存（多模型共存：不同模型的结果分别存储）
            if self.enable_cache:
                self.cache[cache_key] = {
                    'content_type': classified['content_type'],
                    'confidence': classified['confidence'],
                    'ai_relevance': classified['ai_relevance'],  # 缓存AI相关性
                    'tech_categories': classified['tech_categories'],
                    'is_verified': classified['is_verified'],
                    'llm_reasoning': classified['llm_reasoning'],
                    'region': classified['region'],
                    'classified_by': classified['classified_by']
                    # 注意：importance 不缓存，因为时效性分数需要实时计算
                }
        # LLM失败，根据错误原因执行智能降级
        self.stats['fallback_calls'] += 1
        self.stats['errors'] += 1
        
        if error_reason:
            self.fallback_strategy.record_error(error_reason)
        
        fallback_reason = error_reason.value if error_reason else 'unknown_error'
        self.stats['fallback_details'].append({
            'title': item.get('title', '')[:50],
            'source': item.get('source', ''),
            'reason': fallback_reason,
            'mode': 'single'
        })
        
        log.warning(t('llm_fallback', title=item.get('title', '')[:30]) + f" ({fallback_reason})")
        classified = self.rule_classifier.classify_item(item)
        classified['classified_by'] = f'rule:fallback:{fallback_reason}'
        
        return classified
    
    def _call_llm_with_fallback(self, prompt: str, item: Dict, max_retries: int = 1) -> Tuple[Optional[str], Optional[FallbackReason]]:
        """带智能降级的 LLM 调用
        
        Args:
            prompt: 提示词
            item: 内容项（用于降级策略判断）
            max_retries: 最大重试次数
            
        Returns:
            (response, error_reason): 响应和错误原因
        """
        for attempt in range(max_retries + 1):
            response, error_reason = self._call_llm(prompt)
            
            if response:
                return (response, None)
            
            if error_reason:
                action = self.fallback_strategy.get_fallback_action(error_reason, item)
                
                if action == 'retry' and attempt < max_retries:
                    log.dual_info(f"🔄 Retrying LLM call (attempt {attempt + 2}/{max_retries + 1})...")
                    continue
                elif action == 'quick':
                    # 快速降级：返回错误，外部使用简化规则
                    return (None, error_reason)
                else:
                    # 完整降级：返回错误，外部使用完整规则分类
                    return (None, error_reason)
            
            # 未知错误，不重试
            break
        
        return (None, error_reason or FallbackReason.MODEL_ERROR)
    
    def classify_batch(self, items: List[Dict], show_progress: bool = True, 
                       use_batch_api: bool = True) -> List[Dict]:
        """
        批量分类（支持两种模式）
        
        Args:
            items: 内容项列表
            show_progress: 是否显示进度
            use_batch_api: 是否使用批量API（一次调用分类多条，更快）
            
        Returns:
            分类后的内容项列表
        """
        total = len(items)
        
        # 重置统计数据（每次批量分类开始时清零，确保统计反映当前批次）
        self.stats = {
            'total_calls': 0,
            'cache_hits': 0,
            'llm_calls': 0,
            'fallback_calls': 0,
            'errors': 0,
            'fallback_details': []
        }
        
        # 先检查缓存，分离已缓存和未缓存的内容
        # 多模型共存设计：缓存key已包含模型信息，无需额外验证模型匹配
        cached_items = []
        uncached_items = []
        uncached_indices = []
        
        current_model = self._get_current_model_identifier()
        
        for i, item in enumerate(items):
            cache_key = self._get_cache_key(item)  # 复合key：content_hash:model_id
            if self.enable_cache and cache_key in self.cache:
                cached = self.cache[cache_key]
                self.stats['cache_hits'] += 1
                self.stats['total_calls'] += 1
                classified = item.copy()
                classified.update(cached)
                classified['from_cache'] = True
                # 确保有 classified_by 字段（兼容旧缓存）
                if 'classified_by' not in classified:
                    classified['classified_by'] = f'llm:cached:{current_model}'
                
                # 重要性分数始终重新计算（因为时效性会随时间变化）
                importance, breakdown = self.importance_evaluator.calculate_importance(
                    item,
                    {'content_type': classified.get('content_type', 'news'), 
                     'confidence': classified.get('confidence', 0.5),
                     'ai_relevance': classified.get('ai_relevance', 0.7)}
                )
                classified['importance'] = importance
                classified['importance_breakdown'] = breakdown
                level, _ = self.importance_evaluator.get_importance_level(importance)
                classified['importance_level'] = level
                
                cached_items.append((i, classified))
            else:
                uncached_items.append(item)
                uncached_indices.append(i)
        
        cached_count = len(cached_items)
        uncached_count = len(uncached_items)
        
        log.dual_start(t('llm_batch_start', total=total))
        log.dual_ai(t('llm_batch_info', provider=self.provider.value, model=self.model))
        log.dual_data(t('llm_batch_cache', workers=self.max_workers, cached=cached_count, total=total))
        
        if uncached_count == 0:
            log.dual_success(t('llm_all_cached'))
            cached_items.sort(key=lambda x: x[0])
            return [item for _, item in cached_items]
        
        # 模型预热（仅Ollama且未预热时）
        if self.provider == LLMProvider.OLLAMA and not self.is_warmed_up:
            self.warmup_model()
        
        start_time = time.time()
        classified_uncached = []
        
        # 选择分类策略
        # Ollama 和 Azure OpenAI 都支持批量模式
        if use_batch_api and self.batch_size > 1 and self.provider in (LLMProvider.OLLAMA, LLMProvider.AZURE_OPENAI):
            # 批量API模式：一次调用分类多条（更快、更省成本）
            log.dual_info(t('llm_batch_mode', batch_size=self.batch_size))
            classified_uncached = self._classify_batch_mode(uncached_items, uncached_indices, show_progress)
        else:
            # 并发单条模式
            log.dual_info(t('llm_concurrent_mode'))
            classified_uncached = self._classify_concurrent_mode(uncached_items, uncached_indices, show_progress)
        
        # 合并结果
        all_items = cached_items + classified_uncached
        all_items.sort(key=lambda x: x[0])
        result = [item for _, item in all_items]
        
        # 保存缓存
        self._save_cache()
        
        # 统计
        elapsed = time.time() - start_time
        self._print_stats(elapsed)
        
        return result
    
    def _classify_batch_mode(self, items: List[Dict], indices: List[int], 
                             show_progress: bool) -> List[Tuple[int, Dict]]:
        """批量分类模式：一次LLM调用处理多条内容"""
        results = []
        total = len(items)
        total_batches = (total + self.batch_size - 1) // self.batch_size
        
        # 分批处理
        batch_num = 0
        for batch_start in range(0, total, self.batch_size):
            batch_num += 1
            batch_start_time = time.time()
            batch_end = min(batch_start + self.batch_size, total)
            batch_items = items[batch_start:batch_end]
            batch_indices = indices[batch_start:batch_end]
            
            # 构建批量prompt
            prompt = self._build_batch_prompt(batch_items)
            response, error_reason = self._call_llm(prompt, is_batch=True)  # 使用批量模式（更多输出tokens）
            batch_results = self._parse_batch_response(response, len(batch_items)) if response else None
            
            # 处理结果
            retry_items = []  # 收集需要重试的条目
            retry_indices = []
            
            for i, (item, idx) in enumerate(zip(batch_items, batch_indices)):
                self.stats['total_calls'] += 1
                classified = item.copy()
                
                if batch_results and i < len(batch_results) and batch_results[i]:
                    result = batch_results[i]
                    self.stats['llm_calls'] += 1
                    
                    classified['content_type'] = result.get('content_type', 'market')
                    classified['confidence'] = result.get('confidence', 0.7)
                    classified['ai_relevance'] = result.get('ai_relevance', 0.7)  # AI相关性评分
                    classified['tech_categories'] = result.get('tech_fields', ['General AI'])
                    classified['is_verified'] = result.get('is_verified', True)
                    classified['llm_reasoning'] = result.get('reasoning', '')
                    classified['classified_by'] = f"llm:batch:{self.provider.value}/{self.model}"
                    classified['classified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    classified['region'] = self.rule_classifier.classify_region(item)
                    
                    # 计算多维度重要性分数
                    importance, importance_breakdown = self.importance_evaluator.calculate_importance(
                        item,
                        {'content_type': classified['content_type'], 'confidence': classified['confidence'],
                         'ai_relevance': classified['ai_relevance']}  # 传入AI相关性
                    )
                    classified['importance'] = importance
                    classified['importance_breakdown'] = importance_breakdown
                    level, _ = self.importance_evaluator.get_importance_level(importance)
                    classified['importance_level'] = level
                    
                    # 缓存（多模型共存：不保存importance，因为时效性会变化）
                    cache_key = self._get_cache_key(item)
                    if self.enable_cache:
                        self.cache[cache_key] = {
                            'content_type': classified['content_type'],
                            'confidence': classified['confidence'],
                            'ai_relevance': classified['ai_relevance'],  # 缓存AI相关性
                            'tech_categories': classified['tech_categories'],
                            'is_verified': classified.get('is_verified', True),
                            'llm_reasoning': classified.get('llm_reasoning', ''),
                            'region': classified['region'],
                            'classified_by': classified['classified_by']
                        }
                    results.append((idx, classified))
                else:
                    # 批量解析失败，加入重试列表
                    retry_items.append(item)
                    retry_indices.append(idx)
            
            # 对批量失败的条目进行单条重试
            if retry_items:
                log.warning(t('llm_batch_retry', count=len(retry_items)))
                for item, idx in zip(retry_items, retry_indices):
                    # 尝试单条 LLM 分类
                    retry_result = self._single_classify_with_llm(item)
                    
                    if retry_result:
                        # 单条重试成功
                        self.stats['llm_calls'] += 1
                        classified = item.copy()
                        classified['content_type'] = retry_result.get('content_type', 'market')
                        classified['confidence'] = retry_result.get('confidence', 0.7)
                        classified['ai_relevance'] = retry_result.get('ai_relevance', 0.7)  # AI相关性评分
                        classified['tech_categories'] = retry_result.get('tech_fields', ['General AI'])
                        classified['is_verified'] = retry_result.get('is_verified', True)
                        classified['llm_reasoning'] = retry_result.get('reasoning', '')
                        classified['classified_by'] = f"llm:retry:{self.provider.value}/{self.model}"
                        classified['classified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        classified['region'] = self.rule_classifier.classify_region(item)
                        
                        # 计算多维度重要性分数
                        importance, importance_breakdown = self.importance_evaluator.calculate_importance(
                            item,
                            {'content_type': classified['content_type'], 'confidence': classified['confidence'],
                             'ai_relevance': classified['ai_relevance']}  # 传入AI相关性
                        )
                        classified['importance'] = importance
                        classified['importance_breakdown'] = importance_breakdown
                        level, _ = self.importance_evaluator.get_importance_level(importance)
                        classified['importance_level'] = level
                        
                        # 缓存（多模型共存：不保存importance）
                        cache_key = self._get_cache_key(item)
                        if self.enable_cache:
                            self.cache[cache_key] = {
                                'content_type': classified['content_type'],
                                'confidence': classified['confidence'],
                                'ai_relevance': classified['ai_relevance'],  # 缓存AI相关性
                                'tech_categories': classified['tech_categories'],
                                'is_verified': classified.get('is_verified', True),
                                'llm_reasoning': classified.get('llm_reasoning', ''),
                                'region': classified['region'],
                                'classified_by': classified['classified_by']
                            }
                        results.append((idx, classified))
                        log.dual_success(t('llm_retry_success', title=item.get('title', '')[:40]))
                    else:
                        # 单条重试也失败，降级到规则分类（规则分类已内置重要性计算）
                        self.stats['fallback_calls'] += 1
                        self.stats['fallback_details'].append({
                            'title': item.get('title', '')[:50],
                            'source': item.get('source', ''),
                            'reason': '批量+单条重试均失败',
                            'mode': 'batch_retry'
                        })
                        classified = self.rule_classifier.classify_item(item)
                        classified['classified_by'] = 'rule:batch_fallback'
                        results.append((idx, classified))
            
            if show_progress:
                completed = min(batch_end, total)
                batch_time = time.time() - batch_start_time
                remaining_batches = total_batches - batch_num
                estimated_remaining = batch_time * remaining_batches
                
                if remaining_batches > 0:
                    log.dual_info(t('llm_progress_eta', completed=completed, total=total, percent=int(completed/total*100), time=f"{batch_time:.1f}", eta=f"{estimated_remaining:.0f}"))
                else:
                    log.dual_info(t('llm_progress', completed=completed, total=total, percent=int(completed/total*100)) + f" | {t('llm_stats_time', time=f'{batch_time:.1f}')}")
        
        return results
    
    def _classify_concurrent_mode(self, items: List[Dict], indices: List[int],
                                   show_progress: bool) -> List[Tuple[int, Dict]]:
        """并发单条分类模式"""
        results = []
        total = len(items)
        last_progress_time = time.time()
        last_progress_count = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.classify_item, item): (i, idx) 
                      for i, (item, idx) in enumerate(zip(items, indices))}
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    _, idx = futures[future]
                    results.append((idx, result))
                    completed += 1
                    
                    if show_progress and completed % 5 == 0:
                        current_time = time.time()
                        interval_time = current_time - last_progress_time
                        interval_count = completed - last_progress_count
                        
                        if interval_count > 0 and interval_time > 0:
                            rate = interval_count / interval_time  # 条/秒
                            remaining = total - completed
                            estimated_remaining = remaining / rate if rate > 0 else 0
                            log.dual_info(t('llm_progress_rate', completed=completed, total=total, percent=int(completed/total*100), rate=f"{rate:.1f}", eta=f"{estimated_remaining:.0f}"))
                        else:
                            log.dual_info(t('llm_progress', completed=completed, total=total, percent=int(completed/total*100)))
                        
                        last_progress_time = current_time
                        last_progress_count = completed
                        
                except Exception as e:
                    log.error(t('llm_task_failed', error=str(e)))
                    self.stats['errors'] += 1
        
        return results
    
    def _single_classify_with_llm(self, item: Dict) -> Optional[Dict]:
        """对单条内容进行 LLM 分类（用于批量失败后的重试）
        
        Args:
            item: 要分类的条目
            
        Returns:
            分类结果字典，失败返回 None
        """
        try:
            prompt = self._build_classification_prompt(item)
            response, error_reason = self._call_llm(prompt, is_batch=False)
            
            if not response:
                return None
            
            # 解析单条响应
            result = self._parse_single_response(response)
            return result
            
        except Exception as e:
            log.warning(f"Single retry failed: {str(e)}")
            return None
    
    def _parse_single_response(self, response: str) -> Optional[Dict]:
        """解析单条分类响应"""
        if not response:
            return None
        
        try:
            # 预处理：移除markdown代码块标记
            cleaned = response.strip()
            if '```json' in cleaned:
                import re
                json_blocks = re.findall(r'```json?\s*(.*?)\s*```', cleaned, re.DOTALL)
                if json_blocks:
                    cleaned = json_blocks[0]
            elif '```' in cleaned:
                import re
                cleaned = re.sub(r'```\w*\s*', '', cleaned)
                cleaned = cleaned.replace('```', '')
            
            # 查找JSON对象
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = cleaned[start:end]
                # 修复常见的JSON格式问题
                json_str = json_str.replace('，', ',')
                json_str = json_str.replace('"', '"').replace('"', '"')
                
                obj = json.loads(json_str)
                
                content_type = obj.get('content_type', obj.get('type', 'market'))
                if isinstance(content_type, str):
                    content_type = content_type.lower().strip()
                    if '(' in content_type:
                        content_type = content_type.split('(')[0].strip()
                
                # 验证content_type
                valid_types = ['research', 'product', 'market', 'developer', 'leader', 'community']
                if content_type not in valid_types:
                    type_mapping = {
                        'paper': 'research', 'academic': 'research', 'study': 'research',
                        'release': 'product', 'launch': 'product', 'tool': 'developer',
                        'news': 'market', 'funding': 'market', 'opinion': 'leader',
                        'discussion': 'community', 'trend': 'community'
                    }
                    content_type = type_mapping.get(content_type, 'market')
                
                return {
                    'content_type': content_type,
                    'confidence': float(obj.get('confidence', 0.7)),
                    'tech_fields': obj.get('tech_fields', obj.get('fields', ['General AI'])),
                    'is_verified': obj.get('is_verified', True),
                    'reasoning': obj.get('reasoning', obj.get('reason', ''))
                }
                
        except Exception as e:
            log.warning(f"Parse single response failed: {str(e)}")
        
        return None

    def _parse_batch_response(self, response: str, expected_count: int) -> List[Optional[Dict]]:
        """解析批量分类响应（增强版）
        
        支持多种LLM输出格式：
        1. 每行一个JSON
        2. Markdown代码块包裹的JSON
        3. 带序号的JSON列表
        4. JSON数组格式
        """
        results = [None] * expected_count
        
        if not response:
            return results
        
        try:
            # 预处理：移除markdown代码块标记
            cleaned = response.strip()
            if '```json' in cleaned:
                # 提取```json ... ```之间的内容
                import re
                json_blocks = re.findall(r'```json?\s*(.*?)\s*```', cleaned, re.DOTALL)
                if json_blocks:
                    cleaned = '\n'.join(json_blocks)
            elif '```' in cleaned:
                # 移除通用代码块标记
                cleaned = re.sub(r'```\w*\s*', '', cleaned)
                cleaned = cleaned.replace('```', '')
            
            json_objects = []
            
            # 方法1：尝试解析为JSON数组
            try:
                arr = json.loads(cleaned)
                if isinstance(arr, list):
                    json_objects = arr
            except json.JSONDecodeError:
                pass
            
            # 方法2：按行解析JSON
            if not json_objects:
                lines = cleaned.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 移除行首的序号（如 "1." 或 "[1]"）
                    import re
                    line = re.sub(r'^[\[\(]?\d+[\]\)\.:]?\s*', '', line)
                    
                    # 查找JSON对象
                    start = line.find('{')
                    end = line.rfind('}') + 1
                    
                    if start >= 0 and end > start:
                        json_str = line[start:end]
                        # 修复常见的JSON格式问题
                        json_str = json_str.replace('，', ',')  # 中文逗号
                        json_str = json_str.replace('"', '"').replace('"', '"')  # 中文引号
                        json_str = json_str.replace(''', "'").replace(''', "'")
                        
                        try:
                            obj = json.loads(json_str)
                            json_objects.append(obj)
                        except json.JSONDecodeError:
                            # 尝试更宽松的解析
                            try:
                                # 修复缺少引号的键名
                                fixed = re.sub(r'(\w+):', r'"\1":', json_str)
                                obj = json.loads(fixed)
                                json_objects.append(obj)
                            except (json.JSONDecodeError, ValueError):
                                continue
            
            # 方法3：查找所有独立的JSON对象（处理多个JSON在一行的情况）
            if not json_objects:
                import re
                pattern = r'\{[^{}]*\}'
                matches = re.findall(pattern, cleaned)
                for match in matches:
                    try:
                        obj = json.loads(match)
                        json_objects.append(obj)
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            # 匹配结果到对应索引
            for i, obj in enumerate(json_objects):
                # 优先使用id字段
                idx = obj.get('id')
                if idx is not None:
                    idx = int(idx) - 1  # id从1开始
                else:
                    # 没有id字段，按顺序分配
                    idx = i
                
                if 0 <= idx < expected_count and results[idx] is None:
                    content_type = obj.get('content_type', obj.get('type', 'market'))
                    if isinstance(content_type, str):
                        content_type = content_type.lower().strip()
                        # 处理带括号的格式，如 "developer(tools/models)" -> "developer"
                        if '(' in content_type:
                            content_type = content_type.split('(')[0].strip()
                    
                    # 验证content_type是否有效
                    valid_types = ['research', 'product', 'market', 'developer', 'leader', 'community']
                    if content_type not in valid_types:
                        # 尝试映射
                        type_mapping = {
                            'paper': 'research', 'academic': 'research', 'study': 'research',
                            'papers': 'research', 'releases': 'product',
                            'release': 'product', 'launch': 'product', 'tool': 'developer',
                            'tools': 'developer', 'models': 'developer', 'tools/models': 'developer',
                            'news': 'market', 'funding': 'market', 'investment': 'market',
                            'funding/news': 'market',
                            'opinion': 'leader', 'quote': 'leader', 'insight': 'leader',
                            'opinions': 'leader',
                            'discussion': 'community', 'trend': 'community', 'trends': 'community'
                        }
                        content_type = type_mapping.get(content_type, 'market')
                    
                    results[idx] = {
                        'content_type': content_type,
                        'confidence': float(obj.get('confidence', 0.7)),
                        'ai_relevance': float(obj.get('ai_relevance', 0.7)),  # AI相关性评分
                        'tech_fields': obj.get('tech_fields', obj.get('fields', ['General AI'])),
                        'is_verified': obj.get('is_verified', True),
                        'reasoning': obj.get('reasoning', obj.get('reason', ''))
                    }
            
        except Exception as e:
            log.warning(t('llm_batch_parse_failed', error=str(e)))
        
        return results
    
    def _print_stats(self, elapsed: float):
        """打印统计信息"""
        log.dual_info(t('llm_stats'))
        log.dual_info(t('llm_stats_total', count=self.stats['total_calls']))
        log.dual_info(t('llm_stats_cached', count=self.stats['cache_hits']) + f" ({self.stats['cache_hits']/max(1,self.stats['total_calls']):.0%})")
        log.dual_info(f"   LLM: {self.stats['llm_calls']}")
        log.dual_info(f"   Fallback: {self.stats['fallback_calls']}")
        log.dual_info(t('llm_stats_failed', count=self.stats['errors']))
        log.dual_info(t('llm_stats_time', time=f"{elapsed:.1f}s"))
        
        if self.stats['llm_calls'] > 0:
            avg_time = elapsed / self.stats['llm_calls']
            log.dual_info(t('llm_stats_avg', time=f"{avg_time:.1f}"))
        
        # 显示降级详情
        if self.stats['fallback_details']:
            log.dual_warning(t('llm_fallback_details', count=len(self.stats['fallback_details'])))
            for i, detail in enumerate(self.stats['fallback_details'], 1):
                log.dual_info(t('llm_fallback_item', i=i, mode=detail['mode'], title=detail['title']))
                log.dual_info(t('llm_fallback_source', source=detail['source'], reason=detail['reason']))
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def clear_cache(self):
        """清空缓存"""
        self.cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        log.dual_success(t('llm_cache_cleared'))


def select_llm_provider() -> Tuple[str, str]:
    """
    交互式选择LLM提供商和模型
    
    Returns:
        (provider, model)
    """
    print("\n" + "="*60)
    print(t('llm_select_provider'))
    print("="*60)
    
    print(t('llm_available_providers'))
    print(t('llm_provider_ollama'))
    print(t('llm_provider_openai'))
    print("  3. Azure OpenAI - 企业级云服务 (需要Azure订阅)")
    
    prompt = "Select provider (1-3) [default: 1]: " if get_language() == 'en' else "请选择提供商 (1-3) [默认: 1]: "
    provider_choice = input(f"\n{prompt}").strip() or '1'
    
    provider_map = {'1': 'ollama', '2': 'openai', '3': 'azure_openai'}
    provider = provider_map.get(provider_choice, 'ollama')
    
    # 选择模型
    print(t('llm_available_models_for', provider=provider.upper()))
    
    provider_enum = LLMProvider(provider)
    models = AVAILABLE_MODELS.get(provider_enum, {})
    
    model_list = list(models.keys())
    for i, (model_id, info) in enumerate(models.items(), 1):
        recommended = " ⭐" if i == 1 else ""
        print(f"  {i}. {info['name']}{recommended}")
        print(f"     {info['description']}")
    
    model_prompt = f"Select model (1-{len(model_list)}) [default: 1]: " if get_language() == 'en' else f"请选择模型 (1-{len(model_list)}) [默认: 1]: "
    model_choice = input(f"\n{model_prompt}").strip() or '1'
    
    try:
        model_idx = int(model_choice) - 1
        model = model_list[model_idx] if 0 <= model_idx < len(model_list) else model_list[0]
    except (ValueError, IndexError):
        model = model_list[0]
    
    log.success(t('llm_selected', provider=provider, model=model))
    
    return provider, model


def get_available_ollama_models() -> List[str]:
    """获取本地可用的Ollama模型列表"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
    except (requests.RequestException, ConnectionError, TimeoutError, json.JSONDecodeError):
        pass
    return []


def check_ollama_status() -> Dict:
    """检查Ollama服务状态（增强版，包含更多诊断信息）"""
    result = {
        'running': False,
        'models': [],
        'recommended': None,
        'loaded_models': [],  # 当前已加载到内存的模型
        'gpu_info': None
    }
    
    try:
        import requests
        
        # 1. 检查Ollama服务是否运行
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            result['running'] = True
            data = response.json()
            result['models'] = [model['name'] for model in data.get('models', [])]
            
            # 推荐模型优先级
            preferred = ['qwen3:8b', 'llama3.2:3b', 'mistral:7b']
            for model in preferred:
                if model in result['models']:
                    result['recommended'] = model
                    break
            
            if not result['recommended'] and result['models']:
                result['recommended'] = result['models'][0]
        
        # 2. 检查当前已加载的模型（ollama ps 等效）
        try:
            ps_response = requests.get('http://localhost:11434/api/ps', timeout=5)
            if ps_response.status_code == 200:
                ps_data = ps_response.json()
                loaded = ps_data.get('models', [])
                result['loaded_models'] = [m.get('name', '') for m in loaded]
                
                # 如果有模型已加载，优先推荐已加载的模型（避免重新加载）
                for loaded_model in result['loaded_models']:
                    if loaded_model in result['models']:
                        result['recommended'] = loaded_model
                        result['model_preloaded'] = True
                        break
        except Exception:
            pass  # ps API 可能不可用，忽略
        
        # 3. 检测GPU状态
        gpu_info = detect_gpu()
        if gpu_info:
            result['gpu_info'] = {
                'available': gpu_info.available,
                'type': gpu_info.gpu_type,
                'name': gpu_info.gpu_name,
                'ollama_supported': gpu_info.ollama_gpu_supported
            }
                
    except requests.exceptions.ConnectionError:
        result['error'] = 'connection_refused'
        result['error_message'] = 'Ollama服务未运行，请先启动 ollama serve'
    except requests.exceptions.Timeout:
        result['error'] = 'timeout'
        result['error_message'] = 'Ollama服务响应超时'
    except Exception as e:
        result['error'] = str(e)
    
    return result


# 便捷函数
def create_llm_classifier(auto_select: bool = False) -> LLMClassifier:
    """
    创建LLM分类器的便捷函数
    
    Args:
        auto_select: 是否自动选择最佳配置
        
    Returns:
        LLMClassifier实例
    """
    if auto_select:
        # 自动选择：优先使用本地Ollama
        status = check_ollama_status()
        if status['running'] and status['recommended']:
            return LLMClassifier(provider='ollama', model=status['recommended'])
        
        # 检查OpenAI
        if os.getenv('OPENAI_API_KEY'):
            return LLMClassifier(provider='openai', model='gpt-4o-mini')
        
        # 检查Azure OpenAI
        if os.getenv('AZURE_OPENAI_API_KEY') and os.getenv('AZURE_OPENAI_ENDPOINT'):
            return LLMClassifier(provider='azure_openai', model='gpt-4o-mini')
        
        log.error(t('llm_no_service'))
        return None
    else:
        # 交互式选择
        provider, model = select_llm_provider()
        return LLMClassifier(provider=provider, model=model)


if __name__ == "__main__":
    # 测试代码
    print("="*60)
    print(t('llm_test_title'))
    print("="*60)
    
    # 检查Ollama状态
    status = check_ollama_status()
    status_text = t('llm_ollama_running_yes') if status['running'] else t('llm_ollama_running_no')
    log.info(t('llm_ollama_status', status=status_text), emoji="🔍")
    if status['models']:
        log.info(t('llm_available_models', models=', '.join(status['models'])), emoji="📦")
        log.info(t('llm_recommended_model', model=status['recommended']), emoji="⭐")
    
    # 创建分类器
    if status['running']:
        classifier = LLMClassifier(
            provider='ollama',
            model=status['recommended'] or 'qwen3:8b'
        )
        
        # 测试分类
        test_item = {
            'title': 'OpenAI officially launches GPT-4o with new features',
            'summary': 'OpenAI announces the general availability of GPT-4o model with improved capabilities',
            'source': 'TechCrunch'
        }
        
        log.info(t('llm_test_content', title=test_item['title']), emoji="🧪")
        result = classifier.classify_item(test_item)
        
        log.info(t('llm_test_result'), emoji="📋")
        log.info(t('llm_test_type', type=result.get('content_type')), emoji="  ")
        log.info(t('llm_test_confidence', confidence=f"{result.get('confidence', 0):.1%}"), emoji="  ")
        log.info(t('llm_test_tech', tech=result.get('tech_categories')), emoji="  ")
        log.info(t('llm_test_verified', verified=result.get('is_verified')), emoji="  ")
        log.info(t('llm_test_reasoning', reasoning=result.get('llm_reasoning')), emoji="  ")
    else:
        log.warning(t('llm_start_ollama'))
