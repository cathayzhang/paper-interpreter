# 部署指南

本文档提供三种部署方案，根据你的需求选择：

---

## 方案对比

| 方案 | 难度 | 成本 | 适合场景 |
|-----|------|-----|---------|
| **A. Streamlit Cloud** | ⭐ 最简单 | 免费 | 个人使用，快速上线 |
| **B. Vercel + Railway** | ⭐⭐ 中等 | 免费-低 | 集成到现有网站 |
| **C. VPS/云服务器** | ⭐⭐⭐ 较复杂 | 中等 | 生产环境，高并发 |

---

## 方案 A：Streamlit Cloud（推荐，30分钟上线）

### 步骤

1. **推送代码到 GitHub**（确保 `.env` 已在 `.gitignore` 中）

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/paper-to-popsci.git
git push -u origin main
```

2. **注册 Streamlit Cloud**
   - 访问 https://streamlit.io/cloud
   - 用 GitHub 账号登录
   - 点击 "New App"
   - 选择你的仓库

3. **配置环境变量**

   在 Streamlit Cloud 控制台：
   ```
   Settings → Secrets → Add Secret

   GEMINI_API_KEY = your-api-key
   NANO_BANANA_API_KEY = your-api-key
   NANO_BANANA_API_URL = https://yunwu.ai
   GEMINI_API_URL = https://yunwu.ai
   ```

4. **设置启动文件**

   Main file path: `streamlit_app.py`

5. **部署**

   点击 "Deploy"，等待 2-3 分钟即可访问

### 访问你的应用

```
https://your-app-name.streamlit.app
```

---

## 方案 B：集成到 getainote.com

### 后端部署（Railway/Render）

1. **注册 Railway**（https://railway.app）

2. **从 GitHub 部署**
   - New Project → Deploy from GitHub repo
   - 选择你的仓库

3. **配置环境变量**
   ```
   Settings → Variables

   GEMINI_API_KEY=xxx
   NANO_BANANA_API_KEY=xxx
   ...
   ```

4. **生成域名**

   Railway 会自动分配域名：
   ```
   https://paper-interpreter-production.up.railway.app
   ```

5. **更新前端代码**

   在 `frontend-example.js` 中：
   ```javascript
   const interpreter = new PaperInterpreter('https://your-railway-domain.up.railway.app');
   ```

6. **添加到 getainote.com**

   将以下代码添加到你的网站页面：
   ```html
   <script src="frontend-example.js"></script>
   <div id="paper-interpreter-widget">
     <input type="url" id="paper-url" placeholder="输入论文链接" />
     <button onclick="startInterpret()">开始解读</button>
     <!-- 进度和结果显示区域 -->
   </div>
   ```

---

## 方案 C：VPS/云服务器部署

### 使用 Docker（推荐）

1. **创建 Dockerfile**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libpango1.0-0 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "web_api:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

2. **构建并运行**

```bash
# 构建镜像
docker build -t paper-interpreter .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -e GEMINI_API_KEY=xxx \
  -e NANO_BANANA_API_KEY=xxx \
  --name paper-interpreter \
  paper-interpreter
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name api.getainote.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 文件存储配置（重要）

目前代码使用临时目录存储文件，生产环境需要配置持久化存储：

### 选项 1：AWS S3

```python
import boto3

s3 = boto3.client('s3')

# 上传文件
s3.upload_file('article.pdf', 'your-bucket', f'{task_id}/article.pdf')

# 生成下载链接
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'your-bucket', 'Key': f'{task_id}/article.pdf'},
    ExpiresIn=3600
)
```

### 选项 2：阿里云 OSS

```python
import oss2

auth = oss2.Auth('access-key-id', 'access-key-secret')
bucket = oss2.Bucket(auth, 'oss-cn-hangzhou.aliyuncs.com', 'your-bucket')

bucket.put_object_from_file(f'{task_id}/article.pdf', 'article.pdf')
```

---

## 安全建议

### 1. API Key 保护

- ✅ 使用环境变量，绝不提交到代码仓库
- ✅ 服务器端存储，前端不直接接触
- ✅ 定期轮换 API Key
- ✅ 监控 API 使用量，设置告警

### 2. 访问控制

```python
# 在 web_api.py 中添加 API Key 验证
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != os.getenv("API_SECRET"):
        raise HTTPException(status_code=403, detail="Invalid token")
```

### 3. 速率限制

```python
from slowapi import Limiter

limiter = Limiter(key_func=lambda: request.client.host)

@app.post("/api/paper/interpret")
@limiter.limit("5/minute")  # 每分钟最多5次请求
async def interpret_paper(...):
    ...
```

---

## 监控与日志

### 使用 Sentry 监控错误

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

### 日志收集

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

---

## 域名与 HTTPS

### 配置自定义域名

1. **Cloudflare**（推荐，免费 SSL）
   - 添加 DNS 记录指向你的服务器
   - 开启 Proxy 模式（橙色云朵）
   - 自动获得 HTTPS

2. **Let's Encrypt 证书**

```bash
sudo certbot --nginx -d api.getainote.com
```

---

## 成本估算

| 资源 | 方案 A (Streamlit) | 方案 B (Railway) | 方案 C (VPS) |
|-----|-------------------|-----------------|-------------|
| 服务器 | 免费 | $5/月 | $5-10/月 |
| 域名 | - | $10/年 | $10/年 |
| API 调用 | 按量 | 按量 | 按量 |
| **总计** | **免费** | **~$5/月** | **~$10/月** |

---

## 故障排除

### 问题：配图生成失败

**原因**：API 限流或超时

**解决**：
```python
# 增加重试逻辑
for attempt in range(3):
    try:
        image = generate_image(prompt)
        break
    except RateLimitError:
        time.sleep(2 ** attempt)
```

### 问题：PDF 导出失败

**原因**：缺少系统字体或依赖

**解决**：
```bash
# Ubuntu/Debian
sudo apt-get install -y libpango1.0-0 libgdk-pixbuf2.0-0

# 安装中文字体
sudo apt-get install -y fonts-wqy-microhei
```

### 问题：内存不足

**原因**：大 PDF 文件处理

**解决**：
```python
# 限制文件大小
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

if file_size > MAX_FILE_SIZE:
    raise HTTPException(413, "File too large")
```

---

## 推荐配置

### 开发环境
- Streamlit Cloud（快速验证）

### 生产环境
- Railway/Render（后端 API）
- Vercel（前端）
- AWS S3（文件存储）
- Cloudflare（CDN + SSL）

---

如有部署问题，请提交 Issue 获取帮助。
