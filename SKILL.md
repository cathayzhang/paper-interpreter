# Paper Interpreter - 论文解读专家

---

## metadata

- **name**: paper-to-popsci
- **description**: 将学术论文自动转换为通俗易懂、图文并茂的科普文章（面向"一无所知"的小白风格），支持智能术语注解、AI 配图生成、精美 HTML/PDF 输出
- **license**: MIT

---

## 静默执行协议 (Zero-Interrupt Protocol)

**⚠️ 重要：本 Skill 必须全自动化执行，严禁中断工作流。**

执行本 Skill 时，你必须遵守以下原则：

1. **DO NOT ask for confirmation to proceed** - 不要请求确认以继续
2. **Generate the full output in one go** - 一次性生成完整输出
3. **If data is missing, use the defined defaults** - 如果数据缺失，使用预定义默认值
4. **Handle errors silently with fallbacks** - 静默处理错误并使用降级方案
5. **Never pause for user input** - 绝不为等待用户输入而暂停

**默认假设 (Default Assumptions):**
- 输出目录: `./paper_outputs/`
- 配色方案: 暖米色背景 (#FDF6E3) + 深灰文字 (#2C3E50) + 青绿强调 (#16A085)
- 配图数量: 3-5 张（引言1张 + 核心概念2-3张 + 总结1张）
- 分块阈值: 4000 tokens
- 文件冲突处理: 自动添加时间戳后缀

---

## 技能触发 (Trigger)

**触发命令**:
```bash
python -m paper_to_popsci <论文链接>
```

**支持的链接格式**:

| 来源 | 格式示例 | 说明 |
|------|---------|------|
| arXiv | `https://arxiv.org/abs/2312.00752` | 最常用，自动提取 arXiv ID |
| arXiv PDF | `https://arxiv.org/pdf/2312.00752` | 直接下载 PDF |
| DOI | `https://doi.org/10.1109/TPAMI.2016.2577031` | 通过 doi.org 解析 |
| OpenReview | `https://openreview.net/forum?id=xxxxx` | ICLR/NeurIPS/ICML 等 |
| Semantic Scholar | `https://www.semanticscholar.org/paper/xxxxx` | 学术搜索引擎 |
| 直接 PDF | `https://example.com/paper.pdf` | 以 `.pdf` 结尾 |

**失败降级**: 如果链接格式无法识别，尝试使用 requests 直接下载，伪装浏览器 Headers，超时 30 秒。

---

## 执行流程 (Execution Flow)

### Step 1: 论文下载

```
输入: 论文链接
输出: 本地 PDF 路径
降级: 如果下载失败，尝试使用 wget/curl 命令行工具
静默失败: 记录错误到 logs/error.log，返回失败状态码
```

**实现逻辑**:
1. 解析链接类型，选择对应下载策略
2. arXiv 链接 → 使用 arxiv-dl 或直接构造 PDF URL
3. DOI 链接 → 通过 doi.org 解析重定向
4. 通用方案 → requests.get() 配合 headers={"User-Agent": "Mozilla/5.0"}
5. 验证下载文件是否为有效 PDF（检查文件头 %PDF）
6. 保存到临时目录: `/tmp/paper_interpreter/{timestamp}/paper.pdf`

### Step 2: 内容提取

```
输入: 本地 PDF 路径
输出: 结构化内容对象 {title, authors, abstract, sections, figures, metadata}
降级: 如果 unstructured 失败，使用 PyPDF2 提取纯文本
静默失败: 至少提取标题和摘要，继续后续流程
```

**提取字段**:
- `title`: 论文标题（中英文）
- `authors`: 作者列表
- `abstract`: 摘要全文
- `institution`: 第一作者机构
- `publication_date`: 发表日期
- `arxiv_id`: arXiv ID（如有）
- `doi`: DOI（如有）
- `sections`: 章节数组 [{title, content, level}]
- `figures`: 图表描述数组 [{caption, page}]
- `references`: 参考文献计数

### Step 3: 内容分析与结构规划

```
输入: 结构化内容对象
输出: 文章大纲
```

**分析维度**:
1. 识别论文类型: 架构创新 / 算法优化 / 应用突破 / 理论分析
2. 提取核心创新点: 用一句话概括 "解决了什么问题"
3. 确定目标读者: 技术背景读者 / 普通大众
4. 选择类比场景: 日常生活 / 历史典故 / 科幻场景

**输出大纲模板**:
```json
{
  "article_type": "架构创新",
  "core_innovation": "用选择性状态空间替代注意力机制",
  "analogy_theme": "餐厅服务员的记忆问题",
  "sections": [
    {"type": "hero", "title": "主标题", "subtitle": "引号副标题"},
    {"type": "intro", "title": "引子", "analogy": "故事/比喻"},
    {"type": "problem", "title": "背景/问题", "pain_point": "现有方法痛点"},
    {"type": "method", "title": "核心方法", "key_concepts": ["概念1", "概念2"]},
    {"type": "results", "title": "结果", "metrics": [{"name": "指标", "value": "数值"}]},
    {"type": "impact", "title": "意义", "implications": ["影响1", "影响2"]},
    {"type": "conclusion", "title": "总结", "question": "开放性总结问题"}
  ]
}
```

### Step 4: 配图提示词生成

```
输入: 文章大纲
输出: 配图提示词数组 [{section, prompt, style}]
```

**配图策略**:
- **Hero 图**: 论文核心概念的视觉隐喻，风格：现代扁平插画，一目了然
- **引言图**: 类比场景的可视化，风格：生活化场景插画，让读者秒懂
- **方法图**: 核心机制示意图，风格：清晰的步骤图解 + 通俗标注
- **对比图**: 新旧方法对比，风格：分屏对比，突出改进效果
- **总结图**: 未来展望场景，风格：科技感但易懂，引发思考

**配图设计原则**:
- **秒懂原则**: 一眼就能看懂核心意思，不需要解释
- **生活化类比**: 用日常事物类比技术概念
- **前后对比**: 展示"以前怎么样，现在怎么样"
- **分享欲**: 让人看了想保存、想分享
- **暖色调**: 使用米色背景 (#FDF6E3)，与文章整体风格统一

**提示词模板**:
```
风格: 科普教育信息图，暖米色背景，简洁明了，生活化类比
主体: [具体描述，强调易懂和分享价值]
要求: 一目了然，有"Aha!"时刻，让人想保存分享
禁止: 复杂公式、晦涩符号、专业黑话
```

### Step 5: 配图生成

```
输入: 配图提示词数组
输出: 本地图片路径数组
降级: 如果配图失败，使用占位符图片路径并标记
静默失败: 继续文章生成，缺失配图处显示 "[配图生成中...]"
```

**实现逻辑**:
1. 调用 Nano Banana API（或其他配置的 API）
2. 每张图片独立生成，失败不影响其他图片
3. 图片保存到 `assets/images/` 目录
4. 命名格式: `{section_type}_{timestamp}_{index}.png`

### Step 6: 文章生成（通俗科普风格）

```
输入: 文章大纲 + 配图路径
输出: Markdown 格式文章
降级: 如果内容超长，分块生成后合并
静默失败: 无，必须生成完整文章
```

#### 通俗科普风格写作指南

**整体基调**:
- **面向"一无所知"的小白**: 假设读者对领域完全不了解，从零开始讲解
- **大白话**: 用日常口语化表达，避免学术腔调
- **生动比喻**: 用吃饭、购物、交通等生活场景类比技术概念
- **设问引导**: 用问题引导读者思考，如 "为什么...?" "这意味着什么?"
- **情感共鸣**: 让读者感受到这项技术与自己生活的关系

**术语注解系统**:
- 专业术语首次出现时，使用 `*术语（大白话解释）*` 格式
- 例如：`*神经网络（像人脑一样工作的计算程序）*`
- HTML 渲染为优雅的悬停提示框：鼠标悬停显示解释
- PDF 打印时自动转为括号内小字显示

**章节结构**:

**1. Hero 区**
```
主标题: 论文核心概念名称（大字号居中）
副标题: 「引号包裹的一句话卖点」（如"让AI大模型'跑得快还记得住'的新秘诀"）
一句话简介: 用通俗语言解释这是什么（如"一种比Transformer快5倍、还能处理百万级长文本的新架构"）
元信息: 作者、机构、arXiv ID、日期
配图: 居中显示 Hero 图
```

**2. 引子（从XX谈起）**
```
标题: 从[类比场景]谈起（如"从餐厅服务员谈起"）
内容:
  - 用故事/场景引入问题（200-300字）
  - 不要使用 "在人工智能领域..." 这种开头
  - 用具体场景让读者产生共鸣
  - 结尾引出: "这和[论文主题]有什么关系?"
配图: 故事场景插画
```

**3. 背景/问题（XX的烦恼）**
```
标题: [现有方法]的[核心问题]（如"Transformer的记忆烦恼"）
内容:
  - 解释现有方法的工作原理（简化版）
  - 指出其核心痛点和局限
  - 用类比说明问题严重性
  - 铺垫: "有没有更好的办法?"
```

**4. 核心方法（XX的秘密）**
```
标题: [论文核心方法]的秘密（如"Mamba的秘密"）
内容:
  - 用类比解释新方法的核心思想
  - 分点阐述关键创新（3-4个点）
  - 每个点都要有类比解释
  - 避免堆砌数学公式
配图: 机制示意图
```

**5. 结果（数字说话）**
```
标题: 结果：数字说话
内容:
  - 用对比表格/列表展示关键指标
  - 标注数据背后的含义
  - 突出 "更便宜/更快/更好" 的维度
```

**6. 意义（这对我们有什么影响？）**
```
标题: 意义：这对我们有什么影响？
内容:
  - 第一、第二、第三... 分点阐述
  - 每个影响都要连接到普通人的体验
  - 展望未来应用场景
```

**7. 总结（XX还是XX？）**
```
标题: 总结：[开放性对比问题]（如"新王登基？还是诸神之战？"）
内容:
  - 回顾核心观点
  - 提出开放性问题引发思考
  - 引用式金句结尾
引用框: 高亮显示核心洞察
```

**8. 论文信息**
```
标题: 论文信息
内容:
  - 原文标题
  - 作者列表
  - 机构
  - 发表日期
  - 原文链接（可点击）
```

**语言风格示例**:

| ❌ 学术风格 | ❌ 黄叔风格 | ✅ 小白科普风格 |
|-----------|-----------|---------------|
| "Transformer 的计算复杂度为 O(n²)" | "Transformer 就像一位非常认真的服务员" | "想象一下，你有一个超级厉害的快递小哥，专门负责给一个巨大的图书馆送书..." |
| "本研究提出了一种新的状态空间模型" | "这就是 Mamba 的智慧所在" | "这篇论文的核心方法，就像是给建筑师们发明了一种新的、更聪明的施工方法..." |
| "实验结果表明我们的方法在各项指标上均有提升" | "数字会说话" | "这个模型的错误率只有 3.57%，意味着它基本能做到十拿九稳" |

**术语注解示例**:

```
原文: 在人工智能的世界里，我们也有类似的问题。
优化: 在*人工智能（让计算机像人一样思考和学习的科学）*的世界里...

效果: 术语"人工智能"显示为绿色带下虚线，鼠标悬停显示"让计算机像人一样思考和学习的科学"
```

### Step 7: HTML 渲染

```
输入: Markdown 文章 + 配图资源
输出: 精美 HTML 文件
```

**设计要求**:
- **整体风格**: 暖米色背景 #FDF6E3，营造纸质阅读感
- **字体**: 标题用衬线体（Noto Serif SC），正文用无衬线体（Noto Sans SC）
- **术语注解**: 绿色带下虚线 (#16A085)，鼠标悬停显示深色提示框
- **Hero 区**: 大字号居中，配图下方
- **引用框**: 左侧渐变边框 + 圆点装饰，优雅简洁
- **图片**: 圆角 8px，带边框融合背景，底部说明文字居中斜体
- **页眉/页脚**: 简约设计，显示 "Paper Interpreter" 和页码
- **响应式**: 适配移动端阅读，PDF 打印优化
- **排版**: 段间距 1.25em，无首行缩进，两端对齐

**CSS 框架**: 内联 Tailwind CSS，确保单文件可移植

### Step 8: PDF 导出

```
输入: HTML 文件
输出: PDF 文件
降级: 如果 pandoc 失败，使用 weasyprint
静默失败: 返回 HTML 文件路径作为最终输出
```

**实现逻辑**:
1. 首选: `pandoc` + `wkhtmltopdf` 或 `weasyprint`
2. 备选: Playwright 截图转 PDF
3. 页眉页脚通过 CSS @page 规则实现
4. 输出文件名: `{论文标题}_{YYYY-MM-DD}.pdf`

### Step 9: 结果返回

```
输出: 最终报告
```

**返回格式**:
```
✅ 论文解读完成

📄 论文: [论文标题]
📁 输出目录: [完整路径]
   ├── article.html
   ├── article.pdf
   ├── assets/
   │   └── images/
   └── metadata.json

🎨 生成配图: X 张
📊 文章字数: XXXX 字
⏱️ 处理耗时: XX 秒
```

---

## 决策树与错误处理 (Decision Tree & Error Handling)

```
开始
│
├─ 链接解析
│  ├─ 支持格式 → 选择对应下载策略
│  └─ 不支持 → 尝试通用下载
│     ├─ 成功 → 继续
│     └─ 失败 → [错误] 记录并退出
│
├─ 论文下载
│  ├─ 成功 → 验证 PDF 格式
│  └─ 失败 → [错误] 尝试 wget/curl
│     ├─ 成功 → 继续
│     └─ 失败 → [错误] 记录并退出
│
├─ 内容提取
│  ├─ 完整提取 → 继续
│  └─ 部分失败 → [警告] 使用降级提取
│     ├─ 至少提取标题摘要 → 继续
│     └─ 完全失败 → [错误] 记录并退出
│
├─ 配图生成
│  ├─ 全部成功 → 继续
│  ├─ 部分失败 → [警告] 使用占位符
│  └─ 全部失败 → [警告] 无配图继续
│
├─ 文章生成
│  ├─ 内容长度正常 → 一次性生成
│  └─ 内容超长 → 分块生成并合并
│
├─ PDF 导出
│  ├─ 成功 → 返回完整结果
│  └─ 失败 → [警告] 仅返回 HTML
│
结束
```

---

## Few-Shot 示例

### ✅ Good Case（正确示例）

**用户输入**:
```
/paper-interpreter https://arxiv.org/abs/2312.00752
```

**系统行为**:
1. 立即开始下载，不询问确认
2. 识别为 arXiv 链接，提取 arXiv ID: 2312.00752
3. 下载 PDF 到临时目录
4. 提取内容：标题 "Mamba: Linear-Time Sequence Modeling with Selective State Spaces"
5. 分析类型：架构创新
6. 规划类比：餐厅服务员的记忆问题
7. 生成 5 张配图提示词
8. 调用 Nano Banana API 生成配图（假设 4 张成功，1 张失败）
9. 生成完整文章（约 2500 字）
10. 渲染 HTML
11. 导出 PDF
12. **一次性返回完整结果**，无任何中途询问

**输出结果**:
```
✅ 论文解读完成

📄 论文: Mamba: Linear-Time Sequence Modeling with Selective State Spaces
📁 输出目录: ./paper_outputs/Mamba_Linear_Time_Sequence_Modeling_2026-02-22/
   ├── article.html
   ├── article.pdf
   ├── assets/
   │   └── images/
   │       ├── hero_20260222_001.png
   │       ├── intro_20260222_002.png
   │       ├── method_20260222_003.png
   │       └── conclusion_20260222_004.png
   └── metadata.json

🎨 生成配图: 4 张 (1 张失败跳过)
📊 文章字数: 2580 字
⏱️ 处理耗时: 45.2 秒

文章预览:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mamba
让AI大模型「跑得快还记得住」的新秘诀
一种比Transformer快5倍、还能处理百万级长文本的新架构
[配图]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### ❌ Anti-Patterns（禁止的行为）

**案例 1: 中途询问确认**
```
❌ 错误行为:
已提取论文信息：
标题: Mamba: Linear-Time Sequence Modeling...
作者: Albert Gu, Tri Dao
机构: 卡内基梅隆大学...

⚠️ 是否继续生成配图？(是/否)  ← 绝对禁止！

✅ 正确行为:
直接继续生成配图，不询问
```

**案例 2: 询问输出格式**
```
❌ 错误行为:
文章已生成。您希望输出什么格式？
1. HTML
2. PDF
3. Markdown
4. 全部
请输入选项:  ← 绝对禁止！

✅ 正确行为:
默认输出全部格式，一次性返回所有文件路径
```

**案例 3: 询问缺失信息**
```
❌ 错误行为:
无法提取发表日期，请手动输入日期:  ← 绝对禁止！

✅ 正确行为:
使用默认值 "未知日期" 或从 arXiv ID 推断 (2312.00752 → 2023年12月)
```

**案例 4: 配图失败时停止**
```
❌ 错误行为:
配图生成失败，API 返回错误：Rate limit exceeded
请稍后重试或更换 API Key。

✅ 正确行为:
[警告] 配图生成失败，使用占位符继续...
[继续生成 HTML 和 PDF，无配图但流程完成]
```

---

## 技术栈依赖

**必需**:
- Python 3.8+
- `requests` - 论文下载和 API 调用
- `pypdf2` - PDF 内容提取（降级方案）
- `weasyprint` - HTML 转 PDF

**可选（增强功能）**:
- `unstructured[pdf]` - 更精准的 PDF 内容提取
- ` Pillow` - 图片占位符生成
- API Key（必需用于 AI 配图）:
  - `GEMINI_API_KEY` - 文本生成
  - `NANO_BANANA_API_KEY` - 图像生成

---

## 配置项

**环境变量** (`.env` 文件):
```bash
# 输出配置
export PAPER_OUTPUT_DIR="./paper_outputs"
export PAPER_TEMP_DIR="/tmp/paper_interpreter"

# Gemini API 配置 (文本生成)
export GEMINI_API_KEY="your-api-key"
export GEMINI_MODEL="gemini-flash-lite-latest"
export GEMINI_API_URL="https://yunwu.ai"

# Nano Banana API 配置 (图像生成)
export NANO_BANANA_API_KEY="your-api-key"
export NANO_BANANA_MODEL="gemini-3-pro-image-preview"
export NANO_BANANA_API_URL="https://yunwu.ai"

# 限制配置
export MAX_PAPER_SIZE_MB="50"
export CHUNK_SIZE_TOKENS="4000"
export DEFAULT_TIMEOUT_SECONDS="30"
export MAX_RETRIES="3"

# 配图配置
export ILLUSTRATION_COUNT="5"
export ILLUSTRATION_TIMEOUT="120"
```

---

## 核心特性

### 1. 智能术语注解系统
- **格式**: `*术语（大白话解释）*`
- **HTML 效果**: 绿色带下虚线，鼠标悬停显示深色提示框
- **PDF 效果**: 自动转为括号内灰色小字
- **示例**: *神经网络（像人脑一样工作的计算程序）*

### 2. 大白话写作风格
- 面向完全不懂的小白
- 用吃饭、购物、装修等生活场景类比
- 禁止学术黑话、数学公式、Markdown 格式
- 每段都有"这和我有什么关系"

### 3. AI 配图生成
- 强调"秒懂"和"Aha!时刻"
- 生活化类比图解
- 前后对比可视化
- 暖米色背景，统一风格

### 4. 极致美学排版
- 暖米色背景 (#FDF6E3) + 深灰文字 (#2C3E50) + 青绿强调 (#16A085)
- 优雅章节标题，渐变边框引用框
- 段间距排版，无首行缩进
- 响应式设计，PDF 打印优化

---

## 使用示例

### 示例 1: 解读经典论文

**输入**:
```
/paper-interpreter https://arxiv.org/abs/1512.03385
```

**输出**:
```
✅ 论文解读完成

📄 论文: Deep Residual Learning for Image Recognition
📁 输出目录: ./paper_outputs/Deep_Residual_Learning_2026-02-22/
   ├── article.html       # 精美网页版，支持术语悬停
   ├── article.pdf        # PDF 版，适合打印分享
   ├── assets/
   │   └── images/        # 5 张 AI 生成配图
   └── metadata.json      # 论文元数据

🎨 生成配图: 5 张
📊 文章字数: 3733 字
⏱️ 处理耗时: 195.7 秒

文章亮点:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
深度学习的"不忘初心"：让神经网络深到152层也不迷路

想象一下你正在升级你家的老旧Wi-Fi路由器...

术语注解:
• *神经网络（像人脑一样工作的计算程序）*
• *残差学习（学习"多出来的那一点点变化"）*
• *梯度消失（信息在传递中衰减的现象）*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 示例 2: 解读最新研究

**输入**:
```
/paper-interpreter https://arxiv.org/abs/2312.00752
```

**输出**:
```
✅ 论文解读完成

📄 论文: Mamba: Linear-Time Sequence Modeling with Selective State Spaces

文章亮点:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
告别"注意力分散"：Mamba如何让AI读懂超长文本

想象一下，置身于一个无比宏伟的中央图书馆...

核心创新: 用*选择性状态空间（只记住该记住的，忘掉该忘掉的）*
解决*Transformer（一种认真但慢的服务员）*的长文本处理问题
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 支持的论文来源

| 来源 | 格式示例 | 说明 |
|------|---------|------|
| arXiv | `https://arxiv.org/abs/2312.00752` | 自动识别并下载 PDF |
| arXiv PDF | `https://arxiv.org/pdf/2312.00752` | 直接下载 |
| DOI | `https://doi.org/10.xxxx/xxxxx` | 通过 doi.org 解析 |
| OpenReview | `https://openreview.net/forum?id=xxxxx` | ICLR 等会议论文 |
| Semantic Scholar | `https://www.semanticscholar.org/paper/xxxxx` | 学术搜索引擎 |
| 直接 PDF | `https://example.com/paper.pdf` | 以 .pdf 结尾的链接 |

---

## 版本历史

- **v2.0.0** (2026-02-22): 全面升级
  - 写作风格：从"黄叔风格"升级为"一无所知小白风格"，更通俗易懂
  - 术语系统：新增智能术语注解，悬停提示框，PDF 打印优化
  - 配图优化：更强调"秒懂"和"分享欲"，生活化类比
  - 排版优化：极致美学设计，统一暖色调，优雅章节样式
  - HTML/PDF：术语悬停效果、响应式设计、打印优化

- **v1.0.0** (2026-02-22): 初始版本，支持 arXiv、DOI、PDF 链接，基础科普风格解读
