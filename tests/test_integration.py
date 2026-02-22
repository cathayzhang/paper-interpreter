#!/usr/bin/env python3
"""
集成测试脚本
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_to_popsci.cli import process_paper


TEST_CASES = [
    {
        "id": "T-001",
        "name": "arXiv Mamba 论文",
        "url": "https://arxiv.org/abs/2312.00752",
    },
    {
        "id": "T-002",
        "name": "arXiv PDF 直接链接",
        "url": "https://arxiv.org/pdf/2312.00752.pdf",
    },
]


def run_test(test_case):
    """运行单个测试用例"""
    print(f"\n{'='*60}")
    print(f"测试 {test_case['id']}: {test_case['name']}")
    print(f"URL: {test_case['url']}")
    print(f"{'='*60}")

    try:
        result = process_paper(test_case['url'])

        if result['success']:
            print(f"✅ 测试通过")
            print(f"   输出目录: {result['output_dir']}")
            print(f"   处理时间: {result['statistics']['elapsed_time']}s")
            return True
        else:
            print(f"❌ 测试失败: {result.get('error', '未知错误')}")
            return False

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("Paper to PopSci - 集成测试")
    print("=" * 60)

    results = []
    for test in TEST_CASES:
        success = run_test(test)
        results.append((test['id'], success))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for test_id, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_id}: {status}")

    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
