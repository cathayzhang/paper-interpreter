"""
论文下载模块
支持 arXiv、DOI、OpenReview、Semantic Scholar 和通用 PDF 链接
"""
import re
import time
import requests
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Optional, Tuple

from .config import Config
from .logger import logger


class PaperDownloader:
    """论文下载器"""

    # 浏览器请求头
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def download(self, url: str, output_dir: Optional[Path] = None) -> Tuple[Path, dict]:
        """
        下载论文

        Args:
            url: 论文链接
            output_dir: 输出目录，默认使用临时目录

        Returns:
            (pdf_path, metadata): PDF 文件路径和元数据
        """
        logger.info(f"开始下载论文: {url}")

        if output_dir is None:
            output_dir = Path(Config.TEMP_DIR) / str(int(time.time()))
        output_dir.mkdir(parents=True, exist_ok=True)

        # 解析链接类型
        link_type = self._detect_link_type(url)
        logger.info(f"检测到链接类型: {link_type}")

        # 根据类型选择下载策略
        if link_type == "arxiv":
            pdf_path, metadata = self._download_arxiv(url, output_dir)
        elif link_type == "doi":
            pdf_path, metadata = self._download_doi(url, output_dir)
        elif link_type == "openreview":
            pdf_path, metadata = self._download_openreview(url, output_dir)
        elif link_type == "semanticscholar":
            pdf_path, metadata = self._download_semanticscholar(url, output_dir)
        elif link_type == "googlescholar":
            pdf_path, metadata = self._download_googlescholar(url, output_dir)
        else:
            # 通用下载方案
            pdf_path, metadata = self._download_generic(url, output_dir)

        # 验证 PDF
        if not self._validate_pdf(pdf_path):
            logger.warning("PDF 验证失败，尝试备用方案...")
            # 尝试使用 wget/curl
            pdf_path = self._try_wget_curl(url, output_dir)

        logger.info(f"论文下载完成: {pdf_path}")
        return pdf_path, metadata

    def _detect_link_type(self, url: str) -> str:
        """检测链接类型"""
        url_lower = url.lower()

        if "arxiv.org" in url_lower:
            return "arxiv"
        elif "doi.org" in url_lower or url_lower.startswith("10."):
            return "doi"
        elif "openreview.net" in url_lower:
            return "openreview"
        elif "semanticscholar.org" in url_lower:
            return "semanticscholar"
        elif "scholar.google.com" in url_lower or "google.com/scholar" in url_lower:
            return "googlescholar"
        elif url_lower.endswith(".pdf"):
            return "pdf_direct"
        else:
            return "generic"

    def _download_arxiv(self, url: str, output_dir: Path) -> Tuple[Path, dict]:
        """下载 arXiv 论文"""
        # 提取 arXiv ID
        patterns = [
            r"arxiv\.org/abs/(\d+\.\d+)",
            r"arxiv\.org/pdf/(\d+\.\d+)",
            r"arxiv\.org/abs/(\d+)",
            r"arxiv\.org/pdf/(\d+)",
        ]

        arxiv_id = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                arxiv_id = match.group(1)
                break

        if not arxiv_id:
            logger.warning("无法提取 arXiv ID，尝试通用下载")
            return self._download_generic(url, output_dir)

        # 构造 PDF URL
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        # 获取元数据
        metadata = self._fetch_arxiv_metadata(arxiv_id)
        metadata["arxiv_id"] = arxiv_id
        metadata["source_url"] = url

        # 下载 PDF
        pdf_path = output_dir / f"{arxiv_id}.pdf"
        self._download_file(pdf_url, pdf_path)

        return pdf_path, metadata

    def _fetch_arxiv_metadata(self, arxiv_id: str) -> dict:
        """获取 arXiv 元数据"""
        try:
            api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            response = self.session.get(api_url, timeout=Config.DEFAULT_TIMEOUT_SECONDS)
            response.raise_for_status()

            # 解析 XML
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.content)

            # 命名空间
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom",
            }

            entry = root.find(".//atom:entry", ns)
            if entry is None:
                return {}

            def get_text(tag, ns_map=None):
                elem = entry.find(tag, ns_map or ns)
                return elem.text if elem is not None else ""

            # 提取日期
            published = get_text("atom:published")
            if published:
                # 格式: 2023-12-01T00:00:00Z -> 2023年12月
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    pub_date = f"{dt.year}年{dt.month}月"
                except:
                    pub_date = published[:7]  # 2023-12
            else:
                # 从 arXiv ID 推断
                if len(arxiv_id) >= 4 and arxiv_id[:2].isdigit():
                    yy, mm = arxiv_id[:2], arxiv_id[2:4]
                    year = 2000 + int(yy)
                    pub_date = f"{year}年{int(mm)}月"
                else:
                    pub_date = "未知日期"

            return {
                "title": get_text("atom:title"),
                "authors": [author.find("atom:name", ns).text for author in entry.findall("atom:author", ns) if author.find("atom:name", ns) is not None],
                "abstract": get_text("atom:summary"),
                "publication_date": pub_date,
                "doi": get_text("arxiv:doi", {"arxiv": "http://arxiv.org/schemas/atom"}),
            }
        except Exception as e:
            logger.warning(f"获取 arXiv 元数据失败: {e}")
            # 从 ID 推断日期
            if len(arxiv_id) >= 4 and arxiv_id[:2].isdigit():
                yy, mm = arxiv_id[:2], arxiv_id[2:4]
                year = 2000 + int(yy)
                pub_date = f"{year}年{int(mm)}月"
            else:
                pub_date = "未知日期"

            return {
                "title": "",
                "authors": [],
                "abstract": "",
                "publication_date": pub_date,
                "doi": "",
            }

    def _download_doi(self, url: str, output_dir: Path) -> Tuple[Path, dict]:
        """下载 DOI 论文"""
        # 解析 DOI
        if url.startswith("http"):
            # 访问 doi.org 获取重定向
            response = self.session.head(url, allow_redirects=True, timeout=Config.DEFAULT_TIMEOUT_SECONDS)
            final_url = response.url
            doi = url.split("doi.org/")[-1]
        else:
            doi = url
            final_url = f"https://doi.org/{doi}"

        metadata = {"doi": doi, "source_url": url}

        # 尝试从各种开放获取源下载
        # 1. 尝试 Unpaywall
        try:
            unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email=user@example.com"
            response = self.session.get(unpaywall_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("is_oa") and data.get("best_oa_location"):
                    pdf_url = data["best_oa_location"].get("url_for_pdf")
                    if pdf_url:
                        pdf_path = output_dir / f"doi_{doi.replace('/', '_')}.pdf"
                        self._download_file(pdf_url, pdf_path)
                        metadata.update({
                            "title": data.get("title", ""),
                            "authors": data.get("z_authors", []),
                        })
                        return pdf_path, metadata
        except Exception as e:
            logger.warning(f"Unpaywall 查询失败: {e}")

        # 2. 尝试直接访问最终 URL
        return self._download_generic(final_url, output_dir, metadata)

    def _download_openreview(self, url: str, output_dir: Path) -> Tuple[Path, dict]:
        """下载 OpenReview 论文"""
        # 提取 forum ID
        match = re.search(r"id=([^&]+)", url)
        if not match:
            return self._download_generic(url, output_dir)

        forum_id = match.group(1)

        # 尝试获取 PDF
        pdf_url = f"https://openreview.net/pdf?id={forum_id}"
        pdf_path = output_dir / f"openreview_{forum_id}.pdf"

        try:
            self._download_file(pdf_url, pdf_path)

            # 尝试获取元数据
            notes_url = f"https://api.openreview.net/notes?id={forum_id}"
            response = self.session.get(notes_url, timeout=Config.DEFAULT_TIMEOUT_SECONDS)
            metadata = {"source_url": url}

            if response.status_code == 200:
                data = response.json()
                if data.get("notes"):
                    note = data["notes"][0]
                    content = note.get("content", {})
                    metadata.update({
                        "title": content.get("title", ""),
                        "authors": content.get("authors", []),
                        "abstract": content.get("abstract", ""),
                    })

            return pdf_path, metadata
        except Exception as e:
            logger.warning(f"OpenReview 下载失败: {e}")
            return self._download_generic(url, output_dir)

    def _download_semanticscholar(self, url: str, output_dir: Path) -> Tuple[Path, dict]:
        """下载 Semantic Scholar 论文

        支持两种 URL 格式：
        1. https://www.semanticscholar.org/paper/PAPER_ID
        2. https://www.semanticscholar.org/paper/标题/PAPER_ID
        """
        # 提取 paper ID - 取最后一个 / 后面的内容（hex 字符串）
        # 格式: .../paper/标题/PAPER_ID 或 .../paper/PAPER_ID
        patterns = [
            r"/paper/(?:[^/]+/)?([a-f0-9]{40})",  # 匹配最后一个 40 位 hex ID（最常见）
            r"/paper/(?:[^/]+/)?([a-f0-9]{32})",  # 匹配 32 位 hex ID
            r"/paper/(?:[^/]+/)?([^/]+)",          # 后备方案：取最后一个 / 后的内容
        ]

        paper_id = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                paper_id = match.group(1)
                # 验证看起来像个 ID（不是纯标题）
                if len(paper_id) >= 20 or re.match(r'^[a-f0-9]+$', paper_id):
                    break

        if not paper_id:
            logger.warning(f"无法从 URL 提取 Semantic Scholar paper ID: {url}")
            return self._download_generic(url, output_dir)
        pdf_path = output_dir / f"semanticscholar_{paper_id}.pdf"

        try:
            # 获取元数据
            api_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=title,authors,abstract,year,openAccessPdf,externalIds"
            response = self.session.get(api_url, timeout=Config.DEFAULT_TIMEOUT_SECONDS)
            metadata = {"source_url": url}

            pdf_url = None
            if response.status_code == 200:
                data = response.json()
                metadata.update({
                    "title": data.get("title", ""),
                    "authors": [a.get("name") for a in data.get("authors", [])],
                    "abstract": data.get("abstract", ""),
                    "publication_date": str(data.get("year", "")),
                })

                oa_pdf = data.get("openAccessPdf")
                if oa_pdf:
                    pdf_url = oa_pdf.get("url")

            if pdf_url:
                self._download_file(pdf_url, pdf_path)
                return pdf_path, metadata
            else:
                logger.warning("Semantic Scholar 未找到开放获取 PDF，尝试其他方案...")
                # 尝试获取 externalIds 中的 arXiv ID
                try:
                    if response.status_code == 200:
                        data = response.json()
                        external_ids = data.get("externalIds", {})
                        arxiv_id = external_ids.get("ArXiv")
                        if arxiv_id:
                            logger.info(f"找到 arXiv ID: {arxiv_id}")
                            return self._download_arxiv(f"https://arxiv.org/abs/{arxiv_id}", output_dir)
                except Exception as e:
                    logger.warning(f"尝试 arXiv 回退失败: {e}")

                # 如果没有开放获取，报错提示用户
                raise RuntimeError(
                    "该论文在 Semantic Scholar 上没有开放获取 PDF。\n"
                    "建议:\n"
                    "1. 如果论文在 arXiv 上，请使用 arXiv 链接\n"
                    "2. 如果论文有 DOI，请使用 DOI 链接\n"
                    "3. 或者直接粘贴 PDF 的直链"
                )

        except Exception as e:
            logger.warning(f"Semantic Scholar 下载失败: {e}")
            raise RuntimeError(f"无法从 Semantic Scholar 下载论文: {e}")

    def _download_googlescholar(self, url: str, output_dir: Path) -> Tuple[Path, dict]:
        """处理 Google Scholar 链接

        Google Scholar 通常不直接提供 PDF 下载，而是提供论文信息页面。
        我们尝试从页面中提取 PDF 链接，或通过标题搜索其他开放获取源。
        """
        logger.info(f"处理 Google Scholar 链接: {url}")
        metadata = {"source_url": url}

        try:
            # 获取 Google Scholar 页面
            response = self.session.get(url, timeout=Config.DEFAULT_TIMEOUT_SECONDS)
            response.raise_for_status()

            # 尝试从页面提取标题
            from html.parser import HTMLParser

            class TitleExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.in_title = False
                    self.title = ""
                    self.title_div_count = 0

                def handle_starttag(self, tag, attrs):
                    attrs_dict = dict(attrs)
                    # Google Scholar 的标题通常在 class="gs_rt" 的 h3 标签中
                    if tag == "h3" and attrs_dict.get("class") == "gs_rt":
                        self.in_title = True
                    elif self.in_title and tag in ["span", "div"]:
                        self.title_div_count += 1

                def handle_endtag(self, tag):
                    if self.in_title:
                        if tag == "h3" and self.title_div_count == 0:
                            self.in_title = False
                        elif tag in ["span", "div"]:
                            self.title_div_count -= 1

                def handle_data(self, data):
                    if self.in_title:
                        self.title += data

            # 尝试提取标题
            title = None
            if "cluster=" in url or "cites=" in url:
                # 提取标题 - 使用简单的正则
                title_match = re.search(r'<h3 class="gs_rt"[^>]*>(.*?)</h3>', response.text, re.DOTALL)
                if title_match:
                    title_html = title_match.group(1)
                    # 移除 HTML 标签
                    title = re.sub(r'<[^>]+>', '', title_html)
                    title = re.sub(r'\[PDF\]|\[HTML\]|\s+', ' ', title).strip()

            if not title:
                # 尝试从页面标题中提取
                title_match = re.search(r'<title>(.*?) - Google Scholar</title>', response.text)
                if title_match:
                    title = title_match.group(1).strip()

            if title:
                logger.info(f"从 Google Scholar 提取到标题: {title}")
                metadata["title"] = title

                # 尝试搜索 arXiv
                arxiv_match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', response.text)
                if arxiv_match:
                    arxiv_id = arxiv_match.group(1)
                    logger.info(f"找到 arXiv 链接: {arxiv_id}")
                    return self._download_arxiv(f"https://arxiv.org/abs/{arxiv_id}", output_dir)

                # 尝试搜索 DOI
                doi_match = re.search(r'10\.\d{4,}/[^\s"<>]+', response.text)
                if doi_match:
                    doi = doi_match.group(0)
                    logger.info(f"找到 DOI: {doi}")
                    return self._download_doi(f"https://doi.org/{doi}", output_dir)

                # 尝试搜索页面中的 PDF 链接
                pdf_patterns = [
                    r'href="([^"]+\.pdf)"',
                    r'href="(/scholar[^"]*cache[^"]*)"',
                ]
                for pattern in pdf_patterns:
                    pdf_match = re.search(pattern, response.text)
                    if pdf_match:
                        pdf_url = pdf_match.group(1)
                        if pdf_url.startswith('/'):
                            pdf_url = f"https://scholar.google.com{pdf_url}"
                        logger.info(f"找到 PDF 链接: {pdf_url}")
                        try:
                            pdf_path = output_dir / f"googlescholar_{int(time.time())}.pdf"
                            self._download_file(pdf_url, pdf_path)
                            if self._validate_pdf(pdf_path):
                                return pdf_path, metadata
                        except Exception as e:
                            logger.warning(f"Google Scholar PDF 下载失败: {e}")

                # 如果都没找到，尝试通过 Semantic Scholar API 搜索
                try:
                    search_url = f"https://api.semanticscholar.org/graph/v1/paper/search"
                    params = {
                        "query": title,
                        "fields": "paperId,openAccessPdf",
                        "limit": 1
                    }
                    ss_response = self.session.get(search_url, params=params, timeout=10)
                    if ss_response.status_code == 200:
                        data = ss_response.json()
                        papers = data.get("data", [])
                        if papers and papers[0].get("openAccessPdf"):
                            pdf_url = papers[0]["openAccessPdf"].get("url")
                            paper_id = papers[0].get("paperId")
                            if pdf_url and paper_id:
                                logger.info(f"通过 Semantic Scholar 找到 PDF: {paper_id}")
                                pdf_path = output_dir / f"semanticscholar_{paper_id}.pdf"
                                self._download_file(pdf_url, pdf_path)
                                if self._validate_pdf(pdf_path):
                                    return pdf_path, metadata
                except Exception as e:
                    logger.warning(f"Semantic Scholar 搜索失败: {e}")

            logger.warning("Google Scholar 无法找到可用的 PDF 下载链接")
            raise RuntimeError(
                "Google Scholar 链接无法直接下载 PDF。\n"
                "建议:\n"
                "1. 如果论文在 arXiv 上，请使用 arXiv 链接\n"
                "2. 如果论文有 DOI，请使用 DOI 链接\n"
                "3. 或者直接粘贴 PDF 的直链"
            )

        except Exception as e:
            logger.warning(f"Google Scholar 处理失败: {e}")
            raise RuntimeError(f"无法从 Google Scholar 链接下载论文: {e}")

    def _download_generic(self, url: str, output_dir: Path, metadata: Optional[dict] = None) -> Tuple[Path, dict]:
        """通用下载方案"""
        if metadata is None:
            metadata = {"source_url": url}

        # 生成文件名
        parsed = urlparse(url)
        filename = Path(unquote(parsed.path)).name
        if not filename or not filename.endswith(".pdf"):
            filename = f"paper_{int(time.time())}.pdf"

        pdf_path = output_dir / filename

        # 下载文件
        self._download_file(url, pdf_path)

        return pdf_path, metadata

    def _download_file(self, url: str, output_path: Path, max_retries: int = None):
        """下载文件到指定路径"""
        if max_retries is None:
            max_retries = Config.MAX_RETRIES

        for attempt in range(max_retries):
            try:
                logger.info(f"下载文件 (尝试 {attempt + 1}/{max_retries}): {url}")

                response = self.session.get(
                    url,
                    stream=True,
                    timeout=Config.DEFAULT_TIMEOUT_SECONDS,
                    allow_redirects=True,
                )
                response.raise_for_status()

                # 检查文件大小
                content_length = response.headers.get("content-length")
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    if size_mb > Config.MAX_PAPER_SIZE_MB:
                        raise ValueError(f"文件过大: {size_mb:.1f}MB > {Config.MAX_PAPER_SIZE_MB}MB")

                # 写入文件
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                return

            except Exception as e:
                logger.warning(f"下载尝试 {attempt + 1} 失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    raise

    def _validate_pdf(self, pdf_path: Path) -> bool:
        """验证文件是否为有效 PDF"""
        try:
            if not pdf_path.exists():
                return False

            if pdf_path.stat().st_size == 0:
                return False

            # 检查 PDF 文件头
            with open(pdf_path, "rb") as f:
                header = f.read(4)
                return header == b"%PDF"
        except Exception as e:
            logger.warning(f"PDF 验证失败: {e}")
            return False

    def _try_wget_curl(self, url: str, output_dir: Path) -> Path:
        """尝试使用 wget 或 curl 下载"""
        import shutil
        import subprocess

        pdf_path = output_dir / f"paper_wget_{int(time.time())}.pdf"

        # 检查 wget
        if shutil.which("wget"):
            try:
                subprocess.run(
                    ["wget", "-O", str(pdf_path), "--timeout=30", "-q", url],
                    check=True,
                    capture_output=True,
                )
                if self._validate_pdf(pdf_path):
                    return pdf_path
            except Exception as e:
                logger.warning(f"wget 下载失败: {e}")

        # 检查 curl
        if shutil.which("curl"):
            try:
                subprocess.run(
                    ["curl", "-L", "-o", str(pdf_path), "--max-time", "30", "-s", url],
                    check=True,
                    capture_output=True,
                )
                if self._validate_pdf(pdf_path):
                    return pdf_path
            except Exception as e:
                logger.warning(f"curl 下载失败: {e}")

        raise RuntimeError("所有下载方案均失败")
