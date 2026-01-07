# 🔴 Red Insight - AI 小红书洞察助手

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Version-3.0-FF6B6B?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<p align="center">
  <b>🤖 基于 AI Agent 的小红书内容抓取与智能分析工具</b><br>
  用自然语言表达需求，Agent 自动理解意图、抓取内容并生成可视化洞察报告
</p>

---

## 📸 效果展示

### 🔍 智能搜索 & 统计分析
搜索任意话题，自动抓取小红书内容，生成互动分布、热词分析、数据洞察

<p align="center">
  <img src="docs/screenshots/search-stats.png" alt="搜索统计" width="90%">
</p>

### ⭐ 内容质量评分 & AI 分析
智能评估内容质量，AI 深度分析趋势和用户关注点

<p align="center">
  <img src="docs/screenshots/quality-analysis.png" alt="质量评分" width="90%">
</p>

### 📷 帖子抓取 & 封面展示
抓取真实小红书帖子，完整显示封面、标题、作者、互动数据

<p align="center">
  <img src="docs/screenshots/posts-grid.png" alt="帖子展示" width="90%">
</p>

### 🏙️ 地区分析
按城市筛选内容，分析地区热门话题和特色推荐

<p align="center">
  <img src="docs/screenshots/regional.png" alt="地区分析" width="90%">
</p>

---

## ✨ 功能特性

<table>
<tr>
<td width="50%">

### 🤖 AI Agent 核心
- **自然语言交互** - 用中文描述需求即可
- **智能意图理解** - 自动识别搜索/榜单/攻略/统计
- **实时执行日志** - 可视化展示 Agent 执行过程
- **多轮对话** - 支持上下文连续对话

</td>
<td width="50%">

### 📊 榜单分析
- **热门榜** - 当前最热门内容
- **新晋爆款** - 快速上升的热门内容
- **分类榜单** - 美妆/穿搭/美食/旅行/健身/数码/家居/萌宠/母婴

</td>
</tr>
<tr>
<td width="50%">

### 🏙️ 地区统计
- **17+ 城市支持** - 北上广深杭成等热门城市
- **城市热门话题** - 景点、美食、探店
- **特色美食** - 城市特色美食统计
- **地区对比** - 多城市数据对比

</td>
<td width="50%">

### 📈 统计报表
- **互动分布** - 点赞评论数据可视化
- **热词分析** - 关键词词频统计
- **作者排名** - 活跃创作者统计
- **质量评分** - 内容质量智能评分

</td>
</tr>
<tr>
<td width="50%">

### 📖 智能攻略
- **游玩攻略** - 景点/交通/住宿全攻略
- **购买推荐** - 产品推荐和购买建议
- **避坑指南** - 常见陷阱和注意事项
- **新手入门** - 零基础入门指南

</td>
<td width="50%">

### ⚖️ 产品对比
- **多产品对比** - 同时对比多个产品
- **优缺点分析** - AI 总结优缺点
- **推荐结论** - 给出最终推荐
- **数据支撑** - 基于真实用户评价

</td>
</tr>
</table>

---

## 🚀 快速开始

### 方式一：本地 Python 运行（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/YOUR_USERNAME/red-insight.git
cd red-insight

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key（编辑 config.py）
# OPENAI_API_KEY = "你的API密钥"

# 4. 安装浏览器（首次运行）
playwright install chromium

# 5. 启动服务
python main.py
```

### 方式二：一键部署脚本

```bash
# 本地启动
bash deploy.sh local

# Docker 启动
bash deploy.sh start
```

### 方式三：Docker 部署

```bash
# 构建并启动
bash deploy.sh start

# 查看状态
bash deploy.sh status

# 查看日志
bash deploy.sh logs

# 停止服务
bash deploy.sh stop
```

**启动后访问**: http://localhost:2026

---

## 💬 使用示例

| 功能 | 示例对话 |
|------|----------|
| 🔍 **搜索分析** | "帮我看看护肤品推荐" |
| 📊 **榜单查看** | "看看美妆榜有什么热门的" |
| 🏙️ **地区探索** | "上海有什么好吃的" |
| 📖 **生成攻略** | "帮我生成杭州旅游攻略" |
| ⚠️ **避坑指南** | "面膜避坑指南" |
| ⚖️ **产品对比** | "对比雅诗兰黛和兰蔻的眼霜" |
| 📈 **数据统计** | "分析咖啡探店的数据趋势" |

---

## ⚙️ 配置说明

### AI 模型配置

编辑 `config.py`:

```python
# 阿里云百炼（通义千问）- 推荐
OPENAI_API_KEY = "sk-xxxxx"
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
OPENAI_MODEL = "qwen-turbo"  # 可选: qwen-plus, qwen-max

# 或使用 OpenAI
# OPENAI_API_KEY = "sk-xxxxx"
# OPENAI_BASE_URL = "https://api.openai.com/v1"
# OPENAI_MODEL = "gpt-4o-mini"
```

### 小红书 Cookie 配置

编辑 `scraper.py` 中的 `COOKIES` 变量（从浏览器 F12 获取）:

```python
COOKIES = [
    {"name": "a1", "value": "xxx", "domain": ".xiaohongshu.com", "path": "/"},
    {"name": "web_session", "value": "xxx", "domain": ".xiaohongshu.com", "path": "/"},
    # ... 其他 cookie
]
```

---

## 📐 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      前端层 (HTML/JS/CSS)                        │
│   对话界面 │ 可视化报告 │ 榜单展示 │ 攻略阅读 │ 执行日志         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                      API 网关 (FastAPI)                          │
│   /api/chat │ /api/ranking │ /api/regional │ /api/guide │ ...  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                     AI Agent 核心层                              │
│   意图理解 → 功能调度 → 内容抓取 → AI 分析 → 报告生成            │
└─────────┬─────────┬─────────┬─────────┬─────────┬───────────────┘
          │         │         │         │         │
    ┌─────┴───┐ ┌───┴───┐ ┌───┴───┐ ┌───┴───┐ ┌───┴───┐
    │ 榜单服务 │ │ 地区  │ │ 统计  │ │ 攻略  │ │ 抓取  │
    │rankings │ │regional│ │analytics│ │guides │ │scraper│
    └─────────┘ └───────┘ └───────┘ └───────┘ └───────┘
```

---

## 📁 项目结构

```
red-insight/
├── main.py              # FastAPI 后端入口
├── agent.py             # AI Agent 核心
├── scraper.py           # 小红书抓取模块
├── rankings.py          # 榜单分析模块
├── regional.py          # 地区统计模块
├── analytics.py         # 统计分析模块
├── guides.py            # 智能攻略模块
├── logger.py            # 日志模块
├── config.py            # 配置文件
├── deploy.sh            # 一键部署脚本
├── requirements.txt     # Python 依赖
├── static/
│   └── index.html       # 前端页面
├── docker/              # Docker 相关配置
├── docs/                # 文档和截图
└── logs/                # 日志目录
```

---

## 🔧 API 接口

<details>
<summary><b>点击展开 API 文档</b></summary>

### 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 与 AI Agent 对话 |
| `/api/search` | POST | 直接搜索帖子 |
| `/api/health` | GET | 健康检查 |

### 榜单接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/ranking` | POST | 获取榜单 |
| `/api/ranking/types` | GET | 获取榜单类型 |

### 地区接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/regional` | POST | 地区分析 |
| `/api/regional/cities` | GET | 获取支持的城市 |

### 攻略接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/guide` | POST | 生成攻略 |
| `/api/guide/types` | GET | 获取攻略类型 |
| `/api/compare` | POST | 对比分析 |
| `/api/statistics` | POST | 统计分析 |

### 示例请求

```bash
# 对话请求
curl -X POST http://localhost:2026/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我看看美妆榜热门"}'

# 获取榜单
curl -X POST http://localhost:2026/api/ranking \
  -H "Content-Type: application/json" \
  -d '{"ranking_type": "beauty", "max_items": 10}'

# 地区分析
curl -X POST http://localhost:2026/api/regional \
  -H "Content-Type: application/json" \
  -d '{"city": "上海", "topic": "美食"}'
```

</details>

---

## 🏙️ 支持的城市

北京 · 上海 · 广州 · 深圳 · 杭州 · 成都 · 重庆 · 南京 · 武汉 · 西安 · 苏州 · 长沙 · 厦门 · 青岛 · 三亚 · 丽江 · 大理

---

## 📊 支持的榜单

| 榜单 | 说明 | 榜单 | 说明 |
|------|------|------|------|
| 🔥 热门榜 | 最热门内容 | 💄 美妆榜 | 美妆护肤 |
| 🚀 新晋爆款 | 快速上升 | 👗 穿搭榜 | 时尚穿搭 |
| 🍜 美食榜 | 美食推荐 | ✈️ 旅行榜 | 旅行攻略 |
| 💪 健身榜 | 健身运动 | 📱 数码榜 | 数码评测 |
| 🏠 家居榜 | 家居生活 | 🐱 萌宠榜 | 宠物日常 |
| 👶 母婴榜 | 母婴育儿 | | |

---

## 🛠️ 部署命令

| 命令 | 说明 |
|------|------|
| `python main.py` | 直接运行 |
| `bash deploy.sh local` | 本地启动 |
| `bash deploy.sh start` | Docker 启动 |
| `bash deploy.sh stop` | 停止服务 |
| `bash deploy.sh restart` | 重启服务 |
| `bash deploy.sh logs` | 查看日志 |
| `bash deploy.sh status` | 查看状态 |
| `bash deploy.sh clean` | 清理容器 |

---

## ⚠️ 注意事项

1. **Cookie 有效期** - 小红书 Cookie 会过期，需定期更新
2. **抓取频率** - 避免频繁抓取，建议间隔 3-5 秒
3. **API 限制** - 注意 AI 模型 API 的调用限制
4. **仅供学习** - 本项目仅供学习研究使用

---

## 🔄 更新日志

### v3.0.0 🎉
- ✨ 新增榜单分析功能（11种分类榜单）
- ✨ 新增地区统计功能（17+城市支持）
- ✨ 新增统计报表功能（互动分布、热词分析等）
- ✨ 新增智能攻略功能（7种攻略类型）
- ✨ 新增产品对比功能
- 🎨 全新前端界面设计
- 🚀 优化 Agent 意图理解能力

### v2.0.0
- 初版 AI Agent 功能
- 基础搜索和分析

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 License

[MIT License](LICENSE) © 2024-2026

---

<p align="center">
  <b>如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！</b>
</p>
