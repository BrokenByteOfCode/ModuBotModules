import os
import io
import random
import asyncio
import numpy as np
import scipy.signal
from pydub import AudioSegment
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

def apply_crunch_effect(audio_segment, bit_depth, target_rate):
    if audio_segment.channels > 1:
        audio_segment = audio_segment.set_channels(1)

    original_rate = audio_segment.frame_rate
    raw_data = np.array(audio_segment.get_array_of_samples(), dtype=np.int16)

    num_samples = int(len(raw_data) * (target_rate / original_rate))
    resampled_data = scipy.signal.resample(raw_data, num_samples)

    shift_amount = 16 - bit_depth
    crushed_data = (resampled_data.astype(np.int16) >> shift_amount) << shift_amount

    crushed_audio = AudioSegment(
        crushed_data.tobytes(),
        frame_rate=target_rate,
        sample_width=2,  
        channels=1
    )

    return crushed_audio

async def bitcrush_command(client: Client, message: Message):
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
    try:
        input_path = await client.download_media(target_message)

        audio = AudioSegment.from_file(input_path)

        processed_audio = apply_crunch_effect(audio, bit_depth, target_rate)

        output_buffer = io.BytesIO()
        output_buffer.name = "crunched.ogg"
        processed_audio.export(output_buffer, format="ogg", codec="libopus")

        caption = f"Crushed: {bit_depth}-bit, {target_rate}Hz"
        if random.randint(1, 3) == 1:
            caption += f"\n\n💡 `.bcr {random.randint(2, 6)} {random.choice([4000, 6000, 8000])}`"

        if target_message.voice:
            await client.send_voice(chat_id=message.chat.id, voice=output_buffer, caption=caption)
        elif target_message.audio:
            await client.send_audio(chat_id=message.chat.id, audio=output_buffer, caption=caption)

        await status_message.delete()

    except Exception as e:
        await status_message.edit_text(f"❌ **Помилка:**\n`{e}`")
    finally:
        if input_path and os.path.exists(input_path):
            os.remove(input_path)

def register_handlers(app: Client):
    bitcrush_handler = MessageHandler(
        bitcrush_command,
        filters.command(["bitcrush", "bcr"], prefixes=".")
    )
    handlers_list = [bitcrush_handler]
    for handler in handlers_list:
        app.add_handler(handler)
    return handlers_list