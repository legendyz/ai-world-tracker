"""直接测试 Qwen3:8b 的 no_think 模式"""
import requests
import time

print("=" * 60)
print("测试 Qwen3:8b no_think 模式")
print("=" * 60)

prompt = """Classify this AI news. Reply with only the category name (llm, vision, robotics, research, industry, tools, ethics):

Title: OpenAI releases GPT-5
Content: OpenAI announced GPT-5 with advanced reasoning.

Category: /no_think"""

print(f"\n🚀 发送请求...")

start = time.time()

response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'qwen3:8b',
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': 0.1,
            'num_predict': 50
        }
    },
    timeout=300
)

elapsed = time.time() - start

if response.status_code == 200:
    result = response.json()
    
    thinking = result.get('thinking', '')
    response_text = result.get('response', '')
    
    print(f"\n⏱️ 耗时: {elapsed:.1f}s")
    print(f"📊 Thinking 长度: {len(thinking)} chars")
    print(f"📊 Response 长度: {len(response_text)} chars")
    
    if thinking:
        print(f"\n💭 Thinking (前200字):")
        print(thinking[:200])
    
    print(f"\n📝 Response:")
    print(response_text[:200] if response_text else "(空)")
    
    print(f"\n📈 Stats:")
    print(f"   Total: {result.get('total_duration', 0) / 1e9:.2f}s")
    print(f"   Load: {result.get('load_duration', 0) / 1e9:.2f}s")
    print(f"   Tokens: {result.get('eval_count', 0)}")
