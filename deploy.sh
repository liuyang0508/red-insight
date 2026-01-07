#!/bin/bash
#
# Red Insight 一键部署脚本
# 用法: bash deploy.sh [命令]
#
# 命令:
#   start    - 启动服务（默认）
#   stop     - 停止服务
#   restart  - 重启服务
#   build    - 构建 Docker 镜像
#   logs     - 查看日志
#   status   - 查看状态
#   clean    - 清理容器和镜像
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
PROJECT_NAME="red-insight"
IMAGE_NAME="red-insight:latest"
CONTAINER_NAME="red-insight"
PORT="${PORT:-2026}"

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 打印 Banner
banner() {
    echo -e "${RED}"
    echo "  ____          _   ___           _       _     _   "
    echo " |  _ \ ___  __| | |_ _|_ __  ___(_) __ _| |__ | |_ "
    echo " | |_) / _ \/ _\` |  | || '_ \/ __| |/ _\` | '_ \| __|"
    echo " |  _ <  __/ (_| |  | || | | \__ \ | (_| | | | | |_ "
    echo " |_| \_\___|\__,_| |___|_| |_|___/_|\__, |_| |_|\__|"
    echo "                                   |___/           "
    echo -e "${NC}"
    echo -e "${BLUE}AI 小红书洞察助手${NC}"
    echo ""
}

# 检查 Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装${NC}"
        echo "请先安装 Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
}

# 检查 Python
check_python() {
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python 未安装${NC}"
        exit 1
    fi
}

# 本地启动（不使用 Docker）
start_local() {
    echo -e "${YELLOW}🚀 本地启动模式...${NC}"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}创建虚拟环境...${NC}"
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    echo -e "${YELLOW}安装依赖...${NC}"
    pip install -r requirements.txt -q
    
    # 检查 Playwright
    if ! python -c "import playwright" 2>/dev/null; then
        echo -e "${YELLOW}安装 Playwright 浏览器...${NC}"
        playwright install chromium
    fi
    
    # 启动服务
    echo -e "${GREEN}✅ 启动服务...${NC}"
    python main.py
}

# Docker 构建
build() {
    echo -e "${YELLOW}🔨 构建 Docker 镜像...${NC}"
    docker build -f docker/Dockerfile -t ${IMAGE_NAME} .
    echo -e "${GREEN}✅ 构建完成: ${IMAGE_NAME}${NC}"
}

# Docker 启动
start_docker() {
    echo -e "${YELLOW}🐳 Docker 启动模式...${NC}"
    
    # 先停止并移除之前的容器
    if docker ps -aq -f name=${CONTAINER_NAME} | grep -q .; then
        echo -e "${YELLOW}⏹️  停止之前的服务...${NC}"
        docker stop ${CONTAINER_NAME} 2>/dev/null || true
        docker rm ${CONTAINER_NAME} 2>/dev/null || true
    fi
    
    # 检查镜像是否存在
    if ! docker images ${IMAGE_NAME} --format "{{.Repository}}" | grep -q "${PROJECT_NAME}"; then
        echo -e "${YELLOW}镜像不存在，开始构建...${NC}"
        build
    fi
    
    # 创建日志目录
    mkdir -p logs
    
    # 启动容器
    echo -e "${YELLOW}🚀 启动容器...${NC}"
    docker run -d \
        --name ${CONTAINER_NAME} \
        -p ${PORT}:8080 \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/config.py:/app/config.py:ro" \
        --restart unless-stopped \
        ${IMAGE_NAME}
    
    echo -e "${GREEN}✅ 服务已启动${NC}"
    echo -e "   访问地址: ${BLUE}http://localhost:${PORT}${NC}"
}

# 停止服务
stop() {
    echo -e "${YELLOW}⏹️  停止服务...${NC}"
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# 重启服务
restart() {
    stop
    start_docker
}

# 查看日志
logs() {
    docker logs -f ${CONTAINER_NAME}
}

# 查看状态
status() {
    echo -e "${BLUE}📊 服务状态${NC}"
    echo ""
    
    if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then
        echo -e "${GREEN}● 运行中${NC}"
        docker ps -f name=${CONTAINER_NAME} --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        echo -e "${RED}○ 未运行${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}📁 日志目录${NC}"
    ls -lh logs/ 2>/dev/null || echo "  (无日志)"
}

# 清理
clean() {
    echo -e "${YELLOW}🧹 清理...${NC}"
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
    docker rmi ${IMAGE_NAME} 2>/dev/null || true
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 帮助信息
help() {
    echo "用法: bash deploy.sh [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动服务 (Docker 模式)"
    echo "  local     启动服务 (本地 Python 模式)"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  build     构建 Docker 镜像"
    echo "  logs      查看日志"
    echo "  status    查看状态"
    echo "  clean     清理容器和镜像"
    echo "  help      显示帮助"
    echo ""
    echo "示例:"
    echo "  bash deploy.sh start    # Docker 启动"
    echo "  bash deploy.sh local    # 本地启动"
    echo "  python main.py          # 直接运行"
}

# 主入口
main() {
    banner
    
    case "${1:-start}" in
        start)
            check_docker
            start_docker
            ;;
        local)
            check_python
            start_local
            ;;
        stop)
            check_docker
            stop
            ;;
        restart)
            check_docker
            restart
            ;;
        build)
            check_docker
            build
            ;;
        logs)
            check_docker
            logs
            ;;
        status)
            check_docker
            status
            ;;
        clean)
            check_docker
            clean
            ;;
        help|--help|-h)
            help
            ;;
        *)
            echo -e "${RED}未知命令: $1${NC}"
            help
            exit 1
            ;;
    esac
}

main "$@"

