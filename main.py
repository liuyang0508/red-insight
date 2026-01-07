"""
Red Insight - 小红书智能洞察 Agent
FastAPI 后端服务
支持：榜单分析、地区统计、智能攻略、量化报表等
"""
# 加载环境变量（必须在其他导入之前）
from dotenv import load_dotenv
load_dotenv()

import os
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

# 日志模块
from logger import logger, request_logger, agent_logger, info, error

# 尝试导入 Agent 和新功能模块
try:
    from agent import RedInsightAgent, AgentResponse
    AGENT_AVAILABLE = True
except ImportError as e:
    error(f"Agent 模块加载失败: {e}")
    AGENT_AVAILABLE = False

try:
    from rankings import RankingService, RankingType, ranking_to_dict, RANKING_CONFIG
    from regional import RegionalService, City, city_analysis_to_dict, CITY_CONFIG
    from analytics import AnalyticsService, report_to_dict
    from guides import GuideGenerator, GuideType, guide_to_dict
    FEATURES_AVAILABLE = True
except ImportError as e:
    error(f"功能模块加载失败: {e}")
    FEATURES_AVAILABLE = False

from scraper import RedBookScraper, posts_to_dict


# Agent 实例存储（简单的会话管理）
agents: Dict[str, "RedInsightAgent"] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    info("🚀 Red Insight Agent 服务启动中...")
    info(f"📊 Agent: {'可用' if AGENT_AVAILABLE else '不可用'}")
    info(f"🔧 扩展功能: {'可用' if FEATURES_AVAILABLE else '不可用'}")
    yield
    info("👋 服务关闭")
    agents.clear()


# 创建 FastAPI 应用
app = FastAPI(
    title="Red Insight - 小红书智能洞察 Agent",
    description="AI Agent 驱动的小红书内容抓取与分析工具，支持榜单分析、地区统计、智能攻略等",
    version="3.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)


# ========== 请求/响应模型 ==========

class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    """对话响应"""
    success: bool
    message: str
    action: Optional[str] = None
    keywords: Optional[List[str]] = None
    posts: Optional[List[Dict[str, Any]]] = None
    analysis: Optional[str] = None
    suggestions: Optional[List[str]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    # 新增功能数据
    ranking: Optional[Dict[str, Any]] = None
    regional: Optional[Dict[str, Any]] = None
    statistics: Optional[Dict[str, Any]] = None
    guide: Optional[Dict[str, Any]] = None
    comparison: Optional[Dict[str, Any]] = None
    timestamp: str


class SearchRequest(BaseModel):
    """直接搜索请求"""
    keyword: str
    max_posts: int = 10


class SearchResponse(BaseModel):
    """搜索响应"""
    success: bool
    keyword: str
    posts: List[Dict[str, Any]]
    total: int
    scraped_at: str
    message: Optional[str] = None


class RankingRequest(BaseModel):
    """榜单请求"""
    ranking_type: str = "hot"  # hot, beauty, fashion, food, travel, fitness, digital, home, pet, mother
    max_items: int = 10


class RegionalRequest(BaseModel):
    """地区分析请求"""
    city: str  # 城市名称
    topic: Optional[str] = None
    max_posts: int = 10


class GuideRequest(BaseModel):
    """攻略生成请求"""
    topic: str
    guide_type: str = "travel"  # travel, shopping, food, pitfalls, comparison, budget, beginner


class CompareRequest(BaseModel):
    """对比请求"""
    items: List[str]  # 要对比的项目列表


# ========== API 路由 ==========

@app.get("/", response_class=HTMLResponse)
async def home():
    """首页 - 返回前端页面"""
    html_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>请创建 static/index.html</h1>")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    与 AI Agent 对话
    
    Agent 会理解用户意图，自动执行相应操作：
    - 内容搜索
    - 榜单分析
    - 地区统计
    - 智能攻略
    - 统计报表
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    if not AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="AI Agent 未就绪，请检查 OPENAI_API_KEY 配置"
        )
    
    try:
        import config
        api_key = config.OPENAI_API_KEY
    except:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise HTTPException(
            status_code=400, 
            detail="请在 config.py 中配置 OPENAI_API_KEY"
        )
    
    try:
        session_id = request.session_id
        if session_id not in agents:
            print(f"🤖 创建新的 Agent 实例，session: {session_id}")
            agents[session_id] = RedInsightAgent()
        
        agent = agents[session_id]
        
        print(f"💬 用户消息: {request.message.strip()[:50]}...")
        response = await agent.chat(request.message.strip())
        print(f"✅ Agent 响应成功")
        
        return ChatResponse(
            success=True,
            message=response.message,
            action=response.action,
            keywords=response.keywords,
            posts=response.posts,
            analysis=response.analysis,
            suggestions=response.suggestions,
            steps=response.steps,
            ranking=response.ranking,
            regional=response.regional,
            statistics=response.statistics,
            guide=response.guide,
            comparison=response.comparison,
            timestamp=datetime.now().isoformat()
        )
        
    except ValueError as e:
        print(f"❌ ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Chat error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.post("/api/search", response_model=SearchResponse)
async def search_posts(request: SearchRequest):
    """直接搜索小红书帖子（不经过 Agent）"""
    if not request.keyword or not request.keyword.strip():
        raise HTTPException(status_code=400, detail="关键词不能为空")
    
    keyword = request.keyword.strip()
    max_posts = min(max(1, request.max_posts), 20)
    
    try:
        scraper = RedBookScraper()
        posts = await scraper.search_posts(keyword, max_posts)
        posts_dict = posts_to_dict(posts)
        
        return SearchResponse(
            success=True,
            keyword=keyword,
            posts=posts_dict,
            total=len(posts_dict),
            scraped_at=datetime.now().isoformat(),
            message=f"成功获取 {len(posts_dict)} 条关于「{keyword}」的帖子"
        )
    
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"抓取失败: {str(e)}")


@app.post("/api/ranking")
async def get_ranking(request: RankingRequest):
    """获取榜单"""
    if not FEATURES_AVAILABLE:
        raise HTTPException(status_code=503, detail="榜单功能未就绪")
    
    try:
        # 解析榜单类型
        type_mapping = {
            "hot": RankingType.HOT,
            "rising": RankingType.RISING,
            "beauty": RankingType.BEAUTY,
            "fashion": RankingType.FASHION,
            "food": RankingType.FOOD,
            "travel": RankingType.TRAVEL,
            "fitness": RankingType.FITNESS,
            "digital": RankingType.DIGITAL,
            "home": RankingType.HOME,
            "pet": RankingType.PET,
            "mother": RankingType.MOTHER,
        }
        
        ranking_type = type_mapping.get(request.ranking_type.lower(), RankingType.HOT)
        max_items = min(max(1, request.max_items), 20)
        
        service = RankingService()
        ranking = await service.get_ranking(ranking_type, max_items)
        
        return {
            "success": True,
            "ranking": ranking_to_dict(ranking),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Ranking error: {e}")
        raise HTTPException(status_code=500, detail=f"获取榜单失败: {str(e)}")


@app.get("/api/ranking/types")
async def get_ranking_types():
    """获取支持的榜单类型"""
    if not FEATURES_AVAILABLE:
        return {"types": []}
    
    types = []
    for rt, config in RANKING_CONFIG.items():
        types.append({
            "type": rt.value,
            "title": config["title"],
            "description": config["description"]
        })
    
    return {"types": types}


@app.post("/api/regional")
async def analyze_region(request: RegionalRequest):
    """地区分析"""
    if not FEATURES_AVAILABLE:
        raise HTTPException(status_code=503, detail="地区分析功能未就绪")
    
    try:
        # 解析城市
        city_mapping = {
            "北京": City.BEIJING, "上海": City.SHANGHAI, "广州": City.GUANGZHOU,
            "深圳": City.SHENZHEN, "杭州": City.HANGZHOU, "成都": City.CHENGDU,
            "重庆": City.CHONGQING, "南京": City.NANJING, "武汉": City.WUHAN,
            "西安": City.XIAN, "苏州": City.SUZHOU, "长沙": City.CHANGSHA,
            "厦门": City.XIAMEN, "青岛": City.QINGDAO, "三亚": City.SANYA,
            "丽江": City.LIJIANG, "大理": City.DALI
        }
        
        city = city_mapping.get(request.city)
        if not city:
            raise HTTPException(status_code=400, detail=f"不支持的城市: {request.city}")
        
        max_posts = min(max(1, request.max_posts), 20)
        
        service = RegionalService()
        analysis = await service.analyze_city(city, request.topic, max_posts)
        
        return {
            "success": True,
            "analysis": city_analysis_to_dict(analysis),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Regional error: {e}")
        raise HTTPException(status_code=500, detail=f"地区分析失败: {str(e)}")


@app.get("/api/regional/cities")
async def get_supported_cities():
    """获取支持的城市列表"""
    if not FEATURES_AVAILABLE:
        return {"cities": []}
    
    cities = []
    for city, config in CITY_CONFIG.items():
        cities.append({
            "name": config["name"],
            "emoji": config["emoji"],
            "hot_topics": config.get("hot_topics", [])[:5],
            "specialties": config.get("specialties", [])[:5]
        })
    
    return {"cities": cities}


@app.post("/api/statistics")
async def get_statistics(request: SearchRequest):
    """获取统计分析"""
    if not FEATURES_AVAILABLE:
        raise HTTPException(status_code=503, detail="统计分析功能未就绪")
    
    if not request.keyword or not request.keyword.strip():
        raise HTTPException(status_code=400, detail="关键词不能为空")
    
    try:
        keyword = request.keyword.strip()
        max_posts = min(max(1, request.max_posts), 20)
        
        # 抓取帖子
        scraper = RedBookScraper()
        posts = await scraper.search_posts(keyword, max_posts)
        posts_dict = posts_to_dict(posts)
        
        # 生成统计报告
        service = AnalyticsService()
        report = service.generate_report(posts_dict, keyword)
        
        return {
            "success": True,
            "report": report_to_dict(report),
            "posts": posts_dict,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=f"统计分析失败: {str(e)}")


@app.post("/api/guide")
async def generate_guide(request: GuideRequest):
    """生成攻略"""
    if not FEATURES_AVAILABLE:
        raise HTTPException(status_code=503, detail="攻略生成功能未就绪")
    
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="主题不能为空")
    
    try:
        # 解析攻略类型
        type_mapping = {
            "travel": GuideType.TRAVEL,
            "shopping": GuideType.SHOPPING,
            "food": GuideType.FOOD,
            "pitfalls": GuideType.AVOID_PITFALLS,
            "comparison": GuideType.COMPARISON,
            "budget": GuideType.BUDGET,
            "beginner": GuideType.BEGINNER,
        }
        
        guide_type = type_mapping.get(request.guide_type.lower(), GuideType.TRAVEL)
        topic = request.topic.strip()
        
        # 抓取相关内容
        scraper = RedBookScraper()
        posts = await scraper.search_posts(topic, max_posts=10)
        posts_dict = posts_to_dict(posts)
        
        # 生成攻略
        generator = GuideGenerator()
        guide = await generator.generate_guide(posts_dict, topic, guide_type)
        
        return {
            "success": True,
            "guide": guide_to_dict(guide),
            "source_posts": posts_dict[:5],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Guide error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"攻略生成失败: {str(e)}")


@app.get("/api/guide/types")
async def get_guide_types():
    """获取支持的攻略类型"""
    return {
        "types": [
            {"type": "travel", "title": "🗺️ 游玩攻略", "description": "景点、交通、住宿全攻略"},
            {"type": "shopping", "title": "🛍️ 购买推荐", "description": "产品推荐和购买建议"},
            {"type": "food", "title": "🍜 美食攻略", "description": "美食推荐和探店指南"},
            {"type": "pitfalls", "title": "⚠️ 避坑指南", "description": "常见陷阱和注意事项"},
            {"type": "comparison", "title": "⚖️ 产品对比", "description": "多产品对比分析"},
            {"type": "budget", "title": "💰 省钱攻略", "description": "平价替代和优惠渠道"},
            {"type": "beginner", "title": "📚 新手入门", "description": "零基础入门指南"},
        ]
    }


@app.post("/api/compare")
async def compare_items(request: CompareRequest):
    """对比分析"""
    if not FEATURES_AVAILABLE:
        raise HTTPException(status_code=503, detail="对比功能未就绪")
    
    if not request.items or len(request.items) < 2:
        raise HTTPException(status_code=400, detail="至少需要两个对比项目")
    
    try:
        items = [item.strip() for item in request.items[:5] if item.strip()]
        
        # 收集各项目的帖子
        scraper = RedBookScraper()
        all_posts = []
        
        for item in items:
            posts = await scraper.search_posts(item, max_posts=5)
            all_posts.extend(posts_to_dict(posts))
        
        # 生成对比
        generator = GuideGenerator()
        comparison = await generator.generate_comparison(all_posts, items)
        
        return {
            "success": True,
            "comparison": comparison,
            "source_posts_count": len(all_posts),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Compare error: {e}")
        raise HTTPException(status_code=500, detail=f"对比分析失败: {str(e)}")


@app.post("/api/clear-session")
async def clear_session(session_id: str = "default"):
    """清除会话历史"""
    if session_id in agents:
        agents[session_id].clear_history()
        del agents[session_id]
    return {"success": True, "message": "会话已清除"}


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "agent_available": AGENT_AVAILABLE,
        "features_available": FEATURES_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/config")
async def get_config():
    """获取配置信息"""
    return {
        "agent_enabled": AGENT_AVAILABLE,
        "features_enabled": FEATURES_AVAILABLE,
        "model": os.getenv("OPENAI_MODEL", "qwen-turbo"),
        "version": "3.0.0",
        "features": [
            "榜单分析",
            "地区统计",
            "智能攻略",
            "统计报表",
            "产品对比"
        ] if FEATURES_AVAILABLE else []
    }


@app.get("/api/features")
async def get_features():
    """获取功能列表"""
    return {
        "features": [
            {
                "id": "ranking",
                "name": "榜单分析",
                "icon": "📊",
                "description": "热门榜、美妆榜、穿搭榜等分类榜单",
                "available": FEATURES_AVAILABLE
            },
            {
                "id": "regional",
                "name": "地区统计",
                "icon": "🏙️",
                "description": "城市热门内容和地区对比分析",
                "available": FEATURES_AVAILABLE
            },
            {
                "id": "statistics",
                "name": "统计报表",
                "icon": "📈",
                "description": "量化分析、热词统计、互动分布",
                "available": FEATURES_AVAILABLE
            },
            {
                "id": "guide",
                "name": "智能攻略",
                "icon": "📖",
                "description": "游玩攻略、购买推荐、避坑指南",
                "available": FEATURES_AVAILABLE
            },
            {
                "id": "compare",
                "name": "产品对比",
                "icon": "⚖️",
                "description": "多产品/多选项对比分析",
                "available": FEATURES_AVAILABLE
            },
        ]
    }


# 挂载静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=2026)
