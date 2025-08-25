import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from utils.database import db
from utils.logger import logger
import json

class BroadcastHandler:
    def __init__(self, bot):
        self.bot = bot
        self.broadcast_data = {}

    async def setup_handlers(self):
        """Setup broadcast command handlers"""

        @self.bot.on_message(filters.command("ads") & filters.user(int(os.getenv('CREATOR_ID'))))
        async def start_broadcast(client: Client, message: Message):
            """Start broadcast setup"""
            self.broadcast_data[message.chat.id] = {
                'messages': [],
                'stage': 'collecting'
            }

            await message.reply_text(
                "📢 Send me the announcement you want to broadcast:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
                ]])
            )

        @self.bot.on_message(filters.create(lambda _, __, m:
            m.chat.id in self.broadcast_data and
            self.broadcast_data[m.chat.id]['stage'] == 'collecting'
        ))
        async def collect_message(client: Client, message: Message):
            """Collect broadcast messages"""
            chat_id = message.chat.id

            self.broadcast_data[chat_id]['messages'].append(message)

            await message.reply_text(
                "📢 Message added! Want to add more or send the broadcast?",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Send Now", callback_data="broadcast_send"),
                        InlineKeyboardButton("➕ Add More", callback_data="broadcast_add")
                    ]
                ])
            )

        @self.bot.on_callback_query(filters.regex("^broadcast_"))
        async def broadcast_callback(client: Client, callback_query: CallbackQuery):
            """Handle broadcast callbacks"""
            chat_id = callback_query.message.chat.id
            action = callback_query.data.split('_')[1]

            if action == 'cancel':
                if chat_id in self.broadcast_data:
                    del self.broadcast_data[chat_id]
                await callback_query.message.edit_text("❌ Broadcast cancelled")

            elif action == 'add':
                await callback_query.message.edit_text("📢 Send me another message:")

            elif action == 'send':
                await self.send_broadcast(client, chat_id, callback_query)

    async def send_broadcast(self, client: Client, chat_id: int, callback_query):
        """Send broadcast to all users"""
        if chat_id not in self.broadcast_data:
            return

        # Get all users who have started the bot
        users = db.get_users()
        users.append(int(os.getenv('CREATOR_ID')))

        # Combine messages
        combined_message = ""
        for msg in self.broadcast_data[chat_id]['messages']:
            if msg.text:
                combined_message += msg.text + "\n\n"
            elif msg.caption:
                combined_message += msg.caption + "\n\n"

        # Preview
        await callback_query.message.edit_text(
            f"📢 **Preview:**\n\n{combined_message}\n\nSend this announcement?",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Send", callback_data="broadcast_confirmed"),
                    InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
                ]
            ])
        )

        @client.on_callback_query(filters.regex("^broadcast_confirmed"))
        async def confirmed_broadcast(client: Client, callback_query):
            if callback_query.message.chat.id != chat_id:
                return

            await callback_query.message.edit_text("📢 Sending broadcast...")

            # Get unique users
            all_users = set(users)
            success = 0
            failed = 0
            blocked = 0

            status_msg = await client.send_message(chat_id, "📢 Starting broadcast...")

            for idx, user_id in enumerate(all_users):
                try:
                    await client.send_message(user_id, combined_message.strip())
                    success += 1
                except Exception as e:
                    if "blocked" in str(e).lower():
                        blocked += 1
                    else:
                        failed += 1

                # Update status every 5 users
                if idx % 5 == 0 or idx == len(all_users) - 1:
                    await status_msg.edit_text(
                        f"📢 Broadcasting...\n\n"
                        f"✅ Sent: {success}\n"
                        f"❌ Failed: {failed}\n"
                        f"🚫 Blocked: {blocked}\n"
                        f"⏳ Remaining: {len(all_users) - success - failed - blocked}"
                    )

                await asyncio.sleep(0.5)  # Anti-spam delay

            await status_msg.edit_text(
                f"✅ Broadcast completed!\n\n"
                f"📊 **Summary:**\n"
                f"✅ Sent: {success}\n"
                f"❌ Failed: {failed}\n"
                f"🚫 Blocked: {blocked}"
            )

            # Clean up
            if chat_id in self.broadcast_data:
                del self.broadcast_data[chat_id]
