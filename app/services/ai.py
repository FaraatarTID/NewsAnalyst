import google.generativeai as genai
import logging
import asyncio
import re
from typing import Optional
from app.models import NewsArticle, AnalysisResult, IntelligenceCategory
from app.config import Settings

logger = logging.getLogger("MarketIntelligence.AI")

class AIService:
    def __init__(self, settings: Settings):
        self.settings = settings
        try:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.ai_model)
            logger.info(f"✅ Gemini model configured: {settings.ai_model}")
        except Exception as e:
            logger.error(f"❌ Gemini configuration failed: {e}")
            raise

    async def analyze_article(self, article: NewsArticle) -> Optional[AnalysisResult]:
        """Analyze a news article using Gemini for market intelligence."""
        logger.debug(f"🔍 Analyzing: {article.title[:50]}...")
        
        try:
            # Prepare content for analysis
            content = article.content or article.snippet or article.title
            
            prompt = self.settings.ai_prompt_template.format(
                title=article.title,
                link=article.link,
                published=article.published,
                source=article.source,
                content=content[:500]  # Limit content to 500 chars to avoid token limits
            )
        except KeyError as e:
            logger.error(f"❌ Prompt formatting failed: Missing key {e}")
            return None

        for attempt in range(self.settings.max_retries):
            try:
                # Run the synchronous Gemini call in a thread pool to make it async-compatible
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                
                if not response.text:
                    raise ValueError("Empty response from model")
                
                # Parse the AI response to extract structured data
                result = self._parse_ai_response(response.text, article)
                return result

            except Exception as e:
                error_str = str(e)
                logger.warning(f"⚠️ Gemini error (Attempt {attempt + 1}): {e}")
                
                # Default backoff
                wait_time = self.settings.retry_delay * (attempt + 1)
                
                # Handle 429 Rate Limit specifically
                if "429" in error_str or "quota" in error_str.lower():
                    logger.warning("⏳ Rate limit hit. Cooling down...")
                    # Extract wait time if available (e.g. "retry in 10.8s")
                    import re
                    match = re.search(r'retry in (\d+(\.\d+)?)s', error_str)
                    if match:
                         wait_time = float(match.group(1)) + 2  # Add buffer
                    else:
                         wait_time = 15 # Default long cooling for quota
                
                if attempt < self.settings.max_retries - 1:
                    logger.info(f"Waiting {wait_time:.1f}s before retry...")
                    await asyncio.sleep(wait_time)
        
        logger.error(f"❌ Failed to analyze article: {article.title}")
        return None
    
    def _parse_ai_response(self, ai_text: str, article: NewsArticle) -> AnalysisResult:
        """Parse AI response to extract structured intelligence data."""
        
        # Extract importance score if present
        importance_score = 5  # Default
        score_match = re.search(r'امتیاز اهمیت.*?(\d+)/10', ai_text)
        if score_match:
            try:
                importance_score = int(score_match.group(1))
            except ValueError:
                pass
        
        # Try to determine category from the response
        category = IntelligenceCategory.OTHER
        if 'قانونی' in ai_text or 'regulation' in ai_text.lower():
            category = IntelligenceCategory.REGULATORY_CHANGE
        elif 'سرمایه‌گذاری' in ai_text or 'funding' in ai_text.lower():
            category = IntelligenceCategory.FUNDING_ANNOUNCEMENT
        elif 'رقبا' in ai_text or 'competitor' in ai_text.lower():
            category = IntelligenceCategory.COMPETITOR_ACTIVITY
        elif 'روند بازار' in ai_text or 'market trend' in ai_text.lower():
            category = IntelligenceCategory.MARKET_TREND
        elif 'فناوری' in ai_text or 'technology' in ai_text.lower():
            category = IntelligenceCategory.TECHNOLOGY_BREAKTHROUGH
        else:
            category = IntelligenceCategory.INDUSTRY_NEWS
        
        # Extract keywords if present (look for the keywords section)
        keywords = []
        keywords_match = re.search(r'کلمات کلیدی:.*?\n(.*?)(?:\n\n|\n🏷)', ai_text, re.DOTALL)
        if keywords_match:
            keywords_text = keywords_match.group(1).strip()
            keywords = [k.strip() for k in keywords_text.replace('[', '').replace(']', '').split(',')]
        
        # Extract tags
        tags = []
        tags_match = re.findall(r'#(\w+)', ai_text)
        if tags_match:
            tags = tags_match
        
        return AnalysisResult(
            title=article.title,
            category=category,
            summary=ai_text,  # Full formatted text
            importance_score=importance_score,
            importance="",  # Legacy field
            keywords=keywords[:7],  # Limit to 7
            tags=tags[:5],  # Limit to 5
            original_link=article.link,
            full_formatted_text=ai_text
        )
    
    async def categorize_intelligence(self, text: str) -> IntelligenceCategory:
        """Use AI to categorize intelligence if needed."""
        # Simple keyword-based categorization for now
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['regulation', 'policy', 'law', 'compliance']):
            return IntelligenceCategory.REGULATORY_CHANGE
        elif any(word in text_lower for word in ['funding', 'investment', 'raised', 'series']):
            return IntelligenceCategory.FUNDING_ANNOUNCEMENT
        elif any(word in text_lower for word in ['acquisition', 'merger', 'partnership', 'competitor']):
            return IntelligenceCategory.COMPETITOR_ACTIVITY
        elif any(word in text_lower for word in ['market', 'trend', 'growth', 'forecast']):
            return IntelligenceCategory.MARKET_TREND
        elif any(word in text_lower for word in ['technology', 'innovation', 'breakthrough', 'patent']):
            return IntelligenceCategory.TECHNOLOGY_BREAKTHROUGH
        else:
            return IntelligenceCategory.INDUSTRY_NEWS
