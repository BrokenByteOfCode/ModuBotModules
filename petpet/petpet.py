import asyncio
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from petpetgif import petpet as petpetgif

async def pet_command(client: Client, message: Message):
    source_image_bytes = None
    
    if message.reply_to_message:
        replied = message.reply_to_message
        if replied.photo or (replied.sticker and not replied.sticker.is_animated and not replied.sticker.is_video):
            source_image_bytes = await client.download_media(replied, in_memory=True)
            
    if not source_image_bytes:
        if message.photo or (message.sticker and not message.sticker.is_animated and not message.sticker.is_video):
            source_image_bytes = await client.download_media(message, in_memory=True)

    if not source_image_bytes:
        try:
            user_photos = await client.get_profile_photos(message.from_user.id, limit=1)
            if user_photos:
                source_image_bytes = await client.download_media(user_photos[0].file_id, in_memory=True)
            else:
                await message.reply_text("Не вдалося знайти зображення. Надішліть фото, стікер, або встановіть аватар.")
                return
        except Exception as e:
            await message.reply_text(f"Не вдалося отримати ваш аватар. Помилка: {e}")
            return
            
    if not source_image_bytes:
        await message.reply_text("Будь ласка, надішліть фото/стікер або дайте відповідь на повідомлення з ними.")
        return

    status_message = await message.reply_text(" petting... ")

    try:
        source = BytesIO(source_image_bytes.getvalue())
        dest = BytesIO()

        petpetgif.make(source, dest)
        
        dest.seek(0)
        dest.name = "petpet.gif"

        await message.reply_animation(dest)
        
        await status_message.delete()
        await message.delete()

    except Exception as e:
        await status_message.edit(f"Сталася помилка під час створення GIF: {e}")

def register_handlers(app: Client):
    pet_handler = MessageHandler(
        pet_command,
        filters.command("pet", prefixes=".")
    )

    handlers_list = [pet_handler]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list