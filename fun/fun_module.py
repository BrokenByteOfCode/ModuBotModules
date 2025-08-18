import random
import io
import os
import wave
import dotenv
from gtts import gTTS

import google.generativeai as genai

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pyrogram.enums import ParseMode

dotenv.load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"ПОМИЛКА: Не вдалося налаштувати Gemini API: {e}")
        GEMINI_API_KEY = None

async def fun_help_command(client: Client, message: Message):
    help_text = """
**🥳 Доступні Fun-команди:**

`.dicksize` - Дізнайся свій справжній розмір.
`.rng [min] [max]` - Випадкове число в заданому діапазоні.
`.tts [текст]` - Перетворює текст в голосове повідомлення (Gemini / gTTS).
`.coin` - Підкинути монетку (Орел/Решка).
`.ball [питання]` - Магічна куля 8, що дасть відповідь на все.
`.rev [текст]` - Перевертає твій текст задом наперед.
`.ship` - (у відповідь на повідомлення) Перевіряє любовну сумісність.
"""
    await message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def tts_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть текст для озвучення.")

    text_to_speak = message.text.split(maxsplit=1)[1]
    status_message = await message.reply_text("🎙️ Обробка запиту...")

    if GEMINI_API_KEY:
        try:
            await status_message.edit_text("🎙️ Генерую аудіо через **Gemini API**...", parse_mode=ParseMode.MARKDOWN)

            model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-tts")

            voices = ["Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede", "Callirrhoe"]

            generation_config = {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": random.choice(voices)
                        }
                    }
                }
            }

            response = model.generate_content(
                contents=f"Say cheerfully: {text_to_speak}",
                generation_config=generation_config
            )

            pcm_data = response.candidates[0].content.parts[0].inline_data.data

            audio_fp = io.BytesIO()
            with wave.open(audio_fp, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(pcm_data)
            audio_fp.seek(0)
            audio_fp.name = "gemini_voice.wav"

            await client.send_voice(message.chat.id, voice=audio_fp, reply_to_message_id=message.id)
            await status_message.delete()
            return

        except Exception as e:
            await status_message.edit_text(f"⚠️ Помилка Gemini API: `{e}`\n\n🔄 Спробую через gTTS...")

    try:
        if not GEMINI_API_KEY:
            await status_message.edit_text("🔑 API ключ Gemini не знайдено.\n🎙️ Генерую аудіо через **gTTS**...", parse_mode=ParseMode.MARKDOWN)

        audio_fp = io.BytesIO()
        tts = gTTS(text=text_to_speak, lang='uk')
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        audio_fp.name = 'gtts_voice.ogg'

        await client.send_voice(message.chat.id, voice=audio_fp, reply_to_message_id=message.id)
        await status_message.delete()

    except Exception as e:
        await status_message.edit_text(f"❌ Виникла помилка під час генерації аудіо: {e}")

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
    await message.reply_text(
        f"🎲 Випадкове число від {min_val} до {max_val}: **{random_number}**",
        parse_mode=ParseMode.MARKDOWN
    )

async def coin_command(client: Client, message: Message):
    await message.reply_text(
        f"🪙 Випало: **{random.choice(['Орел', 'Решка'])}**",
        parse_mode=ParseMode.MARKDOWN
    )

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
    await message.reply_text(f"🎱 **{random.choice(answers)}**", parse_mode=ParseMode.MARKDOWN)

async def reverse_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть текст, який потрібно перевернути.")
    text_to_reverse = message.text.split(maxsplit=1)[1]
    reversed_text = text_to_reverse[::-1]
    await message.reply_text(reversed_text)

async def ship_command(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Цю команду потрібно використовувати у відповідь на повідомлення.")

    user1, user2 = message.from_user, message.reply_to_message.from_user
    seed = str(sorted([user1.id, user2.id]))
    random.seed(seed)
    percentage = random.randint(0, 100)

    emoji = "💔"
    if percentage > 40: emoji = "❤️"
    if percentage > 75: emoji = "💞"
    if percentage == 100: emoji = "💍"

    await message.reply_text(
        f"Сумісність між {user1.first_name} та {user2.first_name}:\n`{percentage}%` {emoji}",
        parse_mode=ParseMode.MARKDOWN
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