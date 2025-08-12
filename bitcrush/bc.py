import os
import random
import asyncio
import numpy as np
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

async def bitcrush_command(client: Client, message: Message):
    process = await asyncio.create_subprocess_shell("ffmpeg -version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.communicate()
    if process.returncode != 0:
        await message.reply_text("🔴 **Помилка: `ffmpeg` не знайдено.**\nВстановіть його на сервер: `sudo apt install ffmpeg`")
        return

    if not message.reply_to_message or not (message.reply_to_message.audio or message.reply_to_message.voice):
        await message.reply_text("Дай відповідь на аудіо чи голосове повідомлення.")
        return

    target_message = message.reply_to_message
    
    try:
        bit_depth = int(message.command[1]) if len(message.command) > 1 else 8
        target_rate = int(message.command[2]) if len(message.command) > 2 else 8000
    except (ValueError, IndexError):
        bit_depth = 8
        target_rate = 8000

    status_message = await message.reply_text("👾 crushing...")

    input_path = None
    raw_path = f"downloads/{message.id}.raw"
    output_path = f"downloads/{message.id}.ogg"
    
    try:
        input_path = await client.download_media(target_message)
        
        decode_cmd = f'ffmpeg -y -i "{input_path}" -f s16le -ar 44100 -ac 1 "{raw_path}"'
        p_decode = await asyncio.create_subprocess_shell(decode_cmd, stderr=asyncio.subprocess.PIPE)
        _, stderr_decode = await p_decode.communicate()
        if p_decode.returncode != 0:
            raise RuntimeError(f"FFmpeg (decode) error: {stderr_decode.decode()}")

        audio_data = np.fromfile(raw_path, dtype=np.int16)
        shift_amount = 16 - bit_depth
        crushed_data = (audio_data >> shift_amount) << shift_amount
        crushed_data.tofile(raw_path)
        
        encode_cmd = (
            f'ffmpeg -y -f s16le -ar 44100 -ac 1 -i "{raw_path}" '
            f'-af "aresample={target_rate}" '
            f'-c:a libopus "{output_path}"'
        )
        p_encode = await asyncio.create_subprocess_shell(encode_cmd, stderr=asyncio.subprocess.PIPE)
        _, stderr_encode = await p_encode.communicate()
        if p_encode.returncode != 0:
            raise RuntimeError(f"FFmpeg (encode) error: {stderr_encode.decode()}")

        caption = f"Crushed: {bit_depth}-bit, {target_rate}Hz"
        if random.randint(1, 3) == 1:
            caption += f"\n\n💡 `.bcr {random.randint(2, 8)} {random.choice([4000, 8000, 11025])}`"

        if target_message.voice:
            await client.send_voice(chat_id=message.chat.id, voice=output_path, caption=caption)
        elif target_message.audio:
            await client.send_audio(chat_id=message.chat.id, audio=output_path, caption=caption)

        await status_message.delete()

    except Exception as e:
        await status_message.edit_text(f"❌ **Помилка:**\n`{e}`")
    finally:
        if input_path and os.path.exists(input_path): os.remove(input_path)
        if raw_path and os.path.exists(raw_path): os.remove(raw_path)
        if output_path and os.path.exists(output_path): os.remove(output_path)

def register_handlers(app: Client):
    bitcrush_handler = MessageHandler(
        bitcrush_command,
        filters.command(["bitcrush", "bcr"], prefixes=".")
    )
    handlers_list = [bitcrush_handler]
    for handler in handlers_list:
        app.add_handler(handler)
    return handlers_list