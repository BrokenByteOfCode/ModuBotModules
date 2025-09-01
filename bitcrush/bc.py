from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
import os
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
import tempfile
import asyncio

def bitcrush_audio(audio_data, sample_rate, bit_depth=8, downsample_factor=4):
    original_max = np.max(np.abs(audio_data))
    
    if original_max > 0:
        normalized_audio = audio_data / original_max
    else:
        normalized_audio = audio_data
    
    downsampled = normalized_audio[::downsample_factor]
    
    levels = 2 ** bit_depth
    quantized = np.round(downsampled * (levels - 1)) / (levels - 1)
    
    upsampled = np.repeat(quantized, downsample_factor)
    
    if len(upsampled) > len(audio_data):
        upsampled = upsampled[:len(audio_data)]
    elif len(upsampled) < len(audio_data):
        padding = len(audio_data) - len(upsampled)
        upsampled = np.pad(upsampled, (0, padding), mode='constant')
    
    if original_max > 0:
        upsampled = upsampled * original_max
    
    return upsampled

async def update_progress(msg, step, status, error_msg=None):
    steps = [
        "Downloading audio",
        "Crushing", 
        "Returning back to audio",
        "Publishing",
        "Done"
    ]
    
    progress_text = ""
    
    for i, step_name in enumerate(steps):
        if i < step:
            progress_text += f"[✓] {step_name}\n"
        elif i == step:
            if status == "processing":
                progress_text += f"[?] {step_name}\n"
            elif status == "success":
                progress_text += f"[✓] {step_name}\n"
            elif status == "error":
                progress_text += f"[X] {step_name}\n"
                if error_msg:
                    progress_text += f"Error: {error_msg}\n"
                break
        else:
            progress_text += f"[ ] {step_name}\n"
    
    try:
        await msg.edit_text(f"🎵 **Bitcrushing Progress**\n\n{progress_text}")
    except:
        pass

async def bitcrush_command(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        await message.reply_text("Відповідь на аудіофайл для застосування bitcrushing ефекту.")
        return
    
    params = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    bit_depth = 8
    downsample_factor = 4
    
    for param in params:
        if param.startswith('bits='):
            try:
                bit_depth = int(param.split('=')[1])
                bit_depth = max(1, min(16, bit_depth))
            except ValueError:
                pass
        elif param.startswith('downsample='):
            try:
                downsample_factor = int(param.split('=')[1])
                downsample_factor = max(1, min(10, downsample_factor))
            except ValueError:
                pass
    
    status_msg = await message.reply_text("🎵 **Bitcrushing Progress**\n\n[ ] Downloading audio\n[ ] Crushing\n[ ] Returning back to audio\n[ ] Publishing\n[ ] Done")
    
    try:
        await update_progress(status_msg, 0, "processing")
        audio_file = message.reply_to_message.audio
        
        with tempfile.NamedTemporaryFile(suffix='.tmp') as temp_input:
            await client.download_media(audio_file, temp_input.name)
            await update_progress(status_msg, 0, "success")
            
            await update_progress(status_msg, 1, "processing")
            try:
                audio_data, sample_rate = librosa.load(temp_input.name, sr=None, mono=False)
            except Exception as e:
                await update_progress(status_msg, 1, "error", f"Failed to load audio: {str(e)}")
                return
            
            if len(audio_data.shape) > 1:
                processed_channels = []
                for channel in range(audio_data.shape[0]):
                    processed_channel = bitcrush_audio(
                        audio_data[channel], 
                        sample_rate, 
                        bit_depth, 
                        downsample_factor
                    )
                    processed_channels.append(processed_channel)
                processed_audio = np.array(processed_channels)
            else:
                processed_audio = bitcrush_audio(audio_data, sample_rate, bit_depth, downsample_factor)
            
            await update_progress(status_msg, 1, "success")
            
            await update_progress(status_msg, 2, "processing")
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
                try:
                    if len(processed_audio.shape) > 1:
                        sf.write(temp_output.name, processed_audio.T, sample_rate)
                    else:
                        sf.write(temp_output.name, processed_audio, sample_rate)
                except Exception as e:
                    await update_progress(status_msg, 2, "error", f"Failed to write audio: {str(e)}")
                    return
                
                try:
                    audio_segment = AudioSegment.from_wav(temp_output.name)
                except Exception as e:
                    await update_progress(status_msg, 2, "error", f"Failed to convert audio: {str(e)}")
                    os.unlink(temp_output.name)
                    return
                
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
                    try:
                        audio_segment.export(temp_mp3.name, format="mp3", bitrate="128k")
                        await update_progress(status_msg, 2, "success")
                    except Exception as e:
                        await update_progress(status_msg, 2, "error", f"Failed to export MP3: {str(e)}")
                        os.unlink(temp_output.name)
                        return
                    
                    await update_progress(status_msg, 3, "processing")
                    
                    try:
                        await client.send_audio(
                            chat_id=message.chat.id,
                            audio=temp_mp3.name,
                            caption=f"🎵 Bitcrushed: {bit_depth}-bit, downsample x{downsample_factor}",
                            reply_to_message_id=message.message_id
                        )
                        await update_progress(status_msg, 3, "success")
                    except Exception as e:
                        await update_progress(status_msg, 3, "error", f"Failed to send audio: {str(e)}")
                        os.unlink(temp_output.name)
                        os.unlink(temp_mp3.name)
                        return
                
                os.unlink(temp_output.name)
                os.unlink(temp_mp3.name)
        
        await update_progress(status_msg, 4, "success")
        await asyncio.sleep(2)
        await status_msg.delete()
        
    except Exception as e:
        try:
            current_step = 0
            if "download" in str(e).lower():
                current_step = 0
            elif "load" in str(e).lower() or "crush" in str(e).lower():
                current_step = 1
            elif "write" in str(e).lower() or "convert" in str(e).lower():
                current_step = 2
            elif "send" in str(e).lower():
                current_step = 3
            
            await update_progress(status_msg, current_step, "error", str(e))
        except:
            await message.reply_text(f"❌ Critical error: {str(e)}")

async def bitcrush_help_command(client: Client, message: Message):
    help_text = """🎵 **Bitcrushing Module**

**Команди:**
`.bitcrush` - Застосувати bitcrushing ефект до аудіо (відповідь на аудіофайл)
`.bitcrush_help` - Показати це повідомлення

**Параметри:**
`bits=N` - Глибина біт (1-16, за замовчуванням: 8)
`downsample=N` - Фактор даунсемплінгу (1-10, за замовчуванням: 4)

**Приклади:**
`.bitcrush` - Стандартні налаштування
`.bitcrush bits=4 downsample=8` - Сильний ефект
`.bitcrush bits=12 downsample=2` - М'який ефект

**Підтримувані формати:** MP3, WAV, OGG, FLAC та інші"""
    
    await message.reply_text(help_text)

def register_handlers(app: Client):
    bitcrush_handler = MessageHandler(
        bitcrush_command,
        filters.command("bitcrush", prefixes=".")
    )
    
    help_handler = MessageHandler(
        bitcrush_help_command,
        filters.command("bitcrush_help", prefixes=".")
    )

    handlers_list = [bitcrush_handler, help_handler]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list