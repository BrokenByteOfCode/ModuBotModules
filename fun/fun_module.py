import random
import io
import time
from gtts import gTTS
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pyrogram.enums import ParseMode

async def fun_help_command(client: Client, message: Message):
    help_text = """
**🥳 Доступні Fun-команди:**

`.dicksize` - Дізнайся свій справжній розмір.
`.rng [min] [max]` - Випадкове число в заданому діапазоні.
`.tts [текст]` - Перетворює текст в голосове повідомлення.
`.coin` - Підкинути монетку (Орел/Решка).
`.ball [питання]` - Магічна куля 8, що дасть відповідь на все.
`.rev [текст]` - Перевертає твій текст задом наперед.
`.ship` - (у відповідь на повідомлення) Перевіряє любовну сумісність.
`.echo [текст]` - Повторює твоє повідомлення.
`.mock [текст]` - ПеРеТвОрЮє ТеКсТ В мОкІнГ стиль.
`.choose [варіант1] [варіант2] ...` - Обирає випадковий варіант зі списку.
`.roll [кількість]d[гранів]` - Кидає кубики (наприклад: 2d6).
`.iq` - Перевіряє твій рівень IQ.
`.slot` - Спробуй удачу в слот-машині.
`.ascii [текст]` - Перетворює текст в ASCII арт.
`.uwu [текст]` - Перетворює текст в UwU стиль.
`.typing` - Демонструє швидкість друку.
`.fortune` - Отримай випадкове пророцтво.
`.rate [об'єкт]` - Оцінює щось від 1 до 10.
`.vibe` - Перевіряє твій сьогоднішній настрій.
`.slap` - (у відповідь) Дає ляпаса користувачеві.
`.hug` - (у відповідь) Обіймає користувача.
`.dice` - Кидає звичайний кубик (1-6).
`.percent [що саме]` - Показує випадковий відсоток чогось.
"""
    await message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def tts_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть текст для озвучення.")

    text_to_speak = message.text.split(maxsplit=1)[1]
    status_message = await message.reply_text("🎙️ Генерую голосове повідомлення...")

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

async def echo_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть текст для повторення.")
    text_to_echo = message.text.split(maxsplit=1)[1]
    await message.reply_text(text_to_echo)

async def mock_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть текст для перетворення в мокінг стиль.")
    text = message.text.split(maxsplit=1)[1]
    mocked_text = ''.join(char.upper() if i % 2 == 0 else char.lower() for i, char in enumerate(text))
    await message.reply_text(mocked_text)

async def choose_command(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text("Вкажіть принаймні два варіанти для вибору.")
    choices = message.command[1:]
    chosen = random.choice(choices)
    await message.reply_text(f"🎯 Я обираю: **{chosen}**", parse_mode=ParseMode.MARKDOWN)

async def roll_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Формат: `.roll [кількість]d[гранів]` (наприклад: 2d6)")
    
    dice_notation = message.command[1]
    try:
        if 'd' not in dice_notation:
            raise ValueError
        count, sides = dice_notation.split('d')
        count, sides = int(count), int(sides)
        if count <= 0 or sides <= 0 or count > 20:
            raise ValueError
    except ValueError:
        return await message.reply_text("Неправильний формат! Приклад: 2d6")
    
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls)
    
    if count == 1:
        result = f"🎲 Випало: **{total}**"
    else:
        result = f"🎲 Кинув {count}d{sides}: {rolls}\nСума: **{total}**"
    
    await message.reply_text(result, parse_mode=ParseMode.MARKDOWN)

async def iq_command(client: Client, message: Message):
    user_id = message.from_user.id
    random.seed(f"iq_{user_id}")
    iq = random.randint(50, 200)
    
    if iq < 70: emoji = "🤡"
    elif iq < 90: emoji = "😅"
    elif iq < 110: emoji = "🙂"
    elif iq < 130: emoji = "🤓"
    elif iq < 160: emoji = "🧠"
    else: emoji = "🚀"
    
    await message.reply_text(f"Твій IQ: **{iq}** {emoji}", parse_mode=ParseMode.MARKDOWN)

async def slot_command(client: Client, message: Message):
    symbols = ['🍎', '🍊', '🍋', '🍇', '🍒', '🔔', '💎', '7️⃣']
    reels = [random.choice(symbols) for _ in range(3)]
    
    result_text = f"🎰 {' '.join(reels)}\n\n"
    
    if len(set(reels)) == 1:
        result_text += "🎉 **ДЖЕКПОТ!** Всі символи однакові!"
    elif len(set(reels)) == 2:
        result_text += "✨ Два однакових! Непогано!"
    else:
        result_text += "😔 Спробуй ще раз!"
    
    await message.reply_text(result_text, parse_mode=ParseMode.MARKDOWN)

async def ascii_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть текст для ASCII перетворення.")
    
    text = message.text.split(maxsplit=1)[1]
    if len(text) > 20:
        return await message.reply_text("Текст занадто довгий! Максимум 20 символів.")
    
    ascii_art = f"```\n{text.upper()}\n{'=' * len(text)}\n```"
    await message.reply_text(ascii_art, parse_mode=ParseMode.MARKDOWN)

async def uwu_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть текст для UwU перетворення.")
    
    text = message.text.split(maxsplit=1)[1]
    uwu_text = text.replace('r', 'w').replace('R', 'W').replace('л', 'в').replace('Л', 'В')
    uwu_text += " " + random.choice(['uwu', 'owo', '>w<', 'uwu~', 'owo~'])
    
    await message.reply_text(uwu_text)

async def typing_command(client: Client, message: Message):
    start_time = time.time()
    test_message = await message.reply_text("Напиши 'готово' коли побачиш це повідомлення!")
    
    wpm = random.randint(20, 120)
    await message.reply_text(f"⌨️ Твоя швидкість друку: **{wpm} WPM**", parse_mode=ParseMode.MARKDOWN)

async def fortune_command(client: Client, message: Message):
    fortunes = [
        "Сьогодні тебе чекає приємний сюрприз! 🌟",
        "Зустрінеш старого друга в несподіваному місці. 👥",
        "Твоя впевненість відкриє нові можливості. 💪",
        "Час для творчості! Твої ідеї знайдуть втілення. 🎨",
        "Будь обережний з фінансами цього тижня. 💰",
        "Любов постукає у твої двері найближчим часом. 💕",
        "Відпочинок принесе неочікувані відкриття. 🏖️",
        "Твої зусилля нарешті будуть винагороджені. 🏆",
    ]
    
    fortune = random.choice(fortunes)
    await message.reply_text(f"🔮 **Твоє пророцтво:**\n{fortune}", parse_mode=ParseMode.MARKDOWN)

async def rate_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть, що потрібно оцінити.")
    
    item = message.text.split(maxsplit=1)[1]
    rating = random.randint(1, 10)
    
    if rating <= 3: emoji = "👎"
    elif rating <= 6: emoji = "😐"
    elif rating <= 8: emoji = "👍"
    else: emoji = "🔥"
    
    await message.reply_text(f"Оцінка для '{item}': **{rating}/10** {emoji}", parse_mode=ParseMode.MARKDOWN)

async def vibe_command(client: Client, message: Message):
    vibes = [
        ("😴", "Сонливий", "Час для кави!"),
        ("😎", "Крутий", "Сьогодні твій день!"),
        ("🤪", "Божевільний", "Енергія через край!"),
        ("😇", "Спокійний", "Дзен-режим активований."),
        ("🤔", "Задумливий", "Філософський настрій."),
        ("🔥", "Вогняний", "Готовий підкорювати світ!"),
        ("🌈", "Веселковий", "Все барви емоцій!"),
        ("💪", "Мотивований", "Ніщо не зупинить!"),
    ]
    
    emoji, mood, description = random.choice(vibes)
    await message.reply_text(f"{emoji} **Твій настрій сьогодні:** {mood}\n{description}", parse_mode=ParseMode.MARKDOWN)

async def slap_command(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Цю команду потрібно використовувати у відповідь на повідомлення.")
    
    target = message.reply_to_message.from_user.first_name
    slapper = message.from_user.first_name
    
    actions = [
        f"дав ляпаса",
        f"легенько вдарив",
        f"шльопнув",
        f"дав п'ять по обличчю",
        f"провів виховну бесіду кулаком"
    ]
    
    action = random.choice(actions)
    await message.reply_text(f"👋 **{slapper}** {action} **{target}**!", parse_mode=ParseMode.MARKDOWN)

async def hug_command(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Цю команду потрібно використовувати у відповідь на повідомлення.")
    
    target = message.reply_to_message.from_user.first_name
    hugger = message.from_user.first_name
    
    actions = [
        f"міцно обійняв",
        f"тепло обійняв",
        f"дружньо обійняв",
        f"ніжно обійняв",
        f"по-братськи обійняв"
    ]
    
    action = random.choice(actions)
    await message.reply_text(f"🤗 **{hugger}** {action} **{target}**!", parse_mode=ParseMode.MARKDOWN)

async def dice_command(client: Client, message: Message):
    result = random.randint(1, 6)
    dice_faces = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
    await message.reply_text(f"{dice_faces[result-1]} Випало: **{result}**", parse_mode=ParseMode.MARKDOWN)

async def percent_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть, відсоток чого потрібно показати.")
    
    item = message.text.split(maxsplit=1)[1]
    percentage = random.randint(0, 100)
    
    await message.reply_text(f"📊 {item}: **{percentage}%**", parse_mode=ParseMode.MARKDOWN)

def register_handlers(app: Client):
    handlers_list = [
        MessageHandler(fun_help_command, filters.command("funhelp", prefixes=".")),
        MessageHandler(dicksize_command, filters.command("dicksize", prefixes=".")),
        MessageHandler(rng_command, filters.command("rng", prefixes=".")),
        MessageHandler(tts_command, filters.command("tts", prefixes=".")),
        MessageHandler(coin_command, filters.command("coin", prefixes=".")),
        MessageHandler(ball_command, filters.command("ball", prefixes=".")),
        MessageHandler(reverse_command, filters.command("rev", prefixes=".")),
        MessageHandler(ship_command, filters.command("ship", prefixes=".")),
        MessageHandler(echo_command, filters.command("echo", prefixes=".")),
        MessageHandler(mock_command, filters.command("mock", prefixes=".")),
        MessageHandler(choose_command, filters.command("choose", prefixes=".")),
        MessageHandler(roll_command, filters.command("roll", prefixes=".")),
        MessageHandler(iq_command, filters.command("iq", prefixes=".")),
        MessageHandler(slot_command, filters.command("slot", prefixes=".")),
        MessageHandler(ascii_command, filters.command("ascii", prefixes=".")),
        MessageHandler(uwu_command, filters.command("uwu", prefixes=".")),
        MessageHandler(typing_command, filters.command("typing", prefixes=".")),
        MessageHandler(fortune_command, filters.command("fortune", prefixes=".")),
        MessageHandler(rate_command, filters.command("rate", prefixes=".")),
        MessageHandler(vibe_command, filters.command("vibe", prefixes=".")),
        MessageHandler(slap_command, filters.command("slap", prefixes=".")),
        MessageHandler(hug_command, filters.command("hug", prefixes=".")),
        MessageHandler(dice_command, filters.command("dice", prefixes=".")),
        MessageHandler(percent_command, filters.command("percent", prefixes="."))
    ]
    for handler in handlers_list:
        app.add_handler(handler)
    return handlers_list