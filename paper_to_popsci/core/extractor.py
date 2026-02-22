"""
PDF 内容提取模块
支持 unstructured (主) 和 PyPDF2 (降级)
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .config import Config
from .logger import logger


@dataclass
class PaperSection:
    """论文章节"""
    title: str
    content: str
    level: int = 1  # 标题层级 (1=H1, 2=H2, etc.)


@dataclass
class PaperContent:
    """论文内容数据结构"""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    institution: str = ""
    publication_date: str = ""
    arxiv_id: str = ""
    doi: str = ""
    sections: List[PaperSection] = field(default_factory=list)
    figures: List[Dict[str, Any]] = field(default_factory=list)
    references_count: int = 0
    raw_text: str = ""
    extraction_method: str = ""  # "unstructured" or "pypdf2"


class PDFExtractor:
    """PDF 内容提取器"""

    def __init__(self):
        self.extraction_method = None

    def extract(self, pdf_path: Path, metadata: Optional[Dict] = None) -> PaperContent:
        """
        提取 PDF 内容

        Args:
            pdf_path: PDF 文件路径
            metadata: 已有的元数据（从下载阶段获取）

        Returns:
            PaperContent: 论文内容对象
        """
        logger.info(f"开始提取 PDF 内容: {pdf_path}")

        content = PaperContent()

        # 填充已知元数据
        if metadata:
            content.title = metadata.get("title", "")
            content.authors = metadata.get("authors", [])
            content.abstract = metadata.get("abstract", "")
            content.publication_date = metadata.get("publication_date", "")
            content.arxiv_id = metadata.get("arxiv_id", "")
            content.doi = metadata.get("doi", "")

        # 尝试使用 unstructured 提取
        try:
            content = self._extract_with_unstructured(pdf_path, content)
            content.extraction_method = "unstructured"
            logger.info("使用 unstructured 成功提取内容")
        except Exception as e:
            logger.warning(f"unstructured 提取失败: {e}，降级到 PyPDF2")
            content = self._extract_with_pypdf2(pdf_path, content)
            content.extraction_method = "pypdf2"

        # 后处理
        content = self._post_process(content)

        logger.info(f"内容提取完成: {len(content.sections)} 个章节, {len(content.raw_text)} 字符")
        return content

    def _extract_with_unstructured(self, pdf_path: Path, content: PaperContent) -> PaperContent:
        """使用 unstructured 提取"""
        try:
            from unstructured.partition.pdf import partition_pdf
            from unstructured.documents.elements import (
                Title, NarrativeText, Text, Abstract, Author,
                Header, Footer, Image, Table
            )

            logger.info("使用 unstructured 提取...")

            # 分区提取
            elements = partition_pdf(
                str(pdf_path),
                strategy="hi_res",  # 高质量策略
                include_page_breaks=True,
                infer_table_structure=True,
            )

            # 处理元素
            current_section = None
            current_content = []

            for element in elements:
                # 提取标题
                if isinstance(element, Title):
                    # 保存上一个章节
                    if current_section and current_content:
                        current_section.content = "\n".join(current_content)
                        content.sections.append(current_section)

                    # 创建新章节
                    current_section = PaperSection(
                        title=str(element),
                        content="",
                        level=self._detect_heading_level(str(element), elements)
                    )
                    current_content = []

                # 提取摘要
                elif isinstance(element, Abstract):
                    if not content.abstract:
                        content.abstract = str(element)

                # 提取作者
                elif isinstance(element, Author):
                    if str(element) not in content.authors:
                        content.authors.append(str(element))

                # 提取正文
                elif isinstance(element, (NarrativeText, Text)):
                    text = str(element).strip()
                    if text:
                        if current_section:
                            current_content.append(text)
                        else:
                            # 没有章节时的内容放入 raw_text
                            content.raw_text += text + "\n"

                # 提取图片
                elif isinstance(element, Image):
                    content.figures.append({
                        "type": "image",
                        "description": str(element),
                    })

                # 提取表格
                elif isinstance(element, Table):
                    content.figures.append({
                        "type": "table",
                        "content": str(element),
                    })

            # 保存最后一个章节
            if current_section and current_content:
                current_section.content = "\n".join(current_content)
                content.sections.append(current_section)

            # 如果没有章节，将整个文本作为 raw_text
            if not content.sections:
                content.raw_text = "\n".join([str(e) for e in elements
                                               if hasattr(e, 'text')])

            return content

        except ImportError:
            logger.warning("unstructured 未安装，跳转到降级方案")
            raise
        except Exception as e:
            logger.warning(f"unstructured 处理出错: {e}")
            raise

    def _extract_with_pypdf2(self, pdf_path: Path, content: PaperContent) -> PaperContent:
        """使用 PyPDF2 降级提取"""
        try:
            import PyPDF2

            logger.info("使用 PyPDF2 降级提取...")

            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = len(reader.pages)

                full_text = ""
                for i, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            full_text += f"\n--- Page {i+1} ---\n{text}"
                    except Exception as e:
                        logger.warning(f"第 {i+1} 页提取失败: {e}")

            content.raw_text = full_text

            # 尝试提取标题（第一页的第一行）
            if not content.title:
                lines = [l.strip() for l in full_text.split("\n") if l.strip()]
                if lines:
                    # 通常标题在前几行，排除常见的页眉词
                    for line in lines[:10]:
                        if len(line) > 20 and not any(x in line.lower() for x in ["arxiv", "proceedings", "conference"]):
                            content.title = line
                            break

            # 尝试提取摘要
            if not content.abstract:
                abstract_match = re.search(
                    r'(?i)abstract[\s:]*(.+?)(?=\n\s*\n|\n\s*(?:introduction|1\s|i\s))',
                    full_text,
                    re.DOTALL
                )
                if abstract_match:
                    content.abstract = abstract_match.group(1).strip()[:2000]

            # 将整个文本作为一个章节
            if full_text:
                content.sections.append(PaperSection(
                    title="论文内容",
                    content=full_text[:10000],  # 限制长度
                    level=1
                ))

            return content

        except ImportError:
            logger.error("PyPDF2 未安装，无法提取内容")
            raise RuntimeError("PDF 提取库未安装，请安装 unstructured 或 PyPDF2")
        except Exception as e:
            logger.error(f"PyPDF2 提取失败: {e}")
            raise

    def _detect_heading_level(self, text: str, elements) -> int:
        """检测标题层级"""
        # 简单的启发式规则
        text_lower = text.lower()

        # 一级标题通常包含这些词
        level1_keywords = ['introduction', 'abstract', 'conclusion', 'references',
                          'acknowledgment', 'related work', 'experiments']
        if any(kw in text_lower for kw in level1_keywords):
            return 1

        # 根据字体大小判断（如果可用）
        # 这里简化处理
        if len(text) < 50:
            return 2

        return 1

    def _post_process(self, content: PaperContent) -> PaperContent:
        """后处理提取的内容"""
        # 清理标题
        if content.title:
            content.title = self._clean_text(content.title)

        # 清理摘要
        if content.abstract:
            content.abstract = self._clean_text(content.abstract)
            # 限制摘要长度
            if len(content.abstract) > 3000:
                content.abstract = content.abstract[:3000] + "..."

        # 清理作者
        content.authors = [self._clean_text(a) for a in content.authors if a.strip()]

        # 提取机构信息（从第一页或作者注释）
        if not content.institution and content.raw_text:
            # 尝试匹配常见的机构格式（支持中英文）
            patterns = [
                r'(?i)([^\n]*?(?:university|college|institute|laboratory|lab|研究所|大学|学院)[^\n]{0,50})',
                r'(?i)([^\n]*?(?:dept\.|department)[^\n]{0,50})',
                r'(?i)([^\n]*?(?:school of)[^\n]{0,50})',
            ]
            
            for pattern in patterns:
                inst_match = re.search(pattern, content.raw_text[:2000])
                if inst_match:
                    institution = self._clean_text(inst_match.group(1))
                    # 过滤掉太短或太长的结果
                    if 5 < len(institution) < 100:
                        content.institution = institution
                        break

        return content

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = text.replace('\x00', '')
        # 去除首尾空白
        return text.strip()
