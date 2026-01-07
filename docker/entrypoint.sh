#!/bin/bash
set -e

echo "🚀 Starting Red Insight..."

# 创建日志目录
mkdir -p /app/logs

# 启动应用
exec python main.py

