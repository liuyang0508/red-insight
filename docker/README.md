# Docker 部署说明

## 快速开始

```bash
# 在项目根目录执行
bash deploy.sh
```

## 手动部署

```bash
# 构建镜像
docker build -f docker/Dockerfile -t red-insight .

# 运行容器
docker run -d \
  --name red-insight \
  -p 8080:8080 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config.py:/app/config.py:ro \
  red-insight
```

## Docker Compose

```bash
cd docker
docker-compose up -d
```

## 日志管理

```bash
# 手动归档日志
bash docker/scripts/archive_logs.sh

# 设置定时归档
bash docker/scripts/setup_cron.sh
```

## 文件说明

| 文件 | 说明 |
|------|------|
| Dockerfile | Docker 镜像构建文件 |
| docker-compose.yml | Docker Compose 配置 |
| entrypoint.sh | 容器启动脚本 |
| logrotate.conf | 日志轮转配置 |
| scripts/archive_logs.sh | 日志归档脚本 |
| scripts/setup_cron.sh | 定时任务设置脚本 |

