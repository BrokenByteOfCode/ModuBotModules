import os
import random
import asyncio
import numpy as np
import soundfile as sf
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

    status_message = await message.reply_text("👾...")

    input_path = None
    wav_path = f"downloads/{message.id}.wav"
    output_path = f"downloads/{message.id}.ogg"

    try:
        input_path = await client.download_media(target_message)

        audio_data, original_rate = sf.read(input_path)

        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        num_levels = 2 ** (bit_depth - 1)
        crushed_data = np.round(audio_data * num_levels) / num_levels

        step = int(original_rate / target_rate)
        if step > 1:
            indices = np.arange(0, len(crushed_data), step)

            resampled_data = np.repeat(crushed_data[indices], step)

            crushed_data = resampled_data[:len(crushed_data)]

        sf.write(wav_path, crushed_data, original_rate)

        convert_cmd = f'ffmpeg -y -i "{wav_path}" -c:a libopus "{output_path}"'
        p_convert = await asyncio.create_subprocess_shell(convert_cmd, stderr=asyncio.subprocess.PIPE)
        _, stderr_convert = await p_convert.communicate()
        if p_convert.returncode != 0:
            raise RuntimeError(f"FFmpeg (convert) error: {stderr_convert.decode()}")

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
        if wav_path and os.path.exists(wav_path): os.remove(wav_path)
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