import os
import json
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.database import db
from utils.logger import logger

class AdminHandler:
    def __init__(self, bot):
        self.bot = bot

    async def setup_handlers(self):
        """Setup admin command handlers"""

        @self.bot.on_message(filters.command("add") & filters.user(int(os.getenv('CREATOR_ID'))))
        async def add_user(client: Client, message: Message):
            """Add authorized user"""
            try:
                user_id = int(message.text.split()[1])
                db.add_user(user_id)
                await message.reply_text(f"✅ User {user_id} added successfully!")
                logger.info(f"User {user_id} added by creator")
            except (IndexError, ValueError):
                await message.reply_text("❌ Usage: /add <user_id>")

        @self.bot.on_message(filters.command("remove") & filters.user(int(os.getenv('CREATOR_ID'))))
        async def remove_user(client: Client, message: Message):
            """Remove authorized user"""
            try:
                user_id = int(message.text.split()[1])
                db.remove_user(user_id)
                await message.reply_text(f"✅ User {user_id} removed successfully!")
                logger.info(f"User {user_id} removed by creator")
            except (IndexError, ValueError):
                await message.reply_text("❌ Usage: /remove <user_id>")

        @self.bot.on_message(filters.command("log") & filters.user(int(os.getenv('CREATOR_ID'))))
        async def send_log(client: Client, message: Message):
            """Send bot log file"""
            try:
                if os.path.exists("bot.log"):
                    await client.send_document(
                        message.chat.id,
                        "bot.log",
                        caption="📋 Bot activity log"
                    )
                else:
                    await message.reply_text("❌ Log file not found")
            except Exception as e:
                await message.reply_text(f"❌ Error sending log: {str(e)}")
