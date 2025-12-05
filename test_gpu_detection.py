"""测试 GPU 自动检测与自适应配置"""
from llm_classifier import detect_gpu, LLMClassifier, OllamaOptions
import time

print("=" * 60)
print("🔍 GPU 检测与自适应配置测试")
print("=" * 60)

# 1. 独立测试GPU检测
print("\n📊 GPU 检测结果:")
gpu_info = detect_gpu()
print(f"   GPU可用: {gpu_info.available}")
print(f"   GPU类型: {gpu_info.gpu_type}")
print(f"   GPU名称: {gpu_info.gpu_name}")
print(f"   显存: {gpu_info.vram_mb} MB")
print(f"   驱动版本: {gpu_info.driver_version}")
print(f"   CUDA支持: {gpu_info.cuda_available}")
print(f"   ROCm支持: {gpu_info.rocm_available}")
print(f"   Metal支持: {gpu_info.metal_available}")
print(f"   Ollama GPU支持: {gpu_info.ollama_gpu_supported}")

# 2. 测试自适应配置
print("\n⚙️ 自适应配置:")
options = OllamaOptions.auto_configure(gpu_info)
print(f"   num_gpu: {options.num_gpu}")
print(f"   num_ctx: {options.num_ctx}")
print(f"   num_predict: {options.num_predict}")
print(f"   num_thread: {options.num_thread}")
print(f"   temperature: {options.temperature}")

# 3. 测试 LLM 分类器初始化
print("\n" + "=" * 60)
print("🤖 初始化 LLM 分类器 (自动检测GPU)")
print("=" * 60)

classifier = LLMClassifier(
    provider='ollama',
    model='qwen3:8b',
    enable_cache=True,
    auto_detect_gpu=True
)

# 4. 测试分类
print("\n" + "=" * 60)
print("📝 测试分类")
print("=" * 60)

test_item = {
    'title': 'OpenAI releases GPT-5 with breakthrough capabilities',
    'summary': 'OpenAI announces GPT-5 featuring advanced reasoning and multimodal understanding',
    'source': 'TechCrunch'
}

start = time.time()
result = classifier.classify_item(test_item)
elapsed = time.time() - start

print(f"\n   类别: {result.get('content_type')}")
print(f"   置信度: {result.get('confidence', 0):.0%}")
print(f"   耗时: {elapsed:.1f}s")
print(f"   分类器: {result.get('classified_by')}")

# 5. 显示最终配置信息
print("\n" + "=" * 60)
print("📋 配置总结")
print("=" * 60)
if classifier.gpu_info:
    if classifier.gpu_info.ollama_gpu_supported:
        print("   ✅ GPU加速已启用")
        print(f"   🚀 使用 {classifier.gpu_info.gpu_name}")
    else:
        print("   💻 CPU模式运行")
        print(f"   ℹ️  GPU ({classifier.gpu_info.gpu_name}) 不受 Ollama 支持")
        print(f"   优化: 多线程={classifier.ollama_options.num_thread}, 上下文={classifier.ollama_options.num_ctx}")
