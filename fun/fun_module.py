import random
import io
from gtts import gTTS
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

async def fun_help_command(client: Client, message: Message):
    help_text = """
**🥳 Доступні Fun-команди:**

`<code>.dicksize</code>` - Дізнайся свій справжній розмір.

`<code>.rng [min] [max]</code>` - Випадкове число в заданому діапазоні.
*Приклад:* `.rng 1 100`

`<code>.tts [текст]</code>` - Перетворює текст в голосове повідомлення (мова: українська).
*Приклад:* `.tts привіт, як справи`
"""
    await message.reply_text(help_text, parse_mode="markdown")


async def dicksize_command(client: Client, message: Message):
    size = random.randint(1, 35)
    await message.reply_text(f"Твій розмір сьогодні: {size} см")


async def rng_command(client: Client, message: Message):
    if len(message.command) != 3:
        await message.reply_text("Неправильний формат. Використовуйте: `.rng [min] [max]`")
        return

    try:
        min_val = int(message.command[1])
        max_val = int(message.command[2])
    except ValueError:
        await message.reply_text("Будь ласка, введіть дійсні числа.")
        return

    if min_val > max_val:
        await message.reply_text("Мінімальне значення не може бути більшим за максимальне.")
        return

    random_number = random.randint(min_val, max_val)
    await message.reply_text(f"🎲 Випадкове число від {min_val} до {max_val}: **{random_number}**")


async def tts_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Вкажіть текст для перетворення в голос.\nПриклад: `.tts Привіт, світ`")
        return

    text_to_speak = message.text.split(maxsplit=1)[1]
    
    status_message = await message.reply_text("🎙️ Генерую голосове повідомлення...")

    try:
        audio_fp = io.BytesIO()
        tts = gTTS(text=text_to_speak, lang='uk')
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)

        await client.send_voice(
            chat_id=message.chat.id,
            voice=audio_fp,
            reply_to_message_id=message.id
        )
        await status_message.delete()

    except Exception as e:
        await status_message.edit_text(f"Виникла помилка під час генерації аудіо: {e}")

def register_handlers(app: Client):
    fun_help_handler = MessageHandler(
        fun_help_command,
        filters.command("funhelp", prefixes=".")
    )
    
    dicksize_handler = MessageHandler(
        dicksize_command,
        filters.command("dicksize", prefixes=".")
    )
    
    rng_handler = MessageHandler(
        rng_command,
        filters.command("rng", prefixes=".")
    )
    
    tts_handler = MessageHandler(
        tts_command,
        filters.command("tts", prefixes=".")
    )

    handlers_list = [fun_help_handler, dicksize_handler, rng_handler, tts_handler]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list