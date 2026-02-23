"""
多格式导出器 - 支持 HTML、PDF、Word、Markdown
确保图片在所有格式中正常显示
"""
import base64
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from io import BytesIO
from .config import Config
from .logger import logger


class MultiFormatExporter:
    """多格式导出器"""

    def __init__(self):
        self.style = Config.STYLE

    def export(self, article_sections, paper_content, output_dir: Path, formats: List[str] = None) -> Dict[str, Path]:
        """
        导出多种格式

        Args:
            article_sections: 文章章节列表
            paper_content: 论文内容对象
            output_dir: 输出目录
            formats: 要导出的格式列表 ['html', 'pdf', 'docx', 'md']，默认全部

        Returns:
            格式到文件路径的映射
        """
        if formats is None:
            formats = ['html', 'pdf', 'docx', 'md']

        results = {}

        # 首先生成 HTML（基础格式）
        html_path = output_dir / "article.html"
        html_content = self._generate_html(article_sections, paper_content)
        html_path.write_text(html_content, encoding='utf-8')
        results['html'] = html_path
        logger.info(f"HTML 导出成功: {html_path}")

        # 导出 PDF
        if 'pdf' in formats:
            try:
                pdf_path = self._export_pdf(html_path, output_dir)
                if pdf_path and pdf_path.exists():
                    results['pdf'] = pdf_path
                    logger.info(f"PDF 导出成功: {pdf_path}")
                else:
                    logger.warning("PDF 导出失败: 未生成有效文件")
            except Exception as e:
                logger.warning(f"PDF 导出失败: {e}")

        # 导出 Word
        if 'docx' in formats:
            try:
                docx_path = self._export_docx(article_sections, paper_content, output_dir)
                if docx_path and docx_path.exists():
                    results['docx'] = docx_path
                    logger.info(f"Word 导出成功: {docx_path}")
                else:
                    logger.warning("Word 导出失败: 未生成有效文件")
            except Exception as e:
                logger.warning(f"Word 导出失败: {e}")

        # 导出 Markdown
        if 'md' in formats:
            try:
                md_path = self._export_markdown(article_sections, paper_content, output_dir)
                if md_path and md_path.exists():
                    results['md'] = md_path
                    logger.info(f"Markdown 导出成功: {md_path}")
                else:
                    logger.warning("Markdown 导出失败: 未生成有效文件")
            except Exception as e:
                logger.warning(f"Markdown 导出失败: {e}")

        return results

    def _generate_html(self, article_sections, paper_content) -> str:
        """生成完整 HTML"""
        from .renderer import HTMLRenderer
        renderer = HTMLRenderer()
        # 使用临时文件方式获取HTML内容
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            temp_path = Path(f.name)

        # 渲染到临时文件
        renderer.render(article_sections, paper_content, temp_path)
        html_content = temp_path.read_text(encoding='utf-8')
        temp_path.unlink()
        return html_content

    def _export_pdf(self, html_path: Path, output_dir: Path) -> Path:
        """导出 PDF"""
        from .renderer import PDFExporter
        pdf_path = output_dir / "article.pdf"
        exporter = PDFExporter()
        return exporter.export(html_path, pdf_path)

    def _export_docx(self, article_sections, paper_content, output_dir: Path) -> Path:
        """导出 Word 文档（DOCX）- 包含图片"""
        try:
            from docx import Document
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.enum.style import WD_STYLE_TYPE
        except ImportError:
            raise RuntimeError("python-docx 未安装，请运行: pip install python-docx")

        doc = Document()

        # 设置文档样式 - 暖米色主题
        style = doc.styles['Normal']
        style.font.name = 'Noto Sans SC'
        style.font.size = Pt(11)
        style.paragraph_format.line_spacing = 1.8
        style.paragraph_format.space_after = Pt(12)

        # 添加标题样式
        title_style = doc.styles.add_style('CustomTitle', WD_STYLE_TYPE.PARAGRAPH)
        title_style.font.name = 'Noto Serif SC'
        title_style.font.size = Pt(24)
        title_style.font.bold = True
        title_style.font.color.rgb = RGBColor(44, 62, 80)  # #2C3E50
        title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 处理每个章节
        for section in article_sections:
            section_type = section.section_type
            title = section.title
            content = section.content
            image_path = section.image_path

            if section_type == "hero":
                self._add_hero_to_docx(doc, title, content, image_path)
            elif section_type == "paper_info":
                self._add_paper_info_to_docx(doc, title, content)
            elif section_type == "recommendations":
                self._add_recommendations_to_docx(doc, title, content)
            else:
                self._add_section_to_docx(doc, title, content, image_path)

        # 保存文档
        docx_path = output_dir / "article.docx"
        doc.save(str(docx_path))
        return docx_path

    def _add_hero_to_docx(self, doc: 'Document', title: str, content: str, image_path: Optional[str]):
        """添加 Hero 区到 Word"""
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        lines = content.split("\n")
        main_title = lines[0].strip() if lines else title

        # 主标题
        title_para = doc.add_paragraph()
        title_run = title_para.add_run(main_title)
        title_run.font.name = 'Noto Serif SC'
        title_run.font.size = Pt(28)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(44, 62, 80)
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 副标题
        if len(lines) > 1:
            subtitle = lines[1].strip()
            subtitle_para = doc.add_paragraph()
            subtitle_run = subtitle_para.add_run(subtitle)
            subtitle_run.font.name = 'Noto Sans SC'
            subtitle_run.font.size = Pt(14)
            subtitle_run.font.color.rgb = RGBColor(22, 160, 133)  # #16A085
            subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 元信息
        for line in lines[2:]:
            if line.strip() and "**" in line:
                meta_para = doc.add_paragraph()
                meta_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                # 清理 Markdown 标记
                clean_line = line.replace("**", "").strip()
                meta_run = meta_para.add_run(clean_line)
                meta_run.font.size = Pt(10)
                meta_run.font.color.rgb = RGBColor(102, 102, 102)

        # 添加图片
        if image_path and Path(image_path).exists():
            try:
                doc.add_paragraph()  # 空行
                img_para = doc.add_paragraph()
                img_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = img_para.add_run()
                run.add_picture(str(image_path), width=Inches(5))
                doc.add_paragraph()  # 空行
            except Exception as e:
                logger.warning(f"Word 图片添加失败: {e}")

        # 分隔线
        doc.add_paragraph("_" * 60)
        doc.add_paragraph()

    def _add_section_to_docx(self, doc: 'Document', title: str, content: str, image_path: Optional[str]):
        """添加标准章节到 Word"""
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        # 章节标题
        heading = doc.add_heading(level=2)
        heading_run = heading.add_run(title)
        heading_run.font.name = 'Noto Serif SC'
        heading_run.font.size = Pt(18)
        heading_run.font.color.rgb = RGBColor(44, 62, 80)
        heading_run.font.bold = True

        # 处理内容 - 清理 Markdown
        clean_content = self._clean_markdown_for_word(content)

        # 分段添加
        paragraphs = clean_content.split('\n\n')
        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue

            # 处理术语注解
            para_text = self._process_terms_for_word(para_text)

            para = doc.add_paragraph()
            para.paragraph_format.line_spacing = 1.8
            para.paragraph_format.space_after = Pt(12)

            # 简单处理：直接添加文本
            run = para.add_run(para_text)
            run.font.name = 'Noto Sans SC'
            run.font.size = Pt(11)

        # 添加图片
        if image_path and Path(image_path).exists():
            try:
                doc.add_paragraph()  # 空行
                img_para = doc.add_paragraph()
                img_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = img_para.add_run()
                run.add_picture(str(image_path), width=Inches(5.5))

                # 图片说明
                caption = doc.add_paragraph()
                caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap_run = caption.add_run(f"图：{title}")
                cap_run.font.size = Pt(9)
                cap_run.font.italic = True
                cap_run.font.color.rgb = RGBColor(128, 128, 128)

                doc.add_paragraph()  # 空行
            except Exception as e:
                logger.warning(f"Word 图片添加失败: {e}")

    def _add_paper_info_to_docx(self, doc: 'Document', title: str, content: str):
        """添加论文信息到 Word"""
        from docx.shared import Pt, RGBColor

        # 分隔
        doc.add_paragraph()
        doc.add_paragraph("_" * 60)

        # 标题
        heading = doc.add_heading(level=2)
        heading_run = heading.add_run(title)
        heading_run.font.name = 'Noto Serif SC'
        heading_run.font.size = Pt(14)
        heading_run.font.color.rgb = RGBColor(128, 128, 128)

        # 信息项
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 清理 Markdown
            clean_line = line.replace("**", "").strip()
            if clean_line.startswith("-"):
                clean_line = clean_line[1:].strip()

            if clean_line and ":" in clean_line:
                parts = clean_line.split(":", 1)
                label = parts[0].strip()
                value = parts[1].strip() if len(parts) > 1 else ""

                para = doc.add_paragraph()
                para.paragraph_format.space_after = Pt(6)

                # 标签加粗
                label_run = para.add_run(f"{label}: ")
                label_run.font.name = 'Noto Sans SC'
                label_run.font.bold = True
                label_run.font.size = Pt(10)

                # 值
                if value:
                    value_run = para.add_run(value)
                    value_run.font.name = 'Noto Sans SC'
                    value_run.font.size = Pt(10)

    def _add_recommendations_to_docx(self, doc: 'Document', title: str, content: str):
        """添加推荐章节到 Word"""
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        # 标题
        heading = doc.add_heading(level=2)
        heading_run = heading.add_run(title)
        heading_run.font.name = 'Noto Serif SC'
        heading_run.font.size = Pt(18)
        heading_run.font.color.rgb = RGBColor(44, 62, 80)
        heading_run.font.bold = True

        # 说明文字
        intro_para = doc.add_paragraph()
        intro_run = intro_para.add_run("基于学术论文引用网络和语义相似度分析，为您推荐以下相关研究：")
        intro_run.font.name = 'Noto Sans SC'
        intro_run.font.size = Pt(11)
        intro_run.font.italic = True
        intro_para.paragraph_format.space_after = Pt(12)

        # 处理内容
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过说明文字（已添加）
            if '基于学术论文引用网络' in line or line == '---':
                continue

            # 处理子标题
            if line.startswith('###'):
                sub_heading = doc.add_heading(level=3)
                sub_run = sub_heading.add_run(line.replace('###', '').strip())
                sub_run.font.name = 'Noto Serif SC'
                sub_run.font.size = Pt(14)
                sub_run.font.color.rgb = RGBColor(22, 160, 133)
                sub_run.font.bold = True
                sub_heading.paragraph_format.space_before = Pt(12)
                sub_heading.paragraph_format.space_after = Pt(6)

            # 处理论文标题（**数字. 标题**）
            elif re.match(r'\*\*\d+\.', line):
                # 提取数字和标题
                match = re.match(r'\*\*(\d+)\.\s*([^*]+)\*\*', line)
                if match:
                    num, paper_title = match.groups()
                    title_para = doc.add_paragraph()
                    title_para.paragraph_format.space_before = Pt(8)
                    title_para.paragraph_format.space_after = Pt(4)

                    num_run = title_para.add_run(f"{num}. ")
                    num_run.font.name = 'Noto Sans SC'
                    num_run.font.size = Pt(12)
                    num_run.font.bold = True
                    num_run.font.color.rgb = RGBColor(22, 160, 133)

                    title_run = title_para.add_run(paper_title)
                    title_run.font.name = 'Noto Serif SC'
                    title_run.font.size = Pt(12)
                    title_run.font.bold = True

            # 处理列表项
            elif line.startswith('- **'):
                clean_line = line.replace('- **', '').replace('**', '', 1).strip()
                if ':' in clean_line:
                    label, value = clean_line.split(':', 1)
                    item_para = doc.add_paragraph()
                    item_para.paragraph_format.left_indent = Inches(0.3)
                    item_para.paragraph_format.space_after = Pt(3)

                    label_run = item_para.add_run(f"{label}: ")
                    label_run.font.name = 'Noto Sans SC'
                    label_run.font.size = Pt(10)
                    label_run.font.bold = True

                    value_run = item_para.add_run(value.strip())
                    value_run.font.name = 'Noto Sans SC'
                    value_run.font.size = Pt(10)

            # 处理普通段落
            elif line and not line.startswith('#'):
                para = doc.add_paragraph()
                para.paragraph_format.left_indent = Inches(0.3)
                para.paragraph_format.space_after = Pt(4)

                run = para.add_run(line)
                run.font.name = 'Noto Sans SC'
                run.font.size = Pt(10)

    def _clean_markdown_for_word(self, text: str) -> str:
        """清理 Markdown 标记以便 Word 显示"""
        # 移除代码块标记
        text = re.sub(r'```\w*\n?', '', text)
        text = re.sub(r'```', '', text)

        # 将加粗 **text** 转换为普通文本（Word 会处理）
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)

        # 将斜体 *text* 转换为普通文本
        text = re.sub(r'\*(.+?)\*', r'\1', text)

        # 将列表标记转换为中文数字
        lines = text.split('\n')
        result_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                line = f"• {line[2:]}"
            elif re.match(r'^\d+\.', line):
                line = line
            result_lines.append(line)

        return '\n\n'.join(result_lines)

    def _process_terms_for_word(self, text: str) -> str:
        """处理术语注解为 Word 友好格式"""
        # 将 *术语（解释）* 转换为 "术语（解释）"
        pattern = r'\*([^*（]+?)（(.+?)）\*'

        def replace_term(match):
            term = match.group(1)
            explanation = match.group(2)
            return f"{term}（{explanation}）"

        return re.sub(pattern, replace_term, text)

    def _export_markdown(self, article_sections, paper_content, output_dir: Path) -> Path:
        """导出 Markdown（包含 base64 图片）"""
        md_content = []

        # 添加 YAML frontmatter
        md_content.append("---")
        md_content.append(f'title: "{paper_content.title or "论文解读"}"')
        md_content.append(f'author: "Paper Interpreter"')
        md_content.append(f'date: "{paper_content.publication_date or ""}"')
        md_content.append("---")
        md_content.append("")

        # 处理每个章节
        for section in article_sections:
            section_type = section.section_type
            title = section.title
            content = section.content
            image_path = section.image_path

            if section_type == "hero":
                # Hero 区特殊处理
                lines = content.split("\n")
                if lines:
                    md_content.append(f"# {lines[0]}")
                    if len(lines) > 1:
                        md_content.append(f"")
                        md_content.append(f"> {lines[1]}")
                    md_content.append("")
                    # 元信息
                    for line in lines[2:]:
                        if line.strip():
                            clean_line = line.replace("**", "")
                            md_content.append(f"*{clean_line}*")
                    md_content.append("")
            elif section_type == "paper_info":
                md_content.append(f"## {title}")
                md_content.append("")
                lines = content.split("\n")
                for line in lines:
                    if line.strip():
                        clean_line = line.replace("**", "**")
                        md_content.append(clean_line)
                md_content.append("")
            else:
                # 标准章节
                md_content.append(f"## {title}")
                md_content.append("")

                # 处理内容
                clean_content = self._clean_markdown_for_md(content)
                md_content.append(clean_content)
                md_content.append("")

            # 添加图片（base64 嵌入）
            if image_path and Path(image_path).exists():
                try:
                    base64_img = self._image_to_base64(image_path)
                    if base64_img:
                        ext = Path(image_path).suffix.lower().replace('.', '')
                        if ext == 'jpg':
                            ext = 'jpeg'
                        md_content.append(f"![{title}]({base64_img})")
                        md_content.append(f"*图：{title}*")
                        md_content.append("")
                except Exception as e:
                    logger.warning(f"Markdown 图片嵌入失败: {e}")

        # 保存
        md_path = output_dir / "article.md"
        md_path.write_text('\n'.join(md_content), encoding='utf-8')
        return md_path

    def _clean_markdown_for_md(self, text: str) -> str:
        """清理 Markdown 内容"""
        # 处理术语注解
        pattern = r'\*([^*（]+?)（(.+?)）\*'

        def replace_term(match):
            term = match.group(1)
            explanation = match.group(2)
            return f"**{term}**（{explanation}）"

        text = re.sub(pattern, replace_term, text)

        # 清理其他标记
        text = re.sub(r'```\w*\n?', '', text)
        text = re.sub(r'```', '', text)

        return text.strip()

    def _image_to_base64(self, image_path: str) -> str:
        """将图片转换为 base64"""
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')

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
