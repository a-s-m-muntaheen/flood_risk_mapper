# Option 2: API test (matches your Django code)
import requests, json
r = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'llama3.2',  # ← matches your OLLAMA_MODEL setting
        'prompt': 'Summarize flood risk factors in Bangladesh in 2 sentences.',
        'stream': False
    },
    timeout=30
)
if r.status_code == 200:
    print('✅ Response:', r.json()['response'])
else:
    print('❌ Error:', r.status_code, r.text)
