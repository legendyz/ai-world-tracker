"""
测试LLM分类器功能
"""
import sys

def test_llm_classifier():
    """测试LLM分类器"""
    print("="*60)
    print("🧪 LLM分类器功能测试")
    print("="*60)
    
    # 1. 测试导入
    print("\n【1】测试模块导入...")
    try:
        from llm_classifier import (
            LLMClassifier, 
            check_ollama_status, 
            AVAILABLE_MODELS,
            LLMProvider
        )
        print("   ✅ llm_classifier 导入成功")
    except ImportError as e:
        print(f"   ❌ 导入失败: {e}")
        assert False, f"llm_classifier 导入失败: {e}"
    
    try:
        from config import ConfigManager, get_config
        print("   ✅ config 导入成功")
    except ImportError as e:
        print(f"   ❌ 导入失败: {e}")
    
    # 2. 检查Ollama状态
    print("\n【2】检查Ollama服务状态...")
    status = check_ollama_status()
    
    if status['running']:
        print(f"   ✅ Ollama服务运行中")
        print(f"   📦 可用模型: {', '.join(status['models'])}")
        print(f"   ⭐ 推荐模型: {status['recommended']}")
    else:
        print("   ⚠️ Ollama服务未运行")
        print("   请启动Ollama: ollama serve")
        assert False, "Ollama 服务未运行"
    
    # 3. 测试分类器初始化
    print("\n【3】测试分类器初始化...")
    try:
        classifier = LLMClassifier(
            provider='ollama',
            model=status['recommended'] or 'deepseek-r1:8b',
            enable_cache=True
        )
        print(f"   ✅ 分类器初始化成功")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        assert False, f"分类器初始化失败: {e}"
    
    # 4. 测试单条分类
    print("\n【4】测试单条内容分类...")
    test_items = [
        {
            'title': 'OpenAI officially launches GPT-4o with new features',
            'summary': 'OpenAI announces the general availability of GPT-4o model',
            'source': 'TechCrunch',
            'expected': 'product'
        },
        {
            'title': 'We propose a novel approach for chain-of-thought reasoning',
            'summary': 'Our method achieves state-of-the-art results on benchmark',
            'source': 'arXiv',
            'expected': 'research'
        },
        {
            'title': 'AI startup raises $100 million in Series B funding',
            'summary': 'The company is now valued at $1 billion',
            'source': '36kr',
            'expected': 'market'
        },
    ]
    
    correct = 0
    for i, item in enumerate(test_items, 1):
        expected = item.pop('expected')
        
        print(f"\n   测试 {i}: {item['title'][:40]}...")
        
        try:
            result = classifier.classify_item(item)
            actual = result.get('content_type', 'unknown')
            confidence = result.get('confidence', 0)
            reasoning = result.get('llm_reasoning', '')
            
            is_correct = actual == expected
            status_icon = "✅" if is_correct else "❌"
            
            if is_correct:
                correct += 1
            
            print(f"   {status_icon} 分类: {actual} (预期: {expected})")
            print(f"      置信度: {confidence:.1%}")
            if reasoning:
                print(f"      理由: {reasoning}")
                
        except Exception as e:
            print(f"   ❌ 分类失败: {e}")
    
    # 5. 显示统计
    print("\n" + "="*60)
    print(f"📊 测试结果: {correct}/{len(test_items)} 通过")
    
    stats = classifier.get_stats()
    print(f"\n📈 分类器统计:")
    print(f"   总请求: {stats['total_calls']}")
    print(f"   缓存命中: {stats['cache_hits']}")
    print(f"   LLM调用: {stats['llm_calls']}")
    print(f"   规则降级: {stats['fallback_calls']}")
    
    print("="*60)
    
    assert correct == len(test_items), f"分类测试失败: {correct}/{len(test_items)} 通过"


def test_main_program_integration():
    """测试主程序集成"""
    print("\n" + "="*60)
    print("🧪 主程序集成测试")
    print("="*60)
    
    try:
        from TheWorldOfAI import AIWorldTracker, LLM_AVAILABLE
        print(f"   ✅ 主程序导入成功")
        print(f"   LLM可用: {'是' if LLM_AVAILABLE else '否'}")
        
        # 创建实例（不运行完整流程）
        # tracker = AIWorldTracker()
        # print(f"   ✅ Tracker实例创建成功")
        
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        assert False, f"主程序导入失败: {e}"


if __name__ == "__main__":
    print("\n" + "🔬"*30)
    print("      AI World Tracker - LLM功能测试")
    print("🔬"*30 + "\n")
    
    # 运行测试
    llm_test_passed = test_llm_classifier()
    integration_test_passed = test_main_program_integration()
    
    # 总结
    print("\n" + "="*60)
    print("📋 测试总结")
    print("="*60)
    print(f"   LLM分类器测试: {'✅ 通过' if llm_test_passed else '❌ 失败'}")
    print(f"   主程序集成测试: {'✅ 通过' if integration_test_passed else '❌ 失败'}")
    print("="*60)
