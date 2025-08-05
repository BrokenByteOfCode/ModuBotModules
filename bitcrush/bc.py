import numpy as np
import soundfile as sf
import lameenc
import os
import io
import logging
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler

logger = logging.getLogger(__name__)

def apply_bitcrush_effect(audio_bytes, bit_depth=8, sample_rate_reduction=4):
    try:
        samples, original_samplerate = sf.read(io.BytesIO(audio_bytes))
    except Exception as e:
        raise RuntimeError(f"Failed to read audio file. It may be corrupt or in an unsupported format. Details: {e}")

    if samples.ndim > 1:
        samples = np.mean(samples, axis=1)
    
    max_val = 2**(bit_depth - 1)
    quantized_samples = np.round(samples * max_val) / max_val
    
    downsampled = quantized_samples[::sample_rate_reduction]
    
    original_length = len(samples)
    final_samples_np = np.repeat(downsampled, sample_rate_reduction)
    if len(final_samples_np) > original_length:
        final_samples_np = final_samples_np[:original_length]

    final_samples_int16 = (final_samples_np * 32767).astype(np.int16)
    
    encoder = lameenc.Encoder()
    encoder.set_in_samplerate(original_samplerate)
    encoder.set_channels(1)
    encoder.set_quality(2)

    mp3_bytes = encoder.encode(final_samples_int16)
    mp3_bytes += encoder.flush()
    
    output_buffer = io.BytesIO(mp3_bytes)
    output_buffer.seek(0)
    
    return output_buffer

async def process_audio_for_bitcrush(client, message, bit_depth=8, srr=4):
    replied_message = message.reply_to_message
    if not replied_message or not (replied_message.audio or replied_message.voice):
        await message.reply_text("❌ Будь ласка, дайте відповідь на аудіофайл або голосове повідомлення.")
        return

    status_msg = await message.reply_text("🎵 Обробка...")
    
    media_to_download = replied_message.audio or replied_message.voice
    
    downloaded_file = None
    try:
        downloaded_file = await client.download_media(media_to_download, in_memory=True)
        await status_msg.edit_text("🔧 Застосування ефекту...")
        
        processed_audio_buffer = apply_bitcrush_effect(downloaded_file.getbuffer(), bit_depth, srr)
        
        await status_msg.edit_text("📤 Завантаження...")
        
        caption_text = f"🎛 **Bitcrushed Audio**\n{bit_depth}-bit • {srr}x reduction"
        
        await message.reply_audio(
            processed_audio_buffer, 
            caption=caption_text,
            file_name="bitcrushed.mp3"
        )
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Error processing audio for bitcrush: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Помилка обробки: {str(e)}")
    finally:
        if downloaded_file:
            downloaded_file.close()

async def bitcrush_command(client, message):
    await process_audio_for_bitcrush(client, message, bit_depth=8, srr=4)

async def bitcrush_custom_command(client, message):
    args = message.command[1:]
    if len(args) != 2:
        await message.reply_text("❌ Використання: `.bitcrushcustom <глибина> <редукція>`\nПриклад: `.bitcrushcustom 4 8`")
        return
    
    try:
        bit_depth = int(args[0])
        srr = int(args[1])
        if not (1 <= bit_depth <= 16 and 1 <= srr <= 32):
            raise ValueError("Parameters out of range.")
    except ValueError:
        await message.reply_text("❌ Неправильні параметри. Глибина: 1-16, Редукція: 1-32.")
        return
        
    await process_audio_for_bitcrush(client, message, bit_depth, srr)

def register_handlers(app: Client):
    handlers_list = [
        MessageHandler(bitcrush_command, filters.command("bitcrush", prefixes=".") & filters.reply & filters.me),
        MessageHandler(bitcrush_custom_command, filters.command("bitcrushcustom", prefixes=".") & filters.reply & filters.me)
    ]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list