"""
统计分析模块
生成量化统计报表、数据可视化、热词分析等
"""
import re
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import Counter
from enum import Enum


class MetricType(str, Enum):
    """指标类型"""
    LIKES = "likes"
    COMMENTS = "comments"
    ENGAGEMENT = "engagement"
    QUALITY = "quality"


@dataclass
class EngagementDistribution:
    """互动分布"""
    range_label: str        # 范围标签 如 "0-100", "100-1k"
    count: int              # 帖子数量
    percentage: float       # 占比
    total_engagement: int   # 该范围总互动


@dataclass
class HotWord:
    """热词"""
    word: str
    count: int
    weight: float           # 权重(基于出现次数和互动量)
    related_posts: int      # 相关帖子数


@dataclass
class AuthorStats:
    """作者统计"""
    author: str
    posts_count: int
    total_likes: int
    total_comments: int
    avg_engagement: float
    top_post: str


@dataclass
class TrendPoint:
    """趋势点"""
    label: str              # 标签(如时间点)
    value: float
    change: float = 0       # 变化率


@dataclass
class QualityScore:
    """内容质量评分"""
    post_id: str
    post_title: str
    total_score: float      # 总分 (0-100)
    engagement_score: float # 互动分
    content_score: float    # 内容分
    author_score: float     # 作者影响力分
    viral_potential: str    # 病毒传播潜力: low, medium, high


@dataclass
class StatisticsReport:
    """统计报告"""
    keyword: str
    total_posts: int
    total_likes: int
    total_comments: int
    total_engagement: int
    avg_likes: float
    avg_comments: float
    avg_engagement: float
    max_likes: int
    max_comments: int
    
    # 分布数据
    engagement_distribution: List[EngagementDistribution]
    
    # 热词分析
    hot_words: List[HotWord]
    
    # 标签分析
    top_tags: List[Dict]
    
    # 作者统计
    top_authors: List[AuthorStats]
    
    # 质量评分
    quality_scores: List[QualityScore]
    
    # 洞察
    insights: List[str]
    
    generated_at: str = ""
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


# 中文停用词
STOP_WORDS = {
    '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', '那', '里', '为', '什么', '吗', '个', '能', '么', '做', '被',
    '与', '及', '等', '但', '还', '可以', '这个', '那个', '没', '来', '让', '给',
    '把', '从', '最', '更', '真的', '觉得', '真', '太', '啊', '呢', '吧', '嘛',
    '呀', '哦', '哈', '哈哈', '嗯', '哇', '真的是', '太太太', '超级', '非常',
    '特别', '超', '巨', '绝绝子', '家人们', '姐妹们', '宝子们', '集美们',
}


class AnalyticsService:
    """统计分析服务"""
    
    def __init__(self):
        pass
    
    def _parse_number(self, value: str) -> int:
        """解析数字"""
        if not value:
            return 0
        value = str(value).lower().strip()
        if 'w' in value or '万' in value:
            return int(float(value.replace('w', '').replace('万', '')) * 10000)
        if 'k' in value or '千' in value:
            return int(float(value.replace('k', '').replace('千', '')) * 1000)
        try:
            return int(''.join(filter(str.isdigit, value))) or 0
        except:
            return 0
    
    def _extract_words(self, text: str) -> List[str]:
        """提取中文词汇（简单分词）"""
        if not text:
            return []
        
        # 清理文本
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)
        
        words = []
        
        # 提取2-4字的中文词组
        chinese_text = ''.join(re.findall(r'[\u4e00-\u9fa5]+', text))
        for length in [4, 3, 2]:
            for i in range(len(chinese_text) - length + 1):
                word = chinese_text[i:i+length]
                if word not in STOP_WORDS:
                    words.append(word)
        
        # 提取英文单词
        english_words = re.findall(r'[a-zA-Z]{2,}', text)
        words.extend([w.lower() for w in english_words])
        
        return words
    
    def analyze_engagement_distribution(self, posts: List[Dict]) -> List[EngagementDistribution]:
        """分析互动分布"""
        if not posts:
            return []
        
        # 定义范围
        ranges = [
            (0, 100, "0-100"),
            (100, 500, "100-500"),
            (500, 1000, "500-1k"),
            (1000, 5000, "1k-5k"),
            (5000, 10000, "5k-1w"),
            (10000, 50000, "1w-5w"),
            (50000, float('inf'), "5w+")
        ]
        
        distribution = {r[2]: {'count': 0, 'engagement': 0} for r in ranges}
        
        for post in posts:
            engagement = (
                self._parse_number(post.get('likes', '0')) +
                self._parse_number(post.get('comments', '0'))
            )
            
            for min_val, max_val, label in ranges:
                if min_val <= engagement < max_val:
                    distribution[label]['count'] += 1
                    distribution[label]['engagement'] += engagement
                    break
        
        total = len(posts)
        result = []
        for min_val, max_val, label in ranges:
            data = distribution[label]
            if data['count'] > 0:
                result.append(EngagementDistribution(
                    range_label=label,
                    count=data['count'],
                    percentage=round(data['count'] / total * 100, 1),
                    total_engagement=data['engagement']
                ))
        
        return result
    
    def analyze_hot_words(self, posts: List[Dict], top_n: int = 20) -> List[HotWord]:
        """分析热词"""
        word_stats = {}  # word -> {count, engagement, posts}
        
        for post in posts:
            text = post.get('title', '') + ' ' + post.get('content', '')
            words = self._extract_words(text)
            engagement = self._parse_number(post.get('likes', '0'))
            
            seen_in_post = set()
            for word in words:
                if word not in seen_in_post:
                    seen_in_post.add(word)
                    if word not in word_stats:
                        word_stats[word] = {'count': 0, 'engagement': 0, 'posts': 0}
                    word_stats[word]['posts'] += 1
                word_stats[word]['count'] += 1
                word_stats[word]['engagement'] += engagement
        
        # 计算权重并排序
        hot_words = []
        max_count = max((s['count'] for s in word_stats.values()), default=1)
        max_engagement = max((s['engagement'] for s in word_stats.values()), default=1)
        
        for word, stats in word_stats.items():
            if stats['posts'] >= 2:  # 至少出现在2篇帖子中
                # 权重 = 出现次数 * 0.4 + 互动量 * 0.6 (归一化)
                weight = (
                    (stats['count'] / max_count) * 0.4 +
                    (stats['engagement'] / max_engagement) * 0.6
                )
                hot_words.append(HotWord(
                    word=word,
                    count=stats['count'],
                    weight=round(weight, 3),
                    related_posts=stats['posts']
                ))
        
        hot_words.sort(key=lambda x: x.weight, reverse=True)
        return hot_words[:top_n]
    
    def analyze_tags(self, posts: List[Dict], top_n: int = 10) -> List[Dict]:
        """分析标签"""
        tag_stats = {}  # tag -> {count, engagement}
        
        for post in posts:
            tags = post.get('tags', [])
            engagement = self._parse_number(post.get('likes', '0'))
            
            for tag in tags:
                if tag and len(tag) > 1:
                    if tag not in tag_stats:
                        tag_stats[tag] = {'count': 0, 'engagement': 0}
                    tag_stats[tag]['count'] += 1
                    tag_stats[tag]['engagement'] += engagement
        
        result = [
            {'tag': tag, 'count': stats['count'], 'engagement': stats['engagement']}
            for tag, stats in tag_stats.items()
        ]
        result.sort(key=lambda x: x['engagement'], reverse=True)
        
        return result[:top_n]
    
    def analyze_authors(self, posts: List[Dict], top_n: int = 10) -> List[AuthorStats]:
        """分析作者"""
        author_data = {}  # author -> {posts, likes, comments, top_post}
        
        for post in posts:
            author = post.get('author', '未知')
            if not author or author == '未知':
                continue
            
            likes = self._parse_number(post.get('likes', '0'))
            comments = self._parse_number(post.get('comments', '0'))
            
            if author not in author_data:
                author_data[author] = {
                    'posts': [],
                    'total_likes': 0,
                    'total_comments': 0,
                    'top_post': ('', 0)
                }
            
            author_data[author]['posts'].append(post)
            author_data[author]['total_likes'] += likes
            author_data[author]['total_comments'] += comments
            
            if likes > author_data[author]['top_post'][1]:
                author_data[author]['top_post'] = (post.get('title', '')[:40], likes)
        
        result = []
        for author, data in author_data.items():
            total_engagement = data['total_likes'] + data['total_comments']
            result.append(AuthorStats(
                author=author,
                posts_count=len(data['posts']),
                total_likes=data['total_likes'],
                total_comments=data['total_comments'],
                avg_engagement=round(total_engagement / len(data['posts']), 1),
                top_post=data['top_post'][0]
            ))
        
        result.sort(key=lambda x: x.total_likes, reverse=True)
        return result[:top_n]
    
    def calculate_quality_scores(self, posts: List[Dict]) -> List[QualityScore]:
        """计算内容质量评分"""
        if not posts:
            return []
        
        # 找出最大值用于归一化
        max_likes = max(self._parse_number(p.get('likes', '0')) for p in posts) or 1
        max_comments = max(self._parse_number(p.get('comments', '0')) for p in posts) or 1
        
        scores = []
        for post in posts:
            likes = self._parse_number(post.get('likes', '0'))
            comments = self._parse_number(post.get('comments', '0'))
            title = post.get('title', '')
            content = post.get('content', '')
            
            # 互动分 (0-40)
            engagement_score = (
                (likes / max_likes) * 25 +
                (comments / max_comments) * 15
            )
            
            # 内容分 (0-35)
            content_length = len(title) + len(content)
            title_quality = min(len(title) / 30, 1) * 15  # 标题长度评分
            content_quality = min(content_length / 200, 1) * 10  # 内容丰富度
            emoji_bonus = min(len(re.findall(r'[\U0001F300-\U0001F9FF]', title + content)) * 0.5, 5)
            hashtag_bonus = min(len(post.get('tags', [])) * 1.5, 5)
            content_score = title_quality + content_quality + emoji_bonus + hashtag_bonus
            
            # 作者影响力分 (0-25) - 基于互动率估算
            engagement_rate = (likes + comments * 2) / max(1, likes + 1)
            author_score = min(engagement_rate * 10, 25)
            
            total_score = engagement_score + content_score + author_score
            
            # 病毒传播潜力
            if total_score >= 70:
                viral_potential = "high"
            elif total_score >= 45:
                viral_potential = "medium"
            else:
                viral_potential = "low"
            
            scores.append(QualityScore(
                post_id=post.get('id', ''),
                post_title=title[:50],
                total_score=round(total_score, 1),
                engagement_score=round(engagement_score, 1),
                content_score=round(content_score, 1),
                author_score=round(author_score, 1),
                viral_potential=viral_potential
            ))
        
        scores.sort(key=lambda x: x.total_score, reverse=True)
        return scores
    
    def generate_insights(
        self, 
        posts: List[Dict],
        hot_words: List[HotWord],
        distribution: List[EngagementDistribution],
        authors: List[AuthorStats]
    ) -> List[str]:
        """生成数据洞察"""
        insights = []
        
        if not posts:
            return ["暂无足够数据生成洞察"]
        
        # 总体数据洞察
        total_engagement = sum(
            self._parse_number(p.get('likes', '0')) + 
            self._parse_number(p.get('comments', '0'))
            for p in posts
        )
        avg_engagement = total_engagement / len(posts) if posts else 0
        
        insights.append(f"📊 共分析 {len(posts)} 篇内容，总互动量 {total_engagement:,}")
        
        if avg_engagement > 10000:
            insights.append(f"🔥 平均互动量 {avg_engagement:,.0f}，内容热度极高")
        elif avg_engagement > 1000:
            insights.append(f"✨ 平均互动量 {avg_engagement:,.0f}，内容热度较高")
        
        # 热词洞察
        if hot_words and len(hot_words) >= 3:
            top_words = ', '.join(hw.word for hw in hot_words[:5])
            insights.append(f"💬 热门关键词：{top_words}")
        
        # 分布洞察
        if distribution:
            high_engagement = [d for d in distribution if '1w' in d.range_label or '5w' in d.range_label]
            if high_engagement:
                high_count = sum(d.count for d in high_engagement)
                high_pct = sum(d.percentage for d in high_engagement)
                if high_pct > 20:
                    insights.append(f"🚀 {high_pct:.1f}% 的内容互动量过万，爆款率较高")
        
        # 作者洞察
        if authors and len(authors) >= 1:
            top_author = authors[0]
            insights.append(f"👑 头部创作者「{top_author.author}」贡献了 {top_author.total_likes:,} 点赞")
        
        # 互动比例洞察
        total_likes = sum(self._parse_number(p.get('likes', '0')) for p in posts)
        total_comments = sum(self._parse_number(p.get('comments', '0')) for p in posts)
        if total_likes > 0:
            comment_rate = total_comments / total_likes
            if comment_rate > 0.1:
                insights.append(f"💭 评论率 {comment_rate*100:.1f}%，用户讨论热度高")
        
        return insights
    
    def generate_report(self, posts: List[Dict], keyword: str = "") -> StatisticsReport:
        """生成完整统计报告"""
        if not posts:
            return StatisticsReport(
                keyword=keyword,
                total_posts=0,
                total_likes=0,
                total_comments=0,
                total_engagement=0,
                avg_likes=0,
                avg_comments=0,
                avg_engagement=0,
                max_likes=0,
                max_comments=0,
                engagement_distribution=[],
                hot_words=[],
                top_tags=[],
                top_authors=[],
                quality_scores=[],
                insights=["暂无数据"]
            )
        
        # 基础统计
        likes_list = [self._parse_number(p.get('likes', '0')) for p in posts]
        comments_list = [self._parse_number(p.get('comments', '0')) for p in posts]
        
        total_likes = sum(likes_list)
        total_comments = sum(comments_list)
        total_engagement = total_likes + total_comments
        
        # 分析各项
        distribution = self.analyze_engagement_distribution(posts)
        hot_words = self.analyze_hot_words(posts)
        tags = self.analyze_tags(posts)
        authors = self.analyze_authors(posts)
        quality_scores = self.calculate_quality_scores(posts)
        insights = self.generate_insights(posts, hot_words, distribution, authors)
        
        return StatisticsReport(
            keyword=keyword,
            total_posts=len(posts),
            total_likes=total_likes,
            total_comments=total_comments,
            total_engagement=total_engagement,
            avg_likes=round(total_likes / len(posts), 1),
            avg_comments=round(total_comments / len(posts), 1),
            avg_engagement=round(total_engagement / len(posts), 1),
            max_likes=max(likes_list),
            max_comments=max(comments_list),
            engagement_distribution=distribution,
            hot_words=hot_words,
            top_tags=tags,
            top_authors=authors,
            quality_scores=quality_scores,
            insights=insights
        )
    
    def compare_keywords(
        self, 
        keyword_posts: Dict[str, List[Dict]]
    ) -> Dict:
        """对比多个关键词的数据"""
        comparison = {
            "keywords": [],
            "comparison_chart": [],
            "winner": None,
            "insights": []
        }
        
        keyword_stats = []
        for keyword, posts in keyword_posts.items():
            total_likes = sum(self._parse_number(p.get('likes', '0')) for p in posts)
            total_comments = sum(self._parse_number(p.get('comments', '0')) for p in posts)
            
            stat = {
                "keyword": keyword,
                "posts_count": len(posts),
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_engagement": total_likes + total_comments,
                "avg_engagement": round((total_likes + total_comments) / len(posts), 1) if posts else 0
            }
            keyword_stats.append(stat)
            comparison["keywords"].append(keyword)
        
        # 排序找出赢家
        keyword_stats.sort(key=lambda x: x['total_engagement'], reverse=True)
        comparison["comparison_chart"] = keyword_stats
        
        if keyword_stats:
            comparison["winner"] = keyword_stats[0]["keyword"]
            
            # 生成对比洞察
            if len(keyword_stats) >= 2:
                first = keyword_stats[0]
                second = keyword_stats[1]
                ratio = first['total_engagement'] / max(second['total_engagement'], 1)
                comparison["insights"].append(
                    f"「{first['keyword']}」热度领先，是「{second['keyword']}」的 {ratio:.1f} 倍"
                )
        
        return comparison


def report_to_dict(report: StatisticsReport) -> Dict:
    """转换报告为字典（用于JSON序列化）"""
    return {
        "keyword": report.keyword,
        "total_posts": report.total_posts,
        "total_likes": report.total_likes,
        "total_comments": report.total_comments,
        "total_engagement": report.total_engagement,
        "avg_likes": report.avg_likes,
        "avg_comments": report.avg_comments,
        "avg_engagement": report.avg_engagement,
        "max_likes": report.max_likes,
        "max_comments": report.max_comments,
        "engagement_distribution": [asdict(d) for d in report.engagement_distribution],
        "hot_words": [asdict(hw) for hw in report.hot_words],
        "top_tags": report.top_tags,
        "top_authors": [asdict(a) for a in report.top_authors],
        "quality_scores": [asdict(q) for q in report.quality_scores],
        "insights": report.insights,
        "generated_at": report.generated_at
    }


async def main():
    """测试统计分析"""
    # 模拟数据
    sample_posts = [
        {"id": "1", "title": "超好用的护肤品推荐！敏感肌必入 🌟", "content": "分享我的护肤心得...", "author": "美妆达人", "likes": "2.3w", "comments": "1234", "tags": ["护肤", "敏感肌"]},
        {"id": "2", "title": "这款面霜真的绝了！平价好用", "content": "用了一个月效果超棒...", "author": "小红薯", "likes": "8500", "comments": "432", "tags": ["护肤", "面霜"]},
        {"id": "3", "title": "护肤新手入门指南", "content": "刚开始护肤的姐妹看过来...", "author": "护肤小课堂", "likes": "1.5w", "comments": "876", "tags": ["护肤", "新手"]},
    ]
    
    service = AnalyticsService()
    report = service.generate_report(sample_posts, "护肤品")
    
    print("📊 统计报告")
    print("=" * 50)
    print(f"关键词: {report.keyword}")
    print(f"帖子数: {report.total_posts}")
    print(f"总点赞: {report.total_likes:,}")
    print(f"总评论: {report.total_comments:,}")
    print(f"平均互动: {report.avg_engagement:,.1f}")
    
    print("\n🔥 热词:")
    for hw in report.hot_words[:5]:
        print(f"  • {hw.word}: {hw.count}次, 权重 {hw.weight}")
    
    print("\n📈 洞察:")
    for insight in report.insights:
        print(f"  {insight}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

