from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from utils.database import db
from utils.helpers import get_language_keyboard
from utils.logger import logger
import os
import json

class LanguageHandler:
    def __init__(self, bot):
        self.bot = bot
    
    async def setup_handlers(self):
        """Setup language command handlers"""
        
        @self.bot.on_message(filters.command("setlang"))
        async def set_language(client: Client, message: Message):
            """Change bot language"""
            user_id = message.from_user.id
            
            # Check authorization
            if user_id != int(os.getenv('CREATOR_ID')) and user_id not in db.get_users():
                await message.reply_text("❌ You are not authorized to use this bot.")
                return
            
            await message.reply_text(
                "🌐 Select your language:",
                reply_markup=get_language_keyboard()
            )
        
        @self.bot.on_callback_query(filters.regex("^lang_"))
        async def language_callback(client: Client, callback_query: CallbackQuery):
            """Handle language selection callback"""
            user_id = callback_query.from_user.id
            lang_code = callback_query.data.split('_')[1]
            
            db.set_user_language(user_id, lang_code)
            
            # Load language strings
            lang_file = f"lang/{lang_code}.json"
            with open(lang_file, 'r') as f:
                lang = json.load(f)
            
            await callback_query.message.edit_text(lang['language_changed'])
