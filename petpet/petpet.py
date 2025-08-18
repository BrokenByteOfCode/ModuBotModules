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
        elif replied.from_user:
            try:
                async for photo in client.get_chat_photos(replied.from_user.id, limit=1):
                    source_image_bytes = await client.download_media(photo.file_id, in_memory=True)
                    break
            except Exception as e:
                pass

    if not source_image_bytes:
        if message.photo or (message.sticker and not message.sticker.is_animated and not message.sticker.is_video):
            source_image_bytes = await client.download_media(message, in_memory=True)

    if not source_image_bytes:
        try:
            async for photo in client.get_chat_photos(message.from_user.id, limit=1):
                source_image_bytes = await client.download_media(photo.file_id, in_memory=True)
                break 
            else:
                await message.reply_text("Не вдалося знайти зображення. Надішліть фото, стікер, або встановіть аватар.")
                return
        except Exception as e:
            await message.reply_text(f"Не вдалося отримати аватар. Помилка: {e}")
            return

    status_message = await message.reply_text("` petting... `")

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