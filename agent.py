"""
Red Insight AI Agent
智能理解用户意图，自动抓取小红书内容并生成洞察报告
支持：榜单分析、地区统计、智能攻略、量化报表等
"""
import os
import json
import asyncio
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime
from openai import AsyncOpenAI

from scraper import RedBookScraper, RedBookPost, posts_to_dict
from rankings import RankingService, RankingType, ranking_to_dict, RANKING_CONFIG
from regional import RegionalService, City, city_analysis_to_dict, CITY_CONFIG
from analytics import AnalyticsService, report_to_dict
from guides import GuideGenerator, GuideType, guide_to_dict
import config


@dataclass
class ExecutionStep:
    """执行步骤"""
    step: int
    action: str  # 'thinking', 'extract_keywords', 'searching', 'fetching', 'analyzing', 'ranking', 'regional', 'guide', 'complete', 'error'
    title: str
    description: str
    status: str  # 'running', 'completed', 'error'
    data: Optional[Dict] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class AgentMessage:
    """Agent 消息"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str = ""
    data: Optional[Dict] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass 
class AgentResponse:
    """Agent 响应"""
    message: str
    action: Optional[str] = None
    keywords: Optional[List[str]] = None
    posts: Optional[List[Dict]] = None
    analysis: Optional[str] = None
    suggestions: Optional[List[str]] = None
    steps: List[Dict] = field(default_factory=list)
    # 新增功能数据
    ranking: Optional[Dict] = None          # 榜单数据
    regional: Optional[Dict] = None         # 地区分析数据
    statistics: Optional[Dict] = None       # 统计报表数据
    guide: Optional[Dict] = None            # 攻略数据
    comparison: Optional[Dict] = None       # 对比数据


class RedInsightAgent:
    """
    小红书洞察 AI Agent
    
    能力：
    1. 理解用户自然语言输入
    2. 提取搜索关键词
    3. 自动抓取小红书内容
    4. 智能分析和总结
    5. 生成洞察报告
    6. 【新】榜单分析 - 热门榜、分类榜单
    7. 【新】地区分析 - 城市热门、地区对比
    8. 【新】统计报表 - 量化分析、热词统计
    9. 【新】智能攻略 - 游玩攻略、购买推荐、避坑指南
    """
    
    SYSTEM_PROMPT = """你是 Red Insight 智能助手，专门帮助用户从小红书发现和分析热门内容。

## 你的能力：
1. **内容搜索** - 搜索小红书热门内容
2. **榜单分析** - 查看热门榜、分类榜单（美妆、穿搭、美食、旅行、健身、数码等）
3. **地区分析** - 按城市筛选内容、城市间对比（北京、上海、杭州、成都、广州、深圳等）
4. **统计分析** - 生成量化统计报表、热词分析、互动分布
5. **智能攻略** - 生成游玩攻略、购买推荐、避坑指南、新手入门等

## 交互规则：
- 根据用户需求判断使用哪种功能
- 提取合适的关键词、城市、分类等参数
- 用友好、专业的语气回复

## 输出格式（必须是 JSON）：
{
    "message": "给用户的回复文本",
    "action": "search" | "ranking" | "regional" | "statistics" | "guide" | "compare" | "chat",
    "keywords": ["关键词1", "关键词2"],
    "params": {
        "ranking_type": "hot/beauty/fashion/food/travel/fitness/digital/home/pet/mother",
        "city": "上海/北京/杭州/成都/广州/深圳/重庆/南京/武汉/西安/苏州/长沙/厦门/青岛/三亚/丽江/大理",
        "guide_type": "travel/shopping/food/pitfalls/comparison/budget/beginner",
        "compare_items": ["项目1", "项目2"]
    },
    "follow_up": ["建议的后续问题1", "建议的后续问题2"]
}

## 示例：

用户：看看美妆榜有什么热门的
回复：{"message": "好的！让我来看看小红书美妆榜的热门内容~ 💄", "action": "ranking", "keywords": ["美妆"], "params": {"ranking_type": "beauty"}, "follow_up": ["想了解护肤品还是彩妆？", "有特定的价格范围吗？"]}

用户：上海有什么好吃的
回复：{"message": "让我来看看上海的美食热门内容~ 🍜", "action": "regional", "keywords": ["上海美食"], "params": {"city": "上海", "topic": "美食"}, "follow_up": ["想去哪个区？", "有预算要求吗？"]}

用户：帮我生成一份杭州旅游攻略
回复：{"message": "好的！我来为你生成杭州旅游攻略~ 🗺️", "action": "guide", "keywords": ["杭州旅游"], "params": {"city": "杭州", "guide_type": "travel"}, "follow_up": ["几天的行程？", "有特别想去的景点吗？"]}

用户：对比一下雅诗兰黛和兰蔻的眼霜
回复：{"message": "让我来帮你对比这两款眼霜~ ⚖️", "action": "compare", "keywords": ["雅诗兰黛眼霜", "兰蔻眼霜"], "params": {"compare_items": ["雅诗兰黛眼霜", "兰蔻眼霜"]}, "follow_up": ["关注哪些功效？", "预算是多少？"]}

用户：我想看看护肤品的统计分析
回复：{"message": "好的！让我来分析护肤品相关内容的数据~ 📊", "action": "statistics", "keywords": ["护肤品"], "params": {}, "follow_up": ["想看哪个品类？", "有特定的品牌吗？"]}

用户：有什么避坑指南吗，我想买面膜
回复：{"message": "让我来帮你整理面膜的避坑指南~ ⚠️", "action": "guide", "keywords": ["面膜"], "params": {"guide_type": "pitfalls"}, "follow_up": ["什么肤质？", "有预算要求吗？"]}

用户：你好
回复：{"message": "你好呀！👋 我是 Red Insight 智能助手，可以帮你：\\n\\n📊 **榜单分析** - 美妆榜、穿搭榜、美食榜等\\n🏙️ **城市热门** - 各城市探店、美食、景点\\n📈 **数据统计** - 互动分析、热词统计\\n🗺️ **智能攻略** - 游玩攻略、购买推荐、避坑指南\\n\\n告诉我你想了解什么吧！", "action": null, "keywords": null, "follow_up": ["看看美妆榜热门", "上海有什么好吃的", "帮我生成杭州旅游攻略"]}
"""

    ANALYSIS_PROMPT = """你是一位专业的内容分析师。请分析以下从小红书抓取的帖子内容，提供有价值的洞察。

## 分析维度：
1. **内容趋势**：这些帖子反映了什么样的趋势或热点？
2. **用户关注点**：用户最关心的是什么？
3. **热门观点**：有哪些普遍的观点或建议？
4. **数据洞察**：从互动数据（点赞、评论）能看出什么？
5. **建议**：基于分析给出2-3条建议

## 抓取的帖子数据：
{posts_data}

## 输出要求：
- 使用中文回复
- 条理清晰，重点突出
- 适当使用 emoji 增加可读性
- 回复长度适中（200-400字）
"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """初始化 Agent"""
        self.api_key = api_key or config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or config.OPENAI_BASE_URL or os.getenv("OPENAI_BASE_URL")
        
        if not self.api_key:
            raise ValueError("需要提供 API Key，请在 config.py 中配置 OPENAI_API_KEY")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # 初始化各服务
        self.scraper = RedBookScraper()
        self.ranking_service = RankingService()
        self.regional_service = RegionalService()
        self.analytics_service = AnalyticsService()
        self.guide_generator = GuideGenerator()
        
        self.conversation_history: List[AgentMessage] = []
        self.model = config.OPENAI_MODEL or os.getenv("OPENAI_MODEL", "glm-4-flash")
        self.execution_steps: List[ExecutionStep] = []
    
    def _add_step(self, action: str, title: str, description: str, 
                  status: str = "running", data: Optional[Dict] = None) -> ExecutionStep:
        """添加执行步骤"""
        step = ExecutionStep(
            step=len(self.execution_steps) + 1,
            action=action,
            title=title,
            description=description,
            status=status,
            data=data
        )
        self.execution_steps.append(step)
        return step
    
    def _update_step(self, step_index: int, status: str, 
                     description: Optional[str] = None, data: Optional[Dict] = None):
        """更新步骤状态"""
        if 0 <= step_index < len(self.execution_steps):
            self.execution_steps[step_index].status = status
            if description:
                self.execution_steps[step_index].description = description
            if data:
                self.execution_steps[step_index].data = data
    
    def _parse_city(self, city_name: str) -> Optional[City]:
        """解析城市名称"""
        city_mapping = {
            "北京": City.BEIJING, "上海": City.SHANGHAI, "广州": City.GUANGZHOU,
            "深圳": City.SHENZHEN, "杭州": City.HANGZHOU, "成都": City.CHENGDU,
            "重庆": City.CHONGQING, "南京": City.NANJING, "武汉": City.WUHAN,
            "西安": City.XIAN, "苏州": City.SUZHOU, "长沙": City.CHANGSHA,
            "厦门": City.XIAMEN, "青岛": City.QINGDAO, "三亚": City.SANYA,
            "丽江": City.LIJIANG, "大理": City.DALI
        }
        return city_mapping.get(city_name)
    
    def _parse_ranking_type(self, type_name: str) -> RankingType:
        """解析榜单类型"""
        type_mapping = {
            "hot": RankingType.HOT, "热门": RankingType.HOT,
            "rising": RankingType.RISING, "新晋": RankingType.RISING,
            "beauty": RankingType.BEAUTY, "美妆": RankingType.BEAUTY,
            "fashion": RankingType.FASHION, "穿搭": RankingType.FASHION,
            "food": RankingType.FOOD, "美食": RankingType.FOOD,
            "travel": RankingType.TRAVEL, "旅行": RankingType.TRAVEL,
            "fitness": RankingType.FITNESS, "健身": RankingType.FITNESS,
            "digital": RankingType.DIGITAL, "数码": RankingType.DIGITAL,
            "home": RankingType.HOME, "家居": RankingType.HOME,
            "pet": RankingType.PET, "萌宠": RankingType.PET,
            "mother": RankingType.MOTHER, "母婴": RankingType.MOTHER,
        }
        return type_mapping.get(type_name.lower(), RankingType.HOT)
    
    def _parse_guide_type(self, type_name: str) -> GuideType:
        """解析攻略类型"""
        type_mapping = {
            "travel": GuideType.TRAVEL, "游玩": GuideType.TRAVEL, "旅游": GuideType.TRAVEL,
            "shopping": GuideType.SHOPPING, "购买": GuideType.SHOPPING, "购物": GuideType.SHOPPING,
            "food": GuideType.FOOD, "美食": GuideType.FOOD,
            "pitfalls": GuideType.AVOID_PITFALLS, "避坑": GuideType.AVOID_PITFALLS,
            "comparison": GuideType.COMPARISON, "对比": GuideType.COMPARISON,
            "budget": GuideType.BUDGET, "省钱": GuideType.BUDGET,
            "beginner": GuideType.BEGINNER, "新手": GuideType.BEGINNER, "入门": GuideType.BEGINNER,
        }
        return type_mapping.get(type_name.lower(), GuideType.TRAVEL)
    
    async def chat(self, user_input: str) -> AgentResponse:
        """处理用户输入，返回 Agent 响应"""
        # 清空之前的执行步骤
        self.execution_steps = []
        
        # 添加用户消息到历史
        self.conversation_history.append(AgentMessage(role="user", content=user_input))
        
        try:
            # Step 1: 理解用户意图
            self._add_step(
                action="thinking",
                title="理解用户意图",
                description=f"正在分析用户输入：「{user_input[:50]}{'...' if len(user_input) > 50 else ''}」",
                status="running"
            )
            
            intent_response = await self._understand_intent(user_input)
            
            action = intent_response.get("action")
            message = intent_response.get("message", "")
            keywords = intent_response.get("keywords", [])
            suggestions = intent_response.get("follow_up", [])
            params = intent_response.get("params", {})
            
            self._update_step(0, "completed", 
                f"已理解用户意图，操作类型：{action or '对话'}",
                {"intent": action, "keywords": keywords, "params": params})
            
            # 初始化返回数据
            posts = None
            analysis = None
            ranking = None
            regional = None
            statistics = None
            guide = None
            comparison = None
            
            # 根据 action 执行不同操作
            if action == "ranking":
                # 榜单分析
                ranking_type = self._parse_ranking_type(params.get("ranking_type", "hot"))
                ranking, posts = await self._handle_ranking(ranking_type, keywords)
                
            elif action == "regional":
                # 地区分析
                city_name = params.get("city", "")
                topic = params.get("topic", keywords[0] if keywords else "")
                city = self._parse_city(city_name)
                if city:
                    regional, posts = await self._handle_regional(city, topic)
                else:
                    # 如果没有识别到城市，执行普通搜索
                    posts = await self._handle_search(keywords)
                    
            elif action == "statistics":
                # 统计分析
                posts = await self._handle_search(keywords)
                if posts:
                    statistics = await self._handle_statistics(posts, keywords[0] if keywords else "")
                    
            elif action == "guide":
                # 生成攻略
                guide_type = self._parse_guide_type(params.get("guide_type", "travel"))
                topic = keywords[0] if keywords else params.get("city", "")
                guide, posts = await self._handle_guide(keywords, topic, guide_type)
                
            elif action == "compare":
                # 对比分析
                compare_items = params.get("compare_items", keywords)
                comparison, posts = await self._handle_compare(compare_items)
                
            elif action in ["search", "analyze"]:
                # 普通搜索
                posts = await self._handle_search(keywords)
                if posts:
                    statistics = await self._handle_statistics(posts, keywords[0] if keywords else "")
                    analysis = await self._analyze_posts(posts, keywords[0] if keywords else "")
            
            # 最终步骤
            self._add_step(
                action="complete",
                title="任务完成",
                description="所有步骤执行完毕",
                status="completed",
                data={
                    "total_posts": len(posts) if posts else 0,
                    "has_ranking": ranking is not None,
                    "has_regional": regional is not None,
                    "has_statistics": statistics is not None,
                    "has_guide": guide is not None
                }
            )
            
            # 构建响应
            response = AgentResponse(
                message=message,
                action=action,
                keywords=keywords,
                posts=posts,
                analysis=analysis,
                suggestions=suggestions,
                steps=[asdict(s) for s in self.execution_steps],
                ranking=ranking,
                regional=regional,
                statistics=statistics,
                guide=guide,
                comparison=comparison
            )
            
            # 保存助手回复到历史
            self.conversation_history.append(AgentMessage(
                role="assistant",
                content=message,
                data={"action": action}
            ))
            
            return response
            
        except Exception as e:
            # 记录错误步骤
            self._add_step(
                action="error",
                title="执行出错",
                description=f"错误信息：{str(e)}",
                status="error",
                data={"error": str(e)}
            )
            
            import traceback
            traceback.print_exc()
            
            error_message = f"抱歉，处理请求时遇到了问题：{str(e)}"
            return AgentResponse(
                message=error_message,
                suggestions=["换个方式描述试试", "检查网络连接"],
                steps=[asdict(s) for s in self.execution_steps]
            )
    
    async def _handle_search(self, keywords: List[str]) -> List[Dict]:
        """处理搜索请求"""
        if not keywords:
            return []
        
        primary_keyword = keywords[0]
        
        self._add_step(
            action="searching",
            title="搜索小红书",
            description=f"正在小红书搜索「{primary_keyword}」相关内容...",
            status="running"
        )
        
        self._add_step(
            action="fetching",
            title="抓取帖子数据",
            description="正在抓取帖子信息...",
            status="running"
        )
        
        posts_list = await self.scraper.search_posts(primary_keyword, max_posts=10)
        posts = posts_to_dict(posts_list)
        
        self._update_step(len(self.execution_steps) - 2, "completed",
            f"搜索完成，找到 {len(posts)} 条相关内容")
        
        self._update_step(len(self.execution_steps) - 1, "completed",
            f"成功抓取 {len(posts)} 条帖子数据",
            {"posts_count": len(posts)})
        
        return posts
    
    async def _handle_ranking(self, ranking_type: RankingType, keywords: List[str]) -> tuple:
        """处理榜单请求"""
        config = RANKING_CONFIG.get(ranking_type, {})
        
        self._add_step(
            action="ranking",
            title="获取榜单",
            description=f"正在获取 {config.get('title', '榜单')}...",
            status="running"
        )
        
        ranking_result = await self.ranking_service.get_ranking(ranking_type, max_items=10)
        
        self._update_step(len(self.execution_steps) - 1, "completed",
            f"榜单获取完成，共 {len(ranking_result.items)} 条内容",
            {"ranking_type": ranking_type.value, "items_count": len(ranking_result.items)})
        
        # 提取帖子
        posts = [item.post for item in ranking_result.items]
        
        return ranking_to_dict(ranking_result), posts
    
    async def _handle_regional(self, city: City, topic: str) -> tuple:
        """处理地区分析请求"""
        city_config = CITY_CONFIG.get(city, {})
        city_name = city_config.get('name', city.value)
        
        self._add_step(
            action="regional",
            title="地区分析",
            description=f"正在分析 {city_config.get('emoji', '📍')} {city_name} 的热门内容...",
            status="running"
        )
        
        analysis = await self.regional_service.analyze_city(city, topic, max_posts=10)
        
        self._update_step(len(self.execution_steps) - 1, "completed",
            f"地区分析完成，共 {analysis.total_posts} 条内容",
            {"city": city_name, "posts_count": analysis.total_posts})
        
        return city_analysis_to_dict(analysis), analysis.posts
    
    async def _handle_statistics(self, posts: List[Dict], keyword: str) -> Dict:
        """处理统计分析请求"""
        self._add_step(
            action="analyzing",
            title="统计分析",
            description="正在生成量化统计报表...",
            status="running"
        )
        
        report = self.analytics_service.generate_report(posts, keyword)
        
        self._update_step(len(self.execution_steps) - 1, "completed",
            f"统计分析完成，共分析 {report.total_posts} 条内容",
            {"total_engagement": report.total_engagement})
        
        return report_to_dict(report)
    
    async def _handle_guide(self, keywords: List[str], topic: str, guide_type: GuideType) -> tuple:
        """处理攻略生成请求"""
        # 先抓取相关内容
        search_keyword = keywords[0] if keywords else topic
        
        self._add_step(
            action="searching",
            title="收集素材",
            description=f"正在收集「{search_keyword}」相关内容...",
            status="running"
        )
        
        posts_list = await self.scraper.search_posts(search_keyword, max_posts=10)
        posts = posts_to_dict(posts_list)
        
        self._update_step(len(self.execution_steps) - 1, "completed",
            f"收集到 {len(posts)} 条相关内容")
        
        # 生成攻略
        self._add_step(
            action="guide",
            title="生成攻略",
            description="正在使用 AI 生成攻略...",
            status="running"
        )
        
        guide_result = await self.guide_generator.generate_guide(posts, topic, guide_type)
        
        self._update_step(len(self.execution_steps) - 1, "completed",
            f"攻略生成完成：{guide_result.title}",
            {"guide_type": guide_type.value})
        
        return guide_to_dict(guide_result), posts
    
    async def _handle_compare(self, items: List[str]) -> tuple:
        """处理对比请求"""
        all_posts = []
        
        self._add_step(
            action="searching",
            title="收集对比素材",
            description=f"正在收集 {', '.join(items)} 的相关内容...",
            status="running"
        )
        
        for item in items[:3]:  # 最多对比3个
            posts_list = await self.scraper.search_posts(item, max_posts=5)
            all_posts.extend(posts_to_dict(posts_list))
            await asyncio.sleep(0.5)
        
        self._update_step(len(self.execution_steps) - 1, "completed",
            f"收集到 {len(all_posts)} 条相关内容")
        
        # 生成对比
        self._add_step(
            action="analyzing",
            title="对比分析",
            description="正在使用 AI 进行对比分析...",
            status="running"
        )
        
        comparison = await self.guide_generator.generate_comparison(all_posts, items)
        
        self._update_step(len(self.execution_steps) - 1, "completed",
            "对比分析完成")
        
        return comparison, all_posts
    
    async def _understand_intent(self, user_input: str) -> Dict[str, Any]:
        """使用 LLM 理解用户意图"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
        ]
        
        for msg in self.conversation_history[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        
        # 尝试提取 JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return {"message": content, "action": "search", "keywords": [user_input[:20]]}
    
    async def _analyze_posts(self, posts: List[Dict], keyword: str) -> str:
        """分析抓取到的帖子内容"""
        posts_summary = []
        for i, post in enumerate(posts[:10], 1):
            posts_summary.append(f"""
帖子 {i}：
- 标题：{post.get('title', '')}
- 内容：{post.get('content', '')[:200]}...
- 作者：{post.get('author', '')}
- 点赞：{post.get('likes', '0')}
- 评论：{post.get('comments', '0')}
- 标签：{', '.join(post.get('tags', []))}
""")
        
        posts_data = f"搜索关键词：{keyword}\n\n" + "\n".join(posts_summary)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.ANALYSIS_PROMPT.format(posts_data=posts_data)}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content
    
    def clear_history(self):
        """清除对话历史"""
        self.conversation_history = []
        self.execution_steps = []
    
    def get_history(self) -> List[Dict]:
        """获取对话历史"""
        return [asdict(msg) for msg in self.conversation_history]


async def main():
    """测试 Agent"""
    agent = RedInsightAgent()
    
    print("🔴 Red Insight Agent 已启动！输入 'quit' 退出\n")
    print("💡 支持功能：榜单分析、地区统计、智能攻略、数据报表\n")
    
    while True:
        user_input = input("你: ").strip()
        if user_input.lower() == 'quit':
            break
        
        if not user_input:
            continue
            
        response = await agent.chat(user_input)
        
        print("\n📋 执行步骤：")
        for step in response.steps:
            status_icon = "✅" if step["status"] == "completed" else "❌" if step["status"] == "error" else "⏳"
            print(f"  {status_icon} Step {step['step']}: {step['title']} - {step['description']}")
        
        print(f"\n🤖 Agent: {response.message}")
        
        if response.ranking:
            print(f"\n📊 榜单: {response.ranking.get('title', '')}")
        
        if response.regional:
            print(f"\n🏙️ 地区分析: {response.regional.get('city', '')}")
        
        if response.guide:
            print(f"\n📖 攻略: {response.guide.get('title', '')}")
        
        if response.posts:
            print(f"\n📚 相关帖子 ({len(response.posts)}条)")
        
        if response.analysis:
            print(f"\n📊 分析洞察:\n{response.analysis[:300]}...")
        
        print()


if __name__ == "__main__":
    asyncio.run(main())
