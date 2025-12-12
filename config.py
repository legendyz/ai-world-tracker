"""
配置管理模块 - Config Manager
统一管理LLM和应用配置

支持多种配置源:
- YAML配置文件 (config.yaml)
- 环境变量
- .env文件
- 默认值

优先级: 环境变量 > .env文件 > YAML配置 > 默认值
"""

import os
import yaml
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
from logger import get_log_helper

# 模块日志器
log = get_log_helper('config')


@dataclass
class OllamaConfig:
    """Ollama配置"""
    base_url: str = "http://localhost:11434"
    default_model: str = "qwen3:8b"
    timeout: int = 60
    num_predict: int = 300
    num_ctx: int = 2048
    temperature: float = 0.1


@dataclass
class OpenAIConfig:
    """OpenAI配置"""
    api_key: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    timeout: int = 30
    max_tokens: int = 300
    temperature: float = 0.1


@dataclass
class AzureOpenAIConfig:
    """Azure OpenAI配置"""
    api_key: Optional[str] = None
    endpoint: Optional[str] = None  # Azure端点URL，如 https://xxx.openai.azure.com/
    api_version: str = "2024-02-15-preview"
    deployment_name: str = "gpt-4o-mini"  # Azure部署名称
    timeout: int = 30
    max_tokens: int = 300
    temperature: float = 0.1


@dataclass
class ClassifierConfig:
    """分类器配置"""
    # 默认模式: 'llm' 或 'rule'
    default_mode: str = "rule"
    
    # LLM配置
    llm_provider: str = "ollama"
    llm_model: str = "qwen3:8b"
    
    # 缓存配置
    enable_cache: bool = True
    cache_file: str = "llm_classification_cache.json"
    
    # 并发配置
    max_workers: int = 3
    
    # 自动降级
    auto_fallback: bool = True


@dataclass 
class CollectorConfig:
    """数据采集配置"""
    product_count: int = 10
    community_count: int = 10
    leader_count: int = 15
    research_count: int = 15
    developer_count: int = 20
    news_count: int = 25
    max_total: int = 100
    timeout: int = 30
    data_retention_days: int = 7  # 数据采集时间窗口（天）


@dataclass 
class AppConfig:
    """应用总配置"""
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    azure_openai: AzureOpenAIConfig = field(default_factory=AzureOpenAIConfig)
    classifier: ClassifierConfig = field(default_factory=ClassifierConfig)
    collector: CollectorConfig = field(default_factory=CollectorConfig)
    
    # 输出配置
    output_dir: str = "."
    web_output_dir: str = "web_output"
    visualization_dir: str = "visualizations"


class ConfigManager:
    """配置管理器 - 统一管理所有配置
    
    支持多种配置源，优先级: 环境变量 > .env文件 > YAML配置 > 默认值
    """
    
    _instance = None
    _config: AppConfig = None
    _yaml_config: Dict = None
    
    def __new__(cls, config_path: str = 'config.yaml'):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config_path = config_path
            cls._instance._load_config()
        return cls._instance
    
    def _load_yaml_config(self) -> Dict:
        """加载YAML配置文件"""
        config_file = Path(self._config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                log.warning(f"加载YAML配置失败: {e}")
        return {}
    
    def _get_yaml_value(self, key_path: str, default: Any = None) -> Any:
        """从YAML配置获取值，支持点号路径"""
        if not self._yaml_config:
            return default
        keys = key_path.split('.')
        val = self._yaml_config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val
    
    def _load_config(self):
        """加载配置"""
        # 1. 加载.env文件
        self._load_env_file()
        
        # 2. 加载YAML配置
        self._yaml_config = self._load_yaml_config()
        
        # 3. 创建配置对象（按优先级合并）
        self._config = AppConfig(
            ollama=OllamaConfig(
                base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
                default_model=os.getenv('OLLAMA_MODEL', 
                    self._get_yaml_value('classification.model', 'qwen3:8b')),
                timeout=int(os.getenv('OLLAMA_TIMEOUT', '60')),
            ),
            openai=OpenAIConfig(
                api_key=os.getenv('OPENAI_API_KEY'),
                default_model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            ),
            azure_openai=AzureOpenAIConfig(
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
                deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini'),
            ),
            classifier=ClassifierConfig(
                default_mode=os.getenv('CLASSIFIER_MODE', 
                    self._get_yaml_value('classification.mode', 'rule')),
                llm_provider=os.getenv('LLM_PROVIDER', 
                    self._get_yaml_value('classification.provider', 'ollama')),
                llm_model=os.getenv('LLM_MODEL', 
                    self._get_yaml_value('classification.model', 'qwen3:8b')),
                enable_cache=os.getenv('ENABLE_CACHE', 'true').lower() == 'true',
                max_workers=int(os.getenv('MAX_WORKERS', 
                    str(self._get_yaml_value('classification.max_workers', 3)))),
            ),
            collector=CollectorConfig(
                product_count=self._get_yaml_value('collector.product_count', 10),
                community_count=self._get_yaml_value('collector.community_count', 10),
                leader_count=self._get_yaml_value('collector.leader_count', 15),
                research_count=self._get_yaml_value('collector.research_count', 15),
                developer_count=self._get_yaml_value('collector.developer_count', 20),
                news_count=self._get_yaml_value('collector.news_count', 25),
                max_total=self._get_yaml_value('collector.max_total', 100),
                data_retention_days=self._get_yaml_value('collector.data_retention_days', 7),
            ),
            output_dir=self._get_yaml_value('output.report_dir', '.'),
            web_output_dir=self._get_yaml_value('output.web_dir', 'web_output'),
        )
    
    def _load_env_file(self):
        """加载.env文件"""
        env_file = Path('.env')
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key and value and key not in os.environ:
                                os.environ[key] = value
            except Exception as e:
                log.warning(f"加载.env文件失败: {e}")
    
    @property
    def config(self) -> AppConfig:
        """获取配置"""
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split('.')
        obj = self._config
        for k in keys[:-1]:
            if hasattr(obj, k):
                obj = getattr(obj, k)
            else:
                return
        if hasattr(obj, keys[-1]):
            setattr(obj, keys[-1], value)
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取当前LLM配置"""
        provider = self._config.classifier.llm_provider
        model = self._config.classifier.llm_model
        
        if provider == 'ollama':
            return {
                'provider': 'ollama',
                'model': model,
                'base_url': self._config.ollama.base_url,
                'timeout': self._config.ollama.timeout,
            }
        elif provider == 'openai':
            return {
                'provider': 'openai',
                'model': model,
                'api_key': self._config.openai.api_key,
            }
        elif provider == 'azure_openai':
            return {
                'provider': 'azure_openai',
                'model': self._config.azure_openai.deployment_name,
                'api_key': self._config.azure_openai.api_key,
                'azure_endpoint': self._config.azure_openai.endpoint,
                'azure_api_version': self._config.azure_openai.api_version,
            }
        
        return {'provider': 'ollama', 'model': 'qwen3:8b'}
    
    def print_config(self):
        """打印当前配置"""
        log.section("📋 当前配置")
        
        log.config("【分类器】")
        log.menu(f"  默认模式: {self._config.classifier.default_mode}")
        log.menu(f"  LLM提供商: {self._config.classifier.llm_provider}")
        log.menu(f"  LLM模型: {self._config.classifier.llm_model}")
        log.menu(f"  缓存: {'启用' if self._config.classifier.enable_cache else '禁用'}")
        log.menu(f"  并发数: {self._config.classifier.max_workers}")
        
        log.config("【数据采集】")
        log.menu(f"  产品数: {self._config.collector.product_count}")
        log.menu(f"  社区数: {self._config.collector.community_count}")
        log.menu(f"  领袖数: {self._config.collector.leader_count}")
        log.menu(f"  研究数: {self._config.collector.research_count}")
        log.menu(f"  开发者数: {self._config.collector.developer_count}")
        log.menu(f"  新闻数: {self._config.collector.news_count}")
        
        log.config("【Ollama】")
        log.menu(f"  地址: {self._config.ollama.base_url}")
        log.menu(f"  默认模型: {self._config.ollama.default_model}")
        
        log.config("【OpenAI】")
        log.menu(f"  API密钥: {'已设置 ✅' if self._config.openai.api_key else '未设置 ❌'}")
        log.menu(f"  默认模型: {self._config.openai.default_model}")
        
        log.config("【Azure OpenAI】")
        log.menu(f"  API密钥: {'已设置 ✅' if self._config.azure_openai.api_key else '未设置 ❌'}")
        log.menu(f"  端点: {'已设置 ✅' if self._config.azure_openai.endpoint else '未设置 ❌'}")
        log.menu(f"  部署名称: {self._config.azure_openai.deployment_name}")
        log.menu(f"  API版本: {self._config.azure_openai.api_version}")
        
        log.separator()
    
    def reload(self):
        """重新加载配置"""
        self._load_config()


# 全局配置实例（兼容旧的config_manager模块）
config = ConfigManager()


def get_config() -> ConfigManager:
    """获取配置管理器实例"""
    return ConfigManager()


def create_env_template():
    """创建.env模板文件"""
    template = """# AI World Tracker 配置文件
# 复制此文件为 .env 并填入你的配置

# ============ 分类器配置 ============
# 默认分类模式: rule (规则) 或 llm (大模型)
CLASSIFIER_MODE=rule

# LLM提供商: ollama / openai / azure_openai
LLM_PROVIDER=ollama

# LLM模型名称
LLM_MODEL=qwen3:8b

# 是否启用缓存
ENABLE_CACHE=true

# 并发工作线程数
MAX_WORKERS=3

# ============ Ollama配置 (本地免费) ============
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
OLLAMA_TIMEOUT=60

# ============ OpenAI配置 ============
# OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# ============ Azure OpenAI配置 ============
# 从Azure门户获取这些值: Azure OpenAI资源 -> 密钥和终结点
# AZURE_OPENAI_API_KEY=your-azure-openai-api-key
# AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
# AZURE_OPENAI_API_VERSION=2024-02-15-preview
"""
    
    env_example = Path('.env.example')
    with open(env_example, 'w', encoding='utf-8') as f:
        f.write(template)
    
    log.success(f"已创建配置模板: {env_example}")
    log.info("请复制为 .env 并填入你的配置")


if __name__ == "__main__":
    # 测试配置
    config = get_config()
    config.print_config()
    
    # 创建模板
    create_env_template()
