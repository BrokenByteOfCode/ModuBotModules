import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pathlib import Path
from dotenv import load_dotenv, set_key, find_dotenv

model = None
chat_sessions = {}
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

def initialize_gemini():
    global model
    load_dotenv()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY не знайдено. Очікування ключа через команду .api")
        model = None
        return False
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            safety_settings=safety_settings
        )
        print("Модуль Gemini AI успішно завантажено з кастомними налаштуваннями безпеки.")
        return True
    except Exception as e:
        print(f"Помилка ініціалізації Gemini: {e}")
        model = None
        return False

async def set_api_key_command(client: Client, message: Message):
    global model
    
    if len(message.command) < 2:
        await message.reply_text(
            "Будь ласка, вкажіть ваш API ключ.\n"
            "Приклад: `.api YOUR_API_KEY`\n\n"
            "Ваш ключ буде збережено у файл `.env`."
        )
        return

    new_api_key = message.command[1]
    
    dotenv_path = find_dotenv()
    if not dotenv_path:
        dotenv_path = os.path.join(os.getcwd(), '.env')

    try:
        set_key(dotenv_path, "GEMINI_API_KEY", new_api_key)
        await message.reply_text("`API ключ збережено. Ініціалізую модель...`")

        if initialize_gemini():
            await message.reply_text("✅ **Успіх!** Модель Gemini активовано.")
        else:
            await message.reply_text("❌ **Помилка.** Ключ збережено, але модель не вдалося ініціалізувати. Можливо, ключ недійсний.")
            
    except Exception as e:
        await message.reply_text(f"**Не вдалося зберегти ключ:**\n`{e}`")

async def clear_memory_command(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in chat_sessions:
        del chat_sessions[chat_id]
        await message.reply_text("🧹 **Пам'ять для цього чату очищено.**")
        print(f"Сесію чату очищено для ID: {chat_id}")
    else:
        await message.reply_text("🤔 Для цього чату немає збереженої історії.")

async def ai_command(client: Client, message: Message):
    if not model:
        await message.reply_text(
            "Помилка: Модуль Gemini AI не налаштовано.\n"
            "Встановіть API ключ, надіславши мені в особисті повідомлення:\n"
            "`.api ВАШ_КЛЮЧ`"
        )
        return

    if len(message.command) < 2 and not (message.reply_to_message and message.reply_to_message.media):
        await message.reply_text(
            "Введіть запит після `.ai` або дайте відповідь на файл цією командою."
        )
        return

    prompt_text = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else ""
    user_name = message.from_user.first_name
    chat_id = message.chat.id
    
    full_prompt_text = f"{user_name}: {prompt_text}"

    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = model.start_chat(history=[])
        print(f"Створено нову сесію чату для ID: {chat_id}")

    thinking_message = await message.reply_text("<code>Запит прийнято, обробляю...</code>")
    
    file_path = None
    content_for_gemini = [full_prompt_text]

    try:
        if message.reply_to_message and message.reply_to_message.media:
            replied_msg = message.reply_to_message
            if replied_msg.photo or replied_msg.document:
                await thinking_message.edit_text("<code>Завантажую файл...</code>")
                file_path = await client.download_media(replied_msg)
                await thinking_message.edit_text("<code>Файл завантажено. Аналізую...</code>")
                uploaded_file = genai.upload_file(path=file_path)
                content_for_gemini.insert(0, uploaded_file)
            else:
                 await thinking_message.edit_text("<code>Цей тип файлу не підтримується.</code>")
                 return

        chat_session = chat_sessions[chat_id]
        response = await chat_session.send_message_async(content_for_gemini)
        
        await thinking_message.edit_text(response.text)

    except Exception as e:
        await thinking_message.edit_text(f"**Помилка Gemini AI:**\n`{e}`")
        if chat_id in chat_sessions:
            del chat_sessions[chat_id]
            
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

def register_handlers(app: Client):
    initialize_gemini()
    
    api_key_handler = MessageHandler(
        set_api_key_command,
        filters.command("api", prefixes=".") & filters.me & filters.private
    )
    
    ai_handler = MessageHandler(
        ai_command,
        filters.command("ai", prefixes=".")
    )
    
    clear_handler = MessageHandler(
        clear_memory_command,
        filters.command("clear", prefixes=".")
    )
    
    handlers_list = [api_key_handler, ai_handler, clear_handler]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list