import os
import asyncio
import time
import tempfile
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.database import db
from utils.hydrax_api import hydrax_api
from utils.helpers import create_progress_bar, format_bytes, get_next_queue_item
from utils.logger import logger
from userbot import userbot
import aiohttp

class UploadHandler:
    def __init__(self, bot):
        self.bot = bot
        self.processing = False

    async def handle_video(self, client: Client, message: Message):
        """Handle video messages"""
        user_id = message.from_user.id

        # Check authorization
        if user_id != int(os.getenv('CREATOR_ID')) and user_id not in db.get_users():
            await message.reply_text("❌ You are not authorized to use this bot.")
            return

        # Add to queue
        file_name = message.video.file_name or f"video_{message.video.file_unique_id}.mp4"
        db.add_to_queue({
            'type': 'telegram',
            'file_name': file_name,
            'file_id': message.video.file_id,
            'user_id': user_id,
            'chat_id': message.chat.id
        })

        await message.reply_text("📋 Added to processing queue!")

        # Process queue if not already processing
        if not self.processing:
            asyncio.create_task(self.process_queue())

    async def handle_url(self, client: Client, message: Message):
        """Handle URL messages"""
        user_id = message.from_user.id

        # Check authorization
        if user_id != int(os.getenv('CREATOR_ID')) and user_id not in db.get_users():
            await message.reply_text("❌ You are not authorized to use this bot.")
            return

        url = message.text.strip()

        # Add to queue
        db.add_to_queue({
            'type': 'url',
            'url': url,
            'user_id': user_id,
            'chat_id': message.chat.id
        })

        await message.reply_text("📋 Added to processing queue!")

        # Process queue if not already processing
        if not self.processing:
            asyncio.create_task(self.process_queue())

    async def process_queue(self):
        """Process the upload queue"""
        if self.processing:
            return

        self.processing = True

        try:
            while True:
                queue = db.get_queue()
                if not queue:
                    break

                item = queue[0]
                user_id = item['user_id']
                chat_id = item['chat_id']

                try:
                    if item['type'] == 'telegram':
                        await self.process_telegram_item(item, chat_id)
                    else:
                        await self.process_url_item(item, chat_id)
                except Exception as e:
                    logger.error(f"Error processing item: {e}")
                    await self.bot.send_message(chat_id, f"❌ Error: {str(e)}")

                # Remove completed item
                db.remove_from_queue(0)

        finally:
            self.processing = False

    async def process_telegram_item(self, item: dict, chat_id: int):
        """Process Telegram video upload"""
        file_name = item['file_name']

        # Download using userbot
        status_msg = await self.bot.send_message(chat_id, f"📥 Downloading {file_name}...")

        try:
            start_time = time.time()

            async def progress(current, total):
                bar = create_progress_bar(current, total)
                percentage = (current / total) * 100
                elapsed = time.time() - start_time
                speed = format_bytes(current / elapsed) if elapsed > 0 else "0 B"
                eta = f"{(total - current) / (current / elapsed):.1f}s" if current > 0 else "∞"

                try:
                    await status_msg.edit_text(
                        f"📥 Downloading...\n\n"
                        f"**File:** {file_name}\n"
                        f"**Progress:** {bar} {percentage:.1f}%\n"
                        f"**Speed:** {speed}/s\n"
                        f"**ETA:** {eta}\n\n"
                        f"**Next:** {get_next_queue_item(db.get_queue())}"
                    )
                except Exception:
                    pass

            file_path = await userbot.download_media(
                item['file_id'],
                file_name=file_name,
                progress=progress
            )

            if not file_path:
                raise Exception("Failed to download file")

            # Check file size (10GB limit)
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024 * 1024:  # 10GB
                raise Exception("File exceeds 10GB limit")

            # Upload to Hydrax
            await status_msg.edit_text(f"📤 Uploading to Hydrax...")

            result = hydrax_api.upload_video(file_path, file_name)

            # Clean up
            if os.path.exists(file_path):
                os.remove(file_path)

            await status_msg.edit_text(
                f"✅ Upload completed!\n\n"
                f"**File:** {file_name}\n"
                f"**URL:** https://hydrax.net/{result.get('slug', 'N/A')}"
            )

        except Exception as e:
            await status_msg.edit_text(f"❌ Upload failed: {str(e)}")
            logger.error(f"Upload failed: {e}")
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)

    async def process_url_item(self, item: dict, chat_id: int):
        """Process URL upload"""
        url = item['url']
        file_name = url.split('/')[-1] or "video.mp4"

        status_msg = await self.bot.send_message(chat_id, f"📥 Downloading from URL...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")

                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    start_time = time.time()

                    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file_name}") as tmp_file:
                        file_path = tmp_file.name

                        async for chunk in response.content.iter_chunked(8192):
                            if chunk:
                                tmp_file.write(chunk)
                                downloaded += len(chunk)

                                if total_size > 0:
                                    bar = create_progress_bar(downloaded, total_size)
                                    percentage = (downloaded / total_size) * 100
                                    elapsed = time.time() - start_time
                                    speed = format_bytes(downloaded / elapsed) if elapsed > 0 else "0 B"
                                    eta = f"{(total_size - downloaded) / (downloaded / elapsed):.1f}s" if downloaded > 0 else "∞"

                                    try:
                                        await status_msg.edit_text(
                                            f"📥 Downloading...\n\n"
                                            f"**File:** {file_name}\n"
                                            f"**Progress:** {bar} {percentage:.1f}%\n"
                                            f"**Speed:** {speed}/s\n"
                                            f"**ETA:** {eta}\n\n"
                                            f"**Next:** {get_next_queue_item(db.get_queue())}"
                                        )
                                    except Exception:
                                        pass

                        tmp_file.flush()

                        # Check file size (10GB limit)
                        file_size = os.path.getsize(file_path)
                        if file_size > 10 * 1024 * 1024 * 1024:  # 10GB
                            raise Exception("File exceeds 10GB limit")

                        # Upload to Hydrax
                        await status_msg.edit_text(f"📤 Uploading to Hydrax...")

                        result = hydrax_api.upload_video(file_path, file_name)

                        # Clean up
                        os.remove(file_path)

                        await status_msg.edit_text(
                            f"✅ Upload completed!\n\n"
                            f"**File:** {file_name}\n"
                            f"**URL:** https://hydrax.net/{result.get('slug', 'N/A')}"
                        )

        except Exception as e:
            await status_msg.edit_text(f"❌ Upload failed: {str(e)}")
            logger.error(f"Upload failed: {e}")
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
