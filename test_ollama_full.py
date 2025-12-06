"""直接测试 Ollama API - 查看完整响应"""
import requests
import json
import time

print("=" * 60)
print("直接测试 Ollama API with deepseek-r1:8b (完整响应)")
print("=" * 60)

# 简单的分类提示
prompt = """Classify this AI news into one category: llm, vision, robotics, research, industry, tools, ethics.

Title: OpenAI releases GPT-5
Content: OpenAI announced GPT-5 with advanced reasoning.

Reply with only the category name."""

print(f"\n📝 Prompt length: {len(prompt)} chars")
print(f"🚀 Sending request to Ollama...")

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
                'num_predict': 200  # 增加生成的token数量
            }
        },
        timeout=300
    )
    
    elapsed = time.time() - start_time
    print(f"⏱️ Response received in {elapsed:.2f} seconds")
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ SUCCESS!")
        print(f"\n📊 完整响应 JSON keys: {list(result.keys())}")
        
        # 打印完整响应内容
        llm_response = result.get('response', '')
        print(f"\n📝 Response 长度: {len(llm_response)} chars")
        print(f"\n📝 Response 内容 (repr):")
        print(repr(llm_response[:500]))
        
        print(f"\n📝 Response 内容 (显示):")
        print(llm_response[:500] if llm_response else "(空)")
        
        # 显示性能统计
        total_duration = result.get('total_duration', 0) / 1e9
        eval_count = result.get('eval_count', 0)
        
        print(f"\n📈 Performance Stats:")
        print(f"   Total Duration: {total_duration:.2f}s")
        print(f"   Tokens Generated: {eval_count}")
        
    else:
        print(f"\n❌ HTTP Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    elapsed = time.time() - start_time
    print(f"\n❌ Error after {elapsed:.2f}s: {type(e).__name__}: {e}")
