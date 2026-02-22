#!/usr/bin/env python3
"""
测试 API 连接
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY", "")
api_url = os.getenv("GEMINI_API_URL", "https://yunwu.ai")

print(f"API Key: {api_key}")
print(f"API URL: {api_url}")
print(f"API Key 长度: {len(api_key)}")
print()

# 测试请求
url = f"{api_url}/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
}

data = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Say this is a test!"}],
    "temperature": 0.7
}

print(f"请求 URL: {url}")
print(f"请求头: {headers}")
print()

try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
    
    if response.status_code == 200:
        print("\n✅ API 连接成功！")
    else:
        print(f"\n❌ API 连接失败: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ 请求异常: {e}")
