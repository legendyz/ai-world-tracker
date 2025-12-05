"""使用 Ollama Chat API 测试 Qwen3:8b 的 no_think 模式"""
import requests
import time

print("=" * 60)
print("测试 Qwen3:8b Chat API (think=false)")
print("=" * 60)

prompt = """Classify this AI news. Reply with only the category name (llm, vision, robotics, research, industry, tools, ethics):

Title: OpenAI releases GPT-5
Content: OpenAI announced GPT-5 with advanced reasoning.

Category:"""

print(f"\n🚀 发送请求...")

start = time.time()

# 使用 chat API 并设置 think=false
response = requests.post(
    'http://localhost:11434/api/chat',
    json={
        'model': 'qwen3:8b',
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'stream': False,
        'think': False,  # 关闭思考模式
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
    
    message = result.get('message', {})
    thinking = message.get('thinking', '')
    content = message.get('content', '')
    
    print(f"\n⏱️ 耗时: {elapsed:.1f}s")
    print(f"📊 Thinking 长度: {len(thinking)} chars")
    print(f"📊 Content 长度: {len(content)} chars")
    
    if thinking:
        print(f"\n💭 Thinking (前200字):")
        print(thinking[:200])
    
    print(f"\n📝 Content:")
    print(content[:200] if content else "(空)")
    
    print(f"\n📈 Stats:")
    print(f"   Total: {result.get('total_duration', 0) / 1e9:.2f}s")
    print(f"   Load: {result.get('load_duration', 0) / 1e9:.2f}s")
    print(f"   Tokens: {result.get('eval_count', 0)}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
