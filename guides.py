"""
智能攻略生成模块
基于抓取的内容生成游玩攻略、购买推荐、避坑指南等
"""
import os
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum

from openai import AsyncOpenAI
import config


class GuideType(str, Enum):
    """攻略类型"""
    TRAVEL = "travel"           # 游玩攻略
    SHOPPING = "shopping"       # 购买推荐
    FOOD = "food"               # 美食攻略
    AVOID_PITFALLS = "pitfalls" # 避坑指南
    COMPARISON = "comparison"   # 产品对比
    BUDGET = "budget"           # 省钱攻略
    BEGINNER = "beginner"       # 新手入门


@dataclass
class GuideSection:
    """攻略章节"""
    title: str
    content: str
    tips: List[str] = field(default_factory=list)
    related_posts: List[Dict] = field(default_factory=list)


@dataclass
class Guide:
    """攻略"""
    guide_type: str
    title: str
    subtitle: str
    summary: str
    sections: List[GuideSection]
    key_points: List[str]           # 要点总结
    warnings: List[str]             # 注意事项
    recommendations: List[Dict]     # 推荐列表
    source_posts_count: int
    generated_at: str = ""
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


@dataclass
class ProductRecommendation:
    """产品推荐"""
    name: str
    category: str
    price_range: str
    rating: float           # 1-5分
    mentions: int           # 提及次数
    pros: List[str]         # 优点
    cons: List[str]         # 缺点
    best_for: str           # 适合人群
    source_posts: List[str]


# 攻略模板配置
GUIDE_TEMPLATES = {
    GuideType.TRAVEL: {
        "title_prefix": "🗺️",
        "sections": ["行前准备", "交通指南", "景点推荐", "住宿推荐", "美食推荐", "注意事项"],
        "prompt_focus": "旅行攻略，包括景点、交通、住宿、美食等实用信息"
    },
    GuideType.SHOPPING: {
        "title_prefix": "🛍️",
        "sections": ["热门推荐", "性价比之选", "高端精选", "购买渠道", "使用技巧"],
        "prompt_focus": "购买攻略，分析产品优缺点、价格对比、购买建议"
    },
    GuideType.FOOD: {
        "title_prefix": "🍜",
        "sections": ["必吃推荐", "人气餐厅", "特色小吃", "美食地图", "点餐技巧"],
        "prompt_focus": "美食攻略，推荐必吃美食、餐厅、点餐建议"
    },
    GuideType.AVOID_PITFALLS: {
        "title_prefix": "⚠️",
        "sections": ["常见陷阱", "防骗指南", "真假辨别", "避坑技巧", "经验总结"],
        "prompt_focus": "避坑指南，总结常见问题、骗局、不推荐的内容"
    },
    GuideType.COMPARISON: {
        "title_prefix": "⚖️",
        "sections": ["产品概述", "功能对比", "价格对比", "用户评价", "推荐结论"],
        "prompt_focus": "产品对比分析，比较不同产品的优缺点"
    },
    GuideType.BUDGET: {
        "title_prefix": "💰",
        "sections": ["省钱技巧", "平价替代", "优惠渠道", "性价比推荐", "预算规划"],
        "prompt_focus": "省钱攻略，推荐平价替代、优惠渠道、省钱技巧"
    },
    GuideType.BEGINNER: {
        "title_prefix": "📚",
        "sections": ["入门须知", "基础知识", "装备推荐", "常见误区", "进阶建议"],
        "prompt_focus": "新手入门指南，从零开始的基础知识和建议"
    }
}


class GuideGenerator:
    """攻略生成器"""
    
    def __init__(self):
        self.api_key = config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.base_url = config.OPENAI_BASE_URL or os.getenv("OPENAI_BASE_URL")
        self.model = config.OPENAI_MODEL or os.getenv("OPENAI_MODEL", "qwen-turbo")
        
        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = None
    
    def _prepare_posts_context(self, posts: List[Dict]) -> str:
        """准备帖子上下文"""
        context_parts = []
        for i, post in enumerate(posts[:10], 1):  # 最多10条
            part = f"""
帖子{i}:
- 标题: {post.get('title', '')}
- 内容: {post.get('content', '')[:300]}
- 作者: {post.get('author', '')}
- 点赞: {post.get('likes', '0')}
- 评论: {post.get('comments', '0')}
- 标签: {', '.join(post.get('tags', []))}
"""
            context_parts.append(part)
        
        return "\n".join(context_parts)
    
    async def generate_guide(
        self,
        posts: List[Dict],
        topic: str,
        guide_type: GuideType = GuideType.TRAVEL
    ) -> Guide:
        """生成攻略"""
        template = GUIDE_TEMPLATES.get(guide_type, GUIDE_TEMPLATES[GuideType.TRAVEL])
        posts_context = self._prepare_posts_context(posts)
        
        prompt = f"""你是一位专业的内容攻略撰写者。请根据以下从小红书抓取的帖子内容，生成一份关于「{topic}」的{template['prompt_focus']}。

## 抓取的帖子内容：
{posts_context}

## 攻略要求：
1. 标题要吸引人，带有emoji
2. 内容要实用、具体、有参考价值
3. 分为以下几个章节: {', '.join(template['sections'])}
4. 每个章节包含具体建议和技巧
5. 总结出5-8个要点
6. 列出3-5个注意事项/避坑提醒
7. 给出3-5个具体推荐（产品/地点/餐厅等）

## 输出格式（JSON）：
{{
    "title": "攻略标题",
    "subtitle": "副标题",
    "summary": "100字左右的摘要",
    "sections": [
        {{
            "title": "章节标题",
            "content": "章节内容（200-300字）",
            "tips": ["技巧1", "技巧2"]
        }}
    ],
    "key_points": ["要点1", "要点2", ...],
    "warnings": ["注意事项1", "注意事项2", ...],
    "recommendations": [
        {{
            "name": "推荐名称",
            "reason": "推荐理由",
            "detail": "详细信息"
        }}
    ]
}}

请直接输出JSON，不要有其他内容。"""

        if not self.client:
            # 无API时返回基于模板的简单攻略
            return self._generate_fallback_guide(posts, topic, guide_type, template)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # 解析JSON
            import json
            import re
            
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                guide_data = json.loads(json_match.group())
            else:
                guide_data = json.loads(content)
            
            # 构建章节
            sections = []
            for sec_data in guide_data.get('sections', []):
                sections.append(GuideSection(
                    title=sec_data.get('title', ''),
                    content=sec_data.get('content', ''),
                    tips=sec_data.get('tips', []),
                    related_posts=[]
                ))
            
            return Guide(
                guide_type=guide_type.value,
                title=f"{template['title_prefix']} {guide_data.get('title', f'{topic}攻略')}",
                subtitle=guide_data.get('subtitle', ''),
                summary=guide_data.get('summary', ''),
                sections=sections,
                key_points=guide_data.get('key_points', []),
                warnings=guide_data.get('warnings', []),
                recommendations=guide_data.get('recommendations', []),
                source_posts_count=len(posts)
            )
            
        except Exception as e:
            print(f"攻略生成失败: {e}")
            return self._generate_fallback_guide(posts, topic, guide_type, template)
    
    def _generate_fallback_guide(
        self, 
        posts: List[Dict], 
        topic: str, 
        guide_type: GuideType,
        template: Dict
    ) -> Guide:
        """生成备用攻略（无API时）"""
        # 从帖子中提取关键信息
        tips = []
        for post in posts[:5]:
            title = post.get('title', '')
            if title:
                tips.append(f"💡 {title[:50]}")
        
        sections = []
        for sec_title in template['sections'][:3]:
            content_parts = []
            for post in posts[:2]:
                if post.get('content'):
                    content_parts.append(post['content'][:100])
            
            sections.append(GuideSection(
                title=sec_title,
                content="根据小红书用户分享，" + "。".join(content_parts)[:300] if content_parts else f"关于{sec_title}的详细内容...",
                tips=[f"来自热门帖子的建议"],
                related_posts=posts[:2]
            ))
        
        return Guide(
            guide_type=guide_type.value,
            title=f"{template['title_prefix']} {topic}完全攻略",
            subtitle=f"基于 {len(posts)} 篇小红书热门内容整理",
            summary=f"这是一份关于「{topic}」的{template['prompt_focus']}，综合了小红书上的热门分享内容。",
            sections=sections,
            key_points=tips[:5] or [f"关于{topic}的重要信息"],
            warnings=["以上内容仅供参考，请结合实际情况", "部分信息可能有时效性，请注意核实"],
            recommendations=[
                {"name": post.get('title', '')[:30], "reason": f"点赞 {post.get('likes', '0')}", "detail": post.get('url', '')}
                for post in posts[:3]
            ],
            source_posts_count=len(posts)
        )
    
    async def generate_product_recommendations(
        self,
        posts: List[Dict],
        category: str
    ) -> List[ProductRecommendation]:
        """生成产品推荐列表"""
        posts_context = self._prepare_posts_context(posts)
        
        prompt = f"""分析以下小红书帖子，提取关于「{category}」的产品推荐。

## 帖子内容：
{posts_context}

## 要求：
为每个提到的产品生成推荐信息，包括：
- 产品名称
- 价格范围（如：￥100-200）
- 评分（1-5分）
- 优点列表
- 缺点列表
- 适合人群

## 输出格式（JSON数组）：
[
    {{
        "name": "产品名称",
        "price_range": "价格范围",
        "rating": 4.5,
        "pros": ["优点1", "优点2"],
        "cons": ["缺点1"],
        "best_for": "适合人群描述"
    }}
]

请直接输出JSON数组。"""

        if not self.client:
            # 返回基于帖子的简单推荐
            return self._extract_simple_recommendations(posts, category)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )
            
            import json
            import re
            
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                products_data = json.loads(json_match.group())
            else:
                products_data = json.loads(content)
            
            recommendations = []
            for i, prod in enumerate(products_data[:10]):
                recommendations.append(ProductRecommendation(
                    name=prod.get('name', f'产品{i+1}'),
                    category=category,
                    price_range=prod.get('price_range', '价格未知'),
                    rating=float(prod.get('rating', 4.0)),
                    mentions=1,
                    pros=prod.get('pros', []),
                    cons=prod.get('cons', []),
                    best_for=prod.get('best_for', '大众'),
                    source_posts=[]
                ))
            
            return recommendations
            
        except Exception as e:
            print(f"产品推荐生成失败: {e}")
            return self._extract_simple_recommendations(posts, category)
    
    def _extract_simple_recommendations(
        self, 
        posts: List[Dict], 
        category: str
    ) -> List[ProductRecommendation]:
        """提取简单推荐（无API时）"""
        recommendations = []
        
        for i, post in enumerate(posts[:5]):
            title = post.get('title', '')
            
            recommendations.append(ProductRecommendation(
                name=title[:30] if title else f"{category}推荐{i+1}",
                category=category,
                price_range="详见原帖",
                rating=4.0 + (i % 10) / 10,
                mentions=1,
                pros=["小红书用户推荐", f"点赞数 {post.get('likes', '0')}"],
                cons=["需要自行判断是否适合"],
                best_for="参考原帖描述",
                source_posts=[post.get('url', '')]
            ))
        
        return recommendations
    
    async def generate_comparison(
        self,
        posts: List[Dict],
        items: List[str]
    ) -> Dict:
        """生成对比分析"""
        posts_context = self._prepare_posts_context(posts)
        items_str = '、'.join(items)
        
        prompt = f"""分析以下小红书帖子，对比「{items_str}」。

## 帖子内容：
{posts_context}

## 要求：
生成详细的对比分析，包括：
1. 各项目的优缺点
2. 价格/性价比对比
3. 适用场景对比
4. 用户评价总结
5. 最终推荐

## 输出格式（JSON）：
{{
    "items": [
        {{
            "name": "项目名",
            "score": 85,
            "pros": ["优点"],
            "cons": ["缺点"],
            "price_value": "性价比评价",
            "best_for": "最适合场景"
        }}
    ],
    "winner": "综合推荐",
    "summary": "总结对比结果"
}}

请直接输出JSON。"""

        if not self.client:
            # 返回简单对比
            return {
                "items": [{"name": item, "score": 80 - i*5, "pros": ["待分析"], "cons": ["待分析"]} for i, item in enumerate(items)],
                "winner": items[0] if items else "",
                "summary": f"关于{items_str}的对比分析需要更多数据"
            }
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )
            
            import json
            import re
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(content)
            
        except Exception as e:
            print(f"对比生成失败: {e}")
            return {
                "items": [{"name": item, "score": 80, "pros": [], "cons": []} for item in items],
                "winner": items[0] if items else "",
                "summary": "对比分析生成失败，请稍后重试"
            }


def guide_to_dict(guide: Guide) -> Dict:
    """转换攻略为字典"""
    return {
        "guide_type": guide.guide_type,
        "title": guide.title,
        "subtitle": guide.subtitle,
        "summary": guide.summary,
        "sections": [asdict(s) for s in guide.sections],
        "key_points": guide.key_points,
        "warnings": guide.warnings,
        "recommendations": guide.recommendations,
        "source_posts_count": guide.source_posts_count,
        "generated_at": guide.generated_at
    }


def recommendation_to_dict(rec: ProductRecommendation) -> Dict:
    """转换产品推荐为字典"""
    return asdict(rec)


async def main():
    """测试攻略生成"""
    sample_posts = [
        {
            "title": "杭州西湖三日游超详细攻略！本地人推荐",
            "content": "第一天：断桥残雪→白堤→孤山→曲院风荷。早起去断桥，人少景美！住宿推荐西湖边的民宿...",
            "author": "旅行达人",
            "likes": "3.2w",
            "comments": "1567",
            "tags": ["杭州旅游", "西湖", "攻略"]
        },
        {
            "title": "杭州美食地图🍜不踩雷的探店清单",
            "content": "外婆家、新白鹿必去！龙井虾仁、东坡肉都很正宗。河坊街的小吃一般，不太推荐...",
            "author": "美食博主",
            "likes": "2.1w",
            "comments": "892",
            "tags": ["杭州美食", "探店"]
        },
    ]
    
    generator = GuideGenerator()
    
    print("📖 生成杭州游玩攻略...")
    guide = await generator.generate_guide(sample_posts, "杭州", GuideType.TRAVEL)
    
    print(f"\n{guide.title}")
    print(f"{guide.subtitle}")
    print(f"\n📝 摘要: {guide.summary}")
    
    print(f"\n📋 要点:")
    for point in guide.key_points:
        print(f"  • {point}")
    
    print(f"\n⚠️ 注意事项:")
    for warning in guide.warnings:
        print(f"  • {warning}")


if __name__ == "__main__":
    asyncio.run(main())

