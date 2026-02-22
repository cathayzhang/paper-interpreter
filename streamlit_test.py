"""
Streamlit API 测试页面
用于诊断 API 连接问题
"""
import streamlit as st
import requests
import os

st.title("🔍 API 连接测试")

# 显示环境变量
st.subheader("环境变量配置")
api_key = os.getenv("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))
api_url = os.getenv("GEMINI_API_URL", st.secrets.get("GEMINI_API_URL", ""))
model = os.getenv("GEMINI_MODEL", st.secrets.get("GEMINI_MODEL", ""))

st.write(f"API URL: `{api_url}`")
st.write(f"Model: `{model}`")
st.write(f"API Key 长度: `{len(api_key)}`")
st.write(f"API Key 前10位: `{api_key[:10]}...`")
st.write(f"API Key 后10位: `...{api_key[-10:]}`")

# 测试按钮
if st.button("🚀 测试 API 连接"):
    with st.spinner("正在测试..."):
        url = f"{api_url}/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "Say this is a test!"}],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        st.write("**请求信息：**")
        st.code(f"URL: {url}")
        st.code(f"Headers: {headers}")
        st.code(f"Data: {data}")
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            st.write(f"**状态码：** `{response.status_code}`")
            
            if response.status_code == 200:
                st.success("✅ API 连接成功！")
                result = response.json()
                st.json(result)
            else:
                st.error(f"❌ API 返回错误: {response.status_code}")
                st.code(response.text)
                
        except Exception as e:
            st.error(f"❌ 请求异常: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

st.divider()
st.caption("如果测试失败，请检查 Streamlit Secrets 配置是否正确")
