import io
import os
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

        bit_depth = int(message.command[1]) if len(message.command) > 1 else 2

        sample_rate = int(message.command[2]) if len(message.command) > 2 else 11025
    except (ValueError, IndexError):
        await message.reply_text(
            "Неправильний формат параметрів.\n"
            "**Приклад:** `.bitcrush 2 11025`\n"
            "Використовую стандартні значення."
        )
        bit_depth = 2  
        sample_rate = 11025

    status_message = await message.reply_text("Обробка аудіо...")

    try:

        downloaded_file = await client.download_media(target_message)

        audio = AudioSegment.from_file(downloaded_file)

        crushed_audio = audio.set_frame_rate(sample_rate)

        crushed_audio = crushed_audio.set_sample_width(bit_depth)

        output_buffer = io.BytesIO()
        output_buffer.name = "bitcrushed_audio.ogg" 
        crushed_audio.export(output_buffer, format="ogg", codec="libopus")

        if target_message.audio:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=output_buffer,
                caption=f"Bitcrush: {bit_depth*8}-bit, {sample_rate}Hz"
            )
        elif target_message.voice:
            await client.send_voice(
                chat_id=message.chat.id,
                voice=output_buffer,
                caption=f"Bitcrush: {bit_depth*8}-bit, {sample_rate}Hz"
            )

        await status_message.delete()

    except Exception as e:
        await status_message.edit_text(f"Сталася помилка під час обробки: {e}")
    finally:

        if 'downloaded_file' in locals() and os.path.exists(downloaded_file):
            os.remove(downloaded_file)

def register_handlers(app: Client):
    bitcrush_handler = MessageHandler(
        bitcrush_command,
        filters.command("bitcrush", prefixes=".")
    )

    handlers_list = [bitcrush_handler]

    for handler in handlers_list:
        app.add_handler(handler)

    return handlers_list