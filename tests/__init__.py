"""
Tests Package - AI World Tracker 测试模块
==========================================

测试文件组织结构:
- test_classifier_*.py: 分类器相关测试
- test_llm_*.py: LLM分类器测试
- test_ollama_*.py: Ollama服务测试
- test_qwen3_*.py: Qwen3模型测试
- test_workflow.py: 工作流程测试
- test_cache.py: 缓存测试
- test_gpu_detection.py: GPU检测测试

运行所有测试:
    pytest tests/ -v

运行特定测试:
    pytest tests/test_classifier_advanced.py -v
"""

import sys
import os

# 添加父目录到路径，以便导入主模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
