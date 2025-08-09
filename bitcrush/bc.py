import numpy as np
import io
import logging
import subprocess
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler

logger = logging.getLogger(__name__)

def apply_authentic_bitcrush_effect(audio_bytes, bit_depth=8, sample_rate_factor=4, drive=1.0, noise_level=0.0):
    try:
        ffmpeg_decode_command = [
            'ffmpeg',
            '-i', 'pipe:0',
            '-f', 's32le',
            '-ac', '1',
            '-ar', '44100',
            'pipe:1'
        ]

        process_decode = subprocess.run(
            ffmpeg_decode_command,
            input=audio_bytes,
            capture_output=True,
            check=True
        )
        raw_audio = process_decode.stdout

    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode() if e.stderr else "Unknown FFmpeg error during decoding."
        logger.error(f"FFmpeg decode error: {error_message}")
        raise RuntimeError(f"FFmpeg помилка при декодуванні: {error_message}")

    samples = np.frombuffer(raw_audio, dtype=np.int32).astype(np.float64) / (2**31)

    if drive != 1.0:
        samples = np.tanh(samples * drive) * (1.0 / np.tanh(drive))

    target_sample_rate = 44100 // sample_rate_factor
    downsample_indices = np.arange(0, len(samples), sample_rate_factor)
    downsampled = samples[downsample_indices]

    if bit_depth < 32:
        max_amplitude = 2**(bit_depth - 1) - 1
        
        quantized = np.round(downsampled * max_amplitude) / max_amplitude
        
        if bit_depth <= 8:
            quantization_error = quantized - downsampled
            quantized += quantization_error * 0.1
        
        downsampled = quantized

    upsampled = np.repeat(downsampled, sample_rate_factor)
    if len(upsampled) > len(samples):
        upsampled = upsampled[:len(samples)]
    elif len(upsampled) < len(samples):
        upsampled = np.pad(upsampled, (0, len(samples) - len(upsampled)), mode='edge')

    if noise_level > 0:
        noise = np.random.normal(0, noise_level * 0.01, len(upsampled))
        upsampled += noise

    upsampled = np.clip(upsampled, -1.0, 1.0)

    if bit_depth <= 4:
        cutoff = 0.3
    elif bit_depth <= 8:
        cutoff = 0.5
    else:
        cutoff = 0.7
    
    nyquist = 0.5
    filter_order = 6
    from scipy.signal import butter, filtfilt
    b, a = butter(filter_order, cutoff * nyquist, btype='low', analog=False)
    upsampled = filtfilt(b, a, upsampled)

    processed_samples_int16 = (upsampled * 32767).astype(np.int16)
    processed_bytes = processed_samples_int16.tobytes()

    try:
        ffmpeg_encode_command = [
            'ffmpeg',
            '-f', 's16le',
            '-ar', '44100',
            '-ac', '1',
            '-i', 'pipe:0',
            '-f', 'mp3',
            '-b:a', '192k',
            'pipe:1'
        ]

        process_encode = subprocess.run(
            ffmpeg_encode_command,
            input=processed_bytes,
            capture_output=True,
            check=True
        )
        mp3_output = process_encode.stdout

    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode() if e.stderr else "Unknown FFmpeg error during encoding."
        logger.error(f"FFmpeg encode error: {error_message}")
        raise RuntimeError(f"FFmpeg помилка при кодуванні: {error_message}")

    output_buffer = io.BytesIO(mp3_output)
    output_buffer.name = "authentic_bitcrushed.mp3"
    output_buffer.seek(0)
    return output_buffer

async def process_audio_for_bitcrush(client, message, bit_depth=8, sample_rate_factor=4, drive=1.0, noise_level=0.0):
    replied_message = message.reply_to_message
    if not replied_message or not (replied_message.audio or replied_message.voice):
        await message.edit_text("❌ Будь ласка, дайте відповідь на аудіофайл або голосове повідомлення.")
        return

    await message.edit_text("🎵 Обробка аудіо...")
    
    media_to_download = replied_message.audio or replied_message.voice
    
    downloaded_file = None
    
    try:
        downloaded_file = await client.download_media(media_to_download, in_memory=True)
        await message.edit_text("🔧 Застосування автентичного bitcrush ефекту...")
        
        processed_audio_buffer = apply_authentic_bitcrush_effect(
            downloaded_file.getbuffer(), 
            bit_depth, 
            sample_rate_factor, 
            drive, 
            noise_level
        )
        
        await message.edit_text("📤 Завантаження обробленого аудіо...")
        
        caption_text = f"🎛 **Authentic Bitcrushed Audio**\n{bit_depth}-bit • {sample_rate_factor}x downsample"
        if drive != 1.0:
            caption_text += f" • {drive:.1f}x drive"
        if noise_level > 0:
            caption_text += f" • {noise_level:.1f}% noise"
        
        await message.reply_document(
            document=processed_audio_buffer,
            caption=caption_text,
            file_name="authentic_bitcrushed.mp3"
        )
        
        await message.delete()

    except Exception as e:
        logger.error(f"Error processing audio for bitcrush: {e}", exc_info=True)
        await message.edit_text(f"❌ Помилка обробки: {str(e)}")
    finally:
        if downloaded_file:
            downloaded_file.close()

async def bitcrush_command(client, message):
    await process_audio_for_bitcrush(client, message, bit_depth=8, sample_rate_factor=4)

async def bitcrush_lofi_command(client, message):
    await process_audio_for_bitcrush(client, message, bit_depth=12, sample_rate_factor=2, drive=1.2, noise_level=0.5)

async def bitcrush_vintage_command(client, message):
    await process_audio_for_bitcrush(client, message, bit_depth=4, sample_rate_factor=8, drive=1.5, noise_level=1.0)

async def bitcrush_extreme_command(client, message):
    await process_audio_for_bitcrush(client, message, bit_depth=2, sample_rate_factor=16, drive=2.0, noise_level=0.3)

async def bitcrush_help_command(client, message):
    help_text = """🎛 **BITCRUSH AUDIO EFFECTS**

**Основні команди:**
• `.bitcrush` - Стандартний ефект (8-біт, 4x)
• `.bitcrushlofi` - Lo-Fi звук (12-біт, драйв, шум)
• `.bitcrushvintage` - Вінтажний звук (4-біт, важкий драйв)
• `.bitcrushextreme` - Екстремальний ефект (2-біт, максимум)

**Налаштування:**
• `.bitcrushcustom <біт> <семпл> [драйв] [шум]`
  Приклад: `.bitcrushcustom 6 8 1.8 1.2`

**Параметри:**
🔹 **Біт-глибина (1-16):** Кількість біт для квантування
   • 16-12: Висока якість
   • 8-6: Класичний lo-fi
   • 4-2: Сильне спотворення
   • 1: Екстремальний ефект

🔹 **Семпл-фактор (1-32):** Зменшення частоти дискретизації
   • 1-2: М'яке зменшення
   • 4-8: Помітний ефект
   • 16-32: Радикальні зміни

🔹 **Драйв (0.1-3.0):** Аналогове насичення
   • 1.0: Без драйву
   • 1.5-2.0: М'яке насичення
   • 2.5-3.0: Жорстке спотворення

🔹 **Шум (0-5%):** Аналогові шуми
   • 0-0.5%: Тонкий шум
   • 1-2%: Помітний вінтажний шум
   • 3-5%: Сильний аналогові артефакти

**Використання:** Дай відповідь на аудіофайл або голосове повідомлення"""
    
    await message.reply_text(help_text)

async def bitcrush_custom_command(client, message):
    args = message.command[1:]
    if len(args) < 2 or len(args) > 4:
        await message.reply_text(
            "❌ Використання: `.bitcrushcustom <глибина> <семплрейт> [драйв] [шум]`\n"
            "Приклад: `.bitcrushcustom 8 4 1.5 0.8`\n"
            "Параметри:\n"
            "• Глибина: 1-16 біт\n"
            "• Семплрейт: 1-32 (фактор зменшення)\n"
            "• Драйв: 0.1-3.0 (необов'язково, за замовчуванням 1.0)\n"
            "• Шум: 0-5% (необов'язково, за замовчуванням 0)\n\n"
            "💡 Використовуй `.help bitcrush` для детальної довідки"
        )
        return
    
    try:
        bit_depth = int(args[0])
        sample_rate_factor = int(args[1])
        drive = float(args[2]) if len(args) > 2 else 1.0
        noise_level = float(args[3]) if len(args) > 3 else 0.0
        
        if not (1 <= bit_depth <= 16):
            raise ValueError("Bit depth must be 1-16")
        if not (1 <= sample_rate_factor <= 32):
            raise ValueError("Sample rate factor must be 1-32")
        if not (0.1 <= drive <= 3.0):
            raise ValueError("Drive must be 0.1-3.0")
        if not (0 <= noise_level <= 5.0):
            raise ValueError("Noise level must be 0-5%")
            
    except ValueError as ve:
        await message.reply_text(f"❌ Неправильні параметри: {str(ve)}")
        return
        
    await process_audio_for_bitcrush(client, message, bit_depth, sample_rate_factor, drive, noise_level)

def register_handlers(app: Client):
    handlers_list = [
        MessageHandler(bitcrush_command, filters.command("bitcrush", prefixes=".")),
        MessageHandler(bitcrush_lofi_command, filters.command("bitcrushlofi", prefixes=".")),
        MessageHandler(bitcrush_vintage_command, filters.command("bitcrushvintage", prefixes=".")),
        MessageHandler(bitcrush_extreme_command, filters.command("bitcrushextreme", prefixes=".")),
        MessageHandler(bitcrush_custom_command, filters.command("bitcrushcustom", prefixes=".")),
        MessageHandler(bitcrush_help_command, filters.command(["help"], prefixes=".") & filters.text & filters.regex(r"bitcrush"))
    ]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list