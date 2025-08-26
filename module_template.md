**1. Структура файлів:**
Кожен модуль — це папка всередині `ModuBotModules`.

ModuBotModules/
└── example_module/
    ├── module_logic.py  # Головний файл з логікою модуля
    └── reqs.txt         # (Необов'язково) Файл з залежностями (бібліотеками)

**2. Основний файл (`module_logic.py`):**
Це серце модуля. Він повинен містити:
*   **Функції-обробники команд**: Це асинхронні функції (`async def`), які виконують роботу, коли користувач викликає команду (наприклад, `.hello`).
*   **Головна функція `register_handlers(app)`**: Це єдина точка входу для твого бота. `app.py` викликає саме цю функцію. Її завдання — створити об'єкти `MessageHandler` для кожної команди та повернути їх у вигляді списку. Це критично важливо для можливості перезавантаження модуля "на льоту".

**3. Файл залежностей (`reqs.txt`):**
Якщо твій модуль використовує бібліотеки, яких немає в основному `requirements.txt` (наприклад, `gtts` для тексту в голос), просто додай їх назви у цей файл, кожну з нового рядка. Бот автоматично встановить їх при завантаженні модуля.

# Приклад reqs.txt
gtts
pillow

Код шаблон

# module_template.py
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

async def hello_command(client: Client, message: Message):
    user_name = message.from_user.first_name
    await message.reply_text(f"Привіт, {user_name}! Це демонстраційний модуль.")

async def echo_command(client: Client, message: Message):
    if len(message.command) > 1:
        text_to_echo = message.text.split(maxsplit=1)[1]
        await message.reply_text(text_to_echo)
    else:
        await message.reply_text("Будь ласка, вкажіть текст для повторення.\nПриклад: `.echo Привіт, світ!`")

def register_handlers(app: Client):
    
    hello_handler = MessageHandler(
        hello_command,
        filters.command("hello", prefixes=".")
    )
    
    echo_handler = MessageHandler(
        echo_command,
        filters.command("echo", prefixes=".")
    )

    handlers_list = [hello_handler, echo_handler]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list