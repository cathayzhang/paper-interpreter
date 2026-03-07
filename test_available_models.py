#!/usr/bin/env python3
"""
测试可用的模型
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_model(model_name, format_type="gemini"):
    """测试特定模型是否可用"""
    api_key = os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("GEMINI_API_URL", "https://yunwu.ai")
    
    if format_type == "gemini":
        url = f"{base_url}/v1beta/models/{model_name}:generateContent"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "role": "user",
                "parts": [{"text": "Hello"}]
            }]
        }
        response = requests.post(url, headers=headers, json=data, params={"key": api_key}, timeout=10)
    else:  # openai
        url = f"{base_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Hello"}]
        }
        response = requests.post(url, headers=headers, json=data, timeout=10)
    
    return response.status_code, response.text[:200]

def main():
    print("🔍 测试可用模型")
    print("="*60)
    
    # 测试不同的模型名称
    models_to_test = [
        ("gemini-2.5-flash", "gemini"),
        ("gemini-2.0-flash", "gemini"),
        ("gemini-flash-lite-latest", "gemini"),
        ("gemini-1.5-flash", "gemini"),
        ("gemini-2.5-flash", "openai"),
        ("gemini-flash-lite-latest", "openai"),
    ]
    
    for model, format_type in models_to_test:
        try:
            status, text = test_model(model, format_type)
            if status == 200:
                print(f"✅ {model} ({format_type}): 可用")
            elif status == 401:
                print(f"❌ {model} ({format_type}): 401 Unauthorized (模型不存在或不支持)")
            elif status == 429:
                print(f"⚠️  {model} ({format_type}): 429 速率限制")
            else:
                print(f"❓ {model} ({format_type}): {status} - {text}")
        except Exception as e:
            print(f"❌ {model} ({format_type}): 错误 - {e}")
    
    print("="*60)

if __name__ == "__main__":
    main()
