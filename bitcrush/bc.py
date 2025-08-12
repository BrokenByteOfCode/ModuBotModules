import os
import random
import asyncio
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

async def bitcrush_command(client: Client, message: Message):
    process = await asyncio.create_subprocess_shell(
        "ffmpeg -version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    if process.returncode != 0:
        await message.reply_text(
            "🔴 **Помилка: `ffmpeg` не знайдено.**\n"
            "Встановіть його на сервер:\n"
            "`sudo apt update && sudo apt install ffmpeg`"
        )
        return

    if not message.reply_to_message or not (message.reply_to_message.audio or message.reply_to_message.voice):
        await message.reply_text("Дай відповідь на аудіо чи голосове повідомлення.")
        return

    target_message = message.reply_to_message
    
    try:
        bit_depth = int(message.command[1]) if len(message.command) > 1 else 8
        sample_rate = int(message.command[2]) if len(message.command) > 2 else 8000
    except (ValueError, IndexError):
        bit_depth = 8
        sample_rate = 8000

    ffmpeg_format = "u8" if bit_depth <= 8 else "s16"
    actual_bit_depth = 8 if bit_depth <= 8 else 16

    status_message = await message.reply_text("👾...")

    input_path = None
    output_path = f"downloads/{message.id}_bitcrushed.ogg"
    
    try:
        input_path = await client.download_media(target_message)
        
        cmd = (
            f'ffmpeg -y -i "{input_path}" '
            f'-af "aformat=sample_fmts={ffmpeg_format},asetrate={sample_rate}" '
            f'-c:a libopus "{output_path}"'
        )

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_log = stderr.decode().strip()
            await status_message.edit_text(f"❌ **Помилка ffmpeg:**\n\n`{error_log}`")
            return

        caption = f"Crushed: {actual_bit_depth}-bit, {sample_rate}Hz"
        if random.randint(1, 3) == 1:
            caption += f"\n\n💡 `.bcr {random.randint(2, 8)} {random.choice([4000, 8000, 11025])}`"

        if target_message.voice:
            await client.send_voice(
                chat_id=message.chat.id,
                voice=output_path,
                caption=caption
            )
        elif target_message.audio:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=output_path,
                caption=caption
            )

        await status_message.delete()

    except Exception as e:
        await status_message.edit_text(f"❌ **Помилка:**\n`{e}`")
    finally:
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)

def register_handlers(app: Client):
    bitcrush_handler = MessageHandler(
        bitcrush_command,
        filters.command(["bitcrush", "bcr"], prefixes=".")
    )

    handlers_list = [bitcrush_handler]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list