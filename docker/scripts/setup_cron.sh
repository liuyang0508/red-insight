#!/bin/bash
# 设置定时任务

set -e

echo "⏰ 设置日志归档定时任务..."

# 添加到 crontab (每天凌晨2点执行)
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/archive_logs.sh"

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "archive_logs.sh"; then
    echo "定时任务已存在"
else
    (crontab -l 2>/dev/null; echo "0 2 * * * ${SCRIPT_PATH} >> /app/logs/cron.log 2>&1") | crontab -
    echo "✅ 已添加定时任务: 每天 02:00 执行日志归档"
fi

crontab -l

