"""
LLM增强分类器 - LLM Classifier
使用大语言模型进行智能内容分类

支持的提供商:
- Ollama (本地): Qwen3:8b, Qwen3:4b, Llama3.2:3b
- OpenAI: GPT-4o-mini, GPT-4o
- Anthropic: Claude-3-Haiku, Claude-3-Sonnet

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
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum

# 导入规则分类器作为备份
from content_classifier import ContentClassifier


class LLMProvider(Enum):
    """LLM提供商枚举"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


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
    num_predict: int = 200
    num_ctx: int = 2048
    num_thread: int = 4
    num_gpu: int = 0  # 0表示自动，-1表示禁用GPU
    
    @classmethod
    def auto_configure(cls, gpu_info: GPUInfo) -> 'OllamaOptions':
        """根据GPU信息自动配置推理选项"""
        options = cls()
        
        if gpu_info.ollama_gpu_supported:
            # GPU加速配置
            options.num_gpu = 999  # 使用所有GPU层
            options.num_ctx = 4096  # GPU可以处理更大上下文
            options.num_predict = 300
            options.num_thread = 4  # GPU模式下CPU线程不需要太多
        else:
            # CPU模式优化配置
            options.num_gpu = 0  # 禁用GPU
            options.num_ctx = 1024  # 减少上下文以提升速度
            options.num_predict = 200
            # 根据CPU核心数设置线程
            try:
                import multiprocessing
                cpu_count = multiprocessing.cpu_count()
                options.num_thread = min(cpu_count, 8)  # 最多8线程
            except:
                options.num_thread = 4
        
        return options


# 预定义的模型配置
AVAILABLE_MODELS = {
    LLMProvider.OLLAMA: {
        'qwen3:8b': {'name': 'Qwen3 8B', 'description': '阿里通义千问，中文能力强，推荐使用'},
        'qwen3:4b': {'name': 'Qwen3 4B', 'description': '轻量模型，CPU友好'},
        'llama3.2:3b': {'name': 'Llama 3.2 3B', 'description': 'Meta轻量模型，速度最快'},
        'mistral:7b': {'name': 'Mistral 7B', 'description': '性能均衡，英文能力强'},
    },
    LLMProvider.OPENAI: {
        'gpt-4o-mini': {'name': 'GPT-4o Mini', 'description': '性价比高，推荐使用'},
        'gpt-4o': {'name': 'GPT-4o', 'description': '最强性能，成本较高'},
        'gpt-3.5-turbo': {'name': 'GPT-3.5 Turbo', 'description': '经济实惠'},
    },
    LLMProvider.ANTHROPIC: {
        'claude-3-haiku-20240307': {'name': 'Claude 3 Haiku', 'description': '快速响应，成本低'},
        'claude-3-sonnet-20240229': {'name': 'Claude 3 Sonnet', 'description': '平衡性能与成本'},
        'claude-3-5-sonnet-20241022': {'name': 'Claude 3.5 Sonnet', 'description': '最新最强'},
    }
}


class LLMClassifier:
    """LLM增强分类器"""
    
    def __init__(self, 
                 provider: str = 'ollama',
                 model: str = 'qwen3:8b',
                 api_key: Optional[str] = None,
                 enable_cache: bool = True,
                 max_workers: int = 3,
                 auto_detect_gpu: bool = True):
        """
        初始化LLM分类器
        
        Args:
            provider: 提供商 ('ollama', 'openai', 'anthropic')
            model: 模型名称
            api_key: API密钥（Ollama不需要）
            enable_cache: 是否启用缓存
            max_workers: 并发工作线程数
            auto_detect_gpu: 是否自动检测GPU并优化配置
        """
        self.provider = LLMProvider(provider)
        self.model = model
        self.api_key = api_key or self._get_api_key()
        self.enable_cache = enable_cache
        self.max_workers = max_workers
        
        # GPU检测与自适应配置
        self.gpu_info: Optional[GPUInfo] = None
        self.ollama_options: Optional[OllamaOptions] = None
        if auto_detect_gpu and self.provider == LLMProvider.OLLAMA:
            self._setup_gpu_acceleration()
        
        # 缓存
        self.cache: Dict[str, Dict] = {}
        self.cache_file = 'llm_classification_cache.json'
        self._load_cache()
        
        # 规则分类器（作为备份）
        self.rule_classifier = ContentClassifier()
        
        # 统计
        self.stats = {
            'total_calls': 0,
            'cache_hits': 0,
            'llm_calls': 0,
            'fallback_calls': 0,
            'errors': 0
        }
        
        # 验证配置
        self._validate_config()
        
        self._print_init_info()
    
    def _setup_gpu_acceleration(self):
        """设置GPU加速"""
        self.gpu_info = detect_gpu()
        self.ollama_options = OllamaOptions.auto_configure(self.gpu_info)
    
    def _print_init_info(self):
        """打印初始化信息"""
        print(f"🤖 LLM分类器初始化完成")
        print(f"   提供商: {self.provider.value}")
        print(f"   模型: {self.model}")
        print(f"   缓存: {'启用' if self.enable_cache else '禁用'}")
        
        if self.gpu_info:
            if self.gpu_info.ollama_gpu_supported:
                print(f"   🚀 GPU加速: 启用 ({self.gpu_info.gpu_name})")
                if self.gpu_info.vram_mb:
                    print(f"   显存: {self.gpu_info.vram_mb} MB")
            else:
                print(f"   💻 运行模式: CPU ({self.gpu_info.gpu_name or '未检测到GPU'})")
                if self.ollama_options:
                    print(f"   CPU线程: {self.ollama_options.num_thread}")
    
    def get_gpu_info(self) -> Optional[GPUInfo]:
        """获取GPU信息"""
        return self.gpu_info
    
    def _get_api_key(self) -> Optional[str]:
        """从环境变量获取API密钥"""
        if self.provider == LLMProvider.OPENAI:
            return os.getenv('OPENAI_API_KEY')
        elif self.provider == LLMProvider.ANTHROPIC:
            return os.getenv('ANTHROPIC_API_KEY')
        return None
    
    def _validate_config(self):
        """验证配置"""
        if self.provider == LLMProvider.OLLAMA:
            # 检查Ollama服务是否运行
            if not self._check_ollama_service():
                print("⚠️ Ollama服务未运行，请先启动: ollama serve")
        elif self.provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]:
            if not self.api_key:
                print(f"⚠️ 未设置 {self.provider.value.upper()}_API_KEY 环境变量")
    
    def _check_ollama_service(self) -> bool:
        """检查Ollama服务是否运行"""
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _load_cache(self):
        """加载缓存"""
        if not self.enable_cache:
            return
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"📦 已加载 {len(self.cache)} 条缓存")
        except Exception as e:
            print(f"⚠️ 加载缓存失败: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """保存缓存"""
        if not self.enable_cache:
            return
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存缓存失败: {e}")
    
    def _get_content_hash(self, item: Dict) -> str:
        """计算内容的MD5哈希"""
        content = f"{item.get('title', '')}|{item.get('summary', '')}|{item.get('source', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _build_classification_prompt(self, item: Dict) -> str:
        """构建分类提示词"""
        title = item.get('title', '')
        summary = item.get('summary', item.get('description', ''))[:500]
        source = item.get('source', '')
        
        prompt = f"""你是一个AI内容分类专家。请分析以下内容并进行分类。

【待分类内容】
标题: {title}
摘要: {summary}
来源: {source}

【分类任务】
1. 内容类型 (content_type): 从以下选项中选择一个
   - research: 学术研究、论文、技术报告
   - product: 产品发布、功能更新、新服务上线
   - market: 融资、收购、行业分析、政策法规
   - developer: 开源项目、SDK、开发工具、教程
   - leader: AI领袖言论、采访、演讲
   - community: 社区讨论、热点话题

2. 置信度 (confidence): 0.0-1.0之间的数值

3. 技术领域 (tech_fields): 可多选
   - NLP, Computer Vision, Generative AI, Reinforcement Learning, MLOps, AI Ethics, General AI

4. 内容可信度 (is_verified): true/false，是否为可信内容（非谣言/传闻）

5. 分类理由 (reasoning): 简短说明分类原因（20字以内）

【输出格式】
请严格按照JSON格式输出，不要包含其他内容:
{{"content_type": "xxx", "confidence": 0.xx, "tech_fields": ["xxx"], "is_verified": true, "reasoning": "xxx"}}"""
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用Ollama API
        
        支持两种模式:
        1. 对于 Qwen3 等支持 think 参数的模型，使用 Chat API + think=false 获得快速响应
        2. 对于其他模型，使用 Generate API 并解析 thinking 字段（如有）
        """
        try:
            import requests
            
            # 检测是否为支持 think 参数的模型（如 Qwen3）
            use_chat_api = 'qwen3' in self.model.lower()
            
            if use_chat_api:
                # 使用 Chat API + think=false 关闭思考模式，大幅提升速度
                # 根据GPU检测结果自适应配置
                options = self._get_ollama_options()
                
                response = requests.post(
                    'http://localhost:11434/api/chat',
                    json={
                        'model': self.model,
                        'messages': [
                            {'role': 'system', 'content': '你是一个专业的AI内容分类助手，请严格按照JSON格式输出分类结果。'},
                            {'role': 'user', 'content': prompt}
                        ],
                        'stream': False,
                        'think': False,  # 关闭思考模式
                        'options': options
                    },
                    timeout=60 if self.gpu_info and self.gpu_info.ollama_gpu_supported else 90
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message = result.get('message', {})
                    return message.get('content', '')
            else:
                # 使用 Generate API（适用于其他模型）
                options = self._get_ollama_options()
                
                response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': self.model,
                        'prompt': prompt,
                        'stream': False,
                        'options': options
                    },
                    timeout=120 if self.gpu_info and self.gpu_info.ollama_gpu_supported else 180
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 部分模型使用 thinking 字段存储思考过程
                    response_text = result.get('response', '')
                    thinking_text = result.get('thinking', '')
                    
                    # 如果 response 为空但 thinking 有内容，从 thinking 中提取
                    if not response_text.strip() and thinking_text:
                        return thinking_text
                    
                    return response_text
            
            print(f"⚠️ Ollama API错误: {response.status_code}")
            return None
                
        except Exception as e:
            print(f"⚠️ Ollama调用失败: {e}")
            return None
    
    def _get_ollama_options(self) -> Dict:
        """获取Ollama推理选项（根据GPU自适应配置）"""
        if self.ollama_options:
            return {
                'temperature': self.ollama_options.temperature,
                'num_predict': self.ollama_options.num_predict,
                'num_ctx': self.ollama_options.num_ctx,
                'num_thread': self.ollama_options.num_thread,
                'num_gpu': self.ollama_options.num_gpu
            }
        else:
            # 默认配置
            return {
                'temperature': 0.1,
                'num_predict': 200,
                'num_ctx': 1024,
                'num_thread': 4
            }
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """调用OpenAI API"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的AI内容分类助手，请严格按照JSON格式输出分类结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"⚠️ OpenAI调用失败: {e}")
            return None
    
    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """调用Anthropic API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"⚠️ Anthropic调用失败: {e}")
            return None
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """调用LLM（根据提供商选择）"""
        if self.provider == LLMProvider.OLLAMA:
            return self._call_ollama(prompt)
        elif self.provider == LLMProvider.OPENAI:
            return self._call_openai(prompt)
        elif self.provider == LLMProvider.ANTHROPIC:
            return self._call_anthropic(prompt)
        return None
    
    def _parse_llm_response(self, response: str) -> Optional[Dict]:
        """解析LLM响应
        
        支持两种格式:
        1. JSON格式: {"content_type": "xxx", ...}
        2. 纯文本格式: 直接返回类别名称（用于 thinking 模式的模型）
        """
        if not response:
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
                    result['tech_fields'] = result.get('tech_fields', ['General AI'])
                    result['is_verified'] = result.get('is_verified', True)
                    result['reasoning'] = result.get('reasoning', '')
                    
                    return result
            
            # JSON解析失败，尝试从文本中提取类别（支持 thinking 模式的模型）
            return self._extract_category_from_text(response)
            
        except json.JSONDecodeError as e:
            # JSON解析失败，尝试从文本中提取类别
            return self._extract_category_from_text(response)
        except Exception as e:
            print(f"⚠️ 响应解析失败: {e}")
        
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
            分类后的内容项
        """
        self.stats['total_calls'] += 1
        
        classified = item.copy()
        content_hash = self._get_content_hash(item)
        
        # 检查缓存
        if use_cache and self.enable_cache and content_hash in self.cache:
            self.stats['cache_hits'] += 1
            cached = self.cache[content_hash]
            classified.update(cached)
            classified['from_cache'] = True
            return classified
        
        # 调用LLM
        prompt = self._build_classification_prompt(item)
        response = self._call_llm(prompt)
        result = self._parse_llm_response(response)
        
        if result:
            self.stats['llm_calls'] += 1
            
            # 更新分类结果
            classified['content_type'] = result['content_type']
            classified['confidence'] = result['confidence']
            classified['tech_categories'] = result['tech_fields']
            classified['is_verified'] = result['is_verified']
            classified['llm_reasoning'] = result['reasoning']
            classified['classified_by'] = f"llm:{self.provider.value}/{self.model}"
            classified['classified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 使用规则分类器补充地区信息
            classified['region'] = self.rule_classifier.classify_region(item)
            
            # 保存到缓存
            if self.enable_cache:
                self.cache[content_hash] = {
                    'content_type': classified['content_type'],
                    'confidence': classified['confidence'],
                    'tech_categories': classified['tech_categories'],
                    'is_verified': classified['is_verified'],
                    'llm_reasoning': classified['llm_reasoning'],
                    'region': classified['region']
                }
        else:
            # LLM失败，降级到规则分类
            self.stats['fallback_calls'] += 1
            self.stats['errors'] += 1
            
            print(f"⚠️ LLM分类失败，降级到规则分类: {item.get('title', '')[:30]}...")
            classified = self.rule_classifier.classify_item(item)
            classified['classified_by'] = 'rule:fallback'
        
        return classified
    
    def classify_batch(self, items: List[Dict], show_progress: bool = True) -> List[Dict]:
        """
        批量分类
        
        Args:
            items: 内容项列表
            show_progress: 是否显示进度
            
        Returns:
            分类后的内容项列表
        """
        total = len(items)
        print(f"\n🤖 开始LLM批量分类 ({total} 条内容)")
        print(f"   提供商: {self.provider.value} | 模型: {self.model}")
        print(f"   并发数: {self.max_workers} | 缓存: {'启用' if self.enable_cache else '禁用'}")
        
        start_time = time.time()
        classified_items = []
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.classify_item, item): i for i, item in enumerate(items)}
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    classified_items.append((futures[future], result))
                    completed += 1
                    
                    if show_progress and completed % 5 == 0:
                        print(f"   进度: {completed}/{total} ({completed/total:.0%})")
                        
                except Exception as e:
                    print(f"⚠️ 分类任务失败: {e}")
                    self.stats['errors'] += 1
        
        # 按原顺序排序
        classified_items.sort(key=lambda x: x[0])
        classified_items = [item for _, item in classified_items]
        
        # 保存缓存
        self._save_cache()
        
        # 统计
        elapsed = time.time() - start_time
        self._print_stats(elapsed)
        
        return classified_items
    
    def _print_stats(self, elapsed: float):
        """打印统计信息"""
        print(f"\n📊 分类统计:")
        print(f"   总请求: {self.stats['total_calls']}")
        print(f"   缓存命中: {self.stats['cache_hits']} ({self.stats['cache_hits']/max(1,self.stats['total_calls']):.0%})")
        print(f"   LLM调用: {self.stats['llm_calls']}")
        print(f"   规则降级: {self.stats['fallback_calls']}")
        print(f"   错误数: {self.stats['errors']}")
        print(f"   耗时: {elapsed:.1f}秒")
        
        if self.stats['llm_calls'] > 0:
            avg_time = elapsed / self.stats['llm_calls']
            print(f"   平均每条: {avg_time:.1f}秒")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def clear_cache(self):
        """清空缓存"""
        self.cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        print("🗑️ 缓存已清空")


def select_llm_provider() -> Tuple[str, str]:
    """
    交互式选择LLM提供商和模型
    
    Returns:
        (provider, model)
    """
    print("\n" + "="*60)
    print("🤖 选择LLM提供商")
    print("="*60)
    
    print("\n可用的提供商:")
    print("  1. Ollama (本地免费) ⭐ 推荐")
    print("  2. OpenAI (需要API密钥)")
    print("  3. Anthropic (需要API密钥)")
    
    provider_choice = input("\n请选择提供商 (1-3) [默认: 1]: ").strip() or '1'
    
    provider_map = {'1': 'ollama', '2': 'openai', '3': 'anthropic'}
    provider = provider_map.get(provider_choice, 'ollama')
    
    # 选择模型
    print(f"\n可用的 {provider.upper()} 模型:")
    
    provider_enum = LLMProvider(provider)
    models = AVAILABLE_MODELS.get(provider_enum, {})
    
    model_list = list(models.keys())
    for i, (model_id, info) in enumerate(models.items(), 1):
        recommended = " ⭐" if i == 1 else ""
        print(f"  {i}. {info['name']}{recommended}")
        print(f"     {info['description']}")
    
    model_choice = input(f"\n请选择模型 (1-{len(model_list)}) [默认: 1]: ").strip() or '1'
    
    try:
        model_idx = int(model_choice) - 1
        model = model_list[model_idx] if 0 <= model_idx < len(model_list) else model_list[0]
    except:
        model = model_list[0]
    
    print(f"\n✅ 已选择: {provider} / {model}")
    
    return provider, model


def get_available_ollama_models() -> List[str]:
    """获取本地可用的Ollama模型列表"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
    except:
        pass
    return []


def check_ollama_status() -> Dict:
    """检查Ollama服务状态"""
    result = {
        'running': False,
        'models': [],
        'recommended': None
    }
    
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            result['running'] = True
            data = response.json()
            result['models'] = [model['name'] for model in data.get('models', [])]
            
            # 推荐模型优先级
            preferred = ['qwen3:8b', 'qwen3:4b', 'llama3.2:3b', 'mistral:7b']
            for model in preferred:
                if model in result['models']:
                    result['recommended'] = model
                    break
            
            if not result['recommended'] and result['models']:
                result['recommended'] = result['models'][0]
                
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
        
        # 检查Anthropic
        if os.getenv('ANTHROPIC_API_KEY'):
            return LLMClassifier(provider='anthropic', model='claude-3-haiku-20240307')
        
        print("⚠️ 未找到可用的LLM服务，将使用规则分类")
        return None
    else:
        # 交互式选择
        provider, model = select_llm_provider()
        return LLMClassifier(provider=provider, model=model)


if __name__ == "__main__":
    # 测试代码
    print("="*60)
    print("LLM分类器测试")
    print("="*60)
    
    # 检查Ollama状态
    status = check_ollama_status()
    print(f"\nOllama状态: {'运行中 ✅' if status['running'] else '未运行 ❌'}")
    if status['models']:
        print(f"可用模型: {', '.join(status['models'])}")
        print(f"推荐模型: {status['recommended']}")
    
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
        
        print(f"\n测试内容: {test_item['title']}")
        result = classifier.classify_item(test_item)
        
        print(f"\n分类结果:")
        print(f"  类型: {result.get('content_type')}")
        print(f"  置信度: {result.get('confidence', 0):.1%}")
        print(f"  技术领域: {result.get('tech_categories')}")
        print(f"  可信: {result.get('is_verified')}")
        print(f"  理由: {result.get('llm_reasoning')}")
    else:
        print("\n⚠️ 请先启动Ollama服务: ollama serve")
