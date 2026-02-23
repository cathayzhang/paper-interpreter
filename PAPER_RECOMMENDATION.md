# 论文关系探索与智能推荐功能

## 🎯 重要说明：无需 API Key 也能使用！

本功能**完全免费**，**无需申请任何 API Key** 即可使用基础功能。系统会自动降级到免费方案：

1. ✅ **Semantic Scholar API** - 无需 Key，共享速率限制
2. ✅ **arXiv API** - 完全免费，无需注册
3. ✅ **本地关键词匹配** - 离线可用，无需网络

提供 API Key 可以获得更高请求速率，但不是必需的。

## 功能概述

系统现在集成了**论文关系探索与智能推荐**功能，在生成科普文章时，会自动添加一个新章节：
- **位置**：在"总结与展望"之后，"论文信息"之前
- **内容**：
  - 🔬 **相关论文推荐**：基于 Semantic Scholar 智能算法的相关论文
  - 📚 **引用网络**：引用该论文的研究 + 该论文引用的前期工作
  - 🔍 **相似主题研究**：基于标题关键词的相似主题搜索

## 技术架构

### 推荐算法来源（按优先级）

1. **Semantic Scholar API**（主要）
   - 端点：`/recommendations/v1/papers/forpaper/{paper_id}`
   - 算法：基于引用网络 + 内容相似度 + 共被引分析
   - 特点：优先推荐最近60天发表的相关论文
   - **费用**：免费，无需 API Key（有共享速率限制）

2. **arXiv API**（备选）
   - 功能：基于标题关键词搜索相关预印本
   - **费用**：完全免费，无需注册
   - 适用：当 Semantic Scholar 不可用时自动切换

3. **本地关键词匹配**（降级方案）
   - 功能：提取论文关键词，生成搜索链接
   - **费用**：离线可用，无需网络
   - 适用：当所有 API 都不可用时提供手动搜索链接

4. **SPECTER 模型**（未来扩展）
   - 用途：本地计算论文语义相似度
   - 优势：专为学术论文设计的嵌入模型

## 配置说明（完全可选）

### 基础使用（无需任何配置）

直接部署即可使用，系统会自动使用免费方案：
- Semantic Scholar API（无 Key 模式）
- arXiv API（完全免费）
- 本地关键词匹配（离线可用）

### 高级配置（可选，提高体验）

```bash
# Semantic Scholar API Key（可选）
# 作用：提高请求速率（1 request/sec vs 共享限制）
# 获取地址：https://www.semanticscholar.org/product/api
SEMANTIC_SCHOLAR_API_KEY=your_api_key

# OpenAlex Email（可选）
# 作用：进入"礼貌池"，获得更快访问速度
OPENALEX_EMAIL=your@email.com
```

### 依赖安装

```bash
pip install pyalex transformers torch numpy
```

或者在 requirements.txt 中已包含：
```
pyalex>=0.14.0
transformers>=4.30.0
torch>=2.0.0
numpy>=1.24.0
```

## 使用方式

无需额外操作！系统会自动处理：

1. 当用户输入论文链接时，系统提取 arXiv ID 或 DOI
2. 调用 `PaperRecommender.get_recommendations()` 获取相关论文
3. 使用 `format_for_article()` 格式化为 Markdown
4. 在 HTML/PDF/Word 输出中显示推荐章节

## API 响应格式

### Semantic Scholar 推荐响应示例

```json
{
  "recommendedPapers": [
    {
      "paperId": "...",
      "title": "Attention is All You Need",
      "authors": [{"name": "Ashish Vaswani"}, ...],
      "year": 2017,
      "citationCount": 50000,
      "abstract": "...",
      "url": "https://www.semanticscholar.org/paper/...",
      "openAccessPdf": {"url": "..."},
      "fieldsOfStudy": ["Computer Science"]
    }
  ]
}
```

## 降级策略（自动执行）

系统采用多层降级策略，确保即使所有 API 都不可用也能提供推荐：

### 第一层：Semantic Scholar API
- 无需 Key 即可使用
- 如果达到速率限制（429 错误）→ 自动降级到第二层

### 第二层：arXiv API
- 完全免费，无需注册
- 基于标题关键词搜索相关论文
- 如果 arXiv 不可用 → 自动降级到第三层

### 第三层：本地关键词匹配
- 离线可用，无需网络
- 提取论文关键词
- 生成以下搜索链接：
  - Semantic Scholar 搜索
  - Google Scholar 搜索
  - arXiv 搜索

### 第四层：手动探索建议
- 如果以上都失败
- 提供通用的论文探索建议

**特点**：整个降级过程对用户透明，不中断文章生成。

## 优化建议

### 对于 Streamlit Cloud 部署

1. **API Key 管理**：
   - 在 Streamlit Cloud 的 Secrets 中添加 `SEMANTIC_SCHOLAR_API_KEY`
   - 在代码中使用 `st.secrets.get("SEMANTIC_SCHOLAR_API_KEY")`

2. **缓存策略**：
   - 考虑使用 `@st.cache_data` 缓存推荐结果
   - TTL 设置为 1-7 天（论文推荐不会频繁变化）

3. **限制请求**：
   - Semantic Scholar API 免费版限制：1 request/sec
   - 已内置限制和重试逻辑

## 示例输出

```markdown
## 关系探索与智能推荐

基于学术论文引用网络和语义相似度分析，为您推荐以下相关研究：

### 🔬 相关论文推荐

**1. An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale** (2021)
- **作者**: Alexey Dosovitskiy, et al.
- **被引次数**: 18000+
- **简介**: 将 Transformer 架构应用于图像识别任务的开创性工作...
- **链接**: [查看详情](https://www.semanticscholar.org/paper/...)
- **PDF**: [免费下载](https://arxiv.org/pdf/2010.11929.pdf)
- **推荐理由**: 基于引用网络和语义相似度的智能推荐

### 📚 引用网络

**引用该论文的研究：**
- [Swin Transformer: Hierarchical Vision Transformer...](...) (2021)
- [Masked Autoencoders Are Scalable Vision Learners](...) (2022)

**该论文引用的前期工作：**
- [Attention is All You Need](...) (2017)
- [BERT: Pre-training of Deep Bidirectional Transformers](...) (2019)

### 🔍 相似主题研究

- **[DeiT: Training Data-efficient Image Transformers...](...)** (2021)
  改进了 ViT 的训练方法，使其在较小的数据集上也能取得良好效果
```

## 相关资源

- [Semantic Scholar API 文档](https://api.semanticscholar.org/api-docs/)
- [OpenAlex API 文档](https://docs.openalex.org/)
- [SPECTER 论文](https://arxiv.org/abs/2004.07180)
- [pyalex GitHub](https://github.com/J535D165/pyalex)

## 故障排查

### 问题：推荐结果只有搜索链接，没有具体论文

**这是正常行为！** 当 Semantic Scholar 和 arXiv API 都不可用时，系统会自动降级到**本地关键词匹配**模式，提供以下搜索链接：
- Semantic Scholar 搜索
- Google Scholar 搜索
- arXiv 搜索

用户可以通过这些链接手动查找相关论文。

### 问题：推荐结果为空

**可能原因：**
1. 论文太新，还没有被 Semantic Scholar 或 arXiv 索引
2. 网络连接问题
3. 论文标题过于独特，找不到相似主题

**解决方案：**
- 无需担心，系统会提供手动搜索链接
- 查看日志了解具体使用了哪种降级方案
- 如果是网络问题，稍后重试即可

### 问题：API 调用超时

**解决方案：**
- 已设置 10 秒超时（Semantic Scholar）和 15 秒超时（arXiv）
- 超时后会自动切换到备选方案
- 系统会优雅降级，不影响文章生成
- 最终至少会提供关键词搜索链接

### 问题：如何知道当前使用的是哪种推荐方案？

**查看日志输出：**
- `Semantic Scholar 推荐: N 篇` - 使用了主要推荐源
- `arXiv 推荐: N 篇` - 使用了备选推荐源
- `本地关键词推荐: N 个搜索链接` - 使用了降级方案
- `Semantic Scholar 速率限制` - 达到了 API 限制，已自动降级
