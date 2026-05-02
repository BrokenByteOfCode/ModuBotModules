### Документація по створенню модулів для ModuBot

Ця інструкція описує, як створювати власні модулі, використовуючи всі сучасні можливості платформи ModuBot.

**1. Структура файлів:**
Кожен модуль — це папка всередині `ModuBotModules`. Назва папки є унікальним іменем модуля.

```
ModuBotModules/
└── example_module/
    ├── example_module.py  # Головний файл з логікою модуля
    └── reqs.txt           # (Необов'язково) Файл з залежностями
```

**2. Файл залежностей (`reqs.txt`):**
Це потужний інструмент для керування залежностями вашого модуля. Він підтримує два типи залежностей:

*   **PyPI бібліотеки:** Якщо ваш модуль використовує сторонні бібліотеки (наприклад, `requests` або `Pillow`), просто вкажіть їх назви, кожну з нового рядка.
*   ** Залежності від інших модулів:** Якщо ваш модуль залежить від функціоналу іншого модуля, вкажіть його назву у фігурних дужках `{}`. Ви можете перерахувати кілька модулів через кому.

Система автоматично встановить/завантажить усі залежності перед тим, як завантажити ваш модуль.

*Приклад `reqs.txt`:*
```
# Встановлює бібліотеку Pillow з PyPI
Pillow

# Вимагає, щоб модулі utils_module та logger_module були завантажені
{utils_module, logger_module} 
```

**3. Основний файл (`example_module.py`):**
Це серце модуля. Він повинен містити ключові компоненти:

*   **Функція `help_info()`**: (Рекомендовано)
    *   Повертає текстовий рядок (з підтримкою Markdown), який буде показано за командою `.help <назва_модуля>`. Це ідеальне місце для документації ваших команд.

*   **Функції-обробники команд**:
    *   Асинхронні функції (`async def`), які виконують логіку команди.

*   **Головна функція `register_handlers(app)`**: (Обов'язково)
    *   Єдина точка входу. Система викликає цю функцію для реєстрації команд.
    *   Вона повинна створити обробники Pyrogram (`MessageHandler` тощо) та **повернути їх у вигляді списку**. Ядро бота саме додасть їх.

*   ** Взаємодія між модулями**:
    *   Ви можете викликати функції з інших завантажених модулів. Це робиться через спеціальний доступ до системи модулів.

    ```python
    # Отримуємо доступ до головного екземпляра бота
    bot = client.bot_instance
    
    # Через нього отримуємо доступ до потрібного модуля
    utils = bot.module_system.get_module("utils_module")
    
    # Перевіряємо, чи модуль завантажено, і викликаємо його функцію
    if utils:
        utils.some_function()
    ```

---

### Практичний приклад: Модуль `prettify` залежить від `formatter`

**1. Модуль `formatter` (залежність)**

*   `ModuBotModules/formatter/formatter.py`:
    ```python
    def help_info():
        return "Модуль з утилітами форматування. Не має власних команд."

    def make_pretty(text: str) -> str:
        """Обгортає текст у зірочки."""
        return f"✨ {text} ✨"

    def register_handlers(app):
        # Цей модуль не реєструє жодної команди
        return []
    ```
*   У нього немає `reqs.txt`.

**2. Модуль `prettify` (основний)**

*   `ModuBotModules/prettify/reqs.txt`:
    ```
    {formatter}
    ```

*   `ModuBotModules/prettify/prettify.py`:
    ```python
    from pyrogram import Client, filters
    from pyrogram.handlers import MessageHandler
    from pyrogram.types import Message

    def help_info():
        return """**Модуль Prettify**
    
    Використовує модуль `formatter` для красивого виводу тексту.
    
    **Команди:**
    - `.pretty <текст>`: Робить текст красивим.
    """

    async def pretty_command(client: Client, message: Message):
        bot = client.bot_instance
        formatter_module = bot.module_system.get_module("formatter")

        if not formatter_module:
            await message.reply_text("❌ Помилка: модуль-залежність `formatter` не знайдено!")
            return

        if len(message.command) > 1:
            text_to_format = message.text.split(maxsplit=1)[1]
            # Викликаємо функцію з іншого модуля
            formatted_text = formatter_module.make_pretty(text_to_format)
            await message.reply_text(formatted_text)
        else:
            await message.reply_text("Введіть текст для форматування.")

    def register_handlers(app: Client):
        return [
            MessageHandler(pretty_command, filters.command("pretty", ".") & filters.me)
        ]
    ```

Тепер, коли ви дасте команду `.load prettify`, ModuBot автоматично завантажить `formatter` (навіть завантажить його з репозиторію, якщо потрібно), а потім завантажить `prettify`. Після цього команда `.pretty test` успішно викличе функцію з модуля `formatter` і видасть результат.