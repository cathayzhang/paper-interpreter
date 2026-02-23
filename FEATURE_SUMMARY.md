# 论文关系探索与智能推荐 - 功能完成总结

## 🎯 重要：无需 API Key 也能使用！

本功能**完全免费**，**无需申请任何 API Key** 即可使用。系统采用四层自动降级策略：
1. ✅ **Semantic Scholar API** - 无需 Key，共享速率限制
2. ✅ **arXiv API** - 完全免费，无需注册
3. ✅ **本地关键词匹配** - 离线可用，无需网络
4. ✅ **手动搜索链接** - 最终降级方案

提供 API Key 可以提高请求速率，但不是必需的。

## 已完成的功能

### 1. 核心推荐模块
**文件**: `paper_to_popsci/core/paper_recommender.py`

- **PaperRecommender** 类：整合多个学术数据源
  - **Semantic Scholar API**（主要推荐源）- 无需 Key 也能使用
  - **arXiv API**（完全免费的备选方案）
  - **本地关键词匹配**（离线可用）
  - **四层自动降级策略**（对用户透明）

- **RelatedPaper** 数据类：标准化推荐结果格式

### 2. 降级策略详解

| 层级 | 方案 | 是否需要网络 | 是否需要 Key | 触发条件 |
|------|------|-------------|-------------|----------|
| 1 | Semantic Scholar API | ✅ | ❌ | 默认首选 |
| 2 | arXiv API | ✅ | ❌ | SS 失败时 |
| 3 | 本地关键词匹配 | ❌ | ❌ | 网络不可用时 |
| 4 | 手动搜索建议 | ❌ | ❌ | 以上都失败时 |

### 2. 集成到文章生成流程
**文件**: `paper_to_popsci/core/writer.py`

- 在 `_generate_paper_info` 之前添加 `_generate_recommendations` 调用
- 新增 `recommendations` 章节类型
- 提供默认降级内容（当 API 不可用时）

### 3. HTML 渲染支持
**文件**: `paper_to_popsci/core/renderer.py`

- 新增 `_render_recommendations_section` 方法
- 特殊样式处理：论文标题、来源标签、链接
- 与现有暖米色主题保持一致

### 4. Word 导出支持
**文件**: `paper_to_popsci/core/multi_format_exporter.py`

- 新增 `_add_recommendations_to_docx` 方法
- 特殊格式化：分级标题、缩进、项目符号
- 确保在 Word 中美观显示

### 5. Streamlit 界面配置
**文件**: `streamlit_app.py`

- 侧边栏新增 "论文推荐 API (可选)" 折叠区域
- 支持输入 Semantic Scholar API Key
- 支持输入 OpenAlex Email（礼貌池加速）

### 6. 依赖更新
**文件**: `requirements.txt`

新增依赖：
- `pyalex>=0.14.0` - OpenAlex API Python 客户端
- `transformers>=4.30.0` - 用于未来 SPECTER 模型集成
- `torch>=2.0.0` - PyTorch 深度学习框架
- `numpy>=1.24.0` - 数值计算

### 7. 文档
**文件**: `PAPER_RECOMMENDATION.md`

完整的使用文档，包括：
- 技术架构说明
- API 配置指南
- 使用示例
- 故障排查

## 输出示例

生成的文章将包含以下新章节：

```markdown
## 关系探索与智能推荐

基于学术论文引用网络和语义相似度分析，为您推荐以下相关研究：

### 🔬 相关论文推荐

**1. [论文标题]** (年份)
- **作者**: 作者列表
- **被引次数**: N
- **简介**: 摘要节选
- **链接**: Semantic Scholar 链接
- **PDF**: 免费下载链接（如有）
- **推荐理由**: 基于引用网络和语义相似度的智能推荐

### 📚 引用网络

**引用该论文的研究：**
- [后续研究1] (年份)
- [后续研究2] (年份)

**该论文引用的前期工作：**
- [前期工作1] (年份)
- [前期工作2] (年份)

### 🔍 相似主题研究

- **[相关论文1]** (年份)
  简介...
```

## 部署说明

### 本地部署
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Streamlit Cloud 部署
1. 确保 `requirements.txt` 包含所有依赖
2. （可选）在 Streamlit Secrets 中添加 `SEMANTIC_SCHOLAR_API_KEY`
3. 部署后会自动安装依赖

### 无需 API Key 即可使用！

系统默认使用免费方案：
- **Semantic Scholar API**: 无需 Key，共享速率限制
- **arXiv API**: 完全免费，无需注册
- **本地关键词匹配**: 离线可用

### 可选的高级配置
- **Semantic Scholar API Key** (可选): https://www.semanticscholar.org/product/api
  - 作用：提高请求速率到 1 request/sec
  - 不提供也能使用（共享限制）
- **OpenAlex Email** (可选): 提供邮箱进入"礼貌池"，访问更快

## 技术亮点

1. **四层自动降级策略**（无需 API Key）
   - Semantic Scholar API（无需 Key）
   - arXiv API（完全免费）
   - 本地关键词匹配（离线可用）
   - 手动搜索链接（最终降级）
   - 整个过程对用户透明

2. **完全免费**
   - 无需申请任何 API Key 即可使用
   - 提供 Key 可以获得更高速率，但不是必需的
   - 所有降级方案都免费

3. **多格式支持**
   - HTML：美观的卡片式布局
   - Word：专业的文档格式
   - PDF：通过 HTML 转换
   - Markdown：标准格式

4. **可扩展性**
   - 预留 SPECTER 语义相似度接口
   - 模块化设计，易于添加新推荐源
   - 配置化 API Key 管理

## 文件修改清单

- ✅ `paper_to_popsci/core/paper_recommender.py` (新增)
- ✅ `paper_to_popsci/core/writer.py` (修改)
- ✅ `paper_to_popsci/core/renderer.py` (修改)
- ✅ `paper_to_popsci/core/multi_format_exporter.py` (修改)
- ✅ `paper_to_popsci/core/__init__.py` (修改)
- ✅ `streamlit_app.py` (修改)
- ✅ `requirements.txt` (修改)
- ✅ `PAPER_RECOMMENDATION.md` (新增)
- ✅ `FEATURE_SUMMARY.md` (新增)
