"""直接测试 Ollama API - 跳过封装层"""
import requests
import json
import time

print("=" * 60)
print("直接测试 Ollama API with deepseek-r1:8b")
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
                'num_predict': 50  # 限制生成的token数量
            }
        },
        timeout=300  # 5分钟超时
    )
    
    elapsed = time.time() - start_time
    print(f"⏱️ Response received in {elapsed:.2f} seconds")
    
    if response.status_code == 200:
        result = response.json()
        llm_response = result.get('response', '').strip()
        
        print(f"\n✅ SUCCESS!")
        print(f"📊 LLM Response: {llm_response[:200]}")
        
        # 显示性能统计
        total_duration = result.get('total_duration', 0) / 1e9
        load_duration = result.get('load_duration', 0) / 1e9
        prompt_eval_duration = result.get('prompt_eval_duration', 0) / 1e9
        eval_duration = result.get('eval_duration', 0) / 1e9
        eval_count = result.get('eval_count', 0)
        
        print(f"\n📈 Performance Stats:")
        print(f"   Total Duration: {total_duration:.2f}s")
        print(f"   Model Load: {load_duration:.2f}s")
        print(f"   Prompt Eval: {prompt_eval_duration:.2f}s")
        print(f"   Generation: {eval_duration:.2f}s")
        print(f"   Tokens Generated: {eval_count}")
        
    else:
        print(f"\n❌ HTTP Error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.Timeout:
    elapsed = time.time() - start_time
    print(f"\n⏰ TIMEOUT after {elapsed:.2f} seconds")
    print("模型可能需要更长时间加载，请确保 Ollama 服务正在运行")
    
except requests.exceptions.ConnectionError:
    print("\n🔌 CONNECTION ERROR - Ollama 服务未运行")
    print("请运行: ollama serve")
    
except Exception as e:
    elapsed = time.time() - start_time
    print(f"\n❌ Error after {elapsed:.2f}s: {type(e).__name__}: {e}")
