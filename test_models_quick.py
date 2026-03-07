#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
import time

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
base_url = 'https://yunwu.ai'

models = [
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite', 
    'gemini-2.0-flash',
    'gemini-2.0-flash-exp',
    'gemini-exp-1206',
]

print('🔍 测试多个模型')
print('='*60)

for model in models:
    url = f'{base_url}/v1beta/models/{model}:generateContent'
    headers = {'Content-Type': 'application/json'}
    data = {
        'contents': [{
            'role': 'user',
            'parts': [{'text': 'Hi'}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, params={'key': api_key}, timeout=10)
        
        if response.status_code == 200:
            print(f'✅ {model}: 可用')
        elif response.status_code == 401:
            print(f'❌ {model}: 401 Unauthorized')
        elif response.status_code == 429:
            print(f'⚠️  {model}: 429 速率限制 (可能可用,但当前过载)')
        elif response.status_code == 503:
            print(f'❌ {model}: 503 无可用渠道')
        else:
            print(f'❓ {model}: {response.status_code}')
    except Exception as e:
        print(f'❌ {model}: 错误 - {str(e)[:50]}')
    
    time.sleep(2)

print('='*60)
