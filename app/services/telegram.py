import aiohttp
import logging
import asyncio
from app.config import Settings

logger = logging.getLogger("NewsAnalyst.Telegram")

class TelegramService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = f"https://api.telegram.org/bot{settings.telegram_token}"


    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to the configured Telegram chat."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.settings.telegram_chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }

        for attempt in range(self.settings.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=15) as response:
                        if response.status == 200:
                            logger.debug("✅ Message sent to Telegram")
                            return True
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Telegram API Error: {response.status} - {error_text}")
            
            except Exception as e:
                logger.error(f"❌ Telegram Connection Error (Attempt {attempt + 1}): {e}")
            
            if attempt < self.settings.max_retries - 1:
                await asyncio.sleep(self.settings.retry_delay)
        
        return False

    async def send_report(self, analysis_result) -> bool:
        """Send a formatted analysis report."""
        # Use the AI-generated HTML summary directly
        html_summary = analysis_result.summary

        
        # Use HTML formatting
        final_message = f"{html_summary}\n\n🔗 <a href=\"{analysis_result.original_link}\">مشاهده منبع اصلی</a>"
        
        # Try sending with HTML
        success = await self.send_message(final_message, parse_mode="HTML")
        
        # If HTML fails, try without parse_mode (plain text)
        if not success:
            logger.warning("⚠️ HTML parsing failed, sending as plain text")
            plain_message = f"{analysis_result.summary}\n\n🔗 مشاهده منبع اصلی: {analysis_result.original_link}"
            success = await self.send_message(plain_message, parse_mode="")
        
        return success
