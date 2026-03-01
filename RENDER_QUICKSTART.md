# Render 部署快速指南

本指南介绍如何将 Paper Interpreter API 部署到 Render，获得一个可公开访问的 API 地址。

## 前置要求

- GitHub 账号
- Render 账号（免费）：https://render.com
- 云雾 AI API Key（用于调用 Gemini 模型）

## 方式一：使用蓝图一键部署（推荐）

### 步骤 1：推送代码到 GitHub

确保你的项目已经推送到 GitHub，并且根目录包含 `render.yaml` 文件。

```bash
cd /Users/chuangyangyang/Documents/GitHub/论文解读
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 步骤 2：在 Render 创建蓝图部署

1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 点击 **New** → **Blueprint**
3. 选择你的 GitHub 仓库（例如：`cathayzhang/paper-interpreter`）
4. Render 会自动检测 `render.yaml` 并显示部署配置
5. 点击 **Apply** 开始部署

### 步骤 3：配置环境变量

部署创建后，进入服务页面：

1. 点击服务名称 `paper-interpreter-api`
2. 进入 **Environment** 标签
3. 添加必需的环境变量：
   - `GEMINI_API_KEY`: 你的云雾 AI API Key（例如：`sk-BK9ckovYrzkgvOiuBtqa3h7U5aw4sVMoPSc6lcIOykBRPvkS`）
   - `NANO_BANANA_API_KEY`: 同上（用于图片生成）
4. 点击 **Save Changes**

服务会自动重新部署。

### 步骤 4：获取 API 地址

部署完成后，你会看到服务 URL，例如：
```
https://paper-interpreter-api-xxxx.onrender.com
```

### 步骤 5：验证部署

在浏览器中访问：
```
https://paper-interpreter-api-xxxx.onrender.com/api/health
```

应该返回：
```json
{"status": "ok", "version": "2.0.0"}
```

---

## 方式二：手动创建 Web Service

如果你不想使用蓝图，可以手动创建服务。

### 步骤 1：创建 Web Service

1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 点击 **New** → **Web Service**
3. 连接你的 GitHub 仓库
4. 配置服务：
   - **Name**: `paper-interpreter-api`
   - **Environment**: `Docker`
   - **Region**: 选择离你最近的区域
   - **Branch**: `main`
   - **Dockerfile Path**: `./paper-interpreter/Dockerfile`
   - **Docker Context**: `./paper-interpreter`

### 步骤 2：配置环境变量

在 **Environment Variables** 部分添加：

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | 你的云雾 AI API Key |
| `NANO_BANANA_API_KEY` | 同上 |
| `GEMINI_API_URL` | `https://yunwu.ai` |
| `NANO_BANANA_API_URL` | `https://yunwu.ai` |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` |
| `NANO_BANANA_MODEL` | `gemini-3-pro-image-preview` |
| `ILLUSTRATION_COUNT` | `5` |

### 步骤 3：配置健康检查

- **Health Check Path**: `/api/health`

### 步骤 4：部署

点击 **Create Web Service**，Render 会自动构建并部署你的应用。

---

## 在 Next.js 生产环境中使用

部署完成后，在你的 Next.js 项目（如 Vercel）中添加环境变量：

```env
PAPER_INTERPRETER_API_URL=https://paper-interpreter-api-xxxx.onrender.com
```

注意：不要在 URL 末尾添加 `/`

然后在代码中调用：

```typescript
const response = await fetch(`${process.env.PAPER_INTERPRETER_API_URL}/api/paper/interpret`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://arxiv.org/abs/2010.11929',
    illustration_count: 3
  })
});

const { task_id } = await response.json();

// 轮询任务状态
const statusResponse = await fetch(
  `${process.env.PAPER_INTERPRETER_API_URL}/api/paper/status/${task_id}`
);
const status = await statusResponse.json();
```

---

## 注意事项

### 免费计划限制

Render 免费计划有以下限制：
- 15 分钟无活动后服务会休眠
- 首次请求可能需要 30-60 秒唤醒
- 每月 750 小时免费运行时间
- 512MB RAM

### 性能优化建议

1. **使用付费计划**：如果需要更好的性能，升级到 Starter 计划（$7/月）
2. **减少配图数量**：将 `illustration_count` 从 5 降到 3，可以显著降低处理时间和成本
3. **添加缓存**：对于相同的论文 URL，可以缓存结果避免重复处理

### 成本估算

基于云雾 AI 的定价：
- 文本生成：¥0.4000 / 1M tokens
- 图片生成：¥0.330 / 1K tokens

每篇论文（30万字，5张图）：
- 文本成本：约 ¥0.02
- 图片成本：约 ¥1.65
- 总成本：约 ¥1.67

---

## 故障排查

### 部署失败

1. 检查 Dockerfile 路径是否正确
2. 确认 `requirements-full.txt` 包含所有依赖
3. 查看 Render 日志获取详细错误信息

### API 调用失败

1. 检查环境变量是否正确配置
2. 验证 API Key 是否有效
3. 检查云雾 AI 账户余额

### 服务响应慢

1. 免费计划服务可能处于休眠状态，首次请求需要唤醒
2. 考虑升级到付费计划
3. 减少配图数量以降低处理时间

---

## 相关链接

- [Render 文档](https://render.com/docs)
- [云雾 AI 文档](https://yunwu.ai)
- [FastAPI 文档](https://fastapi.tiangolo.com)
