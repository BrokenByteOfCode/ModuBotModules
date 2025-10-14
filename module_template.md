**1. Структура файлів:**
Кожен модуль — це папка всередині `ModuBotModules`. Назва папки є унікальним іменем модуля.

```
ModuBotModules/
└── example_module/
    ├── example_module.py  # Головний файл з логікою модуля
    └── reqs.txt           # (Необов'язково) Файл з залежностями
```

**2. Основний файл (`example_module.py`):**
Це серце модуля. Він повинен містити три ключові компоненти:

*   **Функція `help_info()`**:
    *   Ця функція не є обов'язковою, але дуже рекомендована.
    *   Вона повинна повертати текстовий рядок (можна використовувати Markdown), який буде показуватися, коли користувач введе команду `.help <назва_модуля>`.
    *   Це ідеальне місце для опису команд модуля та прикладів їх використання.

*   **Функції-обробники команд**:
    *   Це асинхронні функції (`async def`), які виконують роботу, коли користувач викликає команду (наприклад, `.hello`).
    *   Вони приймають два аргументи: `client` та `message`.

*   **Головна функція `register_handlers(app)`**:
    *   Це **єдина обов'язкова точка входу** для вашого бота. Система викликає саме цю функцію.
    *   Її завдання — створити об'єкти `MessageHandler` (або інші обробники Pyrogram) для кожної команди та **повернути їх у вигляді списку**.
    *   **Важливо:** Вам більше не потрібно викликати `app.add_handler` всередині цієї функції. Просто поверніть список, а ядро бота подбає про все інше.

**3. Файл залежностей (`reqs.txt`):**
Якщо ваш модуль використовує бібліотеки, яких немає в основному боті (наприклад, `gtts` для тексту в голос або `Pillow` для зображень), просто додайте їх назви у цей файл, кожну з нового рядка. Бот автоматично встановить їх при завантаженні модуля.

*Приклад `reqs.txt`:*
```
gtts
pillow
```

---

### Оновлений код-шаблон

Цей шаблон тепер міститься у вашому `module_system.py` і буде використовуватися командою `.createmodule`. Він демонструє всі найкращі практики.

```python
# modubot/module_system.py -> boilerplate

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

# 1. Функція допомоги для команди .help <module_name>
def help_info():
    """Повертає рядок з допомогою для цього модуля."""
    return """**Допомога по модулю Example**

Цей модуль демонструє базові можливості системи модулів.

**Команди:**
- `.hello`: Бот вітається з вами.
- `.echo <текст>`: Бот повторює ваш текст.

**Автор:** Ваше ім'я
"""

# 2. Функції-обробники для кожної команди
async def hello_command(client: Client, message: Message):
    """Обробник команди .hello"""
    user_name = message.from_user.first_name
    await message.reply_text(f"Привіт, {user_name}! Це демонстраційний модуль.")

async def echo_command(client: Client, message: Message):
    """Обробник команди .echo"""
    if len(message.command) > 1:
        text_to_echo = message.text.split(maxsplit=1)[1]
        await message.reply_text(text_to_echo)
    else:
        await message.reply_text("Будь ласка, вкажіть текст для повторення.\nПриклад: `.echo Привіт, світ!`")

# 3. Головна функція, яка реєструє всі обробники
def register_handlers(app: Client):
    """Створює та повертає список обробників для цього модуля."""
    
    # Створюємо обробники для кожної команди
    # Фільтр filters.me гарантує, що команда спрацює тільки від вас
    handlers_to_register = [
        MessageHandler(hello_command, filters.command("hello", prefixes=".") & filters.me),
        MessageHandler(echo_command, filters.command("echo", prefixes=".") & filters.me)
    ]
    
    # Просто повертаємо список. Ядро бота саме додасть їх.
    return handlers_to_register
```