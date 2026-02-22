"""
Streamlit 独立部署版本
最快上线方案，支持一键部署到 Streamlit Cloud
"""
import streamlit as st
import tempfile
from pathlib import Path
import time
import os
import requests

from paper_to_popsci.core.downloader import PaperDownloader
from paper_to_popsci.core.extractor import PDFExtractor
from paper_to_popsci.core.analyzer import ContentAnalyzer
from paper_to_popsci.core.illustrator import IllustrationGenerator
from paper_to_popsci.core.writer import ArticleWriter
from paper_to_popsci.core.renderer import HTMLRenderer

st.set_page_config(
    page_title="Paper Interpreter - 论文解读专家",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 添加侧边栏测试功能
with st.sidebar:
    st.title("🔧 调试工具")
    if st.button("🔍 测试 API 连接"):
        st.subheader("API 配置检查")
        
        api_key = os.getenv("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))
        api_url = os.getenv("GEMINI_API_URL", st.secrets.get("GEMINI_API_URL", ""))
        model = os.getenv("GEMINI_MODEL", st.secrets.get("GEMINI_MODEL", ""))
        
        st.write(f"API URL: `{api_url}`")
        st.write(f"Model: `{model}`")
        st.write(f"API Key 长度: `{len(api_key)}`")
        st.write(f"API Key 前10位: `{api_key[:10]}...`")
        st.write(f"API Key 后10位: `...{api_key[-10:]}`")
        
        # 测试连接
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
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            st.write(f"**状态码：** `{response.status_code}`")
            
            if response.status_code == 200:
                st.success("✅ API 连接成功！")
                st.json(response.json())
            else:
                st.error(f"❌ API 返回错误")
                st.code(response.text)
        except Exception as e:
            st.error(f"❌ 请求异常: {str(e)}")

# 自定义样式 - 暖米色主题
st.markdown("""
<style>
    .main {
        background-color: #FDF6E3;
    }
    .stButton>button {
        background-color: #16A085;
        color: white;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 16px;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 2px solid #16A085;
    }
    .result-box {
        background-color: #F5EFE0;
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #16A085;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Hero 区
    st.title("📄 Paper Interpreter")
    st.markdown("### 将学术论文转换为通俗易懂的科普文章")
    st.markdown("面向'一无所知'的小白读者，用大白话讲解复杂的学术概念")

    st.divider()

    # 输入区
    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input(
            "论文链接",
            placeholder="https://arxiv.org/abs/2312.00752",
            help="支持 arXiv、DOI、OpenReview、Semantic Scholar 等"
        )
    with col2:
        illustration_count = st.selectbox(
            "配图数量",
            options=[3, 4, 5],
            index=0
        )

    # 支持的格式说明
    with st.expander("📎 支持的链接格式"):
        st.markdown("""
        - **arXiv**: `https://arxiv.org/abs/2312.00752`
        - **arXiv PDF**: `https://arxiv.org/pdf/2312.00752`
        - **DOI**: `https://doi.org/10.1109/TPAMI.2016.2577031`
        - **OpenReview**: `https://openreview.net/forum?id=xxxxx`
        - **Semantic Scholar**: `https://www.semanticscholar.org/paper/xxxxx`
        - **直接 PDF**: 以 `.pdf` 结尾的链接
        """)

    # 开始按钮
    if st.button("🚀 开始解读", type="primary", use_container_width=True):
        if not url:
            st.error("请输入论文链接")
            return

        process_paper(url, illustration_count)

def process_paper(url: str, illustration_count: int):
    """处理论文"""
    progress_bar = st.progress(0)
    status_text = st.empty()

    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()

        try:
            # Step 1: 下载
            status_text.text("📥 正在下载论文...")
            downloader = PaperDownloader()
            pdf_path, metadata = downloader.download(url, output_dir)

            if not pdf_path:
                st.error("❌ 论文下载失败，请检查链接是否可访问")
                return

            progress_bar.progress(15)

            # Step 2: 提取内容
            status_text.text("📄 正在提取论文内容...")
            extractor = PDFExtractor()
            paper_content = extractor.extract(pdf_path)
            progress_bar.progress(30)

            # Step 3: 分析
            status_text.text("🧠 正在分析论文结构...")
            analyzer = ContentAnalyzer()
            analysis_result = analyzer.analyze(paper_content)
            outline = analysis_result["outline"]
            prompts = analysis_result["illustration_prompts"]
            progress_bar.progress(45)

            # Step 4: 生成配图
            status_text.text("🎨 正在生成配图...")
            prompts = prompts[:illustration_count]

            illustrator = IllustrationGenerator()
            illustrations = illustrator.generate_all(prompts, output_dir / "images")
            progress_bar.progress(65)

            # Step 5: 生成文章
            status_text.text("✍️ 正在撰写科普文章...")
            writer = ArticleWriter()
            
            # 确保 outline 是字典格式
            if not isinstance(outline, dict):
                st.error("❌ 大纲格式错误")
                return
                
            article_sections = writer.write(paper_content, {"outline": outline}, illustrations)
            
            if not article_sections or len(article_sections) <= 1:
                st.error("❌ 文章生成失败，请重试")
                return
                
            progress_bar.progress(80)

            # Step 6: 渲染 HTML
            status_text.text("🎨 正在渲染页面...")
            renderer = HTMLRenderer()
            html_path = output_dir / "article.html"
            renderer.render(article_sections, paper_content, html_path)
            progress_bar.progress(100)

            # 显示结果
            status_text.empty()
            progress_bar.empty()

            # 读取生成的 HTML
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            show_results(paper_content, html_content, html_path, illustrations)

        except Exception as e:
            st.error(f"❌ 处理失败: {str(e)}")
            raise

def show_results(paper_content, html_content, html_path, illustrations):
    """显示结果"""
    st.success(f"✅ 《{paper_content.title}》解读完成！")

    # 统计信息
    success_images = len([i for i in illustrations if i.get("success")])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("配图生成", f"{success_images} 张")
    with col2:
        word_count = len(html_content)
        st.metric("文章字数", f"{word_count} 字")
    with col3:
        st.metric("处理状态", "完成")

    # 下载按钮
    st.divider()
    st.markdown("### 📥 下载结果")

    with open(html_path, "r", encoding="utf-8") as f:
        html_data = f.read()
    st.download_button(
        label="🌐 下载 HTML 网页版",
        data=html_data,
        file_name="article.html",
        mime="text/html",
        use_container_width=True
    )

    # 文章预览
    st.divider()
    st.markdown("### 👁️ 文章预览")

    # 显示文章标题和前几段
    with open(html_path, "r", encoding="utf-8") as f:
        html_preview = f.read()
    
    # 提取正文内容（去除 HTML 标签）
    import re
    text_content = re.sub(r'<[^>]+>', '', html_preview)
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    
    # 显示前 500 字符
    preview_text = text_content[:500] + "..." if len(text_content) > 500 else text_content
    st.text(preview_text)

    # 显示生成的配图
    if any(i.get("success") for i in illustrations):
        st.divider()
        st.markdown("### 🖼️ 生成的配图")

        for ill in illustrations:
            if ill.get("success") and ill.get("filepath"):
                st.image(ill["filepath"], caption=ill.get("section", ""))

if __name__ == "__main__":
    main()
