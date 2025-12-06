"""测试 Ollama API - 处理 DeepSeek R1 的 thinking 字段"""
import requests
import json
import time
import re

print("=" * 60)
print("测试 DeepSeek R1:8b 的 thinking 模式")
print("=" * 60)

# 简单的分类提示
prompt = """Classify this AI news into one category: llm, vision, robotics, research, industry, tools, ethics.

Title: OpenAI releases GPT-5
Content: OpenAI announced GPT-5 with advanced reasoning.

Reply with only the category name."""

print(f"\n🚀 Sending request to Ollama...")

start_time = time.time()

try:
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'deepseek-r1:8b',
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.1,
                'num_predict': 300
            }
        },
        timeout=300
    )
    
    elapsed = time.time() - start_time
    print(f"⏱️ Response received in {elapsed:.2f} seconds")
    
    if response.status_code == 200:
        result = response.json()
        
        # DeepSeek R1 使用 thinking 字段存储思考过程
        thinking = result.get('thinking', '')
        response_text = result.get('response', '')
        
        print(f"\n📊 Thinking 长度: {len(thinking)} chars")
        print(f"📊 Response 长度: {len(response_text)} chars")
        
        print(f"\n💭 Thinking 内容:")
        print("-" * 40)
        print(thinking[:1000] if thinking else "(空)")
        print("-" * 40)
        
        print(f"\n📝 Response 内容:")
        print("-" * 40)
        print(response_text if response_text else "(空)")
        print("-" * 40)
        
        # 尝试从 thinking 或 response 中提取类别
        full_text = (thinking + "\n" + response_text).lower()
        categories = ['llm', 'vision', 'robotics', 'research', 'industry', 'tools', 'ethics']
        
        found_category = None
        for cat in categories:
            if cat in full_text:
                found_category = cat
                break
        
        print(f"\n🎯 提取的类别: {found_category or '未找到'}")
        
        # 显示性能统计
        print(f"\n📈 Performance Stats:")
        print(f"   Total Duration: {result.get('total_duration', 0) / 1e9:.2f}s")
        print(f"   Tokens Generated: {result.get('eval_count', 0)}")
        
    else:
        print(f"\n❌ HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
