#!/usr/bin/env python3
"""
测试 API 连接和配置
"""
import os
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_openai_format():
    """测试 OpenAI 兼容格式"""
    api_key = os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("GEMINI_API_URL", "https://yunwu.ai")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    print(f"🔍 测试配置:")
    print(f"  API Key: {api_key[:20]}..." if api_key else "  API Key: 未设置")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    print()
    
    url = f"{base_url}/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello, say 'API is working' if you can read this."}
        ],
        "temperature": 0.7,
        "max_tokens": 50,
    }
    
    print(f"📡 发送请求到: {url}")
    print(f"📦 请求数据: model={model}")
    print()
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功! 响应内容:")
            print(result)
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                print(f"\n💬 AI 回复: {content}")
        else:
            print(f"❌ 失败! 状态码: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 错误: {e}")


def test_gemini_format():
    """测试 Gemini 原生格式"""
    api_key = os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("GEMINI_API_URL", "https://yunwu.ai")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    url = f"{base_url}/v1beta/models/{model}:generateContent"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    data = {
        "contents": [{
            "role": "user",
            "parts": [{"text": "Hello, say 'API is working' if you can read this."}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 50,
        }
    }
    
    print(f"\n{'='*60}")
    print(f"🔍 测试 Gemini 原生格式")
    print(f"📡 发送请求到: {url}")
    print()
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            params={"key": api_key},
            timeout=30
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功! 响应内容:")
            print(result)
            
            if "candidates" in result and len(result["candidates"]) > 0:
                parts = result["candidates"][0].get("content", {}).get("parts", [])
                if parts:
                    content = parts[0].get("text", "")
                    print(f"\n💬 AI 回复: {content}")
        else:
            print(f"❌ 失败! 状态码: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 错误: {e}")


def check_service_status():
    """检查服务状态"""
    base_url = os.getenv("GEMINI_API_URL", "https://yunwu.ai")
    
    print(f"\n{'='*60}")
    print(f"🏥 检查服务健康状态")
    print(f"🌐 Base URL: {base_url}")
    print()
    
    try:
        # 尝试访问根路径
        response = requests.get(base_url, timeout=10)
        print(f"✅ 服务可访问 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ 服务不可访问: {e}")


if __name__ == "__main__":
    print("="*60)
    print("🧪 API 连接测试")
    print("="*60)
    print()
    
    # 检查服务状态
    check_service_status()
    
    # 测试 OpenAI 格式
    test_openai_format()
    
    # 测试 Gemini 格式
    test_gemini_format()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
