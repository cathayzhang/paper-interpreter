"""
内容分析模块
使用 LLM 分析论文内容，规划文章结构和配图
"""
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

from .config import Config
from .logger import logger
from .llm_client import LLMClient


@dataclass
class ArticleOutline:
    """文章大纲"""
    article_type: str = ""  # 架构创新 / 算法优化 / 应用突破 / 理论分析
    core_innovation: str = ""  # 核心创新点
    analogy_theme: str = ""  # 类比主题
    sections: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class IllustrationPrompt:
    """配图提示词"""
    section: str  # 对应章节
    prompt: str  # 提示词
    style: str = "学术论文配图，暖米色背景，手绘风格，柔和线条，淡雅色彩"
    negative_prompt: str = "文字、字母、数字、水印、杂乱背景"


class ContentAnalyzer:
    """内容分析器"""

    def __init__(self):
        self.llm = LLMClient()

    def analyze(self, paper_content) -> Dict[str, Any]:
        """
        分析论文内容

        Args:
            paper_content: PaperContent 对象

        Returns:
            包含大纲和配图提示词的字典
        """
        logger.info("开始分析论文内容...")

        # 构建分析提示
        analysis_prompt = self._build_analysis_prompt(paper_content)

        # 调用 LLM 分析
        try:
            response = self.llm.generate(
                prompt=analysis_prompt,
                temperature=0.7,
                max_tokens=2000
            )

            # 解析响应
            outline = self._parse_outline(response)
            logger.info(f"分析完成: 类型={outline.article_type}, 创新点={outline.core_innovation[:50]}...")

            # 生成配图提示词
            illustration_prompts = self._generate_illustration_prompts(outline, paper_content)
            logger.info(f"生成配图提示词: {len(illustration_prompts)} 张")

            return {
                "outline": asdict(outline),
                "illustration_prompts": [asdict(p) for p in illustration_prompts]
            }

        except Exception as e:
            logger.error(f"内容分析失败: {e}")
            # 返回默认大纲
            return self._get_default_outline(paper_content)

    def _build_analysis_prompt(self, paper_content) -> str:
        """构建分析提示"""
        title = paper_content.title or "未知标题"
        abstract = paper_content.abstract or ""
        sections_text = "\n\n".join([
            f"## {s.title}\n{s.content[:500]}"
            for s in paper_content.sections[:5]  # 只取前5个章节
        ])

        prompt = f"""请分析以下学术论文，提取关键信息并规划科普文章结构。

# 论文信息

标题: {title}

摘要: {abstract[:1000]}

主要章节:
{sections_text}

# 任务

请输出 JSON 格式的分析结果:
{{
    "article_type": "论文类型(架构创新/算法优化/应用突破/理论分析)",
    "core_innovation": "一句话概括核心创新点",
    "analogy_theme": "选择一个日常生活类比主题(如:餐厅服务员/图书馆/快递配送/城市交通等)",
    "sections": [
        {{
            "type": "hero",
            "title": "主标题(简洁有力)",
            "subtitle": "引号副标题(一句话卖点)"
        }},
        {{
            "type": "intro",
            "title": "引子标题(从XX谈起)",
            "analogy": "故事类比的具体场景描述"
        }},
        {{
            "type": "problem",
            "title": "背景/问题标题",
            "pain_point": "现有方法的核心痛点"
        }},
        {{
            "type": "method",
            "title": "核心方法标题",
            "key_concepts": ["关键概念1", "关键概念2", "关键概念3"]
        }},
        {{
            "type": "results",
            "title": "结果",
            "metrics": [
                {{"name": "指标名称", "value": "数值", "meaning": "含义解释"}}
            ]
        }},
        {{
            "type": "impact",
            "title": "意义",
            "implications": ["对普通人的影响1", "对普通人的影响2"]
        }},
        {{
            "type": "conclusion",
            "title": "总结",
            "question": "开放性总结问题"
        }}
    ]
}}

注意:
1. 用通俗易懂的语言描述，避免学术黑话
2. 类比要贴近日常生活，让非技术读者能理解
3. 突出论文的创新点和实用价值
"""
        return prompt

    def _parse_outline(self, response: str) -> ArticleOutline:
        """解析 LLM 响应"""
        try:
            # 提取 JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            return ArticleOutline(
                article_type=data.get("article_type", "技术创新"),
                core_innovation=data.get("core_innovation", ""),
                analogy_theme=data.get("analogy_theme", "日常生活"),
                sections=data.get("sections", [])
            )
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}，使用文本解析")
            # 简单的文本解析降级
            return self._parse_outline_text(response)

    def _parse_outline_text(self, response: str) -> ArticleOutline:
        """文本方式解析大纲（降级方案）"""
        outline = ArticleOutline()

        # 提取类型
        type_match = re.search(r'article_type[:\"\']+([^\"\',}]+)', response)
        if type_match:
            outline.article_type = type_match.group(1).strip()

        # 提取创新点
        innovation_match = re.search(r'core_innovation[:\"\']+([^\"\',}]+)', response)
        if innovation_match:
            outline.core_innovation = innovation_match.group(1).strip()

        # 提取类比主题
        analogy_match = re.search(r'analogy_theme[:\"\']+([^\"\',}]+)', response)
        if analogy_match:
            outline.analogy_theme = analogy_match.group(1).strip()

        # 默认章节结构
        outline.sections = [
            {"type": "hero", "title": "论文解读", "subtitle": "「一项有趣的技术创新」"},
            {"type": "intro", "title": "从生活谈起", "analogy": "这项技术和我们的生活息息相关"},
            {"type": "problem", "title": "问题的提出", "pain_point": "现有方法存在局限"},
            {"type": "method", "title": "解决方案", "key_concepts": ["创新点1", "创新点2"]},
            {"type": "results", "title": "实验结果", "metrics": []},
            {"type": "impact", "title": "意义与影响", "implications": []},
            {"type": "conclusion", "title": "总结", "question": "这项技术将走向何方？"}
        ]

        return outline

    def _generate_illustration_prompts(self, outline: ArticleOutline, paper_content) -> List[IllustrationPrompt]:
        """生成配图提示词 - 生成有意义的中文技术图表"""
        prompts = []

        # 从论文内容提取技术细节
        paper_title = paper_content.title or ""
        paper_abstract = paper_content.abstract[:200] if paper_content.abstract else ""

        # Hero 图 - 架构概览图
        hero_prompt = f"""Create a technical architecture diagram in Chinese:
- Title: {paper_title[:50]}
- Style: Clean technical diagram, flat design, light beige/cream background (#FDF6E3)
- Content: System architecture overview showing main components and data flow
- Use Chinese labels for key components
- Include boxes, arrows, and connection lines
- Color scheme: Teal (#16A085) for main elements, soft grays for secondary
- Professional, academic paper quality
- No decorative elements, focus on technical clarity"""

        prompts.append(IllustrationPrompt(
            section="hero",
            prompt=hero_prompt,
            style="技术架构图，扁平设计，中文标签"
        ))

        # 引言图 - 问题场景示意图
        intro_section = next((s for s in outline.sections if s.get("type") == "intro"), None)
        if intro_section:
            intro_prompt = f"""Create a problem scenario diagram in Chinese:
- Style: Simple infographic style, warm beige background
- Content: Show the "before" problem situation with labeled components
- Use Chinese text labels to explain the issue
- Include simple icons or symbols (not photos)
- Show data flow or process bottleneck
- Color: Warm tones with teal accents
- Clear, educational diagram style"""

            prompts.append(IllustrationPrompt(
                section="intro",
                prompt=intro_prompt,
                style="问题场景图，信息图表，中文标签"
            ))

        # 方法图 - 核心算法流程图
        method_section = next((s for s in outline.sections if s.get("type") == "method"), None)
        if method_section:
            concepts = method_section.get("key_concepts", [])
            concepts_text = "、".join(concepts[:2]) if concepts else "核心方法"

            method_prompt = f"""Create an algorithm flowchart in Chinese:
- Topic: {concepts_text}
- Style: Technical flowchart with steps and decision points
- Use standard flowchart symbols (rectangles, diamonds, arrows)
- Label each step in Chinese
- Show input, process, and output clearly
- Include key mathematical operations or transformations
- Background: Light cream/beige
- Color: Teal (#16A085) for main flow, gray for secondary
- Clean, readable, academic quality"""

            prompts.append(IllustrationPrompt(
                section="method",
                prompt=method_prompt,
                style="算法流程图，标准符号，中文标签"
            ))

        # 对比图 - 性能对比图表
        problem_section = next((s for s in outline.sections if s.get("type") == "problem"), None)
        if problem_section:
            comparison_prompt = f"""Create a comparison chart in Chinese:
- Style: Side-by-side comparison table or bar chart
- Left side: "传统方法" (Traditional) with metrics like O(N²), high memory
- Right side: "新方法" (New) with metrics like O(N), efficient
- Use Chinese labels for all metrics
- Include visual indicators (checkmarks, arrows)
- Background: Cream/beige with clear contrast
- Color: Gray/blue for traditional, teal/green for new method
- Data visualization style, clear and informative"""

            prompts.append(IllustrationPrompt(
                section="comparison",
                prompt=comparison_prompt,
                style="对比图表，数据可视化，中文标签"
            ))

        # 总结图 - 应用架构图
        conclusion_section = next((s for s in outline.sections if s.get("type") == "conclusion"), None)
        if conclusion_section:
            future_prompt = f"""Create an application architecture diagram in Chinese:
- Style: System integration diagram showing real-world applications
- Show: Input sources → Processing → Output applications
- Use Chinese labels for each component
- Include example applications (NLP, CV, etc.)
- Background: Light warm beige
- Color: Teal and gold accents
- Professional technical diagram style
- Show how the technology fits into larger systems"""

            prompts.append(IllustrationPrompt(
                section="conclusion",
                prompt=future_prompt,
                style="科幻未来感插画，温馨 optimistic"
            ))

        return prompts

    def _get_default_outline(self, paper_content) -> Dict[str, Any]:
        """获取默认大纲（分析失败时的降级方案）"""
        title = paper_content.title or "论文解读"

        outline = ArticleOutline(
            article_type="技术创新",
            core_innovation=f"本文介绍了{title}的核心思想",
            analogy_theme="日常生活",
            sections=[
                {"type": "hero", "title": title, "subtitle": "「一项值得关注的技术进展」"},
                {"type": "intro", "title": "从生活谈起", "analogy": "这项技术与我们的日常生活有着密切的联系"},
                {"type": "problem", "title": "问题的提出", "pain_point": "现有方法面临效率和准确性的挑战"},
                {"type": "method", "title": "解决方案", "key_concepts": ["核心方法", "关键技术"]},
                {"type": "results", "title": "实验结果", "metrics": []},
                {"type": "impact", "title": "意义与影响", "implications": ["提升效率", "改善体验"]},
                {"type": "conclusion", "title": "总结与展望", "question": "这项技术将如何改变我们的未来？"}
            ]
        )

        illustration_prompts = self._generate_illustration_prompts(outline, paper_content)

        return {
            "outline": asdict(outline),
            "illustration_prompts": [asdict(p) for p in illustration_prompts]
        }
