import asyncio
import os
import re
import tempfile

import yt_dlp
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message


async def extract_youtube_url(text):
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://youtu\.be/[\w-]+',
        r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
        r'https?://m\.youtube\.com/watch\?v=[\w-]+',
        r'https?://music\.youtube\.com/watch\?v=[\w-]+',
    ]

    for pattern in youtube_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return None


async def is_youtube_music_url(url):
    return "music.youtube.com" in url


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


async def download_youtube_video(url, download_audio=False):
    temp_dir = tempfile.gettempdir()
    ydl_opts = {
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    if download_audio:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({
            'format': 'best[height<=1080]/best[height<=720]/best[height<=480]/best',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if download_audio:
                filename = f"{os.path.splitext(filename)[0]}.mp3"
            return filename, info.get('title', 'YouTube Video'), info.get('duration', 0)
    except Exception as e:
        error_msg = str(e).lower()
        if 'cookies' in error_msg or 'login' in error_msg or 'sign in' in error_msg:
            raise Exception("Потрібні файли cookie для доступу до цього відео.")
        else:
            raise Exception(f"Помилка завантаження: {e}")


async def yt_command(client: Client, message: Message):
    url = None
    download_audio = 'audio' in message.command

    if message.reply_to_message:
        text_to_check = message.reply_to_message.text or message.reply_to_message.caption
        if text_to_check:
            url = await extract_youtube_url(text_to_check)

    if not url:
        url = await extract_youtube_url(message.text)

    if url and await is_youtube_music_url(url):
        download_audio = True

    if not url:
        await message.reply_text(
            "❌ YouTube посилання не знайдено.\n"
            "Використання: `.yt <посилання>` або `.yt audio <посилання>` для аудіо."
        )
        return

    status_msg = await message.reply_text("⏳ Завантажую з YouTube...")

    try:
        file_path, title, duration = await download_youtube_video(url, download_audio)

        if duration and duration > 1200:
            await status_msg.edit_text("❌ Відео занадто довге (більше 20 хвилин).")
            os.remove(file_path)
            return

        await status_msg.edit_text("📤 Відправляю файл...")

        if download_audio:
            await send_media_with_retry(
                client,
                lambda: client.send_audio(
                    chat_id=message.chat.id,
                    audio=file_path,
                    caption=f"🎵 **{title}**\n\n📱 Завантажено з YouTube",
                    reply_to_message_id=message.id
                )
            )
        else:
            await send_media_with_retry(
                client,
                lambda: client.send_video(
                    chat_id=message.chat.id,
                    video=file_path,
                    caption=f"🎬 **{title}**\n\n📱 Завантажено з YouTube",
                    reply_to_message_id=message.id
                )
            )
        
        os.remove(file_path)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Помилка: {e}")


def register_handlers(app: Client):
    yt_handler = MessageHandler(
        yt_command,
        filters.command("yt", prefixes=".")
    )
    app.add_handler(yt_handler)
    
    return [yt_handler]