import aiohttp
import asyncio
import logging
from typing import List, Optional
from app.models import NewsArticle
from app.config import Settings

logger = logging.getLogger("MarketIntelligence.BraveSearch")

class BraveSearchService:
    """Service for collecting intelligence using Brave Search API."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.brave_api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        
    async def search(self, query: str, count: Optional[int] = None, freshness: str = "pw") -> List[NewsArticle]:
        """
        Execute a search query using Brave Search API.
        
        Args:
            query: Search query string
            count: Number of results to return (defaults to settings.brave_search_count)
            freshness: Time range for search ('pw' = past week, 'pm' = past month, None = no limit)
            
        Returns:
            List of NewsArticle objects
        """
        if not count:
            count = self.settings.brave_search_count
            
        logger.info(f"🔍 Brave Search: {query} (freshness={freshness})")
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": count,
            "search_lang": "en"
        }
        
        if freshness:
            params["freshness"] = freshness
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status != 200:
                        logger.error(f"❌ Brave Search API error: {response.status}")
                        return []
                    
                    data = await response.json()
                    return self._parse_results(data, query)
                    
        except asyncio.TimeoutError:
            logger.error(f"❌ Brave Search timeout for query: {query}")
            return []
        except aiohttp.ClientError as e:
            logger.error(f"❌ Brave Search network error: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Brave Search unexpected error: {e}", exc_info=True)
            return []
    
    def _parse_results(self, data: dict, query: str) -> List[NewsArticle]:
        """Parse Brave Search API response into NewsArticle objects."""
        articles = []
        
        # Brave Search returns results in 'web' key
        web_results = data.get("web", {}).get("results", [])
        
        for result in web_results:
            try:
                article = NewsArticle(
                    title=result.get("title", "No Title"),
                    link=result.get("url", ""),
                    published=result.get("age", "Unknown"),  # Brave returns relative age
                    source=result.get("meta_url", {}).get("hostname", "Unknown"),
                    snippet=result.get("description", ""),
                    content=result.get("description", "")  # Use description as content preview
                )
                articles.append(article)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse Brave Search result: {e}")
                continue
        
        logger.info(f"✅ Brave Search returned {len(articles)} results for: {query}")
        return articles
    
    async def search_industry_news(self) -> List[NewsArticle]:
        """
        Search for industry-specific news using configured keywords and markets.
        
        Returns:
            Aggregated list of NewsArticle objects from multiple searches
        """
        all_articles = []
        
        # Detect custom topic mode (no target markets configured)
        is_custom_topic = len(self.settings.target_markets) == 0
        # Use 'past month' for custom topics to ensure results, 'past week' for daily updates
        freshness = "pm" if is_custom_topic else "pw"
        
        # Build search queries combining keywords with target markets
        queries = []
        
        # General industry queries
        for keyword in self.settings.industry_keywords[:3]:  # Limit to top 3 keywords
            queries.append(keyword)
        
        # Regional queries
        for market in self.settings.target_markets[:3]:  # Limit to top 3 markets
            queries.append(f"recycling {market}")
            queries.append(f"waste management {market}")
        
        # Company-specific queries if watchlist exists
        for company in self.settings.company_watchlist[:5]:  # Limit to 5 companies
            queries.append(company)
        
        # Execute searches concurrently with rate limiting
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
        
        async def search_with_limit(query: str):
            async with semaphore:
                await asyncio.sleep(0.5)  # Rate limiting: 500ms between requests
                return await self.search(query, count=5, freshness=freshness)
        
        tasks = [search_with_limit(q) for q in queries[:10]]  # Limit total queries
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"⚠️ Search query failed: {result}")
        
        # Deduplicate by URL
        unique_articles = {article.link: article for article in all_articles}
        final_articles = list(unique_articles.values())
        
        logger.info(f"📊 Total unique articles from Brave Search: {len(final_articles)}")
        return final_articles
    
    async def search_company(self, company_name: str) -> List[NewsArticle]:
        """
        Search for news about a specific company.
        
        Args:
            company_name: Name of the company to search for
            
        Returns:
            List of NewsArticle objects related to the company
        """
        query = f'"{company_name}" (funding OR investment OR partnership OR expansion)'
        return await self.search(query, count=10)
    
    async def search_regulatory(self, country: str) -> List[NewsArticle]:
        """
        Search for regulatory changes in a specific country.
        
        Args:
            country: Country name
            
        Returns:
            List of NewsArticle objects about regulations
        """
        query = f'{country} (regulation OR policy OR law) (waste OR recycling OR environment)'
        return await self.search(query, count=5)
