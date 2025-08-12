import os
import random
import asyncio
import numpy as np
import soundfile as sf
import scipy.signal
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

    status_message = await message.reply_text("👾 crunching...")

    input_path = None

    temp_wav_path = f"downloads/{message.id}_input.wav"
    processed_wav_path = f"downloads/{message.id}_processed.wav"
    output_path = f"downloads/{message.id}.ogg"

    try:
        input_path = await client.download_media(target_message)

        convert_to_wav_cmd = f'ffmpeg -y -i "{input_path}" "{temp_wav_path}"'
        p_convert_in = await asyncio.create_subprocess_shell(convert_to_wav_cmd, stderr=asyncio.subprocess.PIPE)
        _, stderr_convert_in = await p_convert_in.communicate()
        if p_convert_in.returncode != 0:

            if input_path != temp_wav_path:
                os.remove(input_path)
            raise RuntimeError(f"FFmpeg (input conversion) error: {stderr_convert_in.decode()}")

        audio_data, original_rate = sf.read(temp_wav_path)

        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        num_samples = int(len(audio_data) * (target_rate / original_rate))
        resampled_data = scipy.signal.resample(audio_data, num_samples)

        num_levels = 2 ** bit_depth
        crushed_data = np.round(resampled_data * (num_levels - 1)) / (num_levels - 1)

        sf.write(processed_wav_path, crushed_data, target_rate)

        convert_to_ogg_cmd = f'ffmpeg -y -i "{processed_wav_path}" -c:a libopus "{output_path}"'
        p_convert_out = await asyncio.create_subprocess_shell(convert_to_ogg_cmd, stderr=asyncio.subprocess.PIPE)
        _, stderr_convert_out = await p_convert_out.communicate()
        if p_convert_out.returncode != 0:
            raise RuntimeError(f"FFmpeg (output conversion) error: {stderr_convert_out.decode()}")

        caption = f"Crushed: {bit_depth}-bit, {target_rate}Hz"
        if random.randint(1, 3) == 1:
            caption += f"\n\n💡 `.bcr {random.randint(2, 6)} {random.choice([4000, 6000, 8000])}`"

        if target_message.voice:
            await client.send_voice(chat_id=message.chat.id, voice=output_path, caption=caption)
        elif target_message.audio:
            await client.send_audio(chat_id=message.chat.id, audio=output_path, caption=caption)

        await status_message.delete()

    except Exception as e:
        await status_message.edit_text(f"❌ **Помилка:**\n`{e}`")
    finally:

        if input_path and os.path.exists(input_path): os.remove(input_path)
        if temp_wav_path and os.path.exists(temp_wav_path): os.remove(temp_wav_path)
        if processed_wav_path and os.path.exists(processed_wav_path): os.remove(processed_wav_path)
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