# Paper Interpreter 用户指南

## 📖 简介

Paper Interpreter 是一个将学术论文自动转换为通俗易懂的科普文章的工具。它面向"一无所知"的小白读者，用大白话讲解复杂的学术概念，并配有 AI 生成的精美插图。

## ✨ 核心特性

### 1. 大白话写作风格
- 假设读者对领域完全不了解
- 用吃饭、购物、装修等生活场景类比技术概念
- 每句话都力求通俗易懂

### 2. 智能术语注解
- 专业术语首次出现时自动添加大白话解释
- HTML 版支持鼠标悬停查看解释
- PDF 版自动显示括号内小字注释

### 3. AI 配图生成
- 根据论文内容自动生成 5 张配图
- 强调"秒懂"和"分享欲"
- 暖米色背景，统一风格

### 4. 精美排版输出
- 暖米色纸质阅读感
- 优雅章节标题设计
- 支持 HTML 和 PDF 双格式

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/paper-to-popsci.git
cd paper-to-popsci

# 安装依赖
pip install -r requirements.txt
```

### 配置 API Key

创建 `.env` 文件：

```bash
# 文本生成 API
GEMINI_API_KEY=your-gemini-api-key
GEMINI_API_URL=https://yunwu.ai

# 图像生成 API
NANO_BANANA_API_KEY=your-nano-banana-api-key
NANO_BANANA_API_URL=https://yunwu.ai
```

### 运行

```bash
python -m paper_to_popsci https://arxiv.org/abs/2312.00752
```

## 📚 使用示例

### 解读 arXiv 论文

```bash
python -m paper_to_popsci https://arxiv.org/abs/1512.03385
```

输出：
- `article.html` - 精美网页版，支持术语悬停
- `article.pdf` - PDF 版，适合打印分享
- `assets/images/` - 5 张 AI 生成配图
- `metadata.json` - 论文元数据

### 解读 DOI 论文

```bash
python -m paper_to_popsci https://doi.org/10.1109/TPAMI.2016.2577031
```

### 解读 OpenReview 论文

```bash
python -m paper_to_popsci https://openreview.net/forum?id=xxxxx
```

## 🎨 术语注解说明

### 格式规范

在文章中，专业术语使用如下格式：

```
*术语（大白话解释）*
```

### 示例

**原文**：
```
在人工智能的世界里，神经网络面临着*梯度消失（信息在传递中衰减的现象）*的问题。
```

**HTML 效果**：
- 术语"梯度消失"显示为绿色带下虚线
- 鼠标悬停时显示深色提示框："信息在传递中衰减的现象"

**PDF 效果**：
- 术语"梯度消失"正常显示
- 括号内灰色小字："（信息在传递中衰减的现象）"

## 📊 输出文件说明

### article.html
- 精美网页版
- 支持术语悬停提示
- 响应式设计，适配移动端
- 可直接在浏览器中打开

### article.pdf
- 打印优化版本
- 术语注解显示为括号内小字
- 适合保存和分享

### assets/images/
包含 5 张 AI 生成配图：
1. `hero_xxxxx.png` - Hero 区主图
2. `intro_xxxxx.png` - 引言配图
3. `method_xxxxx.png` - 方法配图
4. `comparison_xxxxx.png` - 对比配图
5. `conclusion_xxxxx.png` - 总结配图

## ⚙️ 高级配置

### 自定义输出目录

```bash
export PAPER_OUTPUT_DIR="/path/to/output"
```

### 调整配图数量

```bash
export ILLUSTRATION_COUNT=3  # 默认 5 张
```

### 调整文章长度

编辑 `paper_to_popsci/core/config.py`：

```python
CHUNK_SIZE_TOKENS = 4000  # 分块阈值
```

## 🔧 故障排除

### 问题：配图生成失败

**现象**：
```
[警告] 配图生成失败: Rate limit exceeded
```

**解决**：
- 检查 API Key 是否有效
- 等待一段时间后重试
- 系统会自动继续生成文章，缺失配图处会跳过

### 问题：PDF 导出失败

**现象**：
```
[警告] WeasyPrint 导出失败
```

**解决**：
- 系统会自动返回 HTML 文件
- 可手动使用浏览器打印为 PDF

### 问题：论文下载失败

**现象**：
```
[错误] 论文下载失败
```

**解决**：
- 检查链接是否可访问
- 尝试使用浏览器下载 PDF 后直接上传
- 检查网络连接

## 📸 截图示例

### HTML 版预览

```
┌─────────────────────────────────────────┐
│  深度学习的"不忘初心"                   │
│  让神经网络深到152层也不迷路           │
│                                         │
│  [Hero 配图]                            │
├─────────────────────────────────────────┤
│                                         │
│  想象一下你正在升级你家的老旧Wi-Fi      │
│  路由器...                              │
│                                         │
│  在*人工智能（让计算机像人一样思考和    │
│  学习的科学）*的世界里...               │
│  [鼠标悬停显示解释]                     │
│                                         │
│  [引言配图]                             │
│                                         │
├─────────────────────────────────────────┤
│  论文信息                               │
│  原文标题: Deep Residual Learning...    │
│  作者: Kaiming He et al.                │
└─────────────────────────────────────────┘
```

### 术语悬停效果

```
文本: 在*神经网络（像人脑一样工作的计算程序）*中...
      ↑
      鼠标悬停
      ↓
┌─────────────────────────────────┐
│ 像人脑一样工作的计算程序        │
└─────────────────────────────────┘
```

## 🤝 贡献指南

欢迎提交 Issue 和 PR！

### 提交 Issue
- 描述问题现象
- 提供复现步骤
- 贴出错误日志

### 提交 PR
1. Fork 仓库
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 📄 许可证

MIT License

## 🙏 致谢

- 论文内容提取：PyPDF2 / unstructured
- 文本生成：Gemini API
- 图像生成：Nano Banana API
- 样式框架：Tailwind CSS

---

如有问题，欢迎提交 Issue 或联系开发者。
