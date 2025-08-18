import random
import io
import time
from gtts import gTTS
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from art import text2art

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
`.fortune` - Отримай випадкове пророцтво.
`.rate [об'єкт]` - Оцінює щось від 1 до 10.
`.vibe` - Перевіряє твій сьогоднішній настрій.
`.slap` - (у відповідь) Дає ляпаса користувачеві.
`.hug` - (у відповідь) Обіймає користувача.
`.dice` - Кидає звичайний кубик (1-6).
`.percent [що саме]` - Показує випадковий відсоток чогось.

**🎭 RP Команди (працюють по тексту):**
Напиши просто: кусьнути, вдарити, поцілувати, обійняти, покарати, домінувати, 
змусити, трахнути, вбити, лизнути, погладити, шльопнути, задушити, знищити, 
розірвати, роздавити, спалити, заморозити, вкрасти, пограбувати та багато іншого!
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
    if len(text) > 15:
        return await message.reply_text("Текст занадто довгий! Максимум 15 символів.")
    
    try:
        fonts = ['small', 'block', 'digital', '3-d', 'mini', 'script', 'slant']
        font = random.choice(fonts)
        ascii_art = text2art(text, font=font)
        
        if len(ascii_art) > 4000:
            ascii_art = text2art(text, font='mini')
        
        await message.reply_text(f"```\n{ascii_art}\n```", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        simple_ascii = f"```\n{text.upper()}\n{'=' * len(text)}\n```"
        await message.reply_text(simple_ascii, parse_mode=ParseMode.MARKDOWN)

async def uwu_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Вкажіть текст для UwU перетворення.")
    
    text = message.text.split(maxsplit=1)[1]
    uwu_text = text.replace('r', 'w').replace('R', 'W').replace('л', 'в').replace('Л', 'В')
    uwu_text += " " + random.choice(['uwu', 'owo', '>w<', 'uwu~', 'owo~'])
    
    await message.reply_text(uwu_text)

async def fortune_command(client: Client, message: Message):
    fortunes = [
        "Твої зусилля нарешті будуть винагороджені.",
        "Вбий себе.",
        "Чи тобі колись казали, що ти тупий? Ти тупий.",
        "Піська твоя не така вже й велика.",
        "Твоя мама пишається тобою, але ти не заслуговуєш на це.",
        "Твоя дівчина зраджує тобі з твоїм другом.",
        "Твій кіт думає, що ти тупий.",
        "Твій пес хоче, щоб ти перестав його дратувати.",
        "Твій комп'ютер скоро зламається, і ти втратиш всі дані.",
        "Твоя робота скоро стане нудною і безперспективною.",
        "Твоя улюблена їжа скоро стане несмачною.",
        "Твій телефон скоро розрядиться, і ти не зможеш його зарядити.",
        "Твоя улюблена гра скоро перестане оновлюватися.",
        "Твоя улюблена музика скоро стане застарілою.",
        "Твоя улюблена книга скоро буде заборонена.",
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

async def rp_action_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return
    
    lines = message.text.strip().split('\n')
    first_line = lines[0].lower().strip()
    
    actor = message.from_user.first_name
    target = message.reply_to_message.from_user.first_name
    
    rp_actions = {
        "кусьнути": ("🦷", ["укусив", "кусьнув", "вкусив", "прикусив"]),
        "вдарити": ("👊", ["вдарив", "залупив", "дав в пику", "шарахнув"]),
        "поцілувати": ("💋", ["поцілував", "чмокнув", "дав поцілунок", "поцілував в губи"]),
        "обійняти": ("🤗", ["обійняв", "притиснув до себе", "міцно обійняв"]),
        "покарати": ("⚡", ["покарав", "наказав", "дав урок", "виховав"]),
        "домінувати": ("👑", ["домінував над", "підкорив", "керував", "панував над"]),
        "змусити": ("⛓️", ["змусив", "приневолив", "примусив", "наказав"]),
        "трахнути": ("🔞", ["трахнув", "використав", "взяв", "відімів"]),
        "вбити": ("💀", ["вбив", "прикінчив", "знищив", "убив"]),
        "лизнути": ("👅", ["лизнув", "облизав", "язиком провів"]),
        "погладити": ("✋", ["погладив", "провів рукою", "приласкав"]),
        "шльопнути": ("👋", ["шльопнув", "дав ляпаса", "ударив долонею"]),
        "задушити": ("🤐", ["задушив", "стиснув горло", "почав душити"]),
        "знищити": ("💥", ["знищив", "розніс", "стер з лиця землі"]),
        "розірвати": ("💢", ["розірвав", "розшматував", "порвав на шматки"]),
        "роздавити": ("🗿", ["роздавив", "розплющив", "стиснув"]),
        "спалити": ("🔥", ["спалив", "підпалив", "обпік", "обгорів"]),
        "заморозити": ("❄️", ["заморозив", "покрив льодом", "скував холодом"]),
        "вкрасти": ("🦹", ["вкрав", "поцупив", "украв", "забрав"]),
        "пограбувати": ("💰", ["пограбував", "обібрав", "обчистив"]),
        "лягати": ("🛏️", ["ліг на", "завалився на", "притиснув"]),
        "сісти": ("💺", ["сів на", "присів на", "розташувався на"]),
        "взяти": ("✊", ["взяв", "схопив", "захопив", "підхопив"]),
        "кинути": ("🎯", ["кинув", "швырнув", "метнув", "запустив"]),
        "штовхнути": ("👐", ["штовхнув", "пхнув", "відштовхнув"]),
        "потягнути": ("🤜", ["потягнув", "витягнув", "потяг за собою"]),
        "підняти": ("🏋️", ["підняв", "підтягнув", "витяг", "піднімав"]),
        "кидати": ("💥", ["кидав", "метав", "швиряв у"]),
        "відлупити": ("🥊", ["відлупив", "відмутузив", "відтузив"]),
        "мордувати": ("😤", ["мордував", "бив по морді", "зрив башню"]),
        "хапати": ("👺", ["хапав", "хватав", "ловив", "тримав"]),
        "кусати": ("🦈", ["кусав", "гриз", "жував"]),
        "душити": ("🤫", ["душив", "стискав шию", "не давав дихати"]),
        "рвати": ("🌪️", ["рвав", "шматував", "розривав"]),
        "палити": ("🔥", ["палив", "підпалював", "жарив"]),
        "морозити": ("🧊", ["морозив", "студив", "охолоджував"])
    }
    
    for keyword, (emoji, actions) in rp_actions.items():
        if keyword in first_line:
            action = random.choice(actions)
            response_text = f"{emoji} **{actor}** {action} **{target}**!"
            
            rest_text = first_line.replace(keyword, '').strip()
            if len(lines) > 1:
                additional_text = '\n'.join(lines[1:]).strip()
                if rest_text:
                    response_text += f", кажучи \"{rest_text} {additional_text}\""
                elif additional_text:
                    response_text += f", кажучи \"{additional_text}\""
            elif rest_text:
                response_text += f", кажучи \"{rest_text}\""
            
            await message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
            return

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
        MessageHandler(fortune_command, filters.command("fortune", prefixes=".")),
        MessageHandler(rate_command, filters.command("rate", prefixes=".")),
        MessageHandler(vibe_command, filters.command("vibe", prefixes=".")),
        MessageHandler(dice_command, filters.command("dice", prefixes=".")),
        MessageHandler(percent_command, filters.command("percent", prefixes=".")),
        MessageHandler(rp_action_handler, filters.text & filters.reply)
    ]
    return handlers_list