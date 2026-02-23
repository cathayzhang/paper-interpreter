"""
HTML 渲染和 PDF 导出模块
"""
import json
import re
import subprocess
import shutil
import base64
from pathlib import Path
from typing import List, Optional

from .config import Config
from .logger import logger


class HTMLRenderer:
    """HTML 渲染器"""

    def __init__(self):
        self.style = Config.STYLE

    def render(self, article_sections, paper_content, output_path: Path) -> Path:
        """
        渲染文章为 HTML

        Args:
            article_sections: 文章章节列表
            paper_content: 论文内容对象
            output_path: 输出 HTML 路径

        Returns:
            HTML 文件路径
        """
        logger.info(f"渲染 HTML: {output_path}")

        html_content = self._build_html(article_sections, paper_content)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML 渲染完成: {output_path}")
        return output_path

    def _image_to_base64(self, image_path: str) -> str:
        """将图片转换为 base64 编码"""
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # 检测图片格式
            ext = Path(image_path).suffix.lower()
            mime_type = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }.get(ext, 'image/png')
            
            return f"data:{mime_type};base64,{base64_data}"
        except Exception as e:
            logger.warning(f"图片转换失败: {e}")
            return ""

    def _build_html(self, article_sections, paper_content) -> str:
        """构建完整 HTML"""
        # 生成各部分 HTML
        body_sections = []
        for section in article_sections:
            html = self._render_section(section)
            body_sections.append(html)

        body_content = "\n".join(body_sections)

        # 构建完整 HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(paper_content.title or "论文解读")}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
    {self._get_custom_css()}
</head>
<body class="bg-[{self.style['background_color']}] text-[{self.style['text_color']}]">
    <div class="max-w-4xl mx-auto px-6 py-12">
        {body_content}
    </div>
    <footer class="text-center py-8 text-sm text-gray-500">
        <p>由 Paper Interpreter 自动生成</p>
    </footer>
</body>
</html>"""
        return html.strip()

    def _render_section(self, section) -> str:
        """渲染单个章节"""
        section_type = section.section_type
        title = section.title
        content = section.content
        image_path = section.image_path

        if section_type == "hero":
            return self._render_hero(title, content, image_path)
        elif section_type == "intro":
            return self._render_standard_section(title, content, image_path, "intro")
        elif section_type == "problem":
            return self._render_standard_section(title, content, image_path, "problem")
        elif section_type == "method":
            return self._render_standard_section(title, content, image_path, "method")
        elif section_type == "results":
            return self._render_results_section(title, content, image_path)
        elif section_type == "impact":
            return self._render_impact_section(title, content, image_path)
        elif section_type == "conclusion":
            return self._render_conclusion_section(title, content, image_path)
        elif section_type == "paper_info":
            return self._render_paper_info_section(title, content)
        elif section_type == "recommendations":
            return self._render_recommendations_section(title, content, image_path)
        else:
            return self._render_standard_section(title, content, image_path)

    def _render_hero(self, title: str, content: str, image_path: Optional[str]) -> str:
        """渲染 Hero 区"""
        lines = content.split("\n")
        main_title = lines[0].strip() if lines else title
        subtitle = lines[1].strip() if len(lines) > 1 else ""

        # 提取元信息
        meta_info = {}
        for line in lines[2:]:
            if "**作者**" in line:
                meta_info["authors"] = line.split(":", 1)[-1].strip()
            elif "**机构**" in line:
                meta_info["institution"] = line.split(":", 1)[-1].strip()
            elif "**发表时间**" in line:
                meta_info["date"] = line.split(":", 1)[-1].strip()
            elif "**arXiv ID**" in line:
                meta_info["arxiv"] = line.split(":", 1)[-1].strip()

        meta_html = " | ".join([
            f"<span>{v}</span>"
            for v in meta_info.values() if v and v != "N/A"
        ])

        image_html = ""
        if image_path:
            # 将图片转换为 base64
            base64_img = self._image_to_base64(image_path)
            if base64_img:
                image_html = f'''
            <div class="mt-8 flex justify-center">
                <img src="{base64_img}" alt="{main_title}"
                     class="max-h-80 object-contain rounded-lg shadow-lg">
            </div>'''

        return f"""
        <section class="hero text-center py-12 border-b-2 border-[{self.style['accent_color']}]">
            <h1 class="text-5xl font-bold mb-4" style="font-family: {self.style['font_family']}">
                {self._escape_html(main_title)}
            </h1>
            <p class="text-2xl text-[{self.style['accent_color']}] mb-6">
                {self._escape_html(subtitle)}
            </p>
            <div class="text-sm text-gray-600 space-x-4">
                {meta_html}
            </div>
            {image_html}
        </section>"""

    def _render_standard_section(self, title: str, content: str, image_path: Optional[str], section_class: str = "") -> str:
        """渲染标准章节"""
        content_html = self._markdown_to_html(content)

        image_html = ""
        if image_path:
            # 将图片转换为 base64
            base64_img = self._image_to_base64(image_path)
            if base64_img:
                image_html = f'''
            <figure class="my-8 text-center">
                <img src="{base64_img}" alt="{title}"
                     class="max-h-80 object-contain rounded-lg shadow-lg mx-auto border-4 border-[{self.style['background_color']}]">
                <figcaption class="text-sm text-gray-500 mt-3 italic">图：{self._escape_html(title)}</figcaption>
            </figure>'''

        return f"""
        <section class="section py-10 {section_class}">
            <h2 class="text-3xl font-bold mb-8 pb-3 border-b-2 border-[{self.style['accent_color']}] tracking-tight"
                style="font-family: {self.style['font_family']}; color: {self.style['text_color']}">
                {self._escape_html(title)}
            </h2>
            <div class="prose prose-lg max-w-none leading-relaxed">
                {content_html}
            </div>
            {image_html}
        </section>"""

    def _render_results_section(self, title: str, content: str, image_path: Optional[str]) -> str:
        """渲染结果章节（特殊样式）"""
        content_html = self._markdown_to_html(content)

        # 添加数字高亮
        content_html = self._highlight_numbers(content_html)

        image_html = ""
        if image_path:
            # 将图片转换为 base64
            base64_img = self._image_to_base64(image_path)
            if base64_img:
                image_html = f'''
            <figure class="my-8 text-center">
                <img src="{base64_img}" alt="{title}"
                     class="max-h-80 object-contain rounded-lg shadow-lg mx-auto border-4 border-[{self.style['background_color']}]">
            </figure>'''

        return f"""
        <section class="section py-10 results">
            <h2 class="text-3xl font-bold mb-8 pb-3 border-b-2 border-[{self.style['accent_color']}] tracking-tight"
                style="font-family: {self.style['font_family']}; color: {self.style['text_color']}">
                {self._escape_html(title)}
            </h2>
            <div class="prose prose-lg max-w-none leading-relaxed">
                {content_html}
            </div>
            {image_html}
        </section>"""

    def _render_impact_section(self, title: str, content: str, image_path: Optional[str]) -> str:
        """渲染意义章节（优雅引用框样式）"""
        content_html = self._markdown_to_html(content)

        # 包装在优雅引用框中 - 使用与背景协调的颜色
        accent = self.style['accent_color']
        text_color = self.style['text_color']
        return f"""
        <section class="section py-10 impact">
            <h2 class="text-3xl font-bold mb-8 pb-3 border-b-2 border-[{accent}] tracking-tight"
                style="font-family: {self.style['font_family']}; color: {text_color}">
                {self._escape_html(title)}
            </h2>
            <div class="relative pl-8 py-6 my-4">
                <div class="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-[{accent}] to-[{accent}] opacity-60 rounded-full"></div>
                <div class="absolute left-[-4px] top-0 w-3 h-3 rounded-full bg-[{accent}] opacity-80"></div>
                <div class="prose prose-lg max-w-none leading-relaxed italic" style="color: {text_color}">
                    {content_html}
                </div>
            </div>
        </section>"""

    def _render_conclusion_section(self, title: str, content: str, image_path: Optional[str]) -> str:
        """渲染总结章节"""
        content_html = self._markdown_to_html(content)

        image_html = ""
        if image_path:
            # 将图片转换为 base64
            base64_img = self._image_to_base64(image_path)
            if base64_img:
                image_html = f'''
            <figure class="my-8 text-center">
                <img src="{base64_img}" alt="{title}"
                     class="max-h-80 object-contain rounded-lg shadow-lg mx-auto border-4 border-[{self.style['background_color']}]">
            </figure>'''

        return f"""
        <section class="section py-10 conclusion">
            <h2 class="text-3xl font-bold mb-8 pb-3 border-b-2 border-[{self.style['accent_color']}] tracking-tight"
                style="font-family: {self.style['font_family']}; color: {self.style['text_color']}"
>
                {self._escape_html(title)}
            </h2>
            <div class="prose prose-lg max-w-none leading-relaxed">
                {content_html}
            </div>
            {image_html}
        </section>"""

    def _render_paper_info_section(self, title: str, content: str) -> str:
        """渲染论文信息章节"""
        lines = content.split("\n")
        info_items = []

        for line in lines:
            line = line.strip()
            if line.startswith("**") and "**" in line[2:]:
                parts = line[2:].split("**", 1)
                if len(parts) == 2:
                    label = parts[0].replace(":", "").strip()
                    value = parts[1].strip()
                    if value and value != "N/A":
                        info_items.append((label, value))

        def format_value(label: str, value: str) -> str:
            """格式化值，链接做成超链接"""
            # 链接字段处理为超链接
            if label in ["原文链接", "链接", "arXiv", "DOI"]:
                if value.startswith("http"):
                    return f'<a href="{value}" target="_blank" class="text-[{self.style["accent_color"]}] hover:underline">{value}</a>'
            # 清理值中的冒号前缀
            if value.startswith(": "):
                value = value[2:]
            return self._escape_html(value)

        info_html = "\n".join([
            f"""<div class="py-2 border-b border-gray-200">
                <span class="font-bold text-gray-700">{self._escape_html(label)}</span>
                <span class="ml-2">{format_value(label, value)}</span>
            </div>"""
            for label, value in info_items
        ])

        return f"""
        <section class="section py-10 paper-info mt-12 border-t-2 border-[{self.style['accent_color']}] opacity-40">
            <h2 class="text-2xl font-bold mb-6 pb-3" style="color: {self.style['text_color']}; opacity: 0.7;">
                {self._escape_html(title)}
            </h2>
            <div class="text-sm space-y-1">
                {info_html}
            </div>
        </section>"""

    def _render_recommendations_section(self, title: str, content: str, image_path: Optional[str]) -> str:
        """渲染推荐章节"""
        content_html = self._markdown_to_html(content)

        # 特殊处理推荐卡片样式
        content_html = self._style_recommendation_cards(content_html)

        return f"""
        <section class="section py-10 recommendations">
            <h2 class="text-3xl font-bold mb-8 pb-3 border-b-2 border-[{self.style['accent_color']}] tracking-tight"
                style="font-family: {self.style['font_family']}; color: {self.style['text_color']}">
                {self._escape_html(title)}
            </h2>
            <div class="prose prose-lg max-w-none leading-relaxed">
                {content_html}
            </div>
        </section>"""

    def _style_recommendation_cards(self, html: str) -> str:
        """为推荐内容添加卡片样式"""
        # 为推荐论文标题添加样式
        import re

        # 匹配 **数字. 标题** 格式并添加样式
        html = re.sub(
            r'\*\*(\d+)\.\s*([^<]+)\*\*',
            r'<h4 class="text-xl font-bold mt-6 mb-2" style="color: {accent}">\1. \2</h4>'.format(
                accent=self.style['accent_color']
            ),
            html
        )

        # 为来源标签添加样式
        html = re.sub(
            r'\*\*([^*]+)\*\*:',
            r'<span class="font-bold text-gray-700">\1:</span>',
            html
        )

        # 为链接添加样式
        html = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            r'<a href="\2" target="_blank" class="text-[{accent}] hover:underline">\1</a>'.format(
                accent=self.style['accent_color']
            ),
            html
        )

        return html

    def _markdown_to_html(self, text: str) -> str:
        """简单的 Markdown 转 HTML - 清理残留格式"""
        # 首先清理残留的 Markdown 和 LaTeX 格式（双重保险）
        # 移除 Markdown 标题
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        # 移除 LaTeX 公式
        text = re.sub(r'\$\$[^$]*\$\$', '', text)
        text = re.sub(r'\$[^$]*\$', '', text)

        # 先处理代码块（保护起来不转义）
        code_blocks = []
        def save_code_block(match):
            code_blocks.append(match.group(1))
            return f"<<<CODE_BLOCK_{len(code_blocks)-1}>>>"

        # 保存 ``` 代码块
        text = re.sub(r'```(?:\w+)?\n(.*?)```', save_code_block, text, flags=re.DOTALL)
        # 保存 ` 行内代码
        text = re.sub(r'`([^`]+)`', save_code_block, text)

        # 处理段落
        paragraphs = text.split('\n\n')
        html_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            # 检查是否是代码块占位符
            if p.startswith("<<<CODE_BLOCK_"):
                code_idx = int(re.search(r'<<<CODE_BLOCK_(\d+)>>>', p).group(1))
                code_content = code_blocks[code_idx]
                # 检查是否是多行代码
                if '\n' in code_content:
                    html_paragraphs.append(f'<pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code class="font-mono text-sm">{self._escape_html(code_content)}</code></pre>')
                else:
                    html_paragraphs.append(f'<code class="bg-gray-200 px-1 py-0.5 rounded font-mono text-sm">{self._escape_html(code_content)}</code>')
            elif p.startswith('- '):
                # 列表
                items = [item.strip()[2:] for item in p.split('\n') if item.strip().startswith('- ')]
                if items:
                    list_items = '\n'.join([f'<li>{self._apply_inline_formatting(item)}</li>' for item in items])
                    html_paragraphs.append(f'<ul class="list-disc pl-6 my-4 space-y-2">{list_items}</ul>')
            else:
                # 普通段落：先处理 Markdown 格式，再转义剩余 HTML
                formatted = self._apply_inline_formatting(p)
                # 恢复代码块占位符并正确渲染
                formatted = self._restore_code_blocks(formatted, code_blocks)
                html_paragraphs.append(f'<p class="my-4 leading-relaxed">{formatted}</p>')

        return '\n'.join(html_paragraphs)

    def _restore_code_blocks(self, text: str, code_blocks: list) -> str:
        """恢复代码块占位符为实际的 HTML"""
        for i, code in enumerate(code_blocks):
            placeholder = f"<<<CODE_BLOCK_{i}>>>"
            if placeholder in text:
                if '\n' in code:
                    # 多行代码块
                    html = f'<pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code class="font-mono text-sm">{self._escape_html(code)}</code></pre>'
                else:
                    # 行内代码
                    html = f'<code class="bg-gray-200 px-1 py-0.5 rounded font-mono text-sm">{self._escape_html(code)}</code>'
                text = text.replace(placeholder, html)
        return text

    def _apply_inline_formatting(self, text: str) -> str:
        """应用行内格式（加粗、斜体、术语注解）"""
        # 处理术语注解 *术语（解释）* -> 转换为专业格式
        text = self._process_term_annotations(text)
        # 处理加粗 **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # 处理斜体 *text* (剩余的)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        return text

    def _process_term_annotations(self, text: str) -> str:
        """处理术语注解格式 *术语（大白话解释）* -> 专业脚注样式"""
        # 匹配 *术语（解释）* 格式
        pattern = r'\*([^*（]+?)（(.+?)）\*'

        def replace_term(match):
            term = match.group(1)
            explanation = match.group(2)
            return f'<span class="term" data-term="{term}">{term}<span class="term-tooltip">{explanation}</span></span>'

        return re.sub(pattern, replace_term, text)

    def _highlight_numbers(self, html: str) -> str:
        """高亮数字"""
        # 高亮百分比和倍数
        html = re.sub(
            r'(\d+\.?\d*)\s*(倍|%|x|×)',
            rf'<span class="text-[{self.style["accent_color"]}] font-bold text-xl">\1\2</span>',
            html
        )
        return html

    def _escape_html(self, text: str) -> str:
        """转义 HTML 特殊字符"""
        return (text
                .replace("\u0026", "\u0026amp;")
                .replace("<", "\u0026lt;")
                .replace(">", "\u0026gt;")
                .replace('"', "\u0026quot;")
                .replace("'", "\u0026#x27;"))

    def _get_custom_css(self) -> str:
        """获取自定义 CSS - 极致美学设计"""
        bg_color = self.style['background_color']
        text_color = self.style['text_color']
        accent_color = self.style['accent_color']

        return f"""
    <style>
        @page {{
            size: A4;
            margin: 2cm 2.5cm;
            @top-center {{
                content: "Paper Interpreter";
                font-size: 9pt;
                color: #888;
                font-family: 'Noto Sans SC', sans-serif;
            }}
            @bottom-center {{
                content: "第 " counter(page) " 页";
                font-size: 9pt;
                color: #888;
                font-family: 'Noto Sans SC', sans-serif;
            }}
        }}

        /* 基础排版 */
        body {{
            font-family: {self.style['font_family_sans']};
            background-color: {bg_color};
            color: {text_color};
            line-height: 1.8;
            letter-spacing: 0.01em;
        }}

        /* 标题层次 */
        h1, h2, h3 {{
            font-family: {self.style['font_family']};
            color: {text_color};
            line-height: 1.3;
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}

        h2 {{
            font-size: 1.75rem;
            font-weight: 600;
            letter-spacing: -0.01em;
        }}

        /* 正文段落 - 使用段间距而非缩进 */
        .prose p {{
            text-indent: 0;
            margin-bottom: 1.25em;
            text-align: justify;
            hyphens: auto;
            line-height: 1.85;
        }}

        .prose p:last-child {{
            margin-bottom: 0;
        }}

        /* 列表样式优化 */
        .prose ul {{
            margin: 1.25em 0;
            padding-left: 1.5em;
        }}

        .prose li {{
            margin-bottom: 0.5em;
            line-height: 1.75;
        }}

        /* 链接样式 */
        a {{
            color: {accent_color};
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-color 0.2s ease;
        }}

        a:hover {{
            border-bottom-color: {accent_color};
        }}

        /* 代码样式 */
        code {{
            background-color: rgba(0,0,0,0.05);
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-size: 0.9em;
            color: #d73a49;
        }}

        pre code {{
            background-color: transparent;
            color: #f0f0f0;
            padding: 0;
        }}

        /* 图片样式 */
        img {{
            max-width: 100%;
            height: auto;
            page-break-inside: avoid;
        }}

        /* 章节间距 */
        .section {{
            page-break-inside: avoid;
        }}

        /* 强调文字 */
        strong {{
            font-weight: 600;
            color: {text_color};
        }}

        /* 斜体 */
        em {{
            font-style: italic;
            color: #3a4a5a;
        }}

        /* 术语注解样式 - 优雅的悬停提示 */
        .term {{
            position: relative;
            display: inline-block;
            color: {accent_color};
            font-weight: 500;
            cursor: help;
            border-bottom: 1px dotted {accent_color};
        }}

        .term-tooltip {{
            position: absolute;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            background-color: {text_color};
            color: {bg_color};
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.85em;
            line-height: 1.5;
            white-space: normal;
            max-width: 280px;
            min-width: 180px;
            text-align: center;
            z-index: 100;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}

        .term-tooltip::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: {text_color};
        }}

        .term:hover .term-tooltip {{
            opacity: 1;
            visibility: visible;
        }}

        /* PDF打印时显示注解 */
        @media print {{
            .term-tooltip {{
                position: static;
                display: inline;
                background-color: transparent;
                color: #666;
                font-size: 0.8em;
                padding: 0;
                margin-left: 4px;
                opacity: 1;
                visibility: visible;
                box-shadow: none;
                max-width: none;
                transform: none;
            }}
            .term-tooltip::before {{
                content: "(";
            }}
            .term-tooltip::after {{
                content: ")";
                position: static;
                border: none;
                transform: none;
            }}
            .term {{
                border-bottom: none;
            }}
        }}

        /* 响应式调整 */
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}

            h1 {{
                font-size: 2rem;
            }}

            h2 {{
                font-size: 1.5rem;
            }}
        }}
    </style>"""


class PDFExporter:
    """PDF 导出器"""

    def __init__(self):
        self.html_renderer = HTMLRenderer()

    def export(self, html_path: Path, output_path: Path) -> Path:
        """
        导出 HTML 为 PDF

        Args:
            html_path: HTML 文件路径
            output_path: 输出 PDF 路径

        Returns:
            PDF 文件路径
        """
        logger.info(f"导出 PDF: {output_path}")

        # 尝试多种导出方案
        try:
            return self._export_with_playwright(html_path, output_path)
        except Exception as e:
            logger.warning(f"Playwright 导出失败: {e}")

        try:
            return self._export_with_weasyprint(html_path, output_path)
        except Exception as e:
            logger.warning(f"WeasyPrint 导出失败: {e}")

        try:
            return self._export_with_pandoc(html_path, output_path)
        except Exception as e:
            logger.warning(f"Pandoc 导出失败: {e}")

        # 所有方案失败，抛出错误
        raise RuntimeError("所有 PDF 导出方案均失败，请安装 Playwright: pip install playwright && playwright install chromium")

    def _export_with_playwright(self, html_path: Path, output_path: Path) -> Path:
        """使用 Playwright 导出 PDF"""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(f"file://{html_path.absolute()}")
                page.wait_for_load_state("networkidle")

                page.pdf(
                    path=str(output_path),
                    format="A4",
                    margin={
                        "top": "2.5cm",
                        "right": "2.5cm",
                        "bottom": "2.5cm",
                        "left": "2.5cm"
                    },
                    display_header_footer=True,
                    header_template='<div style="font-size: 9px; width: 100%; text-align: center; color: #666;">Paper Interpreter</div>',
                    footer_template='<div style="font-size: 9px; width: 100%; text-align: center; color: #666;">第 <span class="pageNumber"></span> 页</div>'
                )

                browser.close()

            logger.info(f"PDF 导出成功 (Playwright): {output_path}")
            return output_path

        except ImportError:
            raise RuntimeError("Playwright 未安装")

    def _export_with_weasyprint(self, html_path: Path, output_path: Path) -> Path:
        """使用 WeasyPrint 导出 PDF"""
        try:
            from weasyprint import HTML, CSS

            html = HTML(filename=str(html_path))
            html.write_pdf(str(output_path))

            logger.info(f"PDF 导出成功 (WeasyPrint): {output_path}")
            return output_path

        except ImportError:
            raise RuntimeError("WeasyPrint 未安装")

    def _export_with_pandoc(self, html_path: Path, output_path: Path) -> Path:
        """使用 Pandoc 导出 PDF"""
        if not shutil.which("pandoc"):
            raise RuntimeError("Pandoc 未安装")

        # 先转换为 Markdown，再转 PDF
        md_path = html_path.with_suffix(".md")

        subprocess.run(
            ["pandoc", str(html_path), "-o", str(md_path)],
            check=True,
            capture_output=True
        )

        subprocess.run(
            [
                "pandoc",
                str(md_path),
                "-o", str(output_path),
                "--pdf-engine=xelatex",
                "-V", "geometry:margin=2.5cm",
                "-V", "CJKmainfont=Noto Serif CJK SC"
            ],
            check=True,
            capture_output=True
        )

        logger.info(f"PDF 导出成功 (Pandoc): {output_path}")
        return output_path
