#!/bin/bash
# 日志归档脚本

set -e

LOG_DIR="${LOG_DIR:-/app/logs}"
ARCHIVE_DIR="${LOG_DIR}/archive"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

echo "📦 开始日志归档..."
echo "日志目录: ${LOG_DIR}"
echo "保留天数: ${RETENTION_DAYS}"

mkdir -p "${ARCHIVE_DIR}"

# 归档旧日志
DATE=$(date +%Y%m%d)
cd "${LOG_DIR}"

FILES=$(find . -maxdepth 1 -name "*.log.*" -mtime +0 -type f 2>/dev/null || true)
if [ -n "$FILES" ]; then
    echo "$FILES" | xargs tar -czf "${ARCHIVE_DIR}/logs_${DATE}.tar.gz" 2>/dev/null || true
    echo "$FILES" | xargs rm -f 2>/dev/null || true
    echo "✅ 已归档到: logs_${DATE}.tar.gz"
fi

# 清理过期归档
DELETED=$(find "${ARCHIVE_DIR}" -name "logs_*.tar.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
echo "🗑️  清理了 ${DELETED} 个过期归档"

echo "📊 磁盘使用:"
du -sh "${LOG_DIR}" "${ARCHIVE_DIR}" 2>/dev/null || true

echo "✅ 日志归档完成"

