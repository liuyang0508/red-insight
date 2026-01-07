'''
Author: liuyang liuyang05083015@163.com
Date: 2026-01-07 21:31:56
LastEditors: liuyang liuyang05083015@163.com
LastEditTime: 2026-01-07 22:39:18
FilePath: /red-insight/config.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
"""
Red Insight 配置文件
"""

# ========== AI 模型配置 ==========

# 阿里云百炼（通义千问）API 配置
OPENAI_API_KEY = "sk-b859edf6ea854f8a963acb255c3225e0"
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 可用模型: qwen-turbo (快速), qwen-plus (增强), qwen-max (最强)
OPENAI_MODEL = "qwen-max"


# ========== 服务配置 ==========

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 2026
MAX_POSTS = 5
