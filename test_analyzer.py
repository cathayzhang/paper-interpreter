#!/usr/bin/env python3
"""
测试论文分析功能
"""
import os
from dotenv import load_dotenv
from paper_to_popsci.core.analyzer import ContentAnalyzer
from paper_to_popsci.core.extractor import PaperContent

# 加载环境变量
load_dotenv()

def test_analyzer():
    """测试分析器"""
    print("🧪 测试论文分析功能")
    print("="*60)
    
    # 创建一个简单的测试论文内容
    paper_content = PaperContent(
        title="Attention Is All You Need",
        abstract="We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
        authors=["Vaswani et al."],
        raw_text="This paper introduces the Transformer model..."
    )
    
    print(f"📄 测试论文: {paper_content.title}")
    print()
    
    try:
        analyzer = ContentAnalyzer()
        print("🔍 开始分析...")
        result = analyzer.analyze(paper_content)
        
        print("✅ 分析成功!")
        print()
        print(f"📊 结果:")
        print(f"  文章类型: {result['outline']['article_type']}")
        print(f"  核心创新: {result['outline']['core_innovation']}")
        print(f"  类比主题: {result['outline']['analogy_theme']}")
        print(f"  章节数量: {len(result['outline']['sections'])}")
        print(f"  配图数量: {len(result['illustration_prompts'])}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analyzer()
