"""
榜单抓取模块
支持多种类型榜单：热门榜、新晋爆款、分类榜单等
"""
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from urllib.parse import quote

from scraper import RedBookScraper, RedBookPost, posts_to_dict


class RankingType(str, Enum):
    """榜单类型"""
    HOT = "hot"              # 热门榜
    RISING = "rising"        # 新晋爆款
    WEEKLY = "weekly"        # 周榜
    BEAUTY = "beauty"        # 美妆榜
    FASHION = "fashion"      # 穿搭榜
    FOOD = "food"            # 美食榜
    TRAVEL = "travel"        # 旅行榜
    FITNESS = "fitness"      # 健身榜
    DIGITAL = "digital"      # 数码榜
    HOME = "home"            # 家居榜
    PET = "pet"              # 萌宠榜
    MOTHER = "mother"        # 母婴榜


@dataclass
class RankingItem:
    """榜单项目"""
    rank: int                   # 排名
    post: Dict                  # 帖子数据
    score: float                # 热度分数
    trend: str = "stable"       # 趋势: up, down, stable, new
    trend_value: int = 0        # 变化值


@dataclass
class RankingResult:
    """榜单结果"""
    ranking_type: str
    title: str
    description: str
    items: List[RankingItem]
    total_engagement: int       # 总互动量
    avg_score: float            # 平均热度
    generated_at: str = ""
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


# 榜单配置
RANKING_CONFIG = {
    RankingType.HOT: {
        "title": "🔥 热门内容榜",
        "description": "当前小红书最热门的内容",
        "keywords": ["热门", "爆款", "必看"],
        "sort_by": "engagement"
    },
    RankingType.RISING: {
        "title": "🚀 新晋爆款榜",
        "description": "近期快速上升的热门内容",
        "keywords": ["新发现", "小众", "宝藏"],
        "sort_by": "rising"
    },
    RankingType.WEEKLY: {
        "title": "📅 本周热榜",
        "description": "本周最受欢迎的内容",
        "keywords": ["本周", "周榜"],
        "sort_by": "weekly"
    },
    RankingType.BEAUTY: {
        "title": "💄 美妆护肤榜",
        "description": "热门美妆护肤产品和技巧",
        "keywords": ["美妆推荐", "护肤品", "化妆教程", "skincare"],
        "sort_by": "engagement"
    },
    RankingType.FASHION: {
        "title": "👗 穿搭时尚榜",
        "description": "流行穿搭风格和搭配灵感",
        "keywords": ["穿搭分享", "ootd", "时尚穿搭", "日常穿搭"],
        "sort_by": "engagement"
    },
    RankingType.FOOD: {
        "title": "🍜 美食探店榜",
        "description": "热门美食推荐和探店攻略",
        "keywords": ["美食推荐", "探店", "美食攻略", "好吃"],
        "sort_by": "engagement"
    },
    RankingType.TRAVEL: {
        "title": "✈️ 旅行目的地榜",
        "description": "热门旅行目的地和攻略",
        "keywords": ["旅行攻略", "旅游推荐", "出行", "打卡"],
        "sort_by": "engagement"
    },
    RankingType.FITNESS: {
        "title": "💪 健身运动榜",
        "description": "健身减脂技巧和运动分享",
        "keywords": ["健身打卡", "减脂", "运动", "瑜伽"],
        "sort_by": "engagement"
    },
    RankingType.DIGITAL: {
        "title": "📱 数码科技榜",
        "description": "数码产品评测和使用技巧",
        "keywords": ["数码测评", "手机推荐", "电子产品", "科技"],
        "sort_by": "engagement"
    },
    RankingType.HOME: {
        "title": "🏠 家居生活榜",
        "description": "家居好物和生活技巧",
        "keywords": ["家居好物", "收纳", "装修", "居家"],
        "sort_by": "engagement"
    },
    RankingType.PET: {
        "title": "🐱 萌宠榜",
        "description": "宠物日常和养宠技巧",
        "keywords": ["猫咪", "狗狗", "萌宠", "养宠"],
        "sort_by": "engagement"
    },
    RankingType.MOTHER: {
        "title": "👶 母婴亲子榜",
        "description": "母婴产品和育儿经验",
        "keywords": ["母婴好物", "育儿", "宝宝", "亲子"],
        "sort_by": "engagement"
    },
}


class RankingService:
    """榜单服务"""
    
    def __init__(self):
        self.scraper = RedBookScraper()
    
    def _parse_likes(self, likes_str: str) -> int:
        """解析点赞数字符串"""
        if not likes_str:
            return 0
        likes_str = str(likes_str).lower()
        if 'w' in likes_str or '万' in likes_str:
            return int(float(likes_str.replace('w', '').replace('万', '')) * 10000)
        if 'k' in likes_str or '千' in likes_str:
            return int(float(likes_str.replace('k', '').replace('千', '')) * 1000)
        try:
            return int(''.join(filter(str.isdigit, likes_str))) or 0
        except:
            return 0
    
    def _calculate_score(self, post: Dict, sort_by: str = "engagement") -> float:
        """计算帖子热度分数"""
        likes = self._parse_likes(post.get('likes', '0'))
        comments = self._parse_likes(post.get('comments', '0'))
        
        if sort_by == "engagement":
            # 互动总量权重
            return likes * 1.0 + comments * 2.0
        elif sort_by == "rising":
            # 新晋内容权重（假设更多评论代表更活跃）
            return likes * 0.5 + comments * 3.0
        elif sort_by == "weekly":
            # 周榜权重
            return likes * 1.2 + comments * 1.5
        else:
            return likes + comments
    
    async def get_ranking(
        self, 
        ranking_type: RankingType, 
        max_items: int = 10
    ) -> RankingResult:
        """获取指定类型的榜单"""
        config = RANKING_CONFIG.get(ranking_type, RANKING_CONFIG[RankingType.HOT])
        
        # 抓取多个关键词的帖子
        all_posts = []
        for keyword in config["keywords"][:2]:  # 取前2个关键词
            posts = await self.scraper.search_posts(keyword, max_posts=max_items)
            all_posts.extend(posts_to_dict(posts))
            await asyncio.sleep(1)  # 避免频繁请求
        
        # 去重（根据标题）
        seen_titles = set()
        unique_posts = []
        for post in all_posts:
            title = post.get('title', '')[:30]
            if title not in seen_titles:
                seen_titles.add(title)
                unique_posts.append(post)
        
        # 计算分数并排序
        sort_by = config.get("sort_by", "engagement")
        scored_posts = []
        for post in unique_posts:
            score = self._calculate_score(post, sort_by)
            scored_posts.append((post, score))
        
        scored_posts.sort(key=lambda x: x[1], reverse=True)
        
        # 生成榜单项
        items = []
        for i, (post, score) in enumerate(scored_posts[:max_items]):
            # 模拟趋势（实际应用中需要历史数据对比）
            trend = "new" if i < 3 else ("up" if i % 2 == 0 else "stable")
            trend_value = (max_items - i) if trend == "up" else 0
            
            items.append(RankingItem(
                rank=i + 1,
                post=post,
                score=round(score, 2),
                trend=trend,
                trend_value=trend_value
            ))
        
        # 计算总体统计
        total_engagement = sum(item.score for item in items)
        avg_score = total_engagement / len(items) if items else 0
        
        return RankingResult(
            ranking_type=ranking_type.value,
            title=config["title"],
            description=config["description"],
            items=items,
            total_engagement=int(total_engagement),
            avg_score=round(avg_score, 2)
        )
    
    async def get_multiple_rankings(
        self, 
        ranking_types: List[RankingType],
        max_items: int = 5
    ) -> List[RankingResult]:
        """获取多个榜单"""
        results = []
        for rt in ranking_types:
            result = await self.get_ranking(rt, max_items)
            results.append(result)
            await asyncio.sleep(1)
        return results
    
    async def get_category_overview(self, max_items: int = 3) -> Dict:
        """获取分类概览（每个类别top3）"""
        categories = [
            RankingType.BEAUTY, RankingType.FASHION, RankingType.FOOD,
            RankingType.TRAVEL, RankingType.FITNESS, RankingType.DIGITAL
        ]
        
        overview = {
            "title": "📊 分类热门概览",
            "description": "各分类热门内容一览",
            "categories": [],
            "generated_at": datetime.now().isoformat()
        }
        
        for category in categories:
            ranking = await self.get_ranking(category, max_items)
            overview["categories"].append({
                "type": category.value,
                "title": RANKING_CONFIG[category]["title"],
                "top_items": [asdict(item) for item in ranking.items[:max_items]],
                "total_score": ranking.total_engagement
            })
            await asyncio.sleep(0.5)
        
        # 按热度排序类别
        overview["categories"].sort(key=lambda x: x["total_score"], reverse=True)
        
        return overview


def ranking_to_dict(ranking: RankingResult) -> Dict:
    """将榜单结果转换为字典"""
    return {
        "ranking_type": ranking.ranking_type,
        "title": ranking.title,
        "description": ranking.description,
        "items": [asdict(item) for item in ranking.items],
        "total_engagement": ranking.total_engagement,
        "avg_score": ranking.avg_score,
        "generated_at": ranking.generated_at
    }


async def main():
    """测试榜单功能"""
    service = RankingService()
    
    print("🔥 获取热门榜...")
    hot_ranking = await service.get_ranking(RankingType.HOT, max_items=5)
    print(f"\n{hot_ranking.title}")
    print(f"{hot_ranking.description}")
    print(f"总互动量: {hot_ranking.total_engagement}")
    print("-" * 50)
    
    for item in hot_ranking.items:
        trend_icon = {"up": "📈", "down": "📉", "stable": "➡️", "new": "🆕"}[item.trend]
        print(f"#{item.rank} {trend_icon} {item.post['title'][:40]}... | 热度: {item.score}")


if __name__ == "__main__":
    asyncio.run(main())

