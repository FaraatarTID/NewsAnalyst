import asyncio
import logging
import sys
import os
import aiohttp
from dotenv import load_dotenv
from datetime import datetime, time, timedelta
import pytz

# Load environment variables
load_dotenv(override=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] LocalBot - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("LocalBot")

# Import main function from main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import main as run_analysis

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    logger.critical("❌ TELEGRAM_TOKEN not found in environment variables.")
    sys.exit(1)

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Scheduling configuration
SCHEDULED_TIME = time(8, 30)  # 8:30 AM
TIMEZONE = pytz.timezone('Asia/Tehran')  # Iran timezone (UTC+3:30)

async def get_updates(session, offset=None):
    params = {"timeout": 30, "allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    
    try:
        async with session.get(f"{BASE_URL}/getUpdates", params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to get updates: {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error getting updates: {e}")
        return None

async def send_message(session, chat_id, text):
    try:
        await session.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        })
    except Exception as e:
        logger.error(f"Error sending message: {e}")

async def process_update(session, update):
    message = update.get("message")
    if not message or "text" not in message:
        return

    chat_id = message["chat"]["id"]
    text = message["text"].strip()
    
    if text.startswith("/news"):
        # Parse topic
        parts = text.split(maxsplit=1)
        topic = parts[1].strip() if len(parts) > 1 else None
        
        logger.info(f"📩 Received request from {chat_id}: {text}")
        
        status_msg = f"⏳ <b>Request Received</b>\n\nFetching news{' about: ' + topic if topic else ' (Business Intelligence)'}...\nThis may take 30-60 seconds."
        await send_message(session, chat_id, status_msg)
        
        # Run the analysis
        try:
            logger.info("🚀 Triggering analysis...")
            await run_analysis(custom_topic=topic)
            logger.info("✅ Analysis complete.")
        except SystemExit:
            logger.warning("⚠️ Analysis script exited with SystemExit (handled).")
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}", exc_info=True)
            await send_message(session, chat_id, f"❌ Analysis failed: {str(e)}")

async def scheduled_task():
    """Run daily analysis at scheduled time"""
    while True:
        now = datetime.now(TIMEZONE)
        scheduled_datetime = TIMEZONE.localize(datetime.combine(now.date(), SCHEDULED_TIME))
        
        # If scheduled time has passed today, schedule for tomorrow
        if now >= scheduled_datetime:
            scheduled_datetime = TIMEZONE.localize(
                datetime.combine(now.date(), SCHEDULED_TIME)
            ) + timedelta(days=1)
        
        # Calculate seconds until next scheduled run
        seconds_until_run = (scheduled_datetime - now).total_seconds()
        
        logger.info(f"📅 Next scheduled run: {scheduled_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Wait until scheduled time
        await asyncio.sleep(seconds_until_run)
        
        # Run the analysis
        logger.info("⏰ Scheduled time reached - running daily analysis...")
        try:
            await run_analysis(custom_topic=None)
            logger.info("✅ Scheduled analysis complete.")
        except Exception as e:
            logger.error(f"❌ Scheduled analysis failed: {e}", exc_info=True)

async def run_bot():
    logger.info("🤖 Local Telegram Bot Starting...")
    logger.info(f"⏰ Scheduled daily run: {SCHEDULED_TIME.strftime('%H:%M')} {TIMEZONE}")
    logger.info("Clearing old messages from queue...")
    
    offset = 0
    async with aiohttp.ClientSession() as session:
        # Check and delete webhook if it exists to allow polling
        try:
            async with session.get(f"{BASE_URL}/getWebhookInfo") as response:
                if response.status == 200:
                    webhook_info = await response.json()
                    if webhook_info.get("result", {}).get("url"):
                        logger.info("Found active webhook. Deleting to enable local polling...")
                        await session.post(f"{BASE_URL}/deleteWebhook", json={"drop_pending_updates": False})
                        logger.info("✅ Webhook deleted successfully.")
        except Exception as e:
            logger.warning(f"⚠️ Could not check/delete webhook: {e}")

        # First, clear all pending messages by getting updates without processing
        updates = await get_updates(session, offset=0)
        if updates and updates.get("ok"):
            result = updates.get("result", [])
            if result:
                # Set offset to skip all old messages
                offset = result[-1]["update_id"] + 1
                logger.info(f"Skipped {len(result)} old messages. Ready for new commands.")
            else:
                logger.info("No old messages in queue.")
        
        logger.info("Waiting for commands (/news [topic])...")
        
        # Start scheduled task in background
        asyncio.create_task(scheduled_task())
        
        while True:
            updates = await get_updates(session, offset)
            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    update_id = update["update_id"]
                    await process_update(session, update)
                    offset = update_id + 1
            
            # Small delay to prevent tight loop on error
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
