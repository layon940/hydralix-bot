import os
import asyncio
import json
from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery
from dotenv import load_dotenv
from utils.logger import logger
from utils.database import db
from handlers.upload import UploadHandler
from handlers.admin import AdminHandler
from handlers.language import LanguageHandler
from handlers.broadcast import BroadcastHandler
from userbot import userbot, start_userbot, stop_userbot
from utils.helpers import get_next_queue_item

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
CREATOR_ID = int(os.getenv('CREATOR_ID') or 0)

if not BOT_TOKEN or not CREATOR_ID:
    logger.error("BOT_TOKEN and CREATOR_ID must be set in environment variables")
    exit(1)

# Initialize bot
bot = Client(
    "hydrax_uploader_bot",
    bot_token=BOT_TOKEN,
    api_id=2040,
    api_hash="b18441a1ff607e10a989891a5462e627"
)

# Initialize handlers
upload_handler = UploadHandler(bot)
admin_handler = AdminHandler(bot)
language_handler = LanguageHandler(bot)
broadcast_handler = BroadcastHandler(bot)

def get_lang_string(user_id: int, key: str) -> str:
    """Get language string for user"""
    lang = db.get_user_language(user_id)
    lang_file = f"lang/{lang}.json"
    try:
        with open(lang_file, 'r', encoding='utf-8') as f:
            lang_strings = json.load(f)
            return lang_strings.get(key, key)
    except FileNotFoundError:
        return key

# Command handlers
@bot.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Start command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    lang_str = get_lang_string(user_id, 'start')
    await message.reply_text(lang_str)

@bot.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Help command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    lang_str = get_lang_string(user_id, 'help')
    await message.reply_text(lang_str)

@bot.on_message(filters.command("list"))
async def list_command(client: Client, message: Message):
    """List queue command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    queue = db.get_queue()
    if not queue:
        lang_str = get_lang_string(user_id, 'empty_queue')
        await message.reply_text(lang_str)
    else:
        queue_text = "\n".join([
            f"{i+1}. {'📱' if item['type'] == 'telegram' else '🔗'} {item.get('file_name', item.get('url', 'Unknown'))}"
            for i, item in enumerate(queue)
        ])
        next_item = get_next_queue_item(queue)
        
        lang_str = get_lang_string(user_id, 'processing_queue')
        await message.reply_text(
            lang_str.format(queue=queue_text, next_item=next_item)
        )

@bot.on_message(filters.command("server"))
async def server_command(client: Client, message: Message):
    """Server command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    lang_str = get_lang_string(user_id, 'current_server')
    await message.reply_text(lang_str)

@bot.on_message(filters.command("ping"))
async def ping_command(client: Client, message: Message):
    """Ping command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    from utils.helpers import ping_host
    ping_time = await ping_host()
    
    lang_str = get_lang_string(user_id, 'ping_result')
    await message.reply_text(lang_str.format(ms=ping_time))

@bot.on_message(filters.command("hapi"))
async def hapi_command(client: Client, message: Message):
    """Hydrax API command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    lang_str = get_lang_string(user_id, 'hydrax_api_prompt')
    await message.reply_text(lang_str)

@bot.on_message(filters.create(lambda _, __, m: 
    m.text and len(m.text) > 20 and m.reply_to_message and 
    m.reply_to_message.text and "Hydrax API" in m.reply_to_message.text
))
async def update_api_key(client: Client, message: Message):
    """Update Hydrax API key"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    api_key = message.text.strip()
    
    lang_str = get_lang_string(user_id, 'hydrax_api_confirm')
    await message.reply_text(
        lang_str.format(api_key=api_key),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Si", callback_data=f"api_confirm_{api_key}"),
                InlineKeyboardButton("🚫 No", callback_data="api_cancel")
            ]
        ])
    )

@bot.on_callback_query(filters.regex("^api_confirm_"))
async def confirm_api_key(client: Client, callback_query: CallbackQuery):
    """Confirm API key update"""
    api_key = callback_query.data.split('_', 2)[2]
    
    from utils.hydrax_api import hydrax_api
    hydrax_api.update_api_key(api_key)
    
    lang_str = get_lang_string(callback_query.from_user.id, 'hydrax_api_updated')
    await callback_query.message.edit_text(lang_str)

@bot.on_callback_query(filters.regex("^api_cancel"))
async def cancel_api_key(client: Client, callback_query: CallbackQuery):
    """Cancel API key update"""
    await callback_query.message.edit_text("❌ Operation cancelled")

@bot.on_message(filters.command("cancel"))
async def cancel_command(client: Client, message: Message):
    """Cancel command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    # Clear queue for this user
    queue = db.get_queue()
    user_queue = [item for item in queue if item['user_id'] == user_id]
    
    # Remove user's items from queue
    for item in reversed(user_queue):  # Reverse to maintain indices
        queue = db.get_queue()
        index = next(i for i, q in enumerate(queue) if q == item)
        db.remove_from_queue(index)
    
    lang_str = get_lang_string(user_id, 'cancelled')
    await message.reply_text(lang_str)

# Video and URL handlers
@bot.on_message(filters.video)
async def handle_video(client: Client, message: Message):
    """Handle video messages"""
    await upload_handler.handle_video(client, message)

@bot.on_message(filters.text & filters.regex(r'^https?://'))
async def handle_url(client: Client, message: Message):
    """Handle URL messages"""
    await upload_handler.handle_url(client, message)

async def main():
    """Main function"""
    logger.info("Starting Hydrax Uploader Bot...")
    
    # Setup handlers
    await admin_handler.setup_handlers()
    await language_handler.setup_handlers()
    await broadcast_handler.setup_handlers()
    
    # Start userbot
    await start_userbot()
    
    # Start bot
    logger.info("Bot started successfully!")
    await bot.start()
    
    # Keep bot running
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
