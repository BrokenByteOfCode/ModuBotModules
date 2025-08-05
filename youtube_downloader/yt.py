from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
import yt_dlp
import os
import re
import tempfile

async def extract_youtube_url(text):
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://youtu\.be/[\w-]+',
        r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
        r'https?://m\.youtube\.com/watch\?v=[\w-]+',
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return None

async def download_youtube_video(url, download_audio=False):
    if download_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if download_audio:
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            return filename, info.get('title', 'YouTube Video'), info.get('duration', 0)
    except Exception as e:
        raise Exception(f"Помилка завантаження: {str(e)}")

async def yt_command(client: Client, message: Message):
    url = None
    download_audio = False
    
    if len(message.command) > 1 and message.command[1] == 'audio':
        download_audio = True
    
    if message.reply_to_message:
        if message.reply_to_message.text:
            url = await extract_youtube_url(message.reply_to_message.text)
        elif message.reply_to_message.caption:
            url = await extract_youtube_url(message.reply_to_message.caption)
    
    if not url and len(message.command) > 1:
        url = await extract_youtube_url(message.text)
    
    if not url:
        await message.reply_text("❌ YouTube посилання не знайдено.\nВикористання: `.yt <посилання>` або `.yt audio <посилання>` для аудіо")
        return
    
    status_msg = await message.reply_text("⏳ Завантажую з YouTube...")
    
    try:
        file_path, title, duration = await download_youtube_video(url, download_audio)
        
        if duration and duration > 1200:
            await status_msg.edit_text("❌ Відео занадто довге (більше 20 хвилин)")
            return
        
        await status_msg.edit_text("📤 Відправляю файл...")
        
        if download_audio:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=file_path,
                caption=f"🎵 **{title}**\n\n📱 Завантажено з YouTube",
                reply_to_message_id=message.id
            )
        else:
            await client.send_video(
                chat_id=message.chat.id,
                video=file_path,
                caption=f"🎬 **{title}**\n\n📱 Завантажено з YouTube",
                reply_to_message_id=message.id
            )
        
        os.remove(file_path)
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Помилка: {str(e)}")

def register_handlers(app: Client):
    yt_handler = MessageHandler(
        yt_command,
        filters.command("yt", prefixes=".")
    )
    
    handlers_list = [yt_handler]
    
    for handler in handlers_list:
        app.add_handler(handler)
    
    return handlers_list