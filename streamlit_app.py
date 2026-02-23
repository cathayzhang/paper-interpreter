"""
Streamlit 独立部署版本
最快上线方案，支持一键部署到 Streamlit Cloud
修复：下载不跳转，使用 session_state 保持状态
"""
import streamlit as st
import tempfile
from pathlib import Path
import time
import os
import base64

from paper_to_popsci.core.downloader import PaperDownloader
from paper_to_popsci.core.extractor import PDFExtractor
from paper_to_popsci.core.analyzer import ContentAnalyzer
from paper_to_popsci.core.illustrator import IllustrationGenerator
from paper_to_popsci.core.writer import ArticleWriter
from paper_to_popsci.core.renderer import HTMLRenderer
from paper_to_popsci.core.multi_format_exporter import MultiFormatExporter
from paper_to_popsci.core.logger import logger

# 页面配置
st.set_page_config(
    page_title="Paper Interpreter - 论文解读专家",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 初始化 session_state
if 'page' not in st.session_state:
    st.session_state.page = 'input'  # input 或 result
if 'export_results' not in st.session_state:
    st.session_state.export_results = None
if 'paper_title' not in st.session_state:
    st.session_state.paper_title = ""
if 'illustrations' not in st.session_state:
    st.session_state.illustrations = []
if 'html_content' not in st.session_state:
    st.session_state.html_content = ""
if 'base_name' not in st.session_state:
    st.session_state.base_name = ""
if 'recommended_papers' not in st.session_state:
    st.session_state.recommended_papers = []
if 'paper_url' not in st.session_state:
    st.session_state.paper_url = ""

# 侧边栏 - API 配置
with st.sidebar:
    st.title("⚙️ API 配置")
    st.markdown("请输入你自己的 API Key")

    user_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        help="从 https://yunwu.ai 获取你的 API Key"
    )

    if user_api_key:
        os.environ["GEMINI_API_KEY"] = user_api_key
        os.environ["NANO_BANANA_API_KEY"] = user_api_key
        st.success("✅ API Key 已设置")
    else:
        default_key = os.getenv("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))
        if default_key:
            st.info("ℹ️ 使用默认配置")
        else:
            st.warning("⚠️ 请输入 API Key 以使用服务")

    st.divider()

    # 论文推荐配置 (可选)
    with st.expander("🔬 论文推荐配置 (可选)"):
        st.caption("不配置也能使用！系统会自动使用免费方案")

        ss_api_key = st.text_input(
            "Semantic Scholar API Key (可选)",
            type="password",
            help="无需申请也能使用。提供 Key 可以获得更高请求速率。申请地址：semanticscholar.org/product/api"
        )
        if ss_api_key:
            os.environ["SEMANTIC_SCHOLAR_API_KEY"] = ss_api_key
            st.success("✅ Semantic Scholar API 已设置")

        openalex_email = st.text_input(
            "OpenAlex Email (可选)",
            help="提供邮箱可进入'礼貌池'，获得更快访问速度"
        )
        if openalex_email:
            os.environ["OPENALEX_EMAIL"] = openalex_email
            st.success("✅ OpenAlex 已设置")

    st.divider()
    st.caption("你的 API Key 仅在当前会话中使用，不会被保存或分享")

# 自定义样式
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
    .stButton>button:hover {
        background-color: #138d75;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 2px solid #16A085;
    }
    .download-btn {
        background-color: #16A085 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


def reset_to_home():
    """重置到首页"""
    st.session_state.page = 'input'
    st.session_state.export_results = None
    st.session_state.paper_title = ""
    st.session_state.illustrations = []
    st.session_state.html_content = ""
    st.session_state.base_name = ""
    st.rerun()


def show_input_page():
    """显示输入页面"""
    # Hero 区
    st.title("📄 Paper Interpreter")
    st.markdown("### 让每一篇论文都值得被读懂")
    st.markdown("AI驱动的学术论文解读，将前沿研究转化为你触手可及的知识")

    st.divider()

    # 输入区
    col1, col2 = st.columns([3, 1])
    with col1:
        # 如果有预设的URL（来自推荐论文），则使用它
        default_url = st.session_state.get("paper_url", "")
        url = st.text_input(
            "论文链接",
            value=default_url,
            placeholder="https://arxiv.org/abs/2312.00752",
            help="支持 arXiv、DOI、OpenReview、Semantic Scholar 等"
        )
        # 清空预设URL，避免重复
        if default_url:
            st.session_state.paper_url = ""
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
        - **CVPR/CVF**: `https://openaccess.thecvf.com/content/...`
        - **Google Scholar**: `https://scholar.google.com/...`
        - **直接 PDF**: 以 `.pdf` 结尾的链接
        """)

    # 开始按钮
    if st.button("🚀 开始解读", type="primary", use_container_width=True):
        if not url:
            st.error("请输入论文链接")
            return

        api_key = os.getenv("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))
        if not api_key:
            st.error("❌ 请在侧边栏输入 API Key")
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
            paper_content = extractor.extract(pdf_path, metadata)
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

            if not isinstance(outline, dict):
                st.error("❌ 大纲格式错误")
                return

            article_sections = writer.write(paper_content, {"outline": outline}, illustrations)

            if not article_sections or len(article_sections) <= 1:
                st.error("❌ 文章生成失败，请重试")
                return

            # 收集推荐论文列表
            recommended_papers = []
            for section in article_sections:
                if section.section_type == "recommendations" and section.recommended_papers:
                    recommended_papers.extend(section.recommended_papers)
            st.session_state.recommended_papers = recommended_papers

            progress_bar.progress(80)

            # Step 6: 渲染 HTML
            status_text.text("🎨 正在渲染页面...")
            renderer = HTMLRenderer()
            html_path = output_dir / "article.html"
            renderer.render(article_sections, paper_content, html_path)
            progress_bar.progress(90)

            # Step 7: 导出多格式
            status_text.text("📦 正在导出多种格式...")
            exporter = MultiFormatExporter()
            export_results = exporter.export(
                article_sections,
                paper_content,
                output_dir,
                formats=['html', 'pdf', 'docx', 'md']
            )
            progress_bar.progress(100)

            # 读取文件内容到内存
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in paper_content.title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title[:50]
            base_name = f"{safe_title}_{timestamp}" if safe_title else f"paper_{timestamp}"

            # 读取配图为字节并保存
            illustrations_with_bytes = []
            for ill in illustrations:
                if ill.get("success") and ill.get("filepath") and Path(ill["filepath"]).exists():
                    with open(ill["filepath"], "rb") as f:
                        ill_copy = ill.copy()
                        ill_copy["image_bytes"] = f.read()
                        illustrations_with_bytes.append(ill_copy)
                else:
                    illustrations_with_bytes.append(ill)

            # 保存到 session_state
            st.session_state.paper_title = paper_content.title
            st.session_state.illustrations = illustrations_with_bytes
            st.session_state.base_name = base_name
            st.session_state.export_results = {}
            st.session_state.export_paths = {}  # 保存路径用于调试

            # 读取文件内容
            for fmt, path in export_results.items():
                if not path or not Path(path).exists():
                    logger.warning(f"导出文件不存在，跳过: {fmt}")
                    continue
                st.session_state.export_paths[fmt] = str(path)
                if fmt in ['html', 'md']:
                    with open(path, "r", encoding="utf-8") as f:
                        st.session_state.export_results[fmt] = f.read()
                else:
                    # 二进制文件：直接读取字节，不转base64
                    with open(path, "rb") as f:
                        st.session_state.export_results[fmt] = f.read()

            # 读取 HTML 用于预览
            with open(export_results['html'], "r", encoding="utf-8") as f:
                st.session_state.html_content = f.read()

            # 切换到结果页面
            st.session_state.page = 'result'
            status_text.empty()
            progress_bar.empty()
            st.rerun()

        except Exception as e:
            st.error(f"❌ 处理失败: {str(e)}")
            raise


def show_result_page():
    """显示结果页面 - 下载不会跳转"""
    st.title("📄 Paper Interpreter")
    st.success(f"✅ 《{st.session_state.paper_title}》解读完成！")

    # 统计信息
    success_images = len([i for i in st.session_state.illustrations if i.get("success")])
    available_formats = len(st.session_state.export_results) if st.session_state.export_results else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("配图生成", f"{success_images} 张")
    with col2:
        st.metric("处理状态", "完成")
    with col3:
        st.metric("可用格式", f"{available_formats} 种")

    st.divider()

    # 返回首页按钮
    if st.button("🏠 返回首页（处理新论文）", type="secondary", use_container_width=True):
        reset_to_home()
        return

    st.divider()
    st.markdown("### 📥 下载结果（多种格式）")

    export_results = st.session_state.export_results
    base_name = st.session_state.base_name

    col1, col2 = st.columns(2)

    # HTML 下载
    if 'html' in export_results:
        with col1:
            st.download_button(
                label="🌐 下载 HTML 网页版",
                data=export_results['html'],
                file_name=f"{base_name}.html",
                mime="text/html",
                use_container_width=True,
                help="在浏览器中打开，支持术语悬停提示",
                key="download_html"
            )

    # Markdown 下载
    if 'md' in export_results:
        with col2:
            st.download_button(
                label="📝 下载 Markdown",
                data=export_results['md'],
                file_name=f"{base_name}.md",
                mime="text/markdown",
                use_container_width=True,
                help="Markdown 格式，可在各种编辑器中打开",
                key="download_md"
            )

    col3, col4 = st.columns(2)

    # PDF 下载
    if 'pdf' in export_results:
        with col3:
            pdf_data = export_results['pdf']
            # 如果是字节数据直接使用，否则解码base64
            if isinstance(pdf_data, str):
                pdf_data = base64.b64decode(pdf_data)
            st.download_button(
                label="📄 下载 PDF",
                data=pdf_data,
                file_name=f"{base_name}.pdf",
                mime="application/pdf",
                use_container_width=True,
                help="PDF 文档，适合打印和分享，包含图片",
                key="download_pdf"
            )

    # Word 下载
    if 'docx' in export_results:
        with col4:
            docx_data = export_results['docx']
            # 如果是字节数据直接使用，否则解码base64
            if isinstance(docx_data, str):
                docx_data = base64.b64decode(docx_data)
            st.download_button(
                label="📘 下载 Word",
                data=docx_data,
                file_name=f"{base_name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                help="Microsoft Word 文档，包含图片，适合手机查看",
                key="download_docx"
            )

    # PDF 导出失败提示
    if 'pdf' not in export_results:
        st.warning("⚠️ PDF 导出失败。如需 PDF 格式，请确保 Playwright 已安装：\n\n`pip install playwright && playwright install chromium`")

    # 移动端推荐提示
    st.info("📱 **手机用户推荐**: 下载 Word (.docx) 格式，可在手机上用 WPS、Office 等应用打开，图片显示更友好")

    # 显示推荐论文（可点击解读）
    if st.session_state.get("recommended_papers"):
        st.divider()
        st.markdown("### 📚 推荐论文（点击解读）")
        st.caption("点击下方按钮，快速解读相关论文")

        papers = st.session_state.recommended_papers[:5]  # 最多显示5篇
        cols = st.columns(min(len(papers), 3))  # 每行最多3个按钮

        for idx, paper in enumerate(papers):
            with cols[idx % 3]:
                paper_title = paper.get("title", "未知论文")[:30] + "..." if len(paper.get("title", "")) > 30 else paper.get("title", "未知论文")
                paper_url = paper.get("url", "")
                if paper_url and st.button(
                    f"📄 {paper_title}",
                    key=f"interpret_paper_{idx}",
                    use_container_width=True,
                    help=f"解读《{paper.get('title', '')}》"
                ):
                    # 设置URL并开始解读
                    st.session_state.paper_url = paper_url
                    st.session_state.page = 'input'
                    st.rerun()

        with st.expander("🔗 复制推荐论文链接"):
            for idx, paper in enumerate(papers):
                st.text_input(
                    f"论文 {idx + 1}",
                    value=paper.get("url", ""),
                    key=f"paper_url_{idx}",
                    label_visibility="visible"
                )

    # 文章预览
    st.divider()
    st.markdown("### 👁️ 文章预览")

    if st.session_state.html_content:
        import streamlit.components.v1 as components
        components.html(st.session_state.html_content, height=800, scrolling=True)

    # 显示生成的配图
    if any(i.get("success") for i in st.session_state.illustrations):
        st.divider()
        st.markdown("### 🖼️ 生成的配图")

        for ill in st.session_state.illustrations:
            if ill.get("success"):
                # 优先使用字节数据，回退到文件路径
                if ill.get("image_bytes"):
                    st.image(ill["image_bytes"], caption=ill.get("section", ""))
                elif ill.get("filepath") and Path(ill["filepath"]).exists():
                    st.image(ill["filepath"], caption=ill.get("section", ""))

    # 底部返回按钮
    st.divider()
    if st.button("🏠 返回首页（处理新论文）", type="secondary", use_container_width=True, key="bottom_home"):
        reset_to_home()


def check_interpret_url():
    """检查是否有从"一键解读"传递过来的URL"""
    # 从查询参数中获取
    query_params = st.query_params
    if "interpret_url" in query_params:
        encoded_url = query_params["interpret_url"]
        # 解码URL
        actual_url = encoded_url.replace('%2F', '/').replace('%3A', ':')
        # 清空查询参数
        st.query_params.clear()
        # 设置URL并开始解读
        st.session_state.paper_url = actual_url
        return actual_url
    return None

def main():
    """主函数 - 根据状态显示不同页面"""
    # 检查是否有一键解读的URL
    interpret_url = check_interpret_url()

    if st.session_state.page == 'input':
        # 如果有解释URL，自动开始处理
        if interpret_url:
            # 确保API Key已设置
            api_key = os.getenv("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))
            if api_key:
                process_paper(interpret_url, 3)  # 默认3张配图
                return
        show_input_page()
    else:
        show_result_page()


if __name__ == "__main__":
    main()
