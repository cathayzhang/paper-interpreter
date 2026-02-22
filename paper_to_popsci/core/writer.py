"""
文章生成模块
通俗科普风格文章生成
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .config import Config
from .logger import logger
from .llm_client import LLMClient


@dataclass
class ArticleSection:
    """文章章节"""
    section_type: str
    title: str
    content: str
    image_path: Optional[str] = None


class ArticleWriter:
    """通俗科普风格文章写作器"""

    def __init__(self):
        self.llm = LLMClient()

    def write(
        self,
        paper_content,
        outline: Dict[str, Any],
        illustrations: List[Dict[str, Any]]
    ) -> List[ArticleSection]:
        """
        生成完整文章

        Args:
            paper_content: PaperContent 对象
            outline: 文章大纲
            illustrations: 配图结果

        Returns:
            文章章节列表
        """
        logger.info("开始生成文章...")

        sections = []
        outline_data = outline.get("outline", {})
        outline_sections = outline_data.get("sections", [])

        # 构建配图映射
        image_map = {}
        for ill in illustrations:
            if ill.get("success") and ill.get("filepath"):
                image_map[ill["section"]] = ill["filepath"]

        # 生成每个章节
        for section_data in outline_sections:
            section_type = section_data.get("type", "")

            if section_type == "hero":
                section = self._generate_hero(section_data, paper_content)
            elif section_type == "intro":
                section = self._generate_intro(section_data, paper_content, outline_data)
            elif section_type == "problem":
                section = self._generate_problem(section_data, paper_content, outline_data)
            elif section_type == "method":
                section = self._generate_method(section_data, paper_content, outline_data)
            elif section_type == "results":
                section = self._generate_results(section_data, paper_content)
            elif section_type == "impact":
                section = self._generate_impact(section_data, paper_content, outline_data)
            elif section_type == "conclusion":
                section = self._generate_conclusion(section_data, paper_content, outline_data)
            else:
                continue

            # 关联配图
            if section_type in image_map:
                section.image_path = image_map[section_type]

            sections.append(section)

        # 添加论文信息章节
        sections.append(self._generate_paper_info(paper_content))

        logger.info(f"文章生成完成: {len(sections)} 个章节")
        return sections

    def _generate_hero(self, section_data: Dict, paper_content) -> ArticleSection:
        """生成 Hero 区"""
        title = section_data.get("title", paper_content.title or "论文解读")
        subtitle = section_data.get("subtitle", "「一项值得关注的技术」")

        # 构建 Hero 内容
        content = f"""{title}

{subtitle}

**作者**: {', '.join(paper_content.authors) if paper_content.authors else '未知作者'}
**机构**: {paper_content.institution or '未知机构'}
**发表时间**: {paper_content.publication_date or '未知日期'}
**arXiv ID**: {paper_content.arxiv_id or 'N/A'}
"""

        return ArticleSection(
            section_type="hero",
            title=title,
            content=content
        )

    def _generate_intro(self, section_data: Dict, paper_content, outline_data) -> ArticleSection:
        """生成引子"""
        title = section_data.get("title", "从生活谈起")
        analogy = section_data.get("analogy", "这项技术与我们的生活息息相关")
        analogy_theme = outline_data.get("analogy_theme", "日常生活")

        # 使用 LLM 生成引言内容
        prompt = f"""请写一篇面向"一无所知"小白的科普引言。

论文标题: {paper_content.title}
核心创新: {outline_data.get('core_innovation', '')}
类比主题: {analogy_theme}
类比场景: {analogy}

要求:
1. 用生活化的故事场景引入，比如日常生活、吃饭、购物、交通等场景
2. 专业术语首次出现时，用*术语（大白话解释）*格式，例如：*神经网络（像人脑一样工作的计算程序）*
3. 禁止出现Markdown格式（如##、###、- 等）
4. 禁止出现任何数学公式或LaTeX符号（如$、^、_等）
5. 用设问引导读者思考
6. 结尾引出"这和论文主题有什么关系"
7. 200-300字，语言生动有趣，像跟朋友聊天
8. 使用第三人称客观叙述

直接输出正文内容，不要加标题。"""

        try:
            content = self.llm.generate(prompt, temperature=0.8, max_tokens=800)
            content = self._clean_llm_output(content)
        except Exception as e:
            logger.warning(f"引言生成失败，使用模板: {e}")
            content = self._get_default_intro(paper_content, analogy_theme)

        return ArticleSection(
            section_type="intro",
            title=title,
            content=content
        )

    def _generate_problem(self, section_data: Dict, paper_content, outline_data) -> ArticleSection:
        """生成背景/问题"""
        title = section_data.get("title", "问题的提出")
        pain_point = section_data.get("pain_point", "现有方法存在局限")

        prompt = f"""请用大白话向"完全不懂"的读者解释现有方法的问题。

论文标题: {paper_content.title}
核心创新: {outline_data.get('core_innovation', '')}
现有问题: {pain_point}
类比主题: {outline_data.get('analogy_theme', '日常生活')}

论文摘要: {paper_content.abstract[:500] if paper_content.abstract else ''}

要求:
1. 用生活化类比解释问题，比如做饭、搬家、整理房间等场景
2. 专业术语首次出现时，用*术语（大白话解释）*格式，例如：*神经网络（像人脑一样工作的计算程序）*
3. 禁止出现Markdown格式（##、###、- 等）
4. 禁止出现任何数学公式或LaTeX符号（$等）
5. 用设问引出"那怎么办呢？"
6. 300-400字，像给爷爷奶奶讲解一样耐心
7. 使用第三人称客观叙述

直接输出正文内容。"""

        try:
            content = self.llm.generate(prompt, temperature=0.7, max_tokens=1000)
            content = self._clean_llm_output(content)
        except Exception as e:
            logger.warning(f"问题部分生成失败，使用模板: {e}")
            content = self._get_default_problem(paper_content, pain_point)

        return ArticleSection(
            section_type="problem",
            title=title,
            content=content
        )

    def _generate_method(self, section_data: Dict, paper_content, outline_data) -> ArticleSection:
        """生成核心方法"""
        title = section_data.get("title", "解决方案")
        key_concepts = section_data.get("key_concepts", ["核心创新"])

        concepts_text = "、".join(key_concepts)

        prompt = f"""请用大白话向"小白"解释论文的核心方法。

论文标题: {paper_content.title}
核心创新: {outline_data.get('core_innovation', '')}
关键概念: {concepts_text}
类比主题: {outline_data.get('analogy_theme', '日常生活')}

论文方法章节内容:
{paper_content.sections[2].content[:1000] if len(paper_content.sections) > 2 else paper_content.raw_text[:1000]}

要求:
1. 用日常生活类比解释新方法，比如做饭、装修、学骑车等
2. 专业术语首次出现时，用*术语（大白话解释）*格式，例如：*神经网络（像人脑一样工作的计算程序）*
3. 分步骤讲解（第一步、第二步、第三步），不要用编号列表
4. 禁止出现Markdown格式（##、###、- 等）
5. 禁止出现任何数学公式或LaTeX符号（$、^、_等）
6. 400-500字，像讲故事一样娓娓道来
7. 使用第三人称客观叙述

直接输出正文内容。"""

        try:
            content = self.llm.generate(prompt, temperature=0.7, max_tokens=1200)
            content = self._clean_llm_output(content)
        except Exception as e:
            logger.warning(f"方法部分生成失败，使用模板: {e}")
            content = self._get_default_method(paper_content, key_concepts)

        return ArticleSection(
            section_type="method",
            title=title,
            content=content
        )

    def _generate_results(self, section_data: Dict, paper_content) -> ArticleSection:
        """生成结果"""
        title = section_data.get("title", "结果：数字说话")
        metrics = section_data.get("metrics", [])

        # 从论文内容中提取数字
        extracted_metrics = self._extract_metrics_from_paper(paper_content)
        all_metrics = metrics + extracted_metrics

        if all_metrics:
            metrics_text = "\n".join([
                f"- **{m.get('name', '指标')}**: {m.get('value', '')} ({m.get('meaning', '')})"
                for m in all_metrics[:5]
            ])
        else:
            metrics_text = "实验结果显示了显著的改进效果。"

        prompt = f"""请用大白话向"小白"总结实验结果。

论文标题: {paper_content.title}
关键指标:
{metrics_text}

论文结果章节:
{paper_content.sections[3].content[:800] if len(paper_content.sections) > 3 else ''}

要求:
1. 用具体数字说话，并解释这些数字意味着什么
2. 专业术语首次出现时，用*术语（大白话解释）*格式，例如：*神经网络（像人脑一样工作的计算程序）*
3. 用生活化对比（比如"比原来快了3倍，就像从走路变成坐汽车"）
4. 禁止出现Markdown格式（##、###、**等）
5. 禁止出现任何数学公式或LaTeX符号（$等）
6. 200-300字，让普通人也能理解这些数字的意义
7. 使用第三人称客观叙述

直接输出正文内容。"""

        try:
            content = self.llm.generate(prompt, temperature=0.7, max_tokens=800)
            content = self._clean_llm_output(content)
        except Exception as e:
            logger.warning(f"结果部分生成失败，使用模板: {e}")
            content = self._get_default_results(all_metrics)

        return ArticleSection(
            section_type="results",
            title=title,
            content=content
        )

    def _generate_impact(self, section_data: Dict, paper_content, outline_data) -> ArticleSection:
        """生成意义"""
        title = section_data.get("title", "意义：这对我们有什么影响？")
        implications = section_data.get("implications", [])

        prompt = f"""请用大白话向"小白"阐述这项技术的意义。

论文标题: {paper_content.title}
核心创新: {outline_data.get('core_innovation', '')}

要求:
1. 用"第一、第二、第三"分段阐述，不要用编号列表
2. 每个影响都要连接到普通人的日常生活体验
3. 专业术语首次出现时，用*术语（大白话解释）*格式，例如：*神经网络（像人脑一样工作的计算程序）*
4. 禁止出现Markdown格式（##、###、**等）
5. 禁止出现任何数学公式或LaTeX符号（$等）
6. 300-400字，让读者感受到"这和我有什么关系"
7. 使用第三人称客观叙述

直接输出正文内容。"""

        try:
            content = self.llm.generate(prompt, temperature=0.8, max_tokens=1000)
            content = self._clean_llm_output(content)
        except Exception as e:
            logger.warning(f"意义部分生成失败，使用模板: {e}")
            content = self._get_default_impact(implications)

        return ArticleSection(
            section_type="impact",
            title=title,
            content=content
        )

    def _generate_conclusion(self, section_data: Dict, paper_content, outline_data) -> ArticleSection:
        """生成总结"""
        title = section_data.get("title", "总结与展望")
        question = section_data.get("question", "这项技术将走向何方？")

        prompt = f"""请用大白话写一段面向"小白"的总结。

论文标题: {paper_content.title}
核心创新: {outline_data.get('core_innovation', '')}
开放问题: {question}

要求:
1. 用一句话回顾核心观点（像给完全不懂的人总结）
2. 提出一个开放性问题引发思考
3. 用一句通俗易懂的"金句"结尾
4. 专业术语首次出现时，用*术语（大白话解释）*格式，例如：*神经网络（像人脑一样工作的计算程序）*
5. 禁止出现Markdown格式（##、###、> 等）
6. 禁止出现任何数学公式或LaTeX符号（$等）
7. 150-200字，温暖、启发性
8. 使用第三人称客观叙述

直接输出正文内容。"""

        try:
            content = self.llm.generate(prompt, temperature=0.8, max_tokens=600)
            content = self._clean_llm_output(content)
        except Exception as e:
            logger.warning(f"总结部分生成失败，使用模板: {e}")
            content = self._get_default_conclusion(question)

        return ArticleSection(
            section_type="conclusion",
            title=title,
            content=content
        )

    def _generate_paper_info(self, paper_content) -> ArticleSection:
        """生成论文信息"""
        content = f"""**原文标题**: {paper_content.title or 'N/A'}

**作者**: {', '.join(paper_content.authors) if paper_content.authors else 'N/A'}

**机构**: {paper_content.institution or 'N/A'}

**发表日期**: {paper_content.publication_date or 'N/A'}

**arXiv ID**: {paper_content.arxiv_id or 'N/A'}

**DOI**: {paper_content.doi or 'N/A'}

**原文链接**: {'https://arxiv.org/abs/' + paper_content.arxiv_id if paper_content.arxiv_id else 'N/A'}
"""

        return ArticleSection(
            section_type="paper_info",
            title="论文信息",
            content=content
        )

    def _extract_metrics_from_paper(self, paper_content) -> List[Dict[str, str]]:
        """从论文内容中提取指标数据"""
        metrics = []
        text = paper_content.raw_text[:5000]

        # 常见的性能指标模式
        patterns = [
            (r'(\d+\.?\d*)\s*×\s*faster', "速度提升"),
            (r'(\d+\.?\d*)%\s*(?:accuracy|accuracy)', "准确率"),
            (r'(\d+\.?\d*)\s*GB', "内存占用"),
            (r'(\d+\.?\d*)\s*s(?:econd)?', "处理时间"),
        ]

        for pattern, meaning in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:2]:  # 只取前2个
                metrics.append({
                    "name": meaning,
                    "value": match,
                    "meaning": f"论文中提到的{meaning}"
                })

        return metrics

    def _clean_llm_output(self, text: str) -> str:
        """清理 LLM 输出 - 移除Markdown和LaTeX格式"""
        # 移除 markdown 代码块标记
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)

        # 移除 Markdown 标题符号 (##、###等)
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

        # 移除 Markdown 加粗和斜体标记
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)

        # 移除 Markdown 列表标记
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

        # 移除 LaTeX 数学公式 ($...$ 和 $$...$$)
        text = re.sub(r'\$\$[^$]*\$\$', '', text)
        text = re.sub(r'\$[^$]*\$', '', text)

        # 移除 Markdown 引用符号
        text = re.sub(r'^\s*>\s*', '', text, flags=re.MULTILINE)

        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 清理首尾空白
        text = text.strip()

        return text

    # 默认模板（LLM 失败时使用）
    def _get_default_intro(self, paper_content, analogy_theme) -> str:
        return f"""想象一下，在我们的日常生活中，{analogy_theme}的场景随处可见。

这让我想到了今天要介绍的这项研究——{paper_content.title[:50]}...

那么，这和{analogy_theme}有什么关系呢？让我们一探究竟。"""

    def _get_default_problem(self, paper_content, pain_point) -> str:
        return f"""在深入了解这篇论文之前，我们需要先理解一个基本问题：{pain_point}。

现有的方法虽然在某些场景下表现不错，但在实际应用中往往面临着效率低下、成本高昂等问题。就像用一把钝刀切菜——虽然最终能完成任务，但过程却让人煎熬。

那么，有没有更好的解决方案呢？"""

    def _get_default_method(self, paper_content, key_concepts) -> str:
        concepts_str = "、".join(key_concepts[:3])
        return f"""这就是本文的创新之处。研究团队提出了一种全新的思路，主要包含以下几个关键点：

首先，{concepts_str}。这一设计巧妙地解决了传统方法中的核心痛点。

其次，通过优化算法结构，新方法在保证准确性的同时大幅提升了效率。

最后，这种架构还具有很强的通用性，可以应用到各种相关场景中。

可以说，这是一项既实用又优雅的创新。"""

    def _get_default_results(self, metrics) -> str:
        if metrics:
            return "实验结果显示，新方法在各项关键指标上都有显著提升。具体数字说明了这一点：" + \
                   "；".join([f"{m.get('name')}达到{m.get('value')}" for m in metrics[:3]]) + \
                   "。这些数据充分证明了该方法的有效性。"
        return "实验结果表明，新方法相比现有方案有着明显的优势。无论是在处理速度还是准确性方面，都取得了令人满意的结果。这些数字背后，是研究团队的辛勤付出和巧妙设计。"

    def _get_default_impact(self, implications) -> str:
        return """这项技术的意义不仅仅在于学术层面的突破，更重要的是它将对我们的日常生活产生深远影响：

第一，它将使相关应用变得更加高效和便捷；

第二，成本的降低意味着更多用户能够享受到技术进步带来的红利；

第三，这也为未来的进一步创新奠定了坚实基础。"""

    def _get_default_conclusion(self, question) -> str:
        return f"""回顾整篇论文，我们不禁为这项创新所折服。它不仅仅是一个技术方案，更是一种思维方式的突破。

{question}

答案也许就在不远的将来。但可以确定的是，这项技术已经为人工智能领域注入了新的活力。让我们拭目以待！"""
