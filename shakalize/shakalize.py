from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from PIL import Image, ImageFilter
import ffmpeg
import io
import os
import tempfile
import random


async def shakalize_command(client: Client, message: Message):
    quality_level = 10
    
    if len(message.command) > 1:
        try:
            quality_level = int(message.command[1])
            if quality_level < 0 or quality_level > 10:
                await message.reply_text("Рівень якості має бути між 0 та 10")
                return
        except ValueError:
            await message.reply_text("Некоректний рівень якості. Використовуйте число від 0 до 10")
            return
    
    target_message = message.reply_to_message if message.reply_to_message else message
    
    if not target_message:
        await message.reply_text("Надішліть медіа файл або відповідьте на повідомлення з медіа")
        return
    
    media = None
    media_type = None
    
    if target_message.photo:
        media = target_message.photo
        media_type = "photo"
    elif target_message.video:
        media = target_message.video
        media_type = "video"
    elif target_message.audio:
        media = target_message.audio
        media_type = "audio"
    elif target_message.voice:
        media = target_message.voice
        media_type = "voice"
    elif target_message.document:
        if target_message.document.mime_type:
            if target_message.document.mime_type.startswith('image/'):
                media = target_message.document
                media_type = "photo"
            elif target_message.document.mime_type.startswith('video/'):
                media = target_message.document
                media_type = "video"
            elif target_message.document.mime_type.startswith('audio/'):
                media = target_message.document
                media_type = "audio"
    
    if not media:
        await message.reply_text("Медіа файл не знайдено. Підтримуються фото, відео та аудіо")
        return
    
    progress_msg = await message.reply_text(f"🔥 Шакалізую медіа (рівень: {quality_level})...")
    
    try:
        if media_type == "photo":
            await shakalize_photo(client, message, media, quality_level, progress_msg)
        elif media_type == "video":
            await shakalize_video(client, message, media, quality_level, progress_msg)
        elif media_type in ["audio", "voice"]:
            await shakalize_audio(client, message, media, quality_level, progress_msg)
    except Exception as e:
        await progress_msg.edit_text(f"❌ Помилка при обробці: {str(e)}")


async def shakalize_photo(client: Client, message: Message, photo, quality_level: int, progress_msg):
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_input:
        await client.download_media(photo, temp_input.name)
        
        with Image.open(temp_input.name) as img:
            img = img.convert('RGB')
            
            degradation_factor = (10 - quality_level) / 10.0
            
            original_size = img.size
            scale_factor = max(0.1, 1 - degradation_factor * 0.8)
            new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
            
            img = img.resize(new_size, Image.LANCZOS)
            img = img.resize(original_size, Image.NEAREST)
            
            if degradation_factor > 0.3:
                blur_radius = degradation_factor * 2
                img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            
            if degradation_factor > 0.5:
                noise_intensity = int(degradation_factor * 30)
                pixels = img.load()
                for i in range(0, img.width, 3):
                    for j in range(0, img.height, 3):
                        if random.random() < degradation_factor * 0.3:
                            noise = random.randint(-noise_intensity, noise_intensity)
                            r, g, b = pixels[i, j]
                            pixels[i, j] = (
                                max(0, min(255, r + noise)),
                                max(0, min(255, g + noise)),
                                max(0, min(255, b + noise))
                            )
            
            jpeg_quality = max(1, int(100 - degradation_factor * 95))
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_output:
                img.save(temp_output.name, 'JPEG', quality=jpeg_quality, optimize=False)
                
                await progress_msg.delete()
                await message.reply_photo(
                    temp_output.name,
                    caption=f"🔥 Шакалізовано (рівень: {quality_level})"
                )
                
                os.unlink(temp_output.name)
        
        os.unlink(temp_input.name)


async def shakalize_video(client: Client, message: Message, video, quality_level: int, progress_msg):
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
        await client.download_media(video, temp_input.name)
        
        degradation_factor = (10 - quality_level) / 10.0
        
        crf = min(51, int(18 + degradation_factor * 33))
        scale_factor = max(0.3, 1 - degradation_factor * 0.7)
        
        bitrate = max(50, int(1000 - degradation_factor * 950))
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            try:
                input_stream = ffmpeg.input(temp_input.name)
                
                video_stream = input_stream.video
                if scale_factor < 0.9:
                    video_stream = ffmpeg.filter(video_stream, 'scale', 
                                               f'iw*{scale_factor}', f'ih*{scale_factor}')
                    video_stream = ffmpeg.filter(video_stream, 'scale', 
                                               'iw/1', 'ih/1', flags='neighbor')
                
                if degradation_factor > 0.4:
                    noise_strength = int(degradation_factor * 20)
                    video_stream = ffmpeg.filter(video_stream, 'noise', 
                                               alls=noise_strength, allf='t')
                
                audio_stream = input_stream.audio
                if degradation_factor > 0.3:
                    audio_bitrate = max(32, int(128 - degradation_factor * 96))
                    audio_stream = ffmpeg.filter(audio_stream, 'aformat', 
                                               sample_rates=max(8000, int(44100 - degradation_factor * 36100)))
                
                out = ffmpeg.output(
                    video_stream, audio_stream, temp_output.name,
                    vcodec='libx264',
                    acodec='aac',
                    crf=crf,
                    video_bitrate=f'{bitrate}k',
                    audio_bitrate=f'{max(32, int(128 - degradation_factor * 96))}k',
                    preset='ultrafast'
                )
                
                ffmpeg.run(out, overwrite_output=True, quiet=True)
                
                await progress_msg.delete()
                await message.reply_video(
                    temp_output.name,
                    caption=f"🔥 Шакалізовано (рівень: {quality_level})"
                )
                
            except Exception as e:
                await progress_msg.edit_text(f"❌ Помилка обробки відео: {str(e)}")
            finally:
                os.unlink(temp_output.name)
        
        os.unlink(temp_input.name)


async def shakalize_audio(client: Client, message: Message, audio, quality_level: int, progress_msg):
    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_input:
        await client.download_media(audio, temp_input.name)
        
        degradation_factor = (10 - quality_level) / 10.0
        
        sample_rate = max(8000, int(44100 - degradation_factor * 36100))
        bitrate = max(16, int(128 - degradation_factor * 112))
        
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_output:
            try:
                input_stream = ffmpeg.input(temp_input.name)
                audio_stream = input_stream.audio
                
                if degradation_factor > 0.3:
                    audio_stream = ffmpeg.filter(audio_stream, 'aformat', 
                                               sample_rates=sample_rate)
                
                if degradation_factor > 0.5:
                    volume_factor = max(0.3, 1 - degradation_factor * 0.4)
                    audio_stream = ffmpeg.filter(audio_stream, 'volume', volume_factor)
                
                if degradation_factor > 0.6:
                    audio_stream = ffmpeg.filter(audio_stream, 'lowpass', f=max(1000, 8000 - int(degradation_factor * 7000)))
                
                out = ffmpeg.output(
                    audio_stream, temp_output.name,
                    acodec='libvorbis',
                    audio_bitrate=f'{bitrate}k'
                )
                
                ffmpeg.run(out, overwrite_output=True, quiet=True)
                
                await progress_msg.delete()
                await message.reply_audio(
                    temp_output.name,
                    caption=f"🔥 Шакалізовано (рівень: {quality_level})"
                )
                
            except Exception as e:
                await progress_msg.edit_text(f"❌ Помилка обробки аудіо: {str(e)}")
            finally:
                os.unlink(temp_output.name)
        
        os.unlink(temp_input.name)


def register_handlers(app: Client):
    shakalize_handler = MessageHandler(
        shakalize_command,
        filters.command("shakalize", prefixes=".")
    )
    
    handlers_list = [shakalize_handler]
    
    for handler in handlers_list:
        app.add_handler(handler)
    
    return handlers_list