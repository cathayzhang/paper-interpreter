#!/usr/bin/env python3
"""
测试 Analyzer 标题生成
"""
import os
from dotenv import load_dotenv
from paper_to_popsci.core.analyzer import ContentAnalyzer
from paper_to_popsci.core.extractor import PaperContent, PaperSection

load_dotenv()

def test_title_generation():
    """测试标题生成"""
    print("🧪 测试 Analyzer 标题生成")
    print("="*60)
    
    # 创建测试论文
    paper_content = PaperContent(
        title="MobileNetV2: Inverted Residuals and Linear Bottlenecks",
        abstract="In this paper we describe a new mobile architecture, MobileNetV2, that improves the state of the art performance of mobile models on multiple tasks and benchmarks.",
        authors=["Mark Sandler", "Andrew Howard"],
        sections=[
            PaperSection(title="Introduction", content="Mobile vision applications require efficient models. We propose MobileNetV2 with inverted residual structure..."),
            PaperSection(title="Method", content="The key innovation is the inverted residual block with linear bottleneck. This design reduces memory footprint while maintaining accuracy..."),
            PaperSection(title="Experiments", content="We evaluate on ImageNet classification. MobileNetV2 achieves 72% top-1 accuracy with only 3.4M parameters...")
        ],
        raw_text="MobileNetV2 introduces inverted residual structure with linear bottlenecks..."
    )
    
    print(f"📄 测试论文: {paper_content.title}")
    print()
    
    try:
        analyzer = ContentAnalyzer()
        print("🔍 开始分析...")
        result = analyzer.analyze(paper_content)
        
        outline = result['outline']
        print("✅ 分析成功!")
        print()
        print(f"📊 分析结果:")
        print(f"  文章类型: {outline['article_type']}")
        print(f"  核心创新: {outline['core_innovation']}")
        print(f"  类比主题: {outline['analogy_theme']}")
        print()
        
        # 检查 hero 标题
        hero_section = next((s for s in outline['sections'] if s['type'] == 'hero'), None)
        if hero_section:
            title = hero_section.get('title', '')
            subtitle = hero_section.get('subtitle', '')
            
            print(f"📰 生成的标题:")
            print(f"  主标题: {title}")
            print(f"  副标题: {subtitle}")
            print()
            
            # 判断标题质量
            if title == "论文解读":
                print("❌ 标题是默认值'论文解读',未转化为科普标题")
            elif title == paper_content.title:
                print("⚠️  标题是论文原标题,未转化为科普标题")
            elif len(title) < 10:
                print("⚠️  标题太短,可能不够吸引人")
            elif len(title) > 40:
                print("⚠️  标题太长,可能需要精简")
            else:
                print("✅ 标题看起来不错!")
                
            # 检查是否包含关键词
            keywords = ['AI', '手机', '移动', '轻量', '高效', '识别', '视觉']
            found_keywords = [kw for kw in keywords if kw in title]
            if found_keywords:
                print(f"  包含关键词: {', '.join(found_keywords)}")
        else:
            print("❌ 未找到 hero 章节")
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("="*60)

if __name__ == "__main__":
    test_title_generation()
