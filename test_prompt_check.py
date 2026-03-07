#!/usr/bin/env python3
"""
检查 Prompt 是否正确加载
"""
from paper_to_popsci.core.analyzer import ContentAnalyzer
from paper_to_popsci.core.extractor import PaperContent

def test_prompt():
    """测试 prompt 内容"""
    print("🔍 检查 Analyzer Prompt")
    print("="*60)
    
    # 创建测试数据
    paper_content = PaperContent(
        title="Test Paper",
        abstract="This is a test abstract.",
        raw_text="Test content"
    )
    
    analyzer = ContentAnalyzer()
    prompt = analyzer._build_analysis_prompt(paper_content)
    
    print("📄 生成的 Prompt:")
    print("-"*60)
    print(prompt)
    print("-"*60)
    print()
    
    # 检查关键词
    keywords = [
        "科普标题(必须吸引人",
        "15-25字",
        "示例参考",
        "让手机也能'看懂'世界"
    ]
    
    print("✅ 关键词检查:")
    for keyword in keywords:
        if keyword in prompt:
            print(f"  ✓ 找到: {keyword}")
        else:
            print(f"  ✗ 缺失: {keyword}")
    
    print()
    print("="*60)

if __name__ == "__main__":
    test_prompt()
