"""
Red Insight 日志模块
支持控制台输出、文件记录、日志归档
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path


# 日志目录
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器（控制台用）"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = "red_insight",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    archive_daily: bool = True
) -> logging.Logger:
    """
    配置日志记录器
    
    Args:
        name: 日志器名称
        level: 日志级别
        log_to_file: 是否写入文件
        log_to_console: 是否输出到控制台
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的备份文件数量
        archive_daily: 是否按天归档
    
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 日志格式
    file_format = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_format = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 控制台输出
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
    
    # 文件输出
    if log_to_file:
        # 按大小滚动的日志文件
        app_log_file = LOG_DIR / "app.log"
        file_handler = RotatingFileHandler(
            app_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        # 按天归档的日志文件
        if archive_daily:
            daily_log_file = LOG_DIR / "daily.log"
            daily_handler = TimedRotatingFileHandler(
                daily_log_file,
                when='midnight',
                interval=1,
                backupCount=30,  # 保留30天
                encoding='utf-8'
            )
            daily_handler.suffix = "%Y-%m-%d"
            daily_handler.setLevel(level)
            daily_handler.setFormatter(file_format)
            logger.addHandler(daily_handler)
        
        # 错误日志单独记录
        error_log_file = LOG_DIR / "error.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str = "red_insight") -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name)


class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self):
        self.logger = get_logger("red_insight.request")
        self.request_log_file = LOG_DIR / "requests.log"
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_ip: str = "",
        user_agent: str = "",
        request_body: str = "",
        response_summary: str = ""
    ):
        """记录 API 请求"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "user_agent": user_agent[:100] if user_agent else "",
        }
        
        self.logger.info(
            f"{method} {path} - {status_code} - {duration_ms:.2f}ms"
        )
        
        # 写入请求日志文件
        with open(self.request_log_file, 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


class AgentLogger:
    """Agent 执行日志记录器"""
    
    def __init__(self):
        self.logger = get_logger("red_insight.agent")
        self.agent_log_file = LOG_DIR / "agent.log"
    
    def log_execution(
        self,
        session_id: str,
        user_input: str,
        action: str,
        keywords: list,
        posts_count: int,
        has_analysis: bool,
        duration_ms: float,
        steps: list,
        error: str = None
    ):
        """记录 Agent 执行"""
        import json
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "user_input": user_input[:200],
            "action": action,
            "keywords": keywords,
            "posts_count": posts_count,
            "has_analysis": has_analysis,
            "duration_ms": round(duration_ms, 2),
            "steps_count": len(steps),
            "error": error
        }
        
        if error:
            self.logger.error(f"Agent 执行失败: {error}")
        else:
            self.logger.info(
                f"Agent 执行完成: action={action}, keywords={keywords}, "
                f"posts={posts_count}, duration={duration_ms:.2f}ms"
            )
        
        # 写入 Agent 日志文件
        with open(self.agent_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


# 初始化主日志器
logger = setup_logger()
request_logger = RequestLogger()
agent_logger = AgentLogger()


# 便捷函数
def info(msg: str): logger.info(msg)
def debug(msg: str): logger.debug(msg)
def warning(msg: str): logger.warning(msg)
def error(msg: str): logger.error(msg)
def critical(msg: str): logger.critical(msg)

