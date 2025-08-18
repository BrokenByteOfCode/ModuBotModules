import random
import io
from gtts import gTTS
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

async def fun_help_command(client: Client, message: Message):
    help_text = """
**🥳 Доступні Fun-команди:**

`.dicksize` - Дізнайся свій справжній розмір.
`.rng [min] [max]` - Випадкове число в заданому діапазоні.
`.tts [текст]` - Перетворює текст в голосове повідомлення (uk).
`.coin` - Підкинути монетку (Орел/Решка).
`.ball [питання]` - Магічна куля 8, що дасть відповідь на все.
`.rev [текст]` - Перевертає твій текст задом наперед.
`.ship` - (у відповідь на повідомлення) Перевіряє любовну сумісність.
"""
    await message.reply_text(help_text)


async def dicksize_command(client: Client, message: Message):
    size = random.randint(1, 35)
    await message.reply_text(f"Твій розмір сьогодні: {size} см! 😎")


async def rng_command(client: Client, message: Message):
    if len(message.command) != 3:
        return await message.reply_text("Формат: `.rng [min] [max]`")
    try:
        min_val, max_val = int(message.command[1]), int(message.command[2])
    except ValueError:
        return await message.reply_text("Будь ласка, введіть дійсні числа.")
    if min_val > max_val:
        return await message.reply_text("Min не може бути більшим за Max.")
    
    random_number = random.randint(min_val, max_val)
    await message.reply_text(f"🎲 Випадкове число від {min_val} до {max_val}: **{random_number}**")


async def tts_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть текст для озвучення.")

    text_to_speak = message.text.split(maxsplit=1)[1]
    status_message = await message.reply_text("🎙️ Генерую...")
    
    try:
        audio_fp = io.BytesIO()
        tts = gTTS(text=text_to_speak, lang='uk')
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        audio_fp.name = 'voice.ogg'

        await client.send_voice(
            chat_id=message.chat.id,
            voice=audio_fp,
            reply_to_message_id=message.id
        )
        await status_message.delete()
    except Exception as e:
        await status_message.edit_text(f"Помилка: {e}")


async def coin_command(client: Client, message: Message):
    await message.reply_text(f"🪙 Випало: **{random.choice(['Орел', 'Решка'])}**")


async def ball_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("🔮 Задайте питання магічній кулі!")
    
    answers = [
        "Безперечно.", "Це точно.", "Без сумнівів.", "Так, безумовно.",
        "Можеш на це розраховувати.", "Наскільки я бачу, так.", "Найімовірніше.",
        "Перспективи хороші.", "Так.", "Знаки кажуть - так.", "Відповідь туманна, спробуй ще.",
        "Запитай пізніше.", "Краще не казати тобі зараз.", "Неможливо передбачити зараз.",
        "Сконцентруйся і запитай знову.", "Навіть не думай.", "Моя відповідь - ні.",
        "За моїми даними - ні.", "Перспективи не дуже хороші.", "Дуже сумнівно."
    ]
    await message.reply_text(f"🎱 **{random.choice(answers)}**")


async def reverse_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть текст, який потрібно перевернути.")
    
    text_to_reverse = message.text.split(maxsplit=1)[1]
    reversed_text = text_to_reverse[::-1]
    await message.reply_text(reversed_text)


async def ship_command(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Цю команду потрібно використовувати у відповідь на повідомлення.")
    
    user1 = message.from_user
    user2 = message.reply_to_message.from_user
    
    seed = str(sorted([user1.id, user2.id]))
    random.seed(seed)
    
    percentage = random.randint(0, 100)
    
    emoji = "💔"
    if percentage > 40: emoji = "❤️"
    if percentage > 75: emoji = "💞"
    if percentage == 100: emoji = "💍"
    
    await message.reply_text(
        f"Сумісність між {user1.first_name} та {user2.first_name}:\n`{percentage}%` {emoji}"
    )

def register_handlers(app: Client):
    handlers_list = [
        MessageHandler(fun_help_command, filters.command("funhelp", prefixes=".")),
        MessageHandler(dicksize_command, filters.command("dicksize", prefixes=".")),
        MessageHandler(rng_command, filters.command("rng", prefixes=".")),
        MessageHandler(tts_command, filters.command("tts", prefixes=".")),
        MessageHandler(coin_command, filters.command("coin", prefixes=".")),
        MessageHandler(ball_command, filters.command("ball", prefixes=".")),
        MessageHandler(reverse_command, filters.command("rev", prefixes=".")),
        MessageHandler(ship_command, filters.command("ship", prefixes="."))
    ]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list