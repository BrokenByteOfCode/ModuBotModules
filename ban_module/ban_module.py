from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pyrogram.errors import FloodWait, ChatAdminRequired, UserAdminInvalid, PeerIdInvalid
import asyncio
import re

async def ban_command(client: Client, message: Message):
    try:
        if not message.chat or message.chat.type == "private":
            await message.edit_text("❌ Ця команда працює тільки в групах/каналах")
            return

        admin_status = await client.get_chat_member(message.chat.id, message.from_user.id)
        if admin_status.status not in ["administrator", "creator"]:
            await message.edit_text("❌ У вас немає прав адміністратора")
            return

        target_user = None
        reason = "Порушення правил групи"

        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            if len(message.command) > 1:
                reason = message.text.split(maxsplit=1)[1]
        
        elif len(message.command) > 1:
            user_input = message.text.split()[1]
            
            if user_input.startswith('@'):
                username = user_input[1:]
                try:
                    target_user = await client.get_users(username)
                except PeerIdInvalid:
                    await message.edit_text(f"❌ Користувач @{username} не знайдений")
                    return
            
            elif user_input.isdigit():
                try:
                    target_user = await client.get_users(int(user_input))
                except PeerIdInvalid:
                    await message.edit_text("❌ Користувач з таким ID не знайдений")
                    return
            
            else:
                await message.edit_text("❌ Невірний формат користувача. Використовуйте @username або ID")
                return
            
            if len(message.command) > 2:
                reason = " ".join(message.command[2:])
        
        else:
            await message.edit_text(
                "❌ Використання:\n"
                "• `.ban` (у відповіді на повідомлення)\n"
                "• `.ban @username [причина]`\n"
                "• `.ban user_id [причина]`"
            )
            return

        if not target_user:
            await message.edit_text("❌ Не вдалося ідентифікувати користувача для бану")
            return

        if target_user.id == message.from_user.id:
            await message.edit_text("❌ Ви не можете забанити себе")
            return

        target_admin_status = await client.get_chat_member(message.chat.id, target_user.id)
        if target_admin_status.status in ["administrator", "creator"]:
            await message.edit_text("❌ Неможливо забанити адміністратора")
            return

        await client.ban_chat_member(message.chat.id, target_user.id)
        
        user_mention = f"@{target_user.username}" if target_user.username else target_user.first_name
        success_message = f"🔨 **Користувач забанений**\n"
        success_message += f"👤 **Користувач:** {user_mention}\n"
        success_message += f"🆔 **ID:** `{target_user.id}`\n"
        success_message += f"📝 **Причина:** {reason}\n"
        success_message += f"⚖️ **Адміністратор:** {message.from_user.first_name}"
        
        await message.edit_text(success_message)

    except ChatAdminRequired:
        await message.edit_text("❌ Бот не має прав адміністратора в цій групі")
    except UserAdminInvalid:
        await message.edit_text("❌ У вас немає достатніх прав для бану цього користувача")
    except FloodWait as e:
        await message.edit_text(f"⏳ Занадто багато запитів. Спробуйте через {e.x} секунд")
    except Exception as e:
        await message.edit_text(f"❌ Помилка при бані: {str(e)}")

async def unban_command(client: Client, message: Message):
    try:
        if not message.chat or message.chat.type == "private":
            await message.edit_text("❌ Ця команда працює тільки в групах/каналах")
            return

        admin_status = await client.get_chat_member(message.chat.id, message.from_user.id)
        if admin_status.status not in ["administrator", "creator"]:
            await message.edit_text("❌ У вас немає прав адміністратора")
            return

        target_user = None

        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        
        elif len(message.command) > 1:
            user_input = message.text.split()[1]
            
            if user_input.startswith('@'):
                username = user_input[1:]
                try:
                    target_user = await client.get_users(username)
                except PeerIdInvalid:
                    await message.edit_text(f"❌ Користувач @{username} не знайдений")
                    return
            
            elif user_input.isdigit():
                try:
                    target_user = await client.get_users(int(user_input))
                except PeerIdInvalid:
                    await message.edit_text("❌ Користувач з таким ID не знайдений")
                    return
            
            else:
                await message.edit_text("❌ Невірний формат користувача. Використовуйте @username або ID")
                return
        
        else:
            await message.edit_text(
                "❌ Використання:\n"
                "• `.unban` (у відповіді на повідомлення)\n"
                "• `.unban @username`\n"
                "• `.unban user_id`"
            )
            return

        if not target_user:
            await message.edit_text("❌ Не вдалося ідентифікувати користувача для розбану")
            return

        await client.unban_chat_member(message.chat.id, target_user.id)
        
        user_mention = f"@{target_user.username}" if target_user.username else target_user.first_name
        success_message = f"✅ **Користувач розбанений**\n"
        success_message += f"👤 **Користувач:** {user_mention}\n"
        success_message += f"🆔 **ID:** `{target_user.id}`\n"
        success_message += f"⚖️ **Адміністратор:** {message.from_user.first_name}"
        
        await message.edit_text(success_message)

    except ChatAdminRequired:
        await message.edit_text("❌ Бот не має прав адміністратора в цій групі")
    except UserAdminInvalid:
        await message.edit_text("❌ У вас немає достатніх прав для розбану цього користувача")
    except FloodWait as e:
        await message.edit_text(f"⏳ Занадто багато запитів. Спробуйте через {e.x} секунд")
    except Exception as e:
        await message.edit_text(f"❌ Помилка при розбані: {str(e)}")

def register_handlers(app: Client):
    
    ban_handler = MessageHandler(
        ban_command,
        filters.command("ban", prefixes=".") & filters.me
    )
    
    unban_handler = MessageHandler(
        unban_command,
        filters.command("unban", prefixes=".") & filters.me
    )

    handlers_list = [ban_handler, unban_handler]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list