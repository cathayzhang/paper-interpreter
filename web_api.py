"""
Web API 接口 - 用于集成到 getainote.com
提供 RESTful API 供前端调用
"""
import os
import tempfile
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uvicorn

from paper_to_popsci.core.downloader import PaperDownloader
from paper_to_popsci.core.extractor import PDFExtractor
from paper_to_popsci.core.analyzer import ContentAnalyzer
from paper_to_popsci.core.illustrator import IllustrationGenerator
from paper_to_popsci.core.writer import ArticleWriter
from paper_to_popsci.core.renderer import HTMLRenderer, PDFExporter
from paper_to_popsci.core.config import Config
from paper_to_popsci.core.logger import logger

app = FastAPI(
    title="Paper Interpreter API",
    description="将学术论文转换为通俗科普文章",
    version="2.0.0"
)

# CORS 配置 - 允许 getainote.com 访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://getainote.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储任务状态
tasks = {}


class PaperRequest(BaseModel):
    url: HttpUrl
    email: Optional[str] = None  # 可选：完成后发送邮件通知
    illustration_count: int = 3  # 配图数量，默认3张


class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    result: Optional[dict] = None
    error: Optional[str] = None


def process_paper_task(task_id: str, url: str, illustration_count: int):
    """后台处理任务"""
    try:
        tasks[task_id] = {"status": "processing", "progress": 10}

        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Step 1: 下载论文
            tasks[task_id]["progress"] = 20
            downloader = PaperDownloader()
            pdf_path = downloader.download(str(url), output_dir)

            if not pdf_path:
                raise Exception("论文下载失败")

            # Step 2: 提取内容
            tasks[task_id]["progress"] = 30
            extractor = PDFExtractor()
            paper_content = extractor.extract(pdf_path)

            # Step 3: 分析内容
            tasks[task_id]["progress"] = 40
            analyzer = ContentAnalyzer()
            outline = analyzer.analyze(paper_content)

            # Step 4: 生成配图
            tasks[task_id]["progress"] = 50
            prompts = analyzer.generate_illustration_prompts(outline)
            # 限制配图数量
            prompts = prompts[:illustration_count]

            illustrator = IllustrationGenerator()
            illustrations = illustrator.generate_all(prompts, output_dir / "images")

            # Step 5: 生成文章
            tasks[task_id]["progress"] = 70
            writer = ArticleWriter()
            article_sections = writer.write(paper_content, outline, illustrations)

            # Step 6: 渲染 HTML
            tasks[task_id]["progress"] = 85
            renderer = HTMLRenderer()
            html_content = renderer.render(article_sections, paper_content)
            html_path = output_dir / "article.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Step 7: 导出 PDF
            tasks[task_id]["progress"] = 95
            pdf_exporter = PDFExporter()
            pdf_path = output_dir / "article.pdf"
            pdf_exporter.export(html_path, pdf_path)

            # 保存结果到持久存储（如 S3）
            tasks[task_id]["progress"] = 100
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = {
                "paper_title": paper_content.title,
                "html_url": f"/download/{task_id}/article.html",
                "pdf_url": f"/download/{task_id}/article.pdf",
                "illustration_count": len([i for i in illustrations if i.get("success")]),
            }

    except Exception as e:
        logger.error(f"任务处理失败: {e}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)


@app.post("/api/paper/interpret", response_model=TaskStatus)
async def interpret_paper(request: PaperRequest, background_tasks: BackgroundTasks):
    """
    提交论文解读任务

    - **url**: 论文链接 (arXiv, DOI, OpenReview 等)
    - **email**: 可选，完成后发送邮件
    - **illustration_count**: 配图数量 (默认3张)
    """
    import uuid
    task_id = str(uuid.uuid4())

    tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "url": str(request.url)
    }

    # 后台异步处理
    background_tasks.add_task(
        process_paper_task,
        task_id,
        str(request.url),
        request.illustration_count
    )

    return TaskStatus(
        task_id=task_id,
        status="pending",
        progress=0
    )


@app.get("/api/paper/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """查询任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        progress=task.get("progress", 0),
        result=task.get("result"),
        error=task.get("error")
    )


@app.get("/api/paper/download/{task_id}/{filename}")
async def download_result(task_id: str, filename: str):
    """下载生成的文件"""
    # 实际应用中应该从 S3 或持久化存储获取
    # 这里简化处理
    raise HTTPException(status_code=501, detail="请配置文件存储服务 (S3/阿里云OSS)")


@app.get("/")
async def root():
    """API 根路径 - 欢迎页面"""
    return {
        "message": "Paper Interpreter API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "interpret_paper": "POST /api/paper/interpret",
            "get_status": "GET /api/paper/status/{task_id}",
            "download": "GET /api/paper/download/{task_id}/{filename}"
        }
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    # 生产环境建议使用 gunicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
