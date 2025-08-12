import io
import os
import random
import numpy as np
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pydub import AudioSegment

async def bitcrush_command(client: Client, message: Message):
    if not message.reply_to_message or not (message.reply_to_message.audio or message.reply_to_message.voice):
        await message.reply_text("Будь ласка, дайте відповідь на аудіо або голосове повідомлення, щоб застосувати ефект.")
        return

    target_message = message.reply_to_message

    try:

        bit_depth = int(message.command[1]) if len(message.command) > 1 else 4

        sample_rate = int(message.command[2]) if len(message.command) > 2 else 4000

        if bit_depth <= 0 or sample_rate <= 0:
            raise ValueError("Параметри мають бути додатними числами.")

    except (ValueError, IndexError):
        await message.reply_text(
            "Неправильний формат параметрів. Використовую стандартні значення.\n"
            "**Приклад:** `.bitcrush 8 8000`"
        )
        bit_depth = 4
        sample_rate = 4000

    status_message = await message.reply_text(" crushing your audio... 👾")

    downloaded_file = None
    try:

        downloaded_file = await client.download_media(target_message)

        audio = AudioSegment.from_file(downloaded_file)

        samples = np.array(audio.get_array_of_samples())

        shift_amount = (audio.sample_width * 8) - bit_depth
        if shift_amount < 0:
            shift_amount = 0

        crushed_samples = (samples >> shift_amount) << shift_amount

        crushed_audio = audio._spawn(crushed_samples.tobytes())

        final_audio = crushed_audio.set_frame_rate(sample_rate)

        output_buffer = io.BytesIO()
        output_buffer.name = "bitcrushed.ogg"
        final_audio.export(output_buffer, format="ogg", codec="libopus")

        caption = f"Bitcrush: {bit_depth}-bit, {sample_rate}Hz"
        if random.randint(1, 3) == 1: 
            caption += "\n\n💡 Ви можете спробувати: `.bitcrush 8 8000`"

        if target_message.audio:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=output_buffer,
                caption=caption
            )
        elif target_message.voice:
            await client.send_voice(
                chat_id=message.chat.id,
                voice=output_buffer,
                caption=caption
            )

        await status_message.delete()

    except Exception as e:
        await status_message.edit_text(f"❌ Сталася помилка під час обробки:\n`{e}`")
    finally:

        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)

def register_handlers(app: Client):
    bitcrush_handler = MessageHandler(
        bitcrush_command,
        filters.command("bitcrush", prefixes=".") & filters.me
    )

    handlers_list = [bitcrush_handler]

    for handler in handlers_list:
        app.add_handler(handler)

    return handlers_list