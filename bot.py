import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv
from utils.logger import logger
from utils.database import db
from handlers.upload import UploadHandler
from handlers.admin import AdminHandler
from handlers.language import LanguageHandler
from handlers.broadcast import BroadcastHandler
from userbot import userbot, start_userbot, stop_userbot
import json

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
CREATOR_ID = int(os.getenv('CREATOR_ID'))

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

# Command handlers
@bot.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Start command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    # Load language
    lang = db.get_user_language(user_id)
    lang_file = f"lang/{lang}.json"
    with open(lang_file, 'r') as f:
        lang_strings = json.load(f)
    
    await message.reply_text(lang_strings['start'])

@bot.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Help command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    # Load language
    lang = db.get_user_language(user_id)
    lang_file = f"lang/{lang}.json"
    with open(lang_file, 'r') as f:
        lang_strings = json.load(f)
    
    await message.reply_text(lang_strings['help'])

@bot.on_message(filters.command("list"))
async def list_command(client: Client, message: Message):
    """List queue command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    # Load language
    lang = db.get_user_language(user_id)
    lang_file = f"lang/{lang}.json"
    with open(lang_file, 'r') as f:
        lang_strings = json.load(f)
    
    queue = db.get_queue()
    if not queue:
        await message.reply_text(lang_strings['empty_queue'])
    else:
        queue_text = "\n".join([
            f"{i+1}. {'📱' if item['type'] == 'telegram' else '🔗'} {item.get('file_name', item.get('url', 'Unknown'))}"
            for i, item in enumerate(queue)
        ])
        next_item = get_next_queue_item(queue)
        
        await message.reply_text(
            lang_strings['processing_queue'].format(
                queue=queue_text,
                next_item=next_item
            )
        )

@bot.on_message(filters.command("server"))
async def server_command(client: Client, message: Message):
    """Server command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    # Load language
    lang = db.get_user_language(user_id)
    lang_file = f"lang/{lang}.json"
    with open(lang_file, 'r') as f:
        lang_strings = json.load(f)
    
    await message.reply_text(lang_strings['current_server'])

@bot.on_message(filters.command("ping"))
async def ping_command(client: Client, message: Message):
    """Ping command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    # Load language
    lang = db.get_user_language(user_id)
    lang_file = f"lang/{lang}.json"
    with open(lang_file, 'r') as f:
        lang_strings = json.load(f)
    
    from utils.helpers import ping_host
    ping_time = await ping_host()
    
    await message.reply_text(
        lang_strings['ping_result'].format(ms=ping_time)
    )

@bot.on_message(filters.command("hapi"))
async def hapi_command(client: Client, message: Message):
    """Hydrax API command handler"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    # Load language
    lang = db.get_user_language(user_id)
    lang_file = f"lang/{lang}.json"
    with open(lang_file, 'r') as f:
        lang_strings = json.load(f)
    
    await message.reply_text(lang_strings['hydrax_api_prompt'])

@bot.on_message(filters.create(lambda _, __, m: 
    m.text and len(m.text) > 20 and m.reply_to_message and 
    m.reply_to_message.text and "Hydrax API key" in m.reply_to_message.text
))
async def update_api_key(client: Client, message: Message):
    """Update Hydrax API key"""
    user_id = message.from_user.id
    
    # Check authorization
    if user_id != CREATOR_ID and user_id not in db.get_users():
        await message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    api_key = message.text.strip()
    
    # Load language
    lang = db.get_user_language(user_id)
    lang_file = f"lang/{lang}.json"
    with open(lang_file, 'r') as f:
        lang_strings = json.load(f)
    
    await message.reply_text(
        lang_strings['hydrax_api_confirm'].format(api_key=api_key),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Si", callback_data=f"api_confirm_{api_key}"),
                InlineKeyboardButton("🚫 No", callback_data="api_cancel")
            ]
        ])
    )

@bot.on_callback_query(filters.regex("^api_confirm_"))
async def confirm_api_key(client: Client, callback_query):
    """Confirm API key update"""
    api_key = callback_query.data.split('_', 2)[2]
    
    from utils.hydrax_api import hydrax_api
    hydrax_api.update_api_key(api_key)
    
    lang = db.get_user_language(callback_query.from_user.id)
    lang_file = f"lang/{lang}.json"
    with open(lang_file, 'r') as f:
        lang_strings = json.load(f)
    
    await callback_query.message.edit_text(lang_strings['hydrax_api_updated'])

@bot.on_callback_query(filters.regex("^api_cancel"))
async def cancel_api_key(client: Client, callback_query):
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
    for item in user_queue:
        db.remove_from_queue(queue.index(item))
    
    # Load language
    lang = db.get_user_language(user_id)
    lang_file = f"lang/{lang}.json"
    with open(lang_file, 'r') as f:
        lang_strings = json.load(f)
    
    await message.reply_text(lang_strings['cancelled'])

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
    from pyrogram import idle
    asyncio.run(main())
