"""
配置管理模块 - Config Manager
统一管理LLM和应用配置

优先级: 环境变量 > .env文件 > 默认值
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


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
class AnthropicConfig:
    """Anthropic配置"""
    api_key: Optional[str] = None
    default_model: str = "claude-3-haiku-20240307"
    timeout: int = 30
    max_tokens: int = 300


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
class AppConfig:
    """应用总配置"""
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    classifier: ClassifierConfig = field(default_factory=ClassifierConfig)
    
    # 数据采集配置
    collect_max_items: int = 15
    collect_timeout: int = 30
    
    # 输出配置
    output_dir: str = "."
    web_output_dir: str = "web_output"
    visualization_dir: str = "visualizations"


class ConfigManager:
    """配置管理器"""
    
    _instance = None
    _config: AppConfig = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载配置"""
        # 尝试加载.env文件
        self._load_env_file()
        
        # 创建配置对象
        self._config = AppConfig(
            ollama=OllamaConfig(
                base_url=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
                default_model=os.getenv('OLLAMA_MODEL', 'qwen3:8b'),
                timeout=int(os.getenv('OLLAMA_TIMEOUT', '60')),
            ),
            openai=OpenAIConfig(
                api_key=os.getenv('OPENAI_API_KEY'),
                default_model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            ),
            anthropic=AnthropicConfig(
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                default_model=os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            ),
            classifier=ClassifierConfig(
                default_mode=os.getenv('CLASSIFIER_MODE', 'rule'),
                llm_provider=os.getenv('LLM_PROVIDER', 'ollama'),
                llm_model=os.getenv('LLM_MODEL', 'qwen3:8b'),
                enable_cache=os.getenv('ENABLE_CACHE', 'true').lower() == 'true',
                max_workers=int(os.getenv('MAX_WORKERS', '3')),
            ),
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
                print(f"⚠️ 加载.env文件失败: {e}")
    
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
        elif provider == 'anthropic':
            return {
                'provider': 'anthropic',
                'model': model,
                'api_key': self._config.anthropic.api_key,
            }
        
        return {'provider': 'ollama', 'model': 'qwen3:8b'}
    
    def print_config(self):
        """打印当前配置"""
        print("\n" + "="*60)
        print("📋 当前配置")
        print("="*60)
        
        print(f"\n【分类器】")
        print(f"  默认模式: {self._config.classifier.default_mode}")
        print(f"  LLM提供商: {self._config.classifier.llm_provider}")
        print(f"  LLM模型: {self._config.classifier.llm_model}")
        print(f"  缓存: {'启用' if self._config.classifier.enable_cache else '禁用'}")
        print(f"  并发数: {self._config.classifier.max_workers}")
        
        print(f"\n【Ollama】")
        print(f"  地址: {self._config.ollama.base_url}")
        print(f"  默认模型: {self._config.ollama.default_model}")
        
        print(f"\n【OpenAI】")
        print(f"  API密钥: {'已设置 ✅' if self._config.openai.api_key else '未设置 ❌'}")
        print(f"  默认模型: {self._config.openai.default_model}")
        
        print(f"\n【Anthropic】")
        print(f"  API密钥: {'已设置 ✅' if self._config.anthropic.api_key else '未设置 ❌'}")
        print(f"  默认模型: {self._config.anthropic.default_model}")
        
        print("="*60)


# 全局配置实例
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

# LLM提供商: ollama / openai / anthropic
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

# ============ Anthropic配置 ============
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-haiku-20240307
"""
    
    env_example = Path('.env.example')
    with open(env_example, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"✅ 已创建配置模板: {env_example}")
    print("   请复制为 .env 并填入你的配置")


if __name__ == "__main__":
    # 测试配置
    config = get_config()
    config.print_config()
    
    # 创建模板
    create_env_template()
