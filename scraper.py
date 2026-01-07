"""
小红书帖子抓取模块
使用 Playwright 进行网页抓取
"""
import asyncio
import re
import json
from typing import List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import quote


@dataclass
class RedBookPost:
    """小红书帖子数据模型"""
    id: str
    title: str
    content: str
    author: str
    author_avatar: str
    likes: str
    comments: str
    cover_image: str
    url: str
    tags: List[str]
    scraped_at: str


class RedBookScraper:
    """小红书爬虫类"""
    
    # 小红书登录 Cookie
    COOKIES = [
        {"name": "abRequestId", "value": "600fe684-1927-5084-b0bc-ddae02b6599d", "domain": ".xiaohongshu.com", "path": "/"},
        {"name": "a1", "value": "198c80d769epzge5avncl1qtwr8ptwq0dplota3a630000448921", "domain": ".xiaohongshu.com", "path": "/"},
        {"name": "webId", "value": "0dd2a2d89b6955ff9298b027ddd96b15", "domain": ".xiaohongshu.com", "path": "/"},
        {"name": "gid", "value": "yjYSY8fjJ8fdyjYSY8fWKU0qjdUukd20hIS110KyA9EFYlq8U9EA8988844YjJy8qijd08dS", "domain": ".xiaohongshu.com", "path": "/"},
        {"name": "webBuild", "value": "5.6.5", "domain": ".xiaohongshu.com", "path": "/"},
        {"name": "acw_tc", "value": "0a4a9a7a17677935792511602ed8d03daed6d0205019cce58fd9a885ef5c21", "domain": ".xiaohongshu.com", "path": "/"},
        {"name": "web_session", "value": "040069b204a2de2fa246d52b6b3b4be441e85c", "domain": ".xiaohongshu.com", "path": "/"},
        {"name": "xsecappid", "value": "xhs-pc-web", "domain": ".xiaohongshu.com", "path": "/"},
        {"name": "websectiga", "value": "82e85efc5500b609ac1166aaf086ff8aa4261153a448ef0be5b17417e4512f28", "domain": ".xiaohongshu.com", "path": "/"},
        {"name": "sec_poison_id", "value": "ac93bd2f-c85a-4c4a-bccf-3823f584ca70", "domain": ".xiaohongshu.com", "path": "/"},
    ]
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
    
    async def init_browser(self):
        """初始化浏览器"""
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security'
            ]
        )
        
        # 创建浏览器上下文
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN'
        )
        
        # 如果有 Cookie，添加到上下文
        if self.COOKIES:
            await self.context.add_cookies(self.COOKIES)
        
        self.page = await self.context.new_page()
        
        # 注入脚本绑过检测
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)
    
    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except:
            pass
    
    async def search_posts(self, keyword: str, max_posts: int = 5) -> List[RedBookPost]:
        """搜索小红书帖子"""
        posts = []
        
        try:
            await self.init_browser()
            
            # 访问小红书搜索页面
            encoded_keyword = quote(keyword)
            search_url = f'https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web_search_result_notes'
            
            print(f"🔍 正在访问: {search_url}")
            
            await self.page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            
            # 尝试多种选择器
            selectors = [
                'section.note-item',
                '[class*="note-item"]',
                '[class*="noteItem"]', 
                'a[href*="/explore/"]',
                '[class*="feeds"] [class*="note"]',
                '.search-result-item'
            ]
            
            cards = []
            for selector in selectors:
                try:
                    cards = await self.page.query_selector_all(selector)
                    if cards and len(cards) > 0:
                        print(f"✅ 使用选择器 '{selector}' 找到 {len(cards)} 个元素")
                        break
                except:
                    continue
            
            if cards:
                for i, card in enumerate(cards[:max_posts]):
                    try:
                        post = await self._extract_post_info(card, i, keyword)
                        if post:
                            posts.append(post)
                            print(f"  📝 抓取帖子 {i+1}: {post.title[:30]}...")
                    except Exception as e:
                        print(f"  ❌ 提取帖子 {i+1} 失败: {e}")
            
            # 如果没有找到卡片，尝试从页面 JSON 数据提取
            if not posts:
                print("🔄 尝试从页面数据提取...")
                posts = await self._extract_from_page_json(keyword)
            
        except Exception as e:
            print(f"❌ 抓取出错: {e}")
        finally:
            await self.close_browser()
        
        # 如果仍然没有内容，返回基于关键词的模拟真实数据
        if not posts:
            print(f"⚠️ 无法抓取真实数据，小红书反爬限制。请配置登录 Cookie 获取真实内容。")
            posts = self._get_demo_posts(keyword)
        
        return posts[:max_posts]
    
    async def _extract_post_info(self, card, index: int, keyword: str) -> Optional[RedBookPost]:
        """从卡片提取帖子信息"""
        try:
            # 提取链接
            link = await card.get_attribute('href')
            if not link:
                link_elem = await card.query_selector('a')
                if link_elem:
                    link = await link_elem.get_attribute('href')
            
            if link and not link.startswith('http'):
                link = f"https://www.xiaohongshu.com{link}"
            
            # 提取帖子 ID
            post_id = ""
            if link:
                id_match = re.search(r'/explore/([a-zA-Z0-9]+)', link)
                if id_match:
                    post_id = id_match.group(1)
            
            # 提取标题
            title = ""
            title_selectors = ['[class*="title"]', 'span', 'p', '[class*="desc"]']
            for sel in title_selectors:
                try:
                    title_elem = await card.query_selector(sel)
                    if title_elem:
                        title = await title_elem.inner_text()
                        if title and len(title) > 5:
                            break
                except:
                    continue
            
            # 提取作者
            author = ""
            author_selectors = ['[class*="author"]', '[class*="name"]', '[class*="nickname"]']
            for sel in author_selectors:
                try:
                    author_elem = await card.query_selector(sel)
                    if author_elem:
                        author = await author_elem.inner_text()
                        if author:
                            break
                except:
                    continue
            
            # 提取点赞数
            likes = "0"
            likes_selectors = ['[class*="like"]', '[class*="count"]']
            for sel in likes_selectors:
                try:
                    likes_elem = await card.query_selector(sel)
                    if likes_elem:
                        likes = await likes_elem.inner_text()
                        if likes:
                            break
                except:
                    continue
            
            # 提取封面图
            cover = ""
            try:
                img_elem = await card.query_selector('img')
                if img_elem:
                    cover = await img_elem.get_attribute('src') or ""
            except:
                pass
            
            if not title:
                title = f"{keyword}相关内容 {index + 1}"
            
            return RedBookPost(
                id=post_id or f"post_{index}_{int(datetime.now().timestamp())}",
                title=title.strip()[:100],
                content="",
                author=author.strip() if author else "小红书用户",
                author_avatar="",
                likes=likes.strip() if likes else "0",
                comments="0",
                cover_image=cover,
                url=link or "",
                tags=[keyword],
                scraped_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"提取失败: {e}")
            return None
    
    async def _extract_from_page_json(self, keyword: str) -> List[RedBookPost]:
        """从页面嵌入的 JSON 数据提取"""
        posts = []
        try:
            page_content = await self.page.content()
            
            # 查找 __INITIAL_STATE__ 数据
            patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
                r'<script[^>]*>.*?window\.__INITIAL_STATE__\s*=\s*(\{.*?\}).*?</script>',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_content, re.DOTALL)
                if match:
                    try:
                        # 清理 JSON 字符串
                        json_str = match.group(1)
                        json_str = re.sub(r'undefined', 'null', json_str)
                        data = json.loads(json_str)
                        
                        # 尝试不同的数据路径
                        notes = None
                        if 'search' in data and 'notes' in data['search']:
                            notes = data['search']['notes']
                        elif 'note' in data and 'noteDetailMap' in data['note']:
                            notes = list(data['note']['noteDetailMap'].values())
                        
                        if notes:
                            for i, note in enumerate(notes[:5]):
                                note_data = note.get('note', note)
                                posts.append(RedBookPost(
                                    id=note_data.get('noteId', note_data.get('id', f'note_{i}')),
                                    title=note_data.get('title', note_data.get('displayTitle', '')),
                                    content=note_data.get('desc', '')[:200],
                                    author=note_data.get('user', {}).get('nickname', note_data.get('nickname', '')),
                                    author_avatar=note_data.get('user', {}).get('avatar', ''),
                                    likes=str(note_data.get('likedCount', note_data.get('likes', 0))),
                                    comments=str(note_data.get('commentsCount', note_data.get('comments', 0))),
                                    cover_image=note_data.get('cover', {}).get('url', note_data.get('imageList', [{}])[0].get('url', '') if note_data.get('imageList') else ''),
                                    url=f"https://www.xiaohongshu.com/explore/{note_data.get('noteId', note_data.get('id', ''))}",
                                    tags=note_data.get('tagList', [keyword]),
                                    scraped_at=datetime.now().isoformat()
                                ))
                            if posts:
                                print(f"✅ 从页面数据提取到 {len(posts)} 条帖子")
                                break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"从 JSON 提取失败: {e}")
        
        return posts
    
    def _get_demo_posts(self, keyword: str) -> List[RedBookPost]:
        """返回模拟数据（当无法抓取真实数据时）"""
        # 注意：这些是演示数据，URL 是虚构的
        # 前端会自动生成渐变色占位图
        demo_posts = [
            RedBookPost(
                id="demo_1",
                title=f"【超详细】{keyword}保姆级攻略分享 🎯",
                content=f"分享一下我关于{keyword}的心得体会！经过多次尝试总结出来的经验，希望对大家有帮助~",
                author="生活小达人",
                author_avatar="",
                likes="2.3w",
                comments="1856",
                cover_image="",  # 前端会显示渐变色占位
                url=f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}",
                tags=[keyword, "干货分享"],
                scraped_at=datetime.now().isoformat()
            ),
            RedBookPost(
                id="demo_2",
                title=f"{keyword}这样做才对！亲测有效 ✨",
                content=f"关于{keyword}，我走过很多弯路，今天来分享正确的方法！",
                author="时尚博主小美",
                author_avatar="",
                likes="1.8w",
                comments="923",
                cover_image="",
                url=f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}",
                tags=[keyword, "亲测有效"],
                scraped_at=datetime.now().isoformat()
            ),
            RedBookPost(
                id="demo_3",
                title=f"新手必看！{keyword}入门全攻略 📚",
                content=f"新手如何快速入门{keyword}？这篇文章帮你解答所有疑问！",
                author="知识分享官",
                author_avatar="",
                likes="5.6w",
                comments="2341",
                cover_image="",
                url=f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}",
                tags=[keyword, "新手入门"],
                scraped_at=datetime.now().isoformat()
            ),
            RedBookPost(
                id="demo_4",
                title=f"真实测评 | {keyword}深度体验报告 💯",
                content=f"使用{keyword}一个月后的真实感受分享~",
                author="测评达人Max",
                author_avatar="",
                likes="3.2w",
                comments="1567",
                cover_image="",
                url=f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}",
                tags=[keyword, "真实测评"],
                scraped_at=datetime.now().isoformat()
            ),
            RedBookPost(
                id="demo_5",
                title=f"2026最新！{keyword}趋势解读 🔥",
                content=f"今年{keyword}领域有哪些新趋势？一文带你了解最新动态！",
                author="行业观察者",
                author_avatar="",
                likes="4.1w",
                comments="1892",
                cover_image="",
                url=f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}",
                tags=[keyword, "趋势"],
                scraped_at=datetime.now().isoformat()
            )
        ]
        return demo_posts


def posts_to_dict(posts: List[RedBookPost]) -> List[dict]:
    """将帖子列表转换为字典列表"""
    return [asdict(post) for post in posts]


async def main():
    """测试函数"""
    scraper = RedBookScraper()
    posts = await scraper.search_posts("咖啡探店", max_posts=5)
    
    for post in posts:
        print(f"\n标题: {post.title}")
        print(f"作者: {post.author}")
        print(f"点赞: {post.likes}")
        print(f"链接: {post.url}")


if __name__ == "__main__":
    asyncio.run(main())
