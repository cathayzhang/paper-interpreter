# 保持 Render 服务唤醒

Render 免费套餐会在 15 分钟无流量后休眠，首次访问需要 30-90 秒冷启动。

## 方案1：使用 UptimeRobot（推荐，免费）

1. 访问 https://uptimerobot.com/ 注册免费账号
2. 点击 "Add New Monitor"
3. 配置：
   - Monitor Type: HTTP(s)
   - Friendly Name: Paper Interpreter API
   - URL: `https://paper-interpreter-api.onrender.com/api/health`
   - Monitoring Interval: 5 minutes（免费套餐最短间隔）
4. 保存

这样每 5 分钟会自动访问一次，保持服务唤醒。

## 方案2：使用 Cron-job.org（免费）

1. 访问 https://cron-job.org/ 注册
2. 创建新任务：
   - URL: `https://paper-interpreter-api.onrender.com/api/health`
   - Interval: Every 5 minutes
3. 启用任务

## 方案3：使用 GitHub Actions（免费）

在你的仓库中添加 `.github/workflows/keep-alive.yml`：

```yaml
name: Keep Render Service Alive

on:
  schedule:
    # 每 10 分钟运行一次
    - cron: '*/10 * * * *'
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping API
        run: |
          curl -f https://paper-interpreter-api.onrender.com/api/health || exit 0
```

## 方案4：升级到付费套餐

如果需要 24/7 不休眠：
- Render Starter Plan: $7/月
- 无冷启动，始终在线
- 更高性能

## 当前优化

已优化 Dockerfile 和配置：
- ✅ 使用轻量级依赖
- ✅ 添加健康检查
- ✅ 优化启动命令
- ✅ 减少镜像大小

预计冷启动时间从 60-90 秒降低到 30-45 秒。
