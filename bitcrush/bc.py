from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
import os
import numpy as np
import soundfile as sf
from pydub import AudioSegment
import tempfile
import asyncio
import traceback

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

async def safe_edit_message(msg, text):
    try:
        if hasattr(msg, 'edit_text'):
            await msg.edit_text(text)
        elif hasattr(msg, 'edit'):
            await msg.edit(text)
        else:
            print(f"Message object has no edit method: {type(msg)}")
    except Exception as e:
        print(f"Failed to edit message: {e}")

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
    
    await safe_edit_message(msg, f"🎵 **Bitcrushing Progress**\n\n{progress_text}")

def load_audio_with_pydub(file_path):
    try:
        audio = AudioSegment.from_file(file_path)
        
        sample_rate = audio.frame_rate
        
        if audio.channels == 2:
            samples = audio.get_array_of_samples()
            samples_np = np.array(samples, dtype=np.float32)
            audio_data = samples_np.reshape((-1, 2)).T
        else:
            samples = audio.get_array_of_samples()
            audio_data = np.array(samples, dtype=np.float32)
        
        audio_data = audio_data / 32768.0
        
        return audio_data, sample_rate
        
    except Exception as e:
        print(f"Pydub loading error: {e}")
        raise

def save_audio_with_pydub(audio_data, sample_rate, output_path):
    audio_data_int = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
    
    if len(audio_data_int.shape) > 1 and audio_data_int.shape[0] == 2:
        audio_data_int = audio_data_int.T
        audio_segment = AudioSegment(
            audio_data_int.tobytes(), 
            frame_rate=sample_rate,
            sample_width=2,
            channels=2
        )
    else:
        if len(audio_data_int.shape) > 1:
            audio_data_int = audio_data_int.flatten()
        
        audio_segment = AudioSegment(
            audio_data_int.tobytes(), 
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
    
    audio_segment.export(output_path, format="mp3", bitrate="128k")

async def bitcrush_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Відповідь на аудіофайл для застосування bitcrushing ефекту.")
        return
    
    if not message.reply_to_message.audio and not message.reply_to_message.voice and not message.reply_to_message.video_note:
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
    
    status_msg = None
    temp_files = []
    
    try:
        status_msg = await message.reply_text("🎵 **Bitcrushing Progress**\n\n[ ] Downloading audio\n[ ] Crushing\n[ ] Returning back to audio\n[ ] Publishing\n[ ] Done")
        
        await update_progress(status_msg, 0, "processing")
        
        print(f"Starting download of message ID: {message.reply_to_message.id}")
        
        with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as temp_input:
            temp_files.append(temp_input.name)
            
            try:
                await client.download_media(message.reply_to_message, temp_input.name)
                print(f"Downloaded to: {temp_input.name}")
            except Exception as e:
                print(f"Download error: {e}")
                print(f"Full traceback: {traceback.format_exc()}")
                await update_progress(status_msg, 0, "error", f"Download failed: {str(e)}")
                return
            
            await update_progress(status_msg, 0, "success")
            
            await update_progress(status_msg, 1, "processing")
            
            try:
                print(f"Loading audio from: {temp_input.name}")
                audio_data, sample_rate = load_audio_with_pydub(temp_input.name)
                print(f"Loaded audio: shape={audio_data.shape}, sr={sample_rate}")
            except Exception as e:
                print(f"Audio loading error: {e}")
                print(f"Full traceback: {traceback.format_exc()}")
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
            
            print(f"Processed audio: shape={processed_audio.shape}")
            await update_progress(status_msg, 1, "success")
            
            await update_progress(status_msg, 2, "processing")
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_output:
                temp_files.append(temp_output.name)
                
                try:
                    save_audio_with_pydub(processed_audio, sample_rate, temp_output.name)
                    print(f"Saved MP3 to: {temp_output.name}")
                    await update_progress(status_msg, 2, "success")
                except Exception as e:
                    print(f"Save error: {e}")
                    print(f"Full traceback: {traceback.format_exc()}")
                    await update_progress(status_msg, 2, "error", f"Failed to save audio: {str(e)}")
                    return
                
                await update_progress(status_msg, 3, "processing")
                
                try:
                    print(f"Attempting to send audio to chat {message.chat.id}")
                    
                    sent_message = await client.send_audio(
                        chat_id=message.chat.id,
                        audio=temp_output.name,
                        caption=f"🎵 Bitcrushed: {bit_depth}-bit, downsample x{downsample_factor}",
                        reply_to_message_id=message.id
                    )
                    
                    print(f"Audio sent successfully, message ID: {sent_message.id}")
                    await update_progress(status_msg, 3, "success")
                    
                except Exception as e:
                    print(f"Send audio error: {e}")
                    print(f"Full traceback: {traceback.format_exc()}")
                    await update_progress(status_msg, 3, "error", f"Failed to send audio: {str(e)}")
                    return
        
        await update_progress(status_msg, 4, "success")
        await asyncio.sleep(2)
        
        try:
            if status_msg:
                await status_msg.delete()
        except:
            pass
        
    except Exception as e:
        print(f"Critical error: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        
        try:
            if status_msg:
                await update_progress(status_msg, 0, "error", f"Critical error: {str(e)}")
            else:
                await message.reply_text(f"❌ Critical error: {str(e)}")
        except Exception as reply_error:
            print(f"Failed to send error message: {reply_error}")
    
    finally:
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    print(f"Cleaned up: {temp_file}")
            except Exception as cleanup_error:
                print(f"Cleanup error for {temp_file}: {cleanup_error}")

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

**Підтримувані формати:** MP3, WAV, OGG, FLAC, Voice messages"""
    
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