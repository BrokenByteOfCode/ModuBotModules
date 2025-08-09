from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
import yt_dlp
import os
import re
import tempfile
import asyncio
from pyrogram.errors import FloodWait

async def send_media_with_retry(client, send_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await send_func()
        except FloodWait as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(e.value)
                continue
            else:
                raise e
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            else:
                raise e

async def extract_tiktok_url(text):
    tiktok_patterns = [
        r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+',
        r'https?://vm\.tiktok\.com/[\w]+',
        r'https?://(?:www\.)?tiktok\.com/t/[\w]+',
        r'https?://vt\.tiktok\.com/[\w]+',
    ]
    
    for pattern in tiktok_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return None

async def download_tiktok_video(url):
    ydl_opts = {
        'format': 'best[height<=1080]/best[height<=720]/best[height<=480]/best',
        'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'TikTok Video')
    except Exception as e:
        error_msg = str(e).lower()
        if 'cookies' in error_msg or 'login' in error_msg or 'sign in' in error_msg:
            raise Exception("Meh. Need cookies.")
        else:
            raise Exception(f"Помилка завантаження: {str(e)}")

async def tt_command(client: Client, message: Message):
    url = None
    
    if message.reply_to_message:
        if message.reply_to_message.text:
            url = await extract_tiktok_url(message.reply_to_message.text)
        elif message.reply_to_message.caption:
            url = await extract_tiktok_url(message.reply_to_message.caption)
    
    if not url and len(message.command) > 1:
        url = await extract_tiktok_url(message.text)
    
    if not url:
        await message.reply_text("❌ TikTok посилання не знайдено.\nВикористання: `.tt <посилання>` або відповідь на повідомлення з посиланням")
        return
    
    status_msg = await message.reply_text("⏳ Завантажую відео...")
    
    try:
        video_path, title = await download_tiktok_video(url)
        
        await status_msg.edit_text("📤 Відправляю відео...")
        
        await send_media_with_retry(client, lambda: client.send_video(
            chat_id=message.chat.id,
            video=video_path,
            caption=f"🎵 **{title}**\n\n📱 Завантажено з TikTok",
            reply_to_message_id=message.id
        ))
        
        os.remove(video_path)
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Помилка: {str(e)}")

def register_handlers(app: Client):
    tt_handler = MessageHandler(
        tt_command,
        filters.command("tt", prefixes=".")
    )
    
    handlers_list = [tt_handler]
    
    for handler in handlers_list:
        app.add_handler(handler)
    
    return handlers_list