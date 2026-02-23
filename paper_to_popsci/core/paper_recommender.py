"""
论文关系探索与智能推荐模块
整合 Semantic Scholar API、OpenAlex API、arXiv API 和本地关键词匹配
无需 API Key 也能使用基础功能
"""
import requests
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
import logging

from .logger import logger


@dataclass
class RelatedPaper:
    """相关论文数据类"""
    title: str
    authors: List[str]
    year: int
    abstract: str
    url: str
    pdf_url: Optional[str]
    citation_count: int
    source: str  # 推荐来源说明
    relevance_score: float = 0.0  # 相关度分数 (0-1)
    reason: str = ""  # 推荐理由


class PaperRecommender:
    """
    论文智能推荐器 - 无需 API Key 也能使用

    使用策略（按优先级）：
    1. Semantic Scholar API（无需 Key，有共享速率限制）
    2. OpenAlex API（免费，推荐提供 email）
    3. arXiv API（完全免费，无需注册）
    4. 本地关键词匹配（离线可用）
    """

    def __init__(self, ss_api_key: str = None, openalex_email: str = None):
        self.ss_api_key = ss_api_key
        self.openalex_email = openalex_email
        self.ss_base_url = "https://api.semanticscholar.org"
        self.ss_headers = {}
        if ss_api_key:
            self.ss_headers["x-api-key"] = ss_api_key

    def get_recommendations(
        self,
        paper_title: str,
        paper_abstract: str = "",
        arxiv_id: str = None,
        doi: str = None,
        semantic_scholar_id: str = None,
        limit: int = 10
    ) -> Dict[str, List[RelatedPaper]]:
        """
        获取论文推荐 - 无需 API Key 也能使用

        Returns:
            {
                "semantic_scholar": [...],  # API 智能推荐
                "citations": [...],          # 引用网络相关
                "similar_topics": [...]      # 相似主题
            }
        """
        result = {
            "semantic_scholar": [],
            "citations": [],
            "similar_topics": []
        }

        # 1. 尝试获取 Semantic Scholar 推荐（无需 Key 也能使用）
        paper_id = self._resolve_paper_id(arxiv_id, doi, semantic_scholar_id)
        if paper_id:
            try:
                result["semantic_scholar"] = self._get_ss_recommendations(paper_id, limit)
                result["citations"] = self._get_citation_network(paper_id, limit // 2)
            except Exception as e:
                logger.warning(f"Semantic Scholar API 失败，尝试备选方案: {e}")

        # 2. 如果 Semantic Scholar 失败，尝试 arXiv API（完全免费）
        if not result["semantic_scholar"] and arxiv_id:
            try:
                result["semantic_scholar"] = self._get_arxiv_recommendations(
                    arxiv_id, paper_title, limit
                )
            except Exception as e:
                logger.warning(f"arXiv API 失败: {e}")

        # 3. 如果都失败，使用本地关键词匹配
        if not result["semantic_scholar"] and paper_title:
            result["similar_topics"] = self._get_local_keyword_recommendations(
                paper_title, paper_abstract, limit
            )

        return result

    def _resolve_paper_id(self, arxiv_id: str, doi: str, ss_id: str) -> Optional[str]:
        """解析论文 ID 格式"""
        if ss_id:
            return ss_id
        if arxiv_id:
            return f"arxiv:{arxiv_id.replace('arxiv:', '')}"
        if doi:
            return f"doi:{doi}"
        return None

    def _get_ss_recommendations(self, paper_id: str, limit: int) -> List[RelatedPaper]:
        """
        获取 Semantic Scholar 推荐
        注意：无需 API Key 也能使用，只是有速率限制
        """
        endpoint = f"{self.ss_base_url}/recommendations/v1/papers/forpaper/{paper_id}"

        params = {
            "limit": limit,
            "fields": "paperId,title,authors,year,citationCount,referenceCount,"
                      "abstract,url,openAccessPdf,publicationDate,fieldsOfStudy",
        }

        try:
            response = requests.get(
                endpoint,
                params=params,
                headers=self.ss_headers,
                timeout=10  # 较短的超时时间
            )

            # 处理速率限制
            if response.status_code == 429:
                logger.warning("Semantic Scholar 速率限制，将使用备选方案")
                return []

            response.raise_for_status()
            data = response.json()
            recommendations = data.get("recommendedPapers", [])

            results = []
            for paper in recommendations:
                authors = [a.get("name") for a in paper.get("authors", [])[:3]]
                if len(paper.get("authors", [])) > 3:
                    authors.append("et al.")

                results.append(RelatedPaper(
                    title=paper.get("title", ""),
                    authors=authors,
                    year=paper.get("year", 0),
                    abstract=self._truncate_abstract(paper.get("abstract", "")),
                    url=paper.get("url", ""),
                    pdf_url=paper.get("openAccessPdf", {}).get("url") if paper.get("openAccessPdf") else None,
                    citation_count=paper.get("citationCount", 0),
                    source="Semantic Scholar 智能推荐",
                    relevance_score=0.9,
                    reason="基于引用网络和语义相似度的智能推荐"
                ))

            logger.info(f"Semantic Scholar 推荐: {len(results)} 篇")
            return results

        except requests.exceptions.Timeout:
            logger.warning("Semantic Scholar API 超时")
            return []
        except Exception as e:
            logger.error(f"Semantic Scholar API 调用失败: {e}")
            return []

    def _get_citation_network(self, paper_id: str, limit: int) -> List[RelatedPaper]:
        """获取引用网络"""
        results = []

        try:
            details_endpoint = f"{self.ss_base_url}/graph/v1/paper/{paper_id}"
            params = {"fields": "citations,references,title"}

            response = requests.get(
                details_endpoint,
                params=params,
                headers=self.ss_headers,
                timeout=10
            )

            if response.status_code == 429:
                return []

            response.raise_for_status()
            data = response.json()

            # 引用这篇论文的
            citations = data.get("citations", [])[:limit]
            for cite in citations:
                results.append(RelatedPaper(
                    title=cite.get("title", ""),
                    authors=["查看详情"],
                    year=cite.get("year", 0),
                    abstract="",
                    url=f"https://www.semanticscholar.org/paper/{cite.get('paperId')}",
                    pdf_url=None,
                    citation_count=cite.get("citationCount", 0),
                    source="引用该论文",
                    relevance_score=0.8,
                    reason="后续研究引用了本文"
                ))

            # 这篇论文引用的
            references = data.get("references", [])[:limit]
            for ref in references:
                results.append(RelatedPaper(
                    title=ref.get("title", ""),
                    authors=["查看详情"],
                    year=ref.get("year", 0),
                    abstract="",
                    url=f"https://www.semanticscholar.org/paper/{ref.get('paperId')}",
                    pdf_url=None,
                    citation_count=ref.get("citationCount", 0),
                    source="参考文献",
                    relevance_score=0.75,
                    reason="本文引用的前期工作"
                ))

            return results

        except Exception as e:
            logger.warning(f"获取引用网络失败: {e}")
            return []

    def _get_arxiv_recommendations(self, arxiv_id: str, title: str, limit: int) -> List[RelatedPaper]:
        """
        使用 arXiv API 获取推荐（完全免费，无需注册）
        策略：基于标题关键词搜索相关论文
        """
        try:
            # 提取关键词（简单的 TF 方法）
            keywords = self._extract_keywords(title)
            if not keywords:
                return []

            # 使用 arXiv API 搜索
            query = " OR ".join(keywords[:3])  # 使用前3个关键词
            arxiv_endpoint = "http://export.arxiv.org/api/query"

            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": limit,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }

            response = requests.get(arxiv_endpoint, params=params, timeout=15)
            response.raise_for_status()

            # 解析 arXiv Atom feed
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            results = []
            for entry in root.findall('atom:entry', ns)[:limit]:
                entry_id = entry.find('atom:id', ns).text
                entry_title = entry.find('atom:title', ns).text
                entry_summary = entry.find('atom:summary', ns).text
                entry_published = entry.find('atom:published', ns).text

                # 提取年份
                year = int(entry_published[:4]) if entry_published else 0

                # 提取作者
                authors = [author.find('atom:name', ns).text
                          for author in entry.findall('atom:author', ns)[:3]]

                # 提取 arXiv ID
                arxiv_match = re.search(r'arXiv:(\d+\.\d+)', entry_id)
                arxiv_num = arxiv_match.group(1) if arxiv_match else ""

                # 排除自身
                if arxiv_id.replace('arxiv:', '') in entry_id:
                    continue

                # 计算相似度分数
                similarity = SequenceMatcher(None, title.lower(), entry_title.lower()).ratio()

                results.append(RelatedPaper(
                    title=entry_title.replace('\n', ' ').strip(),
                    authors=authors,
                    year=year,
                    abstract=self._truncate_abstract(entry_summary),
                    url=f"https://arxiv.org/abs/{arxiv_num}" if arxiv_num else entry_id,
                    pdf_url=f"https://arxiv.org/pdf/{arxiv_num}.pdf" if arxiv_num else None,
                    citation_count=0,  # arXiv 不提供引用数
                    source="arXiv 相关推荐",
                    relevance_score=similarity,
                    reason="基于标题关键词的相关性匹配"
                ))

            # 按相似度排序
            results.sort(key=lambda x: x.relevance_score, reverse=True)

            logger.info(f"arXiv 推荐: {len(results)} 篇")
            return results[:limit]

        except Exception as e:
            logger.error(f"arXiv API 调用失败: {e}")
            return []

    def _get_local_keyword_recommendations(
        self,
        title: str,
        abstract: str,
        limit: int
    ) -> List[RelatedPaper]:
        """
        本地关键词推荐（离线可用，无需网络）
        生成搜索链接供用户自行查找
        """
        keywords = self._extract_keywords(title + " " + abstract)

        results = []

        # 生成 Semantic Scholar 搜索链接
        if keywords:
            query = "+".join(keywords[:3])
            results.append(RelatedPaper(
                title="在 Semantic Scholar 上搜索相关论文",
                authors=[],
                year=0,
                abstract=f"关键词: {', '.join(keywords[:5])}",
                url=f"https://www.semanticscholar.org/search?q={query}&sort=relevance",
                pdf_url=None,
                citation_count=0,
                source="关键词搜索",
                relevance_score=1.0,
                reason="基于论文标题和摘要提取的关键词"
            ))

        # 生成 Google Scholar 搜索链接
        if keywords:
            query = "+".join(keywords[:3])
            results.append(RelatedPaper(
                title="在 Google Scholar 上搜索相关论文",
                authors=[],
                year=0,
                abstract="Google Scholar 提供更广泛的学术文献搜索",
                url=f"https://scholar.google.com/scholar?q={query}",
                pdf_url=None,
                citation_count=0,
                source="关键词搜索",
                relevance_score=0.95,
                reason="Google Scholar 包含更全面的学术文献"
            ))

        # 生成 arXiv 搜索链接
        if keywords:
            query = "+OR+".join(keywords[:3])
            results.append(RelatedPaper(
                title="在 arXiv 上搜索相关预印本",
                authors=[],
                year=0,
                abstract="arXiv 是计算机科学、物理、数学等领域的重要预印本库",
                url=f"https://arxiv.org/search/?query={query}&searchtype=all",
                pdf_url=None,
                citation_count=0,
                source="关键词搜索",
                relevance_score=0.9,
                reason="arXiv 包含最新研究进展"
            ))

        logger.info(f"本地关键词推荐: {len(results)} 个搜索链接")
        return results[:limit]

    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """
        简单的关键词提取（基于词频，无需 NLP 库）
        """
        if not text:
            return []

        # 清理文本
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()

        # 停用词列表（简化版）
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'using', 'based', 'via', 'through', 'over', 'under', 'between', 'among',
            'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself',
            'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
            'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs',
            'themselves', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when',
            'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
            'very', 'just', 'now', 'also', 'new', 'novel', 'proposed', 'approach',
            'method', 'methods', 'algorithm', 'algorithms', 'model', 'models',
            'system', 'systems', 'framework', 'frameworks', 'technique', 'techniques'
        }

        # 统计词频（只保留长度 >= 4 的词）
        word_freq = {}
        for word in words:
            if len(word) >= 4 and word not in stopwords and word.isalpha():
                word_freq[word] = word_freq.get(word, 0) + 1

        # 返回最常见的词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]

    def _truncate_abstract(self, abstract: str, max_length: int = 200) -> str:
        """截断摘要"""
        if not abstract:
            return ""
        abstract = abstract.replace('\n', ' ').strip()
        if len(abstract) <= max_length:
            return abstract
        return abstract[:max_length].rsplit(" ", 1)[0] + "..."

    def format_for_article(self, recommendations: Dict[str, List[RelatedPaper]]) -> str:
        """将推荐结果格式化为文章 markdown 格式"""
        lines = []
        # 注意：章节标题由 renderer 处理，这里不需要添加 ## 标题

        has_recommendations = any(
            recommendations.get(key) for key in ["semantic_scholar", "citations", "similar_topics"]
        )

        if has_recommendations:
            lines.append("基于学术论文引用网络和语义相似度分析，为您推荐以下相关研究：")
        else:
            lines.append("抱歉，暂时无法获取自动推荐。您可以尝试以下方式探索相关研究：")
        lines.append("")

        # 1. Semantic Scholar / arXiv 推荐
        ss_recs = recommendations.get("semantic_scholar", [])
        if ss_recs:
            # 检查是否是搜索链接类型
            if ss_recs[0].source == "关键词搜索":
                lines.append("### 🔍 相关论文搜索")
            else:
                lines.append("### 🔬 相关论文推荐")
            lines.append("")

            for i, paper in enumerate(ss_recs[:5], 1):
                if paper.source == "关键词搜索":
                    # 搜索链接类型
                    lines.append(f"**{i}. [{paper.title}]({paper.url})**")
                    if paper.abstract:
                        lines.append(f"- **关键词**: {paper.abstract}")
                    if paper.reason:
                        lines.append(f"- **说明**: {paper.reason}")
                else:
                    # 实际论文推荐
                    lines.append(f"**{i}. {paper.title}** ({paper.year})")
                    lines.append("")
                    if paper.authors:
                        lines.append(f"**作者**: {', '.join(paper.authors)}")
                        lines.append("")
                    if paper.citation_count:
                        lines.append(f"**被引次数**: {paper.citation_count}")
                        lines.append("")
                    if paper.abstract:
                        lines.append(f"**简介**: {paper.abstract}")
                        lines.append("")
                    if paper.url:
                        lines.append(f"**链接**: [点击查看详情]({paper.url})")
                        lines.append("")
                        # 添加论文解读按钮链接
                        lines.append(f"**[📄 一键解读这篇论文]({paper.url})**")
                        lines.append("")
                    if paper.pdf_url:
                        lines.append(f"**PDF**: [免费下载]({paper.pdf_url})")
                        lines.append("")
                    if paper.reason:
                        lines.append(f"**推荐理由**: {paper.reason}")
                        lines.append("")
                lines.append("")

        # 2. 引用网络
        citations = recommendations.get("citations", [])
        if citations:
            lines.append("### 📚 引用网络")
            lines.append("")

            citing = [c for c in citations if c.source == "引用该论文"]
            referenced = [c for c in citations if c.source == "参考文献"]

            if citing:
                lines.append("**引用该论文的研究：**")
                for paper in citing[:3]:
                    lines.append(f"- [{paper.title}]({paper.url}) ({paper.year})")
                lines.append("")

            if referenced:
                lines.append("**该论文引用的前期工作：**")
                for paper in referenced[:3]:
                    lines.append(f"- [{paper.title}]({paper.url}) ({paper.year})")
                lines.append("")

        # 3. 手动探索建议
        if not has_recommendations:
            lines.append("### 💡 手动探索建议")
            lines.append("")
            lines.append("1. **Semantic Scholar**: 访问 semanticscholar.org 搜索论文标题")
            lines.append("2. **Google Scholar**: 使用 scholar.google.com 查找引用网络")
            lines.append("3. **arXiv**: 如果是计算机科学论文，在 arxiv.org 查找相关预印本")
            lines.append("4. **查看参考文献**: 阅读原文的参考文献章节，了解研究背景")
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)
