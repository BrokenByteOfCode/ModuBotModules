import asyncio
import os
import tempfile
from typing import Optional
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message


async def _run_ffmpeg(input_path: str, output_path: str) -> None:
    vf = "scale=640:640:force_original_aspect_ratio=decrease,pad=640:640:(ow-iw)/2:(oh-ih)/2,format=yuv420p"

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-t",
        "30",
        "-vf",
        vf,
        "-an",
        "-c:v",
        "libx264",
        "-crf",
        "28",
        "-preset",
        "veryfast",
        "-movflags",
        "+faststart",
        output_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {stderr.decode(errors='ignore')}")


async def _save_bytesio_to_file(data, suffix: str = ".mp4") -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(data)
        tmp.flush()
        tmp.close()
        return tmp.name
    except Exception:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
        raise


async def v2vm_command(client: Client, message: Message):
    target_msg: Optional[Message] = None

    if message.reply_to_message:
        target_msg = message.reply_to_message
    else:
        target_msg = message if (message.video or message.document or message.animation) else None

    if not target_msg:
        await message.reply_text("Надішліть або відповіьте на повідомлення з відео/анімацією, щоб конвертувати у video_note.")
        return

    status = await message.reply_text("`Processing video...`")

    try:
        media = None
        try:
            media = await client.download_media(target_msg, in_memory=True)
        except Exception:
            media_path = await client.download_media(target_msg)
            with open(media_path, "rb") as f:
                media = f.read()
            try:
                os.unlink(media_path)
            except Exception:
                pass

        if not media:
            await status.edit_text("Не вдалося завантажити медіа. Переконайтеся, що це відео або анімація.")
            return

        data = media.getvalue() if hasattr(media, "getvalue") else media

        input_path = await _save_bytesio_to_file(data, suffix=".mp4")
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name

        await _run_ffmpeg(input_path, output_path)

        await message.reply_video_note(output_path)

    except Exception as e:
        await status.edit_text(f"Помилка при конвертації: {e}")
    finally:
        try:
            if 'input_path' in locals() and input_path and os.path.exists(input_path):
                os.unlink(input_path)
        except Exception:
            pass
        try:
            if 'output_path' in locals() and output_path and os.path.exists(output_path):
                os.unlink(output_path)
        except Exception:
            pass
        try:
            await status.delete()
        except Exception:
            pass


def register_handlers(app: Client):
    handler = MessageHandler(
        v2vm_command,
        filters.command(["v2vm", "videomsg"], prefixes=".")
    )

    handlers_list = [handler]

    for h in handlers_list:
        app.add_handler(h)

    return handlers_list
