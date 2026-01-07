"""
地区分析模块
支持按城市/地区筛选内容，进行地区热门话题统计和对比
"""
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum

from scraper import RedBookScraper, posts_to_dict


class City(str, Enum):
    """支持的城市"""
    BEIJING = "北京"
    SHANGHAI = "上海"
    GUANGZHOU = "广州"
    SHENZHEN = "深圳"
    HANGZHOU = "杭州"
    CHENGDU = "成都"
    CHONGQING = "重庆"
    NANJING = "南京"
    WUHAN = "武汉"
    XIAN = "西安"
    SUZHOU = "苏州"
    CHANGSHA = "长沙"
    XIAMEN = "厦门"
    QINGDAO = "青岛"
    SANYA = "三亚"
    LIJIANG = "丽江"
    DALI = "大理"


# 城市配置信息
CITY_CONFIG = {
    City.BEIJING: {
        "name": "北京",
        "aliases": ["北京市", "帝都", "BJ"],
        "emoji": "🏛️",
        "hot_topics": ["故宫", "三里屯", "后海", "798", "环球影城"],
        "specialties": ["烤鸭", "炸酱面", "豆汁儿", "卤煮"]
    },
    City.SHANGHAI: {
        "name": "上海",
        "aliases": ["上海市", "魔都", "SH"],
        "emoji": "🌃",
        "hot_topics": ["外滩", "迪士尼", "武康路", "静安寺", "南京路"],
        "specialties": ["小笼包", "生煎", "本帮菜", "咖啡"]
    },
    City.GUANGZHOU: {
        "name": "广州",
        "aliases": ["广州市", "羊城", "GZ"],
        "emoji": "🌺",
        "hot_topics": ["北京路", "沙面", "珠江夜游", "长隆"],
        "specialties": ["早茶", "肠粉", "烧腊", "糖水"]
    },
    City.SHENZHEN: {
        "name": "深圳",
        "aliases": ["深圳市", "鹏城", "SZ"],
        "emoji": "🏙️",
        "hot_topics": ["华强北", "世界之窗", "大梅沙", "深圳湾"],
        "specialties": ["潮汕美食", "海鲜", "茶饮"]
    },
    City.HANGZHOU: {
        "name": "杭州",
        "aliases": ["杭州市", "杭城"],
        "emoji": "🌊",
        "hot_topics": ["西湖", "灵隐寺", "西溪湿地", "河坊街"],
        "specialties": ["龙井茶", "东坡肉", "西湖醋鱼", "叫花鸡"]
    },
    City.CHENGDU: {
        "name": "成都",
        "aliases": ["成都市", "蓉城"],
        "emoji": "🐼",
        "hot_topics": ["春熙路", "宽窄巷子", "大熊猫基地", "锦里"],
        "specialties": ["火锅", "串串", "担担面", "兔头"]
    },
    City.CHONGQING: {
        "name": "重庆",
        "aliases": ["重庆市", "山城"],
        "emoji": "🌉",
        "hot_topics": ["洪崖洞", "解放碑", "磁器口", "长江索道"],
        "specialties": ["火锅", "小面", "酸辣粉", "毛血旺"]
    },
    City.NANJING: {
        "name": "南京",
        "aliases": ["南京市", "金陵"],
        "emoji": "🏯",
        "hot_topics": ["夫子庙", "玄武湖", "中山陵", "老门东"],
        "specialties": ["盐水鸭", "鸭血粉丝汤", "小笼包"]
    },
    City.WUHAN: {
        "name": "武汉",
        "aliases": ["武汉市", "江城"],
        "emoji": "🌸",
        "hot_topics": ["黄鹤楼", "户部巷", "东湖", "光谷"],
        "specialties": ["热干面", "豆皮", "武昌鱼", "精武鸭脖"]
    },
    City.XIAN: {
        "name": "西安",
        "aliases": ["西安市", "长安"],
        "emoji": "🏰",
        "hot_topics": ["兵马俑", "大雁塔", "回民街", "城墙"],
        "specialties": ["肉夹馍", "凉皮", "羊肉泡馍", "biangbiang面"]
    },
    City.SUZHOU: {
        "name": "苏州",
        "aliases": ["苏州市", "姑苏"],
        "emoji": "🏡",
        "hot_topics": ["拙政园", "虎丘", "平江路", "周庄"],
        "specialties": ["苏式面", "蟹壳黄", "糕团", "阳澄湖大闸蟹"]
    },
    City.CHANGSHA: {
        "name": "长沙",
        "aliases": ["长沙市", "星城"],
        "emoji": "⭐",
        "hot_topics": ["橘子洲", "岳麓山", "太平老街", "五一广场"],
        "specialties": ["臭豆腐", "糖油粑粑", "口味虾", "茶颜悦色"]
    },
    City.XIAMEN: {
        "name": "厦门",
        "aliases": ["厦门市", "鹭岛"],
        "emoji": "🏝️",
        "hot_topics": ["鼓浪屿", "曾厝垵", "中山路", "环岛路"],
        "specialties": ["沙茶面", "海蛎煎", "土笋冻", "花生汤"]
    },
    City.QINGDAO: {
        "name": "青岛",
        "aliases": ["青岛市", "岛城"],
        "emoji": "🍺",
        "hot_topics": ["栈桥", "八大关", "崂山", "金沙滩"],
        "specialties": ["青岛啤酒", "海鲜", "蛤蜊", "鲅鱼饺子"]
    },
    City.SANYA: {
        "name": "三亚",
        "aliases": ["三亚市"],
        "emoji": "🏖️",
        "hot_topics": ["亚龙湾", "天涯海角", "蜈支洲岛", "南山寺"],
        "specialties": ["海鲜", "椰子鸡", "抱罗粉", "清补凉"]
    },
    City.LIJIANG: {
        "name": "丽江",
        "aliases": ["丽江市", "丽江古城"],
        "emoji": "🏔️",
        "hot_topics": ["丽江古城", "玉龙雪山", "束河古镇", "泸沽湖"],
        "specialties": ["纳西烤肉", "丽江粑粑", "鸡豆凉粉"]
    },
    City.DALI: {
        "name": "大理",
        "aliases": ["大理市", "大理古城"],
        "emoji": "🌅",
        "hot_topics": ["洱海", "大理古城", "双廊", "苍山"],
        "specialties": ["乳扇", "饵丝", "砂锅鱼", "喜洲粑粑"]
    },
}


@dataclass
class RegionalPost:
    """地区帖子数据"""
    city: str
    post: Dict
    relevance_score: float  # 城市相关度评分
    topic_matches: List[str]  # 匹配的热门话题


@dataclass
class CityAnalysis:
    """城市分析结果"""
    city: str
    city_emoji: str
    total_posts: int
    posts: List[Dict]
    hot_topics: List[Dict]  # {topic, count, engagement}
    specialties_mentioned: List[str]
    total_engagement: int
    avg_engagement: float
    top_authors: List[Dict]  # {author, posts_count, total_likes}
    generated_at: str = ""
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


@dataclass 
class RegionalComparison:
    """地区对比结果"""
    cities: List[str]
    comparison_data: List[Dict]  # 各城市的对比数据
    winner: str  # 热度最高的城市
    insights: List[str]  # 对比洞察
    generated_at: str = ""
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


class RegionalService:
    """地区分析服务"""
    
    def __init__(self):
        self.scraper = RedBookScraper()
    
    def _parse_engagement(self, value: str) -> int:
        """解析互动数"""
        if not value:
            return 0
        value = str(value).lower()
        if 'w' in value or '万' in value:
            return int(float(value.replace('w', '').replace('万', '')) * 10000)
        if 'k' in value or '千' in value:
            return int(float(value.replace('k', '').replace('千', '')) * 1000)
        try:
            return int(''.join(filter(str.isdigit, value))) or 0
        except:
            return 0
    
    def _calculate_relevance(self, post: Dict, city: City) -> tuple:
        """计算帖子与城市的相关度"""
        config = CITY_CONFIG.get(city, {})
        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        text = title + " " + content
        
        score = 0
        matched_topics = []
        
        # 检查城市名
        city_name = config.get('name', '')
        if city_name.lower() in text:
            score += 10
        
        # 检查别名
        for alias in config.get('aliases', []):
            if alias.lower() in text:
                score += 5
        
        # 检查热门话题
        for topic in config.get('hot_topics', []):
            if topic.lower() in text:
                score += 3
                matched_topics.append(topic)
        
        # 检查特色美食
        for specialty in config.get('specialties', []):
            if specialty.lower() in text:
                score += 2
                matched_topics.append(specialty)
        
        return score, matched_topics
    
    async def analyze_city(
        self, 
        city: City,
        topic: Optional[str] = None,
        max_posts: int = 10
    ) -> CityAnalysis:
        """分析指定城市的内容"""
        config = CITY_CONFIG.get(city, {})
        city_name = config.get('name', city.value)
        
        # 构建搜索关键词
        search_keywords = []
        if topic:
            search_keywords.append(f"{city_name}{topic}")
            search_keywords.append(f"{city_name} {topic}")
        else:
            search_keywords.append(f"{city_name}探店")
            search_keywords.append(f"{city_name}攻略")
            search_keywords.append(f"{city_name}旅游")
        
        # 抓取帖子
        all_posts = []
        for keyword in search_keywords[:2]:
            posts = await self.scraper.search_posts(keyword, max_posts=max_posts)
            all_posts.extend(posts_to_dict(posts))
            await asyncio.sleep(1)
        
        # 去重
        seen = set()
        unique_posts = []
        for post in all_posts:
            title = post.get('title', '')[:30]
            if title not in seen:
                seen.add(title)
                unique_posts.append(post)
        
        # 分析热门话题
        topic_counts = {}
        specialties_found = []
        
        for post in unique_posts:
            text = (post.get('title', '') + post.get('content', '')).lower()
            
            # 统计热门话题
            for topic_name in config.get('hot_topics', []):
                if topic_name.lower() in text:
                    if topic_name not in topic_counts:
                        topic_counts[topic_name] = {'count': 0, 'engagement': 0}
                    topic_counts[topic_name]['count'] += 1
                    engagement = self._parse_engagement(post.get('likes', '0'))
                    topic_counts[topic_name]['engagement'] += engagement
            
            # 统计特色美食
            for specialty in config.get('specialties', []):
                if specialty.lower() in text and specialty not in specialties_found:
                    specialties_found.append(specialty)
        
        # 排序热门话题
        hot_topics = [
            {'topic': topic, 'count': data['count'], 'engagement': data['engagement']}
            for topic, data in topic_counts.items()
        ]
        hot_topics.sort(key=lambda x: x['engagement'], reverse=True)
        
        # 统计作者
        author_stats = {}
        for post in unique_posts:
            author = post.get('author', '未知')
            if author not in author_stats:
                author_stats[author] = {'posts_count': 0, 'total_likes': 0}
            author_stats[author]['posts_count'] += 1
            author_stats[author]['total_likes'] += self._parse_engagement(post.get('likes', '0'))
        
        top_authors = [
            {'author': author, **stats}
            for author, stats in sorted(
                author_stats.items(), 
                key=lambda x: x[1]['total_likes'], 
                reverse=True
            )[:5]
        ]
        
        # 计算总互动
        total_engagement = sum(
            self._parse_engagement(p.get('likes', '0')) + 
            self._parse_engagement(p.get('comments', '0'))
            for p in unique_posts
        )
        avg_engagement = total_engagement / len(unique_posts) if unique_posts else 0
        
        return CityAnalysis(
            city=city_name,
            city_emoji=config.get('emoji', '📍'),
            total_posts=len(unique_posts),
            posts=unique_posts[:max_posts],
            hot_topics=hot_topics[:10],
            specialties_mentioned=specialties_found,
            total_engagement=total_engagement,
            avg_engagement=round(avg_engagement, 2),
            top_authors=top_authors
        )
    
    async def compare_cities(
        self,
        cities: List[City],
        topic: Optional[str] = None
    ) -> RegionalComparison:
        """对比多个城市"""
        comparison_data = []
        
        for city in cities:
            analysis = await self.analyze_city(city, topic, max_posts=5)
            config = CITY_CONFIG.get(city, {})
            
            comparison_data.append({
                'city': analysis.city,
                'emoji': config.get('emoji', '📍'),
                'total_posts': analysis.total_posts,
                'total_engagement': analysis.total_engagement,
                'avg_engagement': analysis.avg_engagement,
                'top_topics': [t['topic'] for t in analysis.hot_topics[:3]],
                'specialties': analysis.specialties_mentioned[:3]
            })
            await asyncio.sleep(1)
        
        # 找出热度最高的城市
        comparison_data.sort(key=lambda x: x['total_engagement'], reverse=True)
        winner = comparison_data[0]['city'] if comparison_data else ""
        
        # 生成洞察
        insights = []
        if len(comparison_data) >= 2:
            insights.append(f"🏆 {winner} 在该话题上热度最高，总互动量达 {comparison_data[0]['total_engagement']}")
            
            if comparison_data[0]['avg_engagement'] > comparison_data[-1]['avg_engagement'] * 2:
                insights.append(f"📊 {comparison_data[0]['city']} 的平均互动量是 {comparison_data[-1]['city']} 的 {round(comparison_data[0]['avg_engagement']/max(comparison_data[-1]['avg_engagement'], 1), 1)} 倍")
            
            all_topics = set()
            for data in comparison_data:
                all_topics.update(data['top_topics'])
            if all_topics:
                insights.append(f"🔥 热门话题包括：{', '.join(list(all_topics)[:5])}")
        
        return RegionalComparison(
            cities=[c.value for c in cities],
            comparison_data=comparison_data,
            winner=winner,
            insights=insights
        )
    
    async def get_trending_cities(self, topic: str, max_cities: int = 5) -> List[Dict]:
        """获取某话题下热门城市排名"""
        city_scores = []
        
        # 采样部分热门城市
        sample_cities = [
            City.SHANGHAI, City.BEIJING, City.HANGZHOU, 
            City.CHENGDU, City.SHENZHEN, City.GUANGZHOU,
            City.CHONGQING, City.XIAMEN, City.SANYA
        ]
        
        for city in sample_cities[:6]:
            config = CITY_CONFIG.get(city, {})
            keyword = f"{config.get('name', '')} {topic}"
            
            posts = await self.scraper.search_posts(keyword, max_posts=3)
            posts_dict = posts_to_dict(posts)
            
            total_engagement = sum(
                self._parse_engagement(p.get('likes', '0'))
                for p in posts_dict
            )
            
            city_scores.append({
                'city': config.get('name', city.value),
                'emoji': config.get('emoji', '📍'),
                'posts_count': len(posts_dict),
                'total_engagement': total_engagement,
                'sample_posts': [p.get('title', '')[:30] for p in posts_dict[:2]]
            })
            
            await asyncio.sleep(0.5)
        
        # 排序
        city_scores.sort(key=lambda x: x['total_engagement'], reverse=True)
        
        return city_scores[:max_cities]


def city_analysis_to_dict(analysis: CityAnalysis) -> Dict:
    """转换城市分析结果为字典"""
    return asdict(analysis)


async def main():
    """测试地区分析功能"""
    service = RegionalService()
    
    print("🏙️ 分析上海美食探店...")
    analysis = await service.analyze_city(City.SHANGHAI, topic="美食")
    
    print(f"\n{analysis.city_emoji} {analysis.city}")
    print(f"帖子数: {analysis.total_posts}")
    print(f"总互动: {analysis.total_engagement}")
    print(f"平均互动: {analysis.avg_engagement}")
    
    print("\n🔥 热门话题:")
    for topic in analysis.hot_topics[:5]:
        print(f"  • {topic['topic']}: {topic['count']}篇, {topic['engagement']}互动")
    
    print("\n🍜 提及的特色美食:")
    print(f"  {', '.join(analysis.specialties_mentioned)}")


if __name__ == "__main__":
    asyncio.run(main())

