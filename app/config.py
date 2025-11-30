from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os

class Settings(BaseSettings):
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    
    # Telegram Settings (Flattened for easier env loading)
    telegram_token: str = Field(..., env="TELEGRAM_TOKEN")
    telegram_chat_id: str = Field(..., env="TELEGRAM_CHAT_ID")
    
    # Brave Search API (Primary Intelligence Source)
    brave_api_key: str = Field(..., env="BRAVE_API_KEY")
    brave_search_count: int = Field(10, env="BRAVE_SEARCH_COUNT")  # Results per query
    
    # Market Intelligence Focus
    target_markets: List[str] = Field(
        default=[
            # Middle East
            "UAE", "Saudi Arabia", "Egypt", "Jordan", "Iran",
            "Qatar", "Kuwait", "Bahrain", "Oman", "Lebanon",
            # Asia
            "China",
            # CIS Countries (Commonwealth of Independent States)
            "Russia", "Kazakhstan", "Uzbekistan", "Azerbaijan", "Armenia",
            "Belarus", "Kyrgyzstan", "Tajikistan", "Turkmenistan", "Moldova"
        ],
        env="TARGET_MARKETS"
    )
    
    industry_keywords: List[str] = Field(
        default=[
            "tire recycling", "crumb rubber", "waste management",
            "circular economy", "recycling technology", "social impact",
            "sustainable waste", "environmental innovation"
        ],
        env="INDUSTRY_KEYWORDS"
    )
    
    # Company Watchlist (can be updated later)
    company_watchlist: List[str] = Field(
        default=[],
        env="COMPANY_WATCHLIST"
    )
    
    # RSS Feeds (Industry-specific)
    rss_feeds: List[str] = Field(
        default=[
            "https://waste-management-world.com/feed/",
            "https://www.recyclingtoday.com/rss.xml",
            "https://resource-recycling.com/feed/",
            "https://www.waste360.com/rss.xml",
            "https://english.alarabiya.net/rss.xml",
            "https://news.google.com/rss/search?q=tire+recycling+Middle+East&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=waste+management+UAE+Saudi+Arabia&hl=en-US&gl=US&ceid=US:en"
        ],
        env="RSS_FEEDS"
    )
    
    # App Settings
    news_count: int = Field(5, env="NEWS_COUNT")  # Increased for more coverage
    debug_mode: bool = Field(False, env="DEBUG_MODE")
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay: int = Field(5, env="RETRY_DELAY")
    
    # Intelligence Collection Settings
    enable_brave_search: bool = Field(True, env="ENABLE_BRAVE_SEARCH")
    enable_rss: bool = Field(True, env="ENABLE_RSS")
    enable_jina_reader: bool = Field(True, env="ENABLE_JINA_READER")  # Free content extraction
    enable_web_scraping: bool = Field(False, env="ENABLE_WEB_SCRAPING")  # Disabled initially
    
    # Alert Thresholds
    alert_on_funding: bool = Field(True, env="ALERT_ON_FUNDING")
    alert_on_regulation: bool = Field(True, env="ALERT_ON_REGULATION")
    alert_on_competitor_move: bool = Field(True, env="ALERT_ON_COMPETITOR_MOVE")
    
    # AI Settings
    ai_model: str = Field("gemini-2.0-flash", env="AI_MODEL")
    ai_prompt_template: str = Field(
        """
        You are a market intelligence analyst specializing in social impact ventures in the recycling industry, 
        particularly tire recycling and waste management in developing countries (Middle East focus).
        
        Analyze the following content and provide a comprehensive intelligence report in Persian (Farsi).
        
        Output format must be EXACTLY as follows (use emojis and HTML tags):
        
        🎯 <b>[Translated Title]</b>
        
        📊 <b>نوع اطلاعات:</b>
        [Categorize as: خبر صنعت | تغییرات قانونی | فعالیت رقبا | روند بازار | فرصت سرمایه‌گذاری]
        
        📝 <b>خلاصه:</b>
        [A comprehensive summary focusing on market intelligence value]
        
        💡 <b>تحلیل تاثیر:</b>
        [Impact on social impact recycling ventures, investment thesis, market dynamics]
        
        🔍 <b>فرصت‌ها و ریسک‌ها:</b>
        [Opportunities for investment/partnership and potential risks]
        
        🏢 <b>شرکت‌ها/بازیگران کلیدی:</b>
        [Mention any companies, investors, or key stakeholders]
        
        🌍 <b>منطقه جغرافیایی:</b>
        [Geographic relevance - which countries/regions]
        
        🎯 <b>کلمات کلیدی:</b>
        [5-7 relevant keywords]
        
        🏷 <b>تگ‌ها:</b> #tag1 #tag2 #tag3
        
        ⭐ <b>امتیاز اهمیت:</b> [1-10]/10
        [Rate importance for a PE fund manager focused on social impact recycling]
        
        IMPORTANT: 
        - Use HTML tags: <b>text</b> for bold, <i>text</i> for italic
        - Do NOT use Markdown (**text** or _text_)
        - In hashtags, avoid underscores and special characters
        - Focus on actionable intelligence for investment decisions
        
        ---
        Original Title: {title}
        Original Link: {link}
        Published: {published}
        Source: {source}
        Content Preview: {content}
        """,
        env="AI_PROMPT_TEMPLATE"
    )

    class Config:
        env_file = ".env"
        extra = "ignore"

def load_config() -> Settings:
    """Load settings from environment variables and optional config file."""
    return Settings()
