"""
配置管理模块测试

测试ConfigManager的配置加载、环境变量、默认值等功能
"""

import sys
import os
import pytest
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ConfigManager, OllamaConfig, AzureOpenAIConfig, ClassifierConfig


class TestConfigManager:
    """配置管理器测试"""
    
    @pytest.fixture
    def config_manager(self):
        """创建配置管理器实例"""
        return ConfigManager()
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        cm1 = ConfigManager()
        cm2 = ConfigManager()
        assert cm1 is cm2
        print("✅ 配置管理器单例模式正常")
    
    def test_default_config_loading(self, config_manager):
        """测试默认配置加载"""
        config = config_manager.config
        
        assert config is not None
        assert hasattr(config, 'ollama')
        assert hasattr(config, 'azure_openai')
        assert hasattr(config, 'classifier')
        
        print("✅ 默认配置加载正常")
    
    def test_ollama_config(self, config_manager):
        """测试Ollama配置"""
        ollama = config_manager.config.ollama
        
        assert isinstance(ollama, OllamaConfig)
        assert ollama.base_url
        assert ollama.default_model
        assert ollama.timeout > 0
        
        print(f"✅ Ollama配置正常: {ollama.base_url}, {ollama.default_model}")
    
    def test_classifier_config(self, config_manager):
        """测试分类器配置"""
        classifier = config_manager.config.classifier
        
        assert isinstance(classifier, ClassifierConfig)
        assert classifier.default_mode in ['llm', 'rule']
        assert classifier.max_workers > 0
        
        print(f"✅ 分类器配置正常: mode={classifier.default_mode}")
    
    def test_get_llm_config(self, config_manager):
        """测试获取LLM配置"""
        llm_config = config_manager.get_llm_config()
        
        assert isinstance(llm_config, dict)
        assert 'provider' in llm_config
        assert 'model' in llm_config
        
        print(f"✅ LLM配置获取正常: {llm_config.get('provider')}")
    
    def test_config_reload(self, config_manager):
        """测试配置重载"""
        original_model = config_manager.config.ollama.default_model
        
        # 重载配置
        config_manager.reload()
        
        # 验证配置仍然有效
        assert config_manager.config.ollama.default_model == original_model
        
        print("✅ 配置重载功能正常")


class TestConfigDataclasses:
    """配置数据类测试"""
    
    def test_ollama_config_creation(self):
        """测试Ollama配置创建"""
        config = OllamaConfig()
        
        assert config.base_url == "http://localhost:11434"
        assert config.timeout == 60
        assert config.temperature == 0.1
        
        print("✅ OllamaConfig默认值正确")
    
    def test_azure_openai_config_creation(self):
        """测试Azure OpenAI配置创建"""
        config = AzureOpenAIConfig()
        
        assert config.deployment_name == "gpt-4o-mini"
        assert config.timeout == 30
        assert config.temperature == 0.1
        assert config.api_version == "2024-02-15-preview"
        
        print("✅ AzureOpenAIConfig默认值正确")
    
    def test_classifier_config_creation(self):
        """测试分类器配置创建"""
        config = ClassifierConfig()
        
        assert config.default_mode == "rule"
        assert config.enable_cache is True
        assert config.max_workers == 3
        
        print("✅ ClassifierConfig默认值正确")


class TestConfigIntegration:
    """配置集成测试"""
    
    @pytest.fixture
    def config_manager(self):
        return ConfigManager()
    
    def test_config_manager_consistency(self, config_manager):
        """测试配置管理器一致性"""
        # 多次获取配置应该返回相同对象
        config1 = config_manager.config
        config2 = config_manager.config
        
        assert config1 is config2
        
        print("✅ 配置对象一致性正常")
    
    def test_config_values_valid(self, config_manager):
        """测试配置值的有效性"""
        config = config_manager.config
        
        # 验证Ollama配置
        assert config.ollama.timeout > 0
        assert config.ollama.num_predict > 0
        assert 0 <= config.ollama.temperature <= 2
        
        # 验证分类器配置
        assert config.classifier.max_workers > 0
        
        print("✅ 所有配置值均在有效范围内")


if __name__ == '__main__':
    print("\n" + "🌟" * 30)
    print("   配置管理模块测试")
    print("🌟" * 30)
    
    # 运行测试
    pytest.main([__file__, '-v', '-s'])
