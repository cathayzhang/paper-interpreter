#!/usr/bin/env python3
"""
测试完整的文章生成流程
"""
import os
from dotenv import load_dotenv
from paper_to_popsci.core.analyzer import ContentAnalyzer
from paper_to_popsci.core.writer import ArticleWriter
from paper_to_popsci.core.extractor import PaperContent, PaperSection

# 加载环境变量
load_dotenv()

def test_full_generation():
    """测试完整生成流程"""
    print("🧪 测试完整文章生成流程")
    print("="*60)
    
    # 创建测试论文内容
    paper_content = PaperContent(
        title="MobileNetV2: Inverted Residuals and Linear Bottlenecks",
        abstract="In this paper we describe a new mobile architecture, MobileNetV2, that improves the state of the art performance of mobile models on multiple tasks and benchmarks as well as across a spectrum of different model sizes.",
        authors=["Mark Sandler", "Andrew Howard"],
        sections=[
            PaperSection(title="Introduction", content="Mobile vision applications require efficient models..."),
            PaperSection(title="Related Work", content="Prior work on efficient neural networks..."),
            PaperSection(title="Method", content="We propose inverted residual blocks with linear bottlenecks..."),
            PaperSection(title="Experiments", content="We evaluate MobileNetV2 on ImageNet classification...")
        ],
        raw_text="MobileNetV2 introduces inverted residual structure..."
    )
    
    print(f"📄 测试论文: {paper_content.title}")
    print()
    
    # 测试 Analyzer
    print("🔍 步骤 1: 分析论文...")
    try:
        analyzer = ContentAnalyzer()
        result = analyzer.analyze(paper_content)
        
        outline = result['outline']
        print(f"✅ 分析成功!")
        print(f"  文章类型: {outline['article_type']}")
        print(f"  核心创新: {outline['core_innovation']}")
        print(f"  类比主题: {outline['analogy_theme']}")
        
        # 检查标题
        hero_section = next((s for s in outline['sections'] if s['type'] == 'hero'), None)
        if hero_section:
            title = hero_section.get('title', '')
            print(f"  生成标题: {title}")
            
            if title == "论文解读" or title == paper_content.title:
                print("  ⚠️  警告: 标题没有转化成科普标题!")
            else:
                print("  ✓ 标题已转化为科普标题")
        
        print()
        
        # 测试 Writer (只测试 hero 部分)
        print("✍️  步骤 2: 生成文章 Hero 部分...")
        writer = ArticleWriter()
        
        if hero_section:
            hero_article = writer._generate_hero(hero_section, paper_content)
            print(f"✅ Hero 生成成功!")
            print(f"  标题: {hero_article.title}")
            print(f"  内容预览: {hero_article.content[:200]}...")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("="*60)

if __name__ == "__main__":
    test_full_generation()
