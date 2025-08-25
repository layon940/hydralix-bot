from pyrogram import Client
import os

# Userbot for downloading files
userbot = Client(
    "userbot",
    api_id=2040,
    api_hash="b18441a1ff607e10a989891a5462e627",
    session_string=os.getenv('SESSION_STRING')
)

async def start_userbot():
    """Start the userbot"""
    await userbot.start()

async def stop_userbot():
    """Stop the userbot"""
    await userbot.stop()
