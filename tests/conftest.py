"""
pytest配置文件 - 提供测试隔离和共享fixtures

确保测试之间不会相互影响，特别是缓存数据的隔离
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="function")
def isolated_cache_dir(tmp_path, monkeypatch):
    """为每个测试提供隔离的缓存目录
    
    这样测试之间不会共享缓存数据，避免相互影响
    """
    # 创建临时缓存目录
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    # 使用monkeypatch替换环境变量或配置
    monkeypatch.setenv("AI_TRACKER_CACHE_DIR", str(cache_dir))
    
    yield cache_dir
    
    # 测试结束后清理（pytest会自动清理tmp_path）


@pytest.fixture(scope="function")
def clean_learning_data(tmp_path, monkeypatch):
    """为每个测试提供干净的学习数据环境
    
    确保ImportanceEvaluator的学习数据不会在测试间共享
    """
    learning_file = tmp_path / "importance_learning.json"
    
    # 可以通过monkeypatch修改ImportanceEvaluator读取的路径
    # 这需要ImportanceEvaluator支持配置文件路径
    
    yield learning_file
    
    # 清理
    if learning_file.exists():
        learning_file.unlink()


@pytest.fixture(scope="session")
def test_data_dir():
    """提供测试数据目录"""
    test_dir = Path(__file__).parent
    data_dir = test_dir / "test_data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture(autouse=True)
def reset_singleton_instances():
    """在每个测试前重置单例实例
    
    如果有使用单例模式的类，在这里重置它们
    """
    # 例如：如果ImportanceEvaluator是单例，可以在这里重置
    yield
    # 测试后清理


@pytest.fixture
def sample_ai_items():
    """提供样本AI数据项用于测试"""
    return [
        {
            'title': 'OpenAI Announces GPT-5',
            'summary': 'Major breakthrough in AI reasoning',
            'source': 'openai.com',
            'url': 'https://openai.com/blog/gpt-5',
            'published': '2025-12-07',
            'category': 'product'
        },
        {
            'title': 'New Transformer Architecture',
            'summary': 'Research paper on efficient attention',
            'source': 'arxiv.org',
            'url': 'https://arxiv.org/abs/2512.xxxxx',
            'published': '2025-12-06',
            'category': 'research'
        },
        {
            'title': 'AI Weekly Roundup',
            'summary': 'Summary of AI news this week',
            'source': 'generic-news.com',
            'url': 'https://news.com/ai-roundup',
            'published': '2025-12-05',
            'category': 'news'
        }
    ]


@pytest.fixture
def mock_rss_feeds():
    """提供模拟的RSS源配置"""
    return {
        'research': [
            {'name': 'Test ArXiv', 'url': 'http://example.com/arxiv.xml'},
        ],
        'product': [
            {'name': 'Test Blog', 'url': 'http://example.com/blog.xml'},
        ]
    }


# 配置pytest选项
def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "async_test: marks tests that test async functionality"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集行为"""
    # 可以根据标记自动跳过某些测试
    pass
