import os
import yaml

class ConfigManager:
    """全局配置管理器，支持YAML加载与属性访问"""
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get(self, key_path, default=None):
        """支持点号路径访问，如 collector.product_count"""
        keys = key_path.split('.')
        val = self.config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def reload(self):
        self.config = self._load_config()

# 全局单例
config = ConfigManager()
