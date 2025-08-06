from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pyrogram.errors import FloodWait, ChatAdminRequired, UserAdminInvalid, PeerIdInvalid, RPCError
import asyncio

async def ban_command(client: Client, message: Message):
    try:
        if not message.chat or message.chat.type == "private":
            await message.edit_text("❌ Команда працює тільки в групах")
            return

        target_user = None
        reason = "Порушення правил"

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
                    await message.edit_text(f"❌ @{username} не знайдений")
                    return
                except Exception as e:
                    await message.edit_text(f"❌ Помилка пошуку користувача: {str(e)}")
                    return
            
            elif user_input.isdigit():
                try:
                    target_user = await client.get_users(int(user_input))
                except PeerIdInvalid:
                    await message.edit_text("❌ Користувач з таким ID не знайдений")
                    return
                except Exception as e:
                    await message.edit_text(f"❌ Помилка пошуку користувача: {str(e)}")
                    return
            
            else:
                await message.edit_text("❌ Формат: `.ban @username` або `.ban ID`")
                return
            
            if len(message.command) > 2:
                reason = " ".join(message.command[2:])
        
        else:
            await message.edit_text(
                "**Використання:**\n"
                "• `.ban` (відповідь на повідомлення)\n"
                "• `.ban @username [причина]`\n" 
                "• `.ban ID [причина]`"
            )
            return

        if not target_user:
            await message.edit_text("❌ Користувач не визначений")
            return

        if target_user.id == message.from_user.id:
            await message.edit_text("❌ Неможливо забанити себе")
            return

        try:
            await message.chat.ban_member(target_user.id)
        except AttributeError:
            await client.ban_chat_member(message.chat.id, target_user.id)
        
        user_name = f"@{target_user.username}" if target_user.username else target_user.first_name
        
        await message.edit_text(
            f"🔨 **ЗАБАНЕНИЙ**\n"
            f"👤 {user_name}\n"
            f"🆔 `{target_user.id}`\n"
            f"📝 {reason}"
        )

    except ChatAdminRequired:
        await message.edit_text("❌ Бот не має прав адміна або ти не адмін")
    except UserAdminInvalid:
        await message.edit_text("❌ Недостатньо прав для бану цього користувача")
    except FloodWait as e:
        await message.edit_text(f"⏳ Флуд контроль: {e.x}с")
    except RPCError as e:
        await message.edit_text(f"❌ Telegram API помилка: {e}")
    except Exception as e:
        await message.edit_text(f"❌ Непередбачена помилка: {str(e)}")

async def unban_command(client: Client, message: Message):
    try:
        if not message.chat or message.chat.type == "private":
            await message.edit_text("❌ Команда працює тільки в групах")
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
                    await message.edit_text(f"❌ @{username} не знайдений")
                    return
                except Exception as e:
                    await message.edit_text(f"❌ Помилка пошуку користувача: {str(e)}")
                    return
            
            elif user_input.isdigit():
                try:
                    target_user = await client.get_users(int(user_input))
                except PeerIdInvalid:
                    await message.edit_text("❌ Користувач з таким ID не знайдений")
                    return
                except Exception as e:
                    await message.edit_text(f"❌ Помилка пошуку користувача: {str(e)}")
                    return
            
            else:
                await message.edit_text("❌ Формат: `.unban @username` або `.unban ID`")
                return
        
        else:
            await message.edit_text(
                "**Використання:**\n"
                "• `.unban` (відповідь на повідомлення)\n"
                "• `.unban @username`\n"
                "• `.unban ID`"
            )
            return

        if not target_user:
            await message.edit_text("❌ Користувач не визначений")
            return

        try:
            await message.chat.unban_member(target_user.id)
        except AttributeError:
            await client.unban_chat_member(message.chat.id, target_user.id)
        
        user_name = f"@{target_user.username}" if target_user.username else target_user.first_name
        
        await message.edit_text(
            f"✅ **РОЗБАНЕНИЙ**\n"
            f"👤 {user_name}\n"
            f"🆔 `{target_user.id}`"
        )

    except ChatAdminRequired:
        await message.edit_text("❌ Бот не має прав адміна або ти не адмін")
    except UserAdminInvalid:
        await message.edit_text("❌ Недостатньо прав для розбану цього користувача")
    except FloodWait as e:
        await message.edit_text(f"⏳ Флуд контроль: {e.x}с")
    except RPCError as e:
        await message.edit_text(f"❌ Telegram API помилка: {e}")
    except Exception as e:
        await message.edit_text(f"❌ Непередбачена помилка: {str(e)}")

async def kick_command(client: Client, message: Message):
    try:
        if not message.chat or message.chat.type == "private":
            await message.edit_text("❌ Команда працює тільки в групах")
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
                    await message.edit_text(f"❌ @{username} не знайдений")
                    return
                except Exception as e:
                    await message.edit_text(f"❌ Помилка пошуку користувача: {str(e)}")
                    return
            
            elif user_input.isdigit():
                try:
                    target_user = await client.get_users(int(user_input))
                except PeerIdInvalid:
                    await message.edit_text("❌ Користувач з таким ID не знайдений")
                    return
                except Exception as e:
                    await message.edit_text(f"❌ Помилка пошуку користувача: {str(e)}")
                    return
            
            else:
                await message.edit_text("❌ Формат: `.kick @username` або `.kick ID`")
                return
        
        else:
            await message.edit_text(
                "**Використання:**\n"
                "• `.kick` (відповідь на повідомлення)\n"
                "• `.kick @username`\n"
                "• `.kick ID`"
            )
            return

        if not target_user:
            await message.edit_text("❌ Користувач не визначений")
            return

        if target_user.id == message.from_user.id:
            await message.edit_text("❌ Неможливо кікнути себе")
            return

        try:
            await message.chat.ban_member(target_user.id)
            await asyncio.sleep(1)
            await message.chat.unban_member(target_user.id)
        except AttributeError:
            await client.ban_chat_member(message.chat.id, target_user.id)
            await asyncio.sleep(1)
            await client.unban_chat_member(message.chat.id, target_user.id)
        
        user_name = f"@{target_user.username}" if target_user.username else target_user.first_name
        
        await message.edit_text(
            f"👢 **КІКНУТИЙ**\n"
            f"👤 {user_name}\n"
            f"🆔 `{target_user.id}`"
        )

    except ChatAdminRequired:
        await message.edit_text("❌ Бот не має прав адміна або ти не адмін")
    except UserAdminInvalid:
        await message.edit_text("❌ Недостатньо прав для кіка цього користувача")
    except FloodWait as e:
        await message.edit_text(f"⏳ Флуд контроль: {e.x}с")
    except RPCError as e:
        await message.edit_text(f"❌ Telegram API помилка: {e}")
    except Exception as e:
        await message.edit_text(f"❌ Непередбачена помилка: {str(e)}")

def register_handlers(app: Client):
    
    ban_handler = MessageHandler(
        ban_command,
        filters.command("ban", prefixes=".")
    )
    
    unban_handler = MessageHandler(
        unban_command,
        filters.command("unban", prefixes=".")
    )

    kick_handler = MessageHandler(
        kick_command,
        filters.command("kick", prefixes=".")
    )

    handlers_list = [ban_handler, unban_handler, kick_handler]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list