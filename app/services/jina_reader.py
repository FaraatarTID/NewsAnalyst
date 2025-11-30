import aiohttp
import asyncio
import logging
from typing import Optional
from app.models import NewsArticle

logger = logging.getLogger("MarketIntelligence.JinaReader")

class JinaReaderService:
    """Service for extracting clean content from URLs using Jina AI Reader (free, no API key)."""
    
    def __init__(self):
        self.base_url = "https://r.jina.ai/"
        
    async def read_url(self, url: str) -> Optional[str]:
        """
        Extract clean, readable content from a URL using Jina AI Reader.
        
        Args:
            url: The URL to read
            
        Returns:
            Clean text content or None if failed
        """
        jina_url = f"{self.base_url}{url}"
        logger.debug(f"📖 Reading URL with Jina: {url[:60]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    jina_url,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️ Jina Reader failed for {url}: Status {response.status}")
                        return None
                    
                    content = await response.text()
                    
                    if not content or len(content) < 100:
                        logger.warning(f"⚠️ Jina Reader returned minimal content for {url}")
                        return None
                    
                    logger.debug(f"✅ Jina Reader extracted {len(content)} chars from {url[:60]}")
                    return content
                    
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ Jina Reader timeout for {url}")
            return None
        except aiohttp.ClientError as e:
            logger.warning(f"⚠️ Jina Reader network error for {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Jina Reader unexpected error for {url}: {e}")
            return None
    
    async def enrich_article(self, article: NewsArticle) -> NewsArticle:
        """
        Enrich a NewsArticle with full content using Jina Reader.
        
        Args:
            article: NewsArticle to enrich
            
        Returns:
            Enriched NewsArticle with content field populated
        """
        if article.content and len(article.content) > 500:
            # Already has good content
            return article
        
        # Try to get full content
        full_content = await self.read_url(article.link)
        
        if full_content:
            article.content = full_content[:2000]  # Limit to 2000 chars to avoid token limits
            logger.info(f"✅ Enriched article: {article.title[:60]}...")
        
        return article
    
    async def enrich_articles(self, articles: list[NewsArticle], max_concurrent: int = 3) -> list[NewsArticle]:
        """
        Enrich multiple articles with full content.
        
        Args:
            articles: List of NewsArticles to enrich
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of enriched NewsArticles
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def enrich_with_limit(article: NewsArticle):
            async with semaphore:
                await asyncio.sleep(0.5)  # Rate limiting
                return await self.enrich_article(article)
        
        logger.info(f"📖 Enriching {len(articles)} articles with Jina Reader...")
        tasks = [enrich_with_limit(article) for article in articles]
        enriched = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        result = []
        for item in enriched:
            if isinstance(item, NewsArticle):
                result.append(item)
            elif isinstance(item, Exception):
                logger.warning(f"⚠️ Failed to enrich article: {item}")
        
        enriched_count = sum(1 for a in result if a.content and len(a.content) > 500)
        logger.info(f"✅ Successfully enriched {enriched_count}/{len(articles)} articles")
        
        return result
