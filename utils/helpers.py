import asyncio
import aiohttp
import time
from typing import List, Dict, Any
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_progress_bar(current: int, total: int, length: int = 20) -> str:
    """Create a progress bar"""
    progress = int((current / total) * length)
    bar = "█" * progress + "░" * (length - progress)
    return bar

def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

async def ping_host(host: str = "api.telegram.org") -> float:
    """Ping a host and return response time in ms"""
    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://{host}", timeout=5) as response:
                await response.text()
        return round((time.time() - start_time) * 1000, 2)
    except:
        return -1

def get_language_keyboard():
    """Get language selection keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
        ]
    ])

def get_confirmation_keyboard(yes_text: str = "✅ Yes", no_text: str = "🚫 No"):
    """Get confirmation keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(yes_text, callback_data="confirm_yes"),
            InlineKeyboardButton(no_text, callback_data="confirm_no")
        ]
    ])

def get_next_queue_item(queue: List[Dict[str, Any]]) -> str:
    """Get next item in queue"""
    if len(queue) > 1:
        next_item = queue[1]
        if next_item.get('type') == 'telegram':
            return f"📱 {next_item.get('file_name', 'Unknown')}"
        else:
            return f"🔗 {next_item.get('url', 'Unknown')}"
    return "None"
