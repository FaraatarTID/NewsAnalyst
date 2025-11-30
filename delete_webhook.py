"""
Telegram Webhook Management Utility

This script helps manage Telegram bot webhooks. Use it to:
- Check current webhook status
- Delete existing webhooks
- Clear pending updates

Run this if you're getting 409 errors when starting the local bot.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Force UTF-8 for stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    print("ERROR: TELEGRAM_TOKEN not found in .env file")
    sys.exit(1)

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def check_webhook():
    """Check current webhook status"""
    response = requests.get(f"{BASE_URL}/getWebhookInfo")
    if response.status_code == 200:
        info = response.json()["result"]
        print("\n=== Webhook Info ===")
        print(f"URL: {info.get('url', 'None')}")
        print(f"Pending Updates: {info.get('pending_update_count', 0)}")
        print(f"Last Error: {info.get('last_error_message', 'None')}")
        return info
    else:
        print(f"Failed to get webhook info: {response.status_code}")
        return None

def delete_webhook(drop_pending=True):
    """Delete webhook and optionally drop pending updates"""
    print(f"\nDeleting webhook (drop_pending={drop_pending})...")
    response = requests.post(
        f"{BASE_URL}/deleteWebhook",
        json={"drop_pending_updates": drop_pending}
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("ok"):
            print("SUCCESS: Webhook deleted")
            return True
        else:
            print(f"FAILED: {result.get('description', 'Unknown error')}")
            return False
    else:
        print(f"FAILED: HTTP {response.status_code}")
        return False

if __name__ == "__main__":
    print("Telegram Webhook Manager")
    print("=" * 40)
    
    # Check current status
    info = check_webhook()
    
    # Delete if webhook exists
    if info and info.get("url"):
        print(f"\nWebhook is set to: {info['url']}")
        delete_webhook(drop_pending=True)
        
        # Verify deletion
        print("\nVerifying deletion...")
        check_webhook()
    else:
        print("\nNo webhook is currently set.")
        print("You can start the local bot with: python run_local_bot.py")
