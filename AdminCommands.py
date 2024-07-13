import json
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from pyrogram.enums import ChatMemberStatus
from datetime import datetime, timedelta

# File to store user warnings
data_file = 'user_data.json'

def load_data():
    try:
        with open(data_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(data_file, 'w') as f:
        json.dump(data, f)

def parse_duration(duration):
    """Parse duration string into timedelta."""
    units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
    amount = int(duration[:-1])
    unit = duration[-1]
    if unit not in units:
        raise ValueError("Invalid duration unit")
    return timedelta(**{units[unit]: amount})

async def is_admin(client, chat_id, user_id):
    """Check if the user is an admin in the chat."""
    member = await client.get_chat_member(chat_id, user_id)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)

def admin_command(func):
    """Decorator to check for admin privileges."""
    async def wrapper(client, message):
        if not await is_admin(client, message.chat.id, message.from_user.id):
            await message.reply_text("This command is only available to admins.")
            return
        await func(client, message)
    return wrapper

async def get_user_and_duration(message):
    """Extract user and duration from the message."""
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        duration = message.text.split()[1] if len(message.text.split()) > 1 else None
    else:
        if len(message.text.split()) < 3:
            return None, None
        user = await message.chat.get_member(message.text.split()[1])
        duration = message.text.split()[2]
    return user, duration

def admin_commands(app: Client):
    @app.on_message(filters.command("ban", prefixes="."))
    @admin_command
    async def ban(client, message):
        user, duration = await get_user_and_duration(message)
        if not user:
            await message.reply_text("Usage: .ban <user> <duration> or reply to a message with .ban <duration>")
            return

        try:
            ban_duration = parse_duration(duration) if duration else None
            until_date = datetime.now() + ban_duration if ban_duration else None
            await client.ban_chat_member(message.chat.id, user.id, until_date=until_date)
            await message.reply_text(f"{user.mention} has been banned for {duration if duration else 'indefinitely'}.")
        except ValueError:
            await message.reply_text("Invalid duration format. Use s, m, h, or d for seconds, minutes, hours, or days respectively.")

    @app.on_message(filters.command("mute", prefixes="."))
    @admin_command
    async def mute(client, message):
        user, duration = await get_user_and_duration(message)
        if not user:
            await message.reply_text("Usage: .mute <user> <duration> or reply to a message with .mute <duration>")
            return

        try:
            mute_duration = parse_duration(duration) if duration else None
            until_date = datetime.now() + mute_duration if mute_duration else None
            permissions = ChatPermissions(can_send_messages=False)
            await client.restrict_chat_member(message.chat.id, user.id, permissions, until_date=until_date)
            await message.reply_text(f"{user.mention} has been muted for {duration if duration else 'indefinitely'}.")
        except ValueError:
            await message.reply_text("Invalid duration format. Use s, m, h, or d for seconds, minutes, hours, or days respectively.")

    @app.on_message(filters.command("warn", prefixes="."))
    @admin_command
    async def warn(client, message):
        if not message.reply_to_message:
            await message.reply_text("Usage: .warn (reply to the user's message)")
            return

        user = message.reply_to_message.from_user
        user_data = load_data()
        user_id = str(user.id)

        if user_id not in user_data:
            user_data[user_id] = {"warnings": 0}
        
        user_data[user_id]["warnings"] += 1
        save_data(user_data)

        warning_count = user_data[user_id]["warnings"]
        await message.reply_text(f"{user.mention} has been warned. Total warnings: {warning_count}.")

        if warning_count >= 3:
            permissions = ChatPermissions(can_send_messages=False)
            await client.restrict_chat_member(message.chat.id, user.id, permissions)
            await message.reply_text(f"{user.mention} has been muted indefinitely due to receiving 3 warnings.")

    @app.on_message(filters.command("unwarn", prefixes="."))
    @admin_command
    async def unwarn(client, message):
        if not message.reply_to_message:
            await message.reply_text("Usage: .unwarn (reply to the user's message)")
            return

        user = message.reply_to_message.from_user
        user_data = load_data()
        user_id = str(user.id)

        if user_id in user_data and user_data[user_id]["warnings"] > 0:
            user_data[user_id]["warnings"] -= 1
            save_data(user_data)
            warning_count = user_data[user_id]["warnings"]
            await message.reply_text(f"One warning removed from {user.mention}. Total warnings: {warning_count}.")
        else:
            await message.reply_text(f"{user.mention} has no warnings to remove.")

    @app.on_message(filters.command("unban", prefixes="."))
    @admin_command
    async def unban(client, message):
        user, _ = await get_user_and_duration(message)
        if not user:
            await message.reply_text("Usage: .unban <user> or reply to a message with .unban")
            return

        await client.unban_chat_member(message.chat.id, user.id)
        await message.reply_text(f"{user.mention} has been unbanned.")

    @app.on_message(filters.command("unmute", prefixes="."))
    @admin_command
    async def unmute(client, message):
        user, _ = await get_user_and_duration(message)
        if not user:
            await message.reply_text("Usage: .unmute <user> or reply to a message with .unmute")
            return

        permissions = ChatPermissions(can_send_messages=True)
        await client.restrict_chat_member(message.chat.id, user.id, permissions)
        await message.reply_text(f"{user.mention} has been unmuted.")

def add_on(app: Client):
    admin_commands(app)