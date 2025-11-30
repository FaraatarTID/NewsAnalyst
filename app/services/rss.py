import feedparser
import aiohttp
import asyncio
import logging
from typing import List
from app.models import NewsArticle
from app.config import Settings

logger = logging.getLogger("NewsAnalyst.RSS")

class RSSService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def fetch_feed(self, session: aiohttp.ClientSession, url: str) -> List[NewsArticle]:
        """Fetch and parse a single RSS feed asynchronously."""
        logger.info(f"📡 Fetching feed: {url}")
        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    logger.warning(f"⚠️ Failed to fetch {url}: Status {response.status}")
                    return []
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                if not feed.entries:
                    logger.warning(f"⚠️ No entries found in {url}")
                    return []
                
                articles = []
                for entry in feed.entries[:self.settings.news_count]:
                    articles.append(NewsArticle(
                        title=entry.title,
                        link=entry.link,
                        published=entry.get('published', 'N/A'),
                        source=feed.feed.get('title', 'Unknown')
                    ))
                return articles
                
        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout fetching {url}")
            return []
        except aiohttp.ClientError as e:
            logger.error(f"❌ Network error fetching {url}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching {url}: {e}", exc_info=True)
            return []

    async def fetch_all(self) -> List[NewsArticle]:
        """Fetch news from all configured feeds concurrently."""
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_feed(session, url) for url in self.settings.rss_feeds]
            results = await asyncio.gather(*tasks)
            
            # Flatten list of lists
            all_articles = [article for sublist in results for article in sublist]
            
            # Deduplicate by link
            unique_articles = {article.link: article for article in all_articles}
            
            # Sort by published date (if parseable) or just take top N overall
            # For simplicity, we'll just return the list, maybe limited by total count if needed
            # But usually we want to analyze what we fetched.
            
            logger.info(f"📰 Total unique articles fetched: {len(unique_articles)}")
            return list(unique_articles.values())
