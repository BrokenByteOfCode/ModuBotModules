from pyrogram import Client, filters
from pytube import YouTube
import os
import shutil

def add_on_download_command(app: Client):
    @app.on_message(filters.command("download", prefixes="."))
    def download_command(client, message):
        if len(message.command) != 2:
            message.reply_text("Usage: .download <YouTube URL>")
            return

        url = message.command[1]
        chat_id = message.chat.id

        try:
            yt = YouTube(url)
            stream = yt.streams.get_highest_resolution()
            
            video_path = stream.download(filename=f"{yt.title}.mp4")
            total_size = os.path.getsize(video_path)

            message.reply_text(f"Downloaded: {yt.title}\nSize: {total_size / (1024*1024):.2f} MB")

            progress_message = message.reply_text("Uploading... 0%")
            last_progress = 0

            def progress_callback(current, total):
                nonlocal last_progress
                progress = int(current * 100 / total)
                if progress > last_progress:
                    progress_message.edit_text(f"Uploading... {progress}%")
                    last_progress = progress

            client.send_video(
                chat_id=chat_id,
                video=video_path,
                caption=f"Title: {yt.title}",
                progress=progress_callback
            )

            videos_folder = "Videos"
            if not os.path.exists(videos_folder):
                os.makedirs(videos_folder)
            new_path = os.path.join(videos_folder, os.path.basename(video_path))
            shutil.move(video_path, new_path)

            client.delete_messages(chat_id=chat_id, message_ids=progress_message.message_id)

        except Exception as e:
            message.reply_text(f"Failed to download or upload video: {e}")
