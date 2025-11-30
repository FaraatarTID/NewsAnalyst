import asyncio
import logging
import sys
import os
from datetime import datetime

# Ensure UTF-8 encoding for console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path if needed (for local execution)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import load_config
from app.services.rss import RSSService
from app.services.brave_search import BraveSearchService
from app.services.jina_reader import JinaReaderService
from app.services.ai import AIService
from app.services.telegram import TelegramService
from app.models import Stats, IntelligenceCategory


# Configure logging with UTF-8 support
file_handler = logging.FileHandler("execution.log", encoding='utf-8')
stream_handler = logging.StreamHandler(sys.stdout)

# On Windows, sys.stdout might not handle emojis well depending on the terminal
# We'll try to set encoding if possible, or just be careful with emojis in console logs
if sys.platform == "win32":
    stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[stream_handler, file_handler]
)
logger = logging.getLogger("MarketIntelligence")

async def main(custom_topic: str = None):
    # 1. Load Configuration
    try:
        settings = load_config()
        
        # Override settings if custom topic is provided
        if custom_topic:
            logger.info(f"🎯 Custom topic received: {custom_topic}")
            settings.industry_keywords = [custom_topic]
            settings.target_markets = [] # Clear markets to trigger "past month" freshness in Brave service
            settings.rss_feeds = [] # Disable default RSS feeds
            
        if settings.debug_mode:
            logger.setLevel(logging.DEBUG)
        logger.info("⚙️ Configuration loaded successfully")
    except Exception as e:
        logger.critical(f"Failed to load configuration: {e}")
        sys.exit(1)

    # 2. Initialize Services
    try:
        rss_service = RSSService(settings)
        brave_service = BraveSearchService(settings) if settings.enable_brave_search else None
        jina_service = JinaReaderService() if settings.enable_jina_reader else None
        ai_service = AIService(settings)
        telegram_service = TelegramService(settings)
        
        stats = Stats()
        logger.info("🚀 Starting Market Intelligence Bot")
        logger.info(f"📊 Intelligence Sources: Brave={'✅' if settings.enable_brave_search else '❌'}, RSS={'✅' if settings.enable_rss else '❌'}, Jina={'✅' if settings.enable_jina_reader else '❌'}")
    except Exception as e:
        logger.critical(f"❌ Failed to initialize services: {e}")
        sys.exit(1)

    # 3. Collect Intelligence from Multiple Sources
    all_articles = []
    
    # Collect from Brave Search
    if brave_service and settings.enable_brave_search:
        try:
            logger.info("🔍 Collecting intelligence from Brave Search...")
            brave_articles = await brave_service.search_industry_news()
            all_articles.extend(brave_articles)
            logger.info(f"✅ Brave Search: {len(brave_articles)} articles")
        except Exception as e:
            logger.error(f"❌ Brave Search failed: {e}")
    
    # Collect from RSS Feeds
    if settings.enable_rss:
        try:
            logger.info("📡 Collecting intelligence from RSS feeds...")
            rss_articles = await rss_service.fetch_all()
            all_articles.extend(rss_articles)
            logger.info(f"✅ RSS Feeds: {len(rss_articles)} articles")
        except Exception as e:
            logger.error(f"❌ RSS collection failed: {e}")
    
    # Deduplicate articles by URL
    unique_articles = {article.link: article for article in all_articles}
    articles = list(unique_articles.values())
    
    stats.total_articles = len(articles)
    logger.info(f"📰 Total unique articles collected: {stats.total_articles}")
    
    if not articles:
        logger.warning("⚠️ No articles found to process.")
        await telegram_service.send_message("⚠️ هیچ اطلاعاتی برای تحلیل یافت نشد.")
        return

    # 3.5. Enrich articles with full content using Jina Reader (if enabled)
    if jina_service and settings.enable_jina_reader:
        try:
            logger.info("📖 Enriching articles with Jina Reader...")
            articles = await jina_service.enrich_articles(articles, max_concurrent=3)
            logger.info(f"✅ Content enrichment complete")
        except Exception as e:
            logger.warning(f"⚠️ Jina Reader enrichment failed (continuing anyway): {e}")

    # 4. Analyze and Report
    # Process articles concurrently with a semaphore to control concurrency
    semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent tasks

    async def process_article(index: int, article):
        async with semaphore:
            logger.info(f"📄 Processing {index}/{len(articles)}: {article.title[:60]}...")
            try:
                analysis = await ai_service.analyze_article(article)
                
                if analysis:
                    # Track by category
                    category = analysis.category or IntelligenceCategory.OTHER
                    stats.by_category[category.value] = stats.by_category.get(category.value, 0) + 1
                    
                    # Track high priority items
                    if analysis.importance_score and analysis.importance_score >= 7:
                        stats.high_priority_count += 1
                    
                    # Send to Telegram
                    if await telegram_service.send_report(analysis):
                        logger.info(f"✅ Article {index} processed (Category: {category.value}, Score: {analysis.importance_score}/10)")
                        return True
            except Exception as e:
                logger.error(f"❌ Error processing article {index}: {e}")
            return False

    tasks = [process_article(i, article) for i, article in enumerate(articles, 1)]
    results = await asyncio.gather(*tasks)
    
    stats.processed = sum(1 for r in results if r)
    stats.failed = len(articles) - stats.processed

    # 5. Send Summary
    stats.end_time = datetime.now()
    duration = (stats.end_time - stats.start_time).total_seconds()
    
    # Build category breakdown
    category_breakdown = "\n".join([
        f"   • {cat.replace('_', ' ').title()}: {count}"
        for cat, count in sorted(stats.by_category.items(), key=lambda x: x[1], reverse=True)
    ])
    
    summary_text = f"""
📊 <b>گزارش تحلیل هوشمند بازار</b>

✅ وضعیت: تکمیل شد
📰 کل مقالات: {stats.total_articles}
✅ تحلیل شده: {stats.processed}
❌ ناموفق: {stats.failed}
⭐ اولویت بالا (≥7): {stats.high_priority_count}
⏱ مدت زمان: {duration:.2f}s

📂 <b>دسته‌بندی:</b>
{category_breakdown if category_breakdown else '   هیچ دسته‌بندی ثبت نشده'}

🎯 <b>منابع:</b>
   • Brave Search: {'✅' if settings.enable_brave_search else '❌'}
   • RSS Feeds: {'✅' if settings.enable_rss else '❌'}
   • Jina Reader: {'✅' if settings.enable_jina_reader else '❌'}
"""
    await telegram_service.send_message(summary_text, parse_mode='HTML')
    logger.info("✨ Execution finished successfully")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Execution interrupted by user")
    except Exception as e:
        logger.critical(f"💥 Critical Error: {e}", exc_info=True)
        sys.exit(1)