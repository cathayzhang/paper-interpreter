#!/usr/bin/env python3
"""
Paper to PopSci - 命令行入口

用法:
    python -m paper_to_popsci.cli <论文链接>

示例:
    python -m paper_to_popsci.cli https://arxiv.org/abs/2312.00752
"""
import sys
import time
import json
import shutil
from pathlib import Path
from datetime import datetime
import argparse
from typing import Optional

from .core.config import Config
from .core.logger import logger
from .core.downloader import PaperDownloader
from .core.extractor import PDFExtractor
from .core.analyzer import ContentAnalyzer
from .core.illustrator import IllustrationGenerator
from .core.writer import ArticleWriter
from .core.renderer import HTMLRenderer, PDFExporter


def sanitize_filename(name: str) -> str:
    """清理文件名"""
    # 移除或替换不安全字符
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        name = name.replace(char, '_')
    # 限制长度
    if len(name) > 100:
        name = name[:100]
    return name.strip()


def process_paper(url: str, output_dir: Optional[str] = None) -> dict:
    """
    处理论文的主流程

    Args:
        url: 论文链接
        output_dir: 输出目录（可选）

    Returns:
        处理结果字典
    """
    start_time = time.time()

    logger.info("=" * 60)
    logger.info(f"开始处理论文: {url}")
    logger.info("=" * 60)

    # 1. 下载论文
    logger.info("\n[1/7] 下载论文...")
    downloader = PaperDownloader()
    try:
        pdf_path, metadata = downloader.download(url)
        logger.info(f"✓ 论文下载成功: {pdf_path}")
    except Exception as e:
        logger.error(f"✗ 论文下载失败: {e}")
        return {"success": False, "error": f"下载失败: {e}"}

    # 2. 提取内容
    logger.info("\n[2/7] 提取 PDF 内容...")
    extractor = PDFExtractor()
    try:
        paper_content = extractor.extract(pdf_path, metadata)
        logger.info(f"✓ 内容提取成功: {len(paper_content.sections)} 个章节")
        logger.info(f"  标题: {paper_content.title[:60] if paper_content.title else 'N/A'}...")
        logger.info(f"  作者: {', '.join(paper_content.authors[:3]) if paper_content.authors else 'N/A'}")
    except Exception as e:
        logger.error(f"✗ 内容提取失败: {e}")
        return {"success": False, "error": f"提取失败: {e}"}

    # 确定输出目录
    if output_dir:
        work_dir = Path(output_dir)
    else:
        paper_title = sanitize_filename(paper_content.title or "untitled")
        work_dir = Path(Config.OUTPUT_DIR) / f"{paper_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 如果目录已存在，添加时间戳
    if work_dir.exists():
        work_dir = Path(str(work_dir) + f"_{int(time.time())}")

    work_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = work_dir / "assets" / "images"
    assets_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"  输出目录: {work_dir}")

    # 保存元数据
    metadata_path = work_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({
            "source_url": url,
            "title": paper_content.title,
            "authors": paper_content.authors,
            "publication_date": paper_content.publication_date,
            "arxiv_id": paper_content.arxiv_id,
            "doi": paper_content.doi,
            "extraction_method": paper_content.extraction_method,
        }, f, ensure_ascii=False, indent=2)

    # 3. 分析内容
    logger.info("\n[3/7] 分析论文内容...")
    analyzer = ContentAnalyzer()
    try:
        analysis_result = analyzer.analyze(paper_content)
        outline = analysis_result["outline"]
        illustration_prompts = analysis_result["illustration_prompts"]
        logger.info(f"✓ 分析完成: 类型={outline.get('article_type', 'N/A')}")
        logger.info(f"  核心创新: {outline.get('core_innovation', 'N/A')[:60]}...")
    except Exception as e:
        logger.warning(f"⚠ 内容分析失败: {e}，使用默认大纲")
        analysis_result = analyzer._get_default_outline(paper_content)
        outline = analysis_result["outline"]
        illustration_prompts = analysis_result["illustration_prompts"]

    # 4. 生成配图
    logger.info("\n[4/7] 生成配图...")
    illustrator = IllustrationGenerator()
    try:
        illustrations = illustrator.generate_all(illustration_prompts, assets_dir)
        success_count = sum(1 for ill in illustrations if ill.get("success"))
        logger.info(f"✓ 配图生成完成: {success_count}/{len(illustrations)} 张成功")
    except Exception as e:
        logger.warning(f"⚠ 配图生成失败: {e}")
        illustrations = []

    # 5. 生成文章
    logger.info("\n[5/7] 生成文章...")
    writer = ArticleWriter()
    try:
        article_sections = writer.write(paper_content, analysis_result, illustrations)
        word_count = sum(len(section.content) for section in article_sections)
        logger.info(f"✓ 文章生成完成: {len(article_sections)} 个章节, {word_count} 字")
    except Exception as e:
        logger.error(f"✗ 文章生成失败: {e}")
        return {"success": False, "error": f"写作失败: {e}"}

    # 6. 渲染 HTML
    logger.info("\n[6/7] 渲染 HTML...")
    html_renderer = HTMLRenderer()
    try:
        html_path = work_dir / "article.html"
        html_renderer.render(article_sections, paper_content, html_path)
        logger.info(f"✓ HTML 渲染完成: {html_path}")
    except Exception as e:
        logger.error(f"✗ HTML 渲染失败: {e}")
        return {"success": False, "error": f"渲染失败: {e}"}

    # 7. 导出 PDF
    logger.info("\n[7/7] 导出 PDF...")
    pdf_exporter = PDFExporter()
    try:
        pdf_path = work_dir / "article.pdf"
        result_path = pdf_exporter.export(html_path, pdf_path)
        if result_path == pdf_path:
            logger.info(f"✓ PDF 导出成功: {pdf_path}")
        else:
            logger.warning(f"⚠ PDF 导出失败，保留 HTML: {result_path}")
    except Exception as e:
        logger.warning(f"⚠ PDF 导出失败: {e}")
        pdf_path = None

    # 清理临时文件
    try:
        shutil.rmtree(pdf_path.parent / "assets" / "temp", ignore_errors=True)
    except:
        pass

    # 统计
    elapsed_time = time.time() - start_time

    result = {
        "success": True,
        "output_dir": str(work_dir),
        "files": {
            "html": str(html_path) if html_path.exists() else None,
            "pdf": str(pdf_path) if pdf_path and pdf_path.exists() else None,
            "metadata": str(metadata_path),
        },
        "statistics": {
            "illustrations_generated": sum(1 for ill in illustrations if ill.get("success")),
            "illustrations_total": len(illustrations),
            "article_sections": len(article_sections),
            "word_count": word_count,
            "elapsed_time": round(elapsed_time, 2),
        },
        "paper_info": {
            "title": paper_content.title,
            "authors": paper_content.authors,
            "publication_date": paper_content.publication_date,
        }
    }

    # 输出结果
    logger.info("\n" + "=" * 60)
    logger.info("✅ 论文解读完成!")
    logger.info("=" * 60)
    logger.info(f"\n📄 论文: {paper_content.title or 'N/A'}")
    logger.info(f"📁 输出目录: {work_dir}")
    logger.info(f"\n生成文件:")
    logger.info(f"  ├── article.html")
    if pdf_path and pdf_path.exists():
        logger.info(f"  ├── article.pdf")
    logger.info(f"  ├── assets/images/ ({result['statistics']['illustrations_generated']} 张配图)")
    logger.info(f"  └── metadata.json")
    logger.info(f"\n📊 统计:")
    logger.info(f"  • 文章字数: {word_count} 字")
    logger.info(f"  • 处理耗时: {elapsed_time:.1f} 秒")

    return result


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="Paper to PopSci - 将学术论文转换为通俗易懂的科普文章",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s https://arxiv.org/abs/2312.00752
  %(prog)s https://doi.org/10.1145/276675.276685 -o ./output
        """
    )

    parser.add_argument(
        "url",
        help="论文链接 (支持 arXiv, DOI, OpenReview, Semantic Scholar 等)"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_dir",
        help="输出目录 (默认: ./paper_outputs/论文标题_时间戳/)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细日志"
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        import logging
        logging.getLogger("paper_to_popsci").setLevel(logging.DEBUG)

    # 处理论文
    result = process_paper(args.url, args.output_dir)

    # 返回状态码
    if result["success"]:
        sys.exit(0)
    else:
        logger.error(f"\n处理失败: {result.get('error', '未知错误')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
