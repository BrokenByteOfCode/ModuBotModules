from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import ffmpeg
import io
import os
import tempfile
import random
import math
import numpy as np


async def shakalize_command(client: Client, message: Message):
    quality_level = 1
    
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
    
    progress_msg = await message.reply_text(f"Обробляю медіа з максимальною деградацією (рівень: {quality_level})...")
    
    try:
        if media_type == "photo":
            await ultra_shakalize_photo(client, message, media, quality_level, progress_msg)
        elif media_type == "video":
            await ultra_shakalize_video(client, message, media, quality_level, progress_msg)
        elif media_type in ["audio", "voice"]:
            await ultra_shakalize_audio(client, message, media, quality_level, progress_msg)
    except Exception as e:
        await progress_msg.edit_text(f"Критична помилка при обробці: {str(e)}")


async def ultra_shakalize_photo(client: Client, message: Message, photo, quality_level: int, progress_msg):
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_input:
        try:
            await client.download_media(photo, temp_input.name)
        except Exception as e:
            if "FILE_REFERENCE_EXPIRED" in str(e):
                target_message = message.reply_to_message if message.reply_to_message else message
                fresh_message = await client.get_messages(target_message.chat.id, target_message.id)
                if fresh_message.photo:
                    await client.download_media(fresh_message.photo, temp_input.name)
                else:
                    raise Exception("Не вдалося отримати свіжий file reference для зображення")
            else:
                raise e
        
        with Image.open(temp_input.name) as img:
            img = img.convert('RGB')
            
            degradation_factor = (10 - quality_level) / 10.0
            chaos_multiplier = 1 + degradation_factor * 3
            
            original_size = img.size
            
            scale_iterations = max(1, int(degradation_factor * 8))
            for i in range(scale_iterations):
                scale_factor = max(0.05, random.uniform(0.1, 0.6))
                tiny_size = (max(1, int(original_size[0] * scale_factor)), 
                           max(1, int(original_size[1] * scale_factor)))
                img = img.resize(tiny_size, Image.LANCZOS)
                img = img.resize(original_size, random.choice([Image.NEAREST, Image.BOX]))
            
            if degradation_factor > 0.2:
                blur_intensity = degradation_factor * 5 * chaos_multiplier
                for _ in range(max(1, int(degradation_factor * 4))):
                    blur_type = random.choice([ImageFilter.GaussianBlur, ImageFilter.BoxBlur])
                    img = img.filter(blur_type(radius=random.uniform(0.5, blur_intensity)))
            
            if degradation_factor > 0.1:
                img_array = np.array(img)
                noise_intensity = int(degradation_factor * 80 * chaos_multiplier)
                
                salt_pepper_prob = degradation_factor * 0.4
                mask = np.random.random(img_array.shape[:2]) < salt_pepper_prob
                img_array[mask] = np.random.choice([0, 255], size=img_array[mask].shape)
                
                gaussian_noise = np.random.normal(0, noise_intensity, img_array.shape).astype(np.int16)
                img_array = np.clip(img_array.astype(np.int16) + gaussian_noise, 0, 255).astype(np.uint8)
                
                if degradation_factor > 0.6:
                    stripe_intensity = int(degradation_factor * 50)
                    for _ in range(max(1, int(degradation_factor * 20))):
                        if random.choice([True, False]):
                            row = random.randint(0, img_array.shape[0] - 1)
                            img_array[row, :] = np.random.randint(0, 256, img_array[row, :].shape)
                        else:
                            col = random.randint(0, img_array.shape[1] - 1)
                            img_array[:, col] = np.random.randint(0, 256, img_array[:, col].shape)
                
                img = Image.fromarray(img_array)
            
            if degradation_factor > 0.3:
                contrast_factor = max(0.1, 1 - degradation_factor * 1.5)
                brightness_factor = random.uniform(0.3, 1.7)
                saturation_factor = random.uniform(0.1, 2.5)
                
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(contrast_factor)
                
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(brightness_factor)
                
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(saturation_factor)
            
            if degradation_factor > 0.5:
                corruption_operations = [
                    lambda x: ImageOps.posterize(x, max(1, int(8 - degradation_factor * 6))),
                    lambda x: ImageOps.solarize(x, int(255 * (1 - degradation_factor))),
                    lambda x: x.filter(ImageFilter.FIND_EDGES) if random.random() < 0.3 else x,
                    lambda x: ImageOps.invert(x) if random.random() < degradation_factor * 0.4 else x
                ]
                
                for op in random.sample(corruption_operations, 
                                      max(1, int(degradation_factor * len(corruption_operations)))):
                    try:
                        img = op(img)
                    except:
                        pass
            
            if degradation_factor > 0.7:
                glitch_blocks = int(degradation_factor * 100)
                img_array = np.array(img)
                for _ in range(glitch_blocks):
                    x1 = random.randint(0, max(1, img_array.shape[1] - 10))
                    y1 = random.randint(0, max(1, img_array.shape[0] - 10))
                    x2 = min(img_array.shape[1], x1 + random.randint(5, 50))
                    y2 = min(img_array.shape[0], y1 + random.randint(5, 50))
                    
                    if random.choice([True, False]):
                        img_array[y1:y2, x1:x2] = np.random.randint(0, 256, 
                                                                   (y2-y1, x2-x1, 3))
                    else:
                        shift_x = random.randint(-20, 20)
                        shift_y = random.randint(-20, 20)
                        try:
                            source_x1 = max(0, x1 + shift_x)
                            source_y1 = max(0, y1 + shift_y)
                            source_x2 = min(img_array.shape[1], x2 + shift_x)
                            source_y2 = min(img_array.shape[0], y2 + shift_y)
                            
                            if source_x2 > source_x1 and source_y2 > source_y1:
                                img_array[y1:y1+(source_y2-source_y1), 
                                         x1:x1+(source_x2-source_x1)] = \
                                    img_array[source_y1:source_y2, source_x1:source_x2]
                        except:
                            pass
                
                img = Image.fromarray(img_array)
            
            jpeg_quality = max(1, int(5 - degradation_factor * 4))
            
            compression_cycles = max(1, int(degradation_factor * 5))
            for cycle in range(compression_cycles):
                cycle_quality = max(1, jpeg_quality + random.randint(-2, 2))
                
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as cycle_temp:
                    img.save(cycle_temp.name, 'JPEG', quality=cycle_quality, optimize=False)
                    img = Image.open(cycle_temp.name)
                    img.load()
                    os.unlink(cycle_temp.name)
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_output:
                img.save(temp_output.name, 'JPEG', quality=jpeg_quality, optimize=False)
                
                await progress_msg.delete()
                await message.reply_photo(
                    temp_output.name,
                    caption=f"Шакалізовано з максимальною деградацією (рівень: {quality_level})"
                )
                
                os.unlink(temp_output.name)
        
        os.unlink(temp_input.name)


async def ultra_shakalize_video(client: Client, message: Message, video, quality_level: int, progress_msg):
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
        try:
            await client.download_media(video, temp_input.name)
        except Exception as e:
            if "FILE_REFERENCE_EXPIRED" in str(e):
                target_message = message.reply_to_message if message.reply_to_message else message
                fresh_message = await client.get_messages(target_message.chat.id, target_message.id)
                if fresh_message.video:
                    await client.download_media(fresh_message.video, temp_input.name)
                elif fresh_message.document and fresh_message.document.mime_type.startswith('video/'):
                    await client.download_media(fresh_message.document, temp_input.name)
                else:
                    raise Exception("Не вдалося отримати свіжий file reference для відео")
            else:
                raise e
        
        degradation_factor = (10 - quality_level) / 10.0
        chaos_multiplier = 1 + degradation_factor * 4
        
        crf = min(51, int(25 + degradation_factor * 26))
        scale_factor = max(0.1, 1 - degradation_factor * 0.9)
        
        bitrate = max(10, int(500 - degradation_factor * 490))
        framerate_factor = max(0.1, 1 - degradation_factor * 0.8)
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            try:
                input_stream = ffmpeg.input(temp_input.name)
                
                video_stream = input_stream.video
                
                if scale_factor < 0.95:
                    scale_iterations = max(1, int(degradation_factor * 3))
                    for i in range(scale_iterations):
                        current_scale = max(0.1, scale_factor * random.uniform(0.5, 1.2))
                        video_stream = ffmpeg.filter(video_stream, 'scale', 
                                                   f'iw*{current_scale}', f'ih*{current_scale}')
                        video_stream = ffmpeg.filter(video_stream, 'scale', 
                                                   'iw/1', 'ih/1', flags='neighbor')
                
                if degradation_factor > 0.2:
                    noise_strength = int(degradation_factor * 40 * chaos_multiplier)
                    video_stream = ffmpeg.filter(video_stream, 'noise', 
                                               alls=noise_strength, allf='t+u')
                
                if degradation_factor > 0.4:
                    video_stream = ffmpeg.filter(video_stream, 'hue', 
                                               h=f'{random.randint(-180, 180)}',
                                               s=f'{random.uniform(0.1, 3.0)}')
                
                if degradation_factor > 0.5:
                    blur_strength = degradation_factor * 8
                    video_stream = ffmpeg.filter(video_stream, 'boxblur', 
                                               luma_radius=f'{blur_strength}',
                                               chroma_radius=f'{blur_strength}')
                
                if degradation_factor > 0.6:
                    video_stream = ffmpeg.filter(video_stream, 'curves', 
                                               vintage='0.5')
                    video_stream = ffmpeg.filter(video_stream, 'eq', 
                                               contrast=random.uniform(0.1, 3.0),
                                               brightness=random.uniform(-0.5, 0.5),
                                               saturation=random.uniform(0.1, 3.0))
                
                if degradation_factor > 0.7:
                    datamosh_strength = int(degradation_factor * 20)
                    video_stream = ffmpeg.filter(video_stream, 'random', 
                                               frames=datamosh_strength)
                
                if framerate_factor < 0.9:
                    target_fps = max(1, int(30 * framerate_factor))
                    video_stream = ffmpeg.filter(video_stream, 'fps', fps=target_fps)
                
                audio_stream = input_stream.audio
                if degradation_factor > 0.2:
                    audio_sample_rate = max(4000, int(44100 - degradation_factor * 40100))
                    audio_bitrate = max(8, int(128 - degradation_factor * 120))
                    
                    audio_stream = ffmpeg.filter(audio_stream, 'aformat', 
                                               sample_rates=audio_sample_rate)
                    
                    if degradation_factor > 0.4:
                        distortion = min(0.9, degradation_factor * 0.8)
                        audio_stream = ffmpeg.filter(audio_stream, 'overdrive', 
                                                   drive=distortion)
                    
                    if degradation_factor > 0.6:
                        audio_stream = ffmpeg.filter(audio_stream, 'lowpass', 
                                                   f=max(500, 8000 - int(degradation_factor * 7500)))
                        audio_stream = ffmpeg.filter(audio_stream, 'volume', 
                                                   volume=random.uniform(0.1, 2.0))
                    
                    if degradation_factor > 0.8:
                        audio_stream = ffmpeg.filter(audio_stream, 'tremolo', 
                                                   f=random.uniform(1, 20),
                                                   d=random.uniform(0.1, 0.9))
                
                out = ffmpeg.output(
                    video_stream, audio_stream, temp_output.name,
                    vcodec='libx264',
                    acodec='aac',
                    crf=crf,
                    video_bitrate=f'{bitrate}k',
                    audio_bitrate=f'{max(8, int(128 - degradation_factor * 120))}k',
                    preset='ultrafast',
                    pix_fmt='yuv420p'
                )
                
                ffmpeg.run(out, overwrite_output=True, quiet=True)
                
                await progress_msg.delete()
                await message.reply_video(
                    temp_output.name,
                    caption=f"Відео шакалізовано з максимальною деградацією (рівень: {quality_level})"
                )
                
            except Exception as e:
                await progress_msg.edit_text(f"Помилка обробки відео: {str(e)}")
            finally:
                os.unlink(temp_output.name)
        
        os.unlink(temp_input.name)


async def ultra_shakalize_audio(client: Client, message: Message, audio, quality_level: int, progress_msg):
    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_input:
        try:
            await client.download_media(audio, temp_input.name)
        except Exception as e:
            if "FILE_REFERENCE_EXPIRED" in str(e):
                target_message = message.reply_to_message if message.reply_to_message else message
                fresh_message = await client.get_messages(target_message.chat.id, target_message.id)
                if fresh_message.audio:
                    await client.download_media(fresh_message.audio, temp_input.name)
                elif fresh_message.voice:
                    await client.download_media(fresh_message.voice, temp_input.name)
                elif fresh_message.document and fresh_message.document.mime_type.startswith('audio/'):
                    await client.download_media(fresh_message.document, temp_input.name)
                else:
                    raise Exception("Не вдалося отримати свіжий file reference для аудіо")
            else:
                raise e
        
        degradation_factor = (10 - quality_level) / 10.0
        chaos_multiplier = 1 + degradation_factor * 5
        
        sample_rate = max(2000, int(44100 - degradation_factor * 42100))
        bitrate = max(4, int(128 - degradation_factor * 124))
        
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_output:
            try:
                input_stream = ffmpeg.input(temp_input.name)
                audio_stream = input_stream.audio
                
                if degradation_factor > 0.1:
                    audio_stream = ffmpeg.filter(audio_stream, 'aformat', 
                                               sample_rates=sample_rate)
                
                if degradation_factor > 0.3:
                    volume_chaos = random.uniform(0.1, 3.0) * chaos_multiplier
                    audio_stream = ffmpeg.filter(audio_stream, 'volume', 
                                               volume=min(3.0, volume_chaos))
                
                if degradation_factor > 0.4:
                    lowpass_freq = max(200, 8000 - int(degradation_factor * 7800))
                    audio_stream = ffmpeg.filter(audio_stream, 'lowpass', f=lowpass_freq)
                
                if degradation_factor > 0.5:
                    distortion_level = min(0.95, degradation_factor * 0.9)
                    audio_stream = ffmpeg.filter(audio_stream, 'overdrive', 
                                               drive=distortion_level)
                
                if degradation_factor > 0.6:
                    tremolo_freq = random.uniform(0.5, 50) * degradation_factor
                    tremolo_depth = min(0.95, degradation_factor * 0.8)
                    audio_stream = ffmpeg.filter(audio_stream, 'tremolo', 
                                               f=tremolo_freq, d=tremolo_depth)
                
                if degradation_factor > 0.7:
                    echo_delay = int(degradation_factor * 1000)
                    echo_decay = min(0.9, degradation_factor * 0.7)
                    audio_stream = ffmpeg.filter(audio_stream, 'aecho', 
                                               delays=f'{echo_delay}',
                                               decays=f'{echo_decay}')
                
                if degradation_factor > 0.8:
                    chorus_delays = '25|40|60'
                    chorus_decays = '0.5|0.4|0.3'
                    chorus_speeds = '0.25|0.4|0.3'
                    chorus_depths = '2|2.3|1.3'
                    
                    audio_stream = ffmpeg.filter(audio_stream, 'chorus', 
                                               delays=chorus_delays,
                                               decays=chorus_decays,
                                               speeds=chorus_speeds,
                                               depths=chorus_depths)
                
                if degradation_factor > 0.9:
                    audio_stream = ffmpeg.filter(audio_stream, 'highpass', f=100)
                    audio_stream = ffmpeg.filter(audio_stream, 'aphaser', 
                                               delay=random.uniform(1, 10),
                                               depth=random.uniform(0.5, 2.0),
                                               speed=random.uniform(0.1, 2.0))
                
                out = ffmpeg.output(
                    audio_stream, temp_output.name,
                    acodec='libvorbis',
                    audio_bitrate=f'{bitrate}k'
                )
                
                ffmpeg.run(out, overwrite_output=True, quiet=True)
                
                await progress_msg.delete()
                await message.reply_audio(
                    temp_output.name,
                    caption=f"Аудіо шакалізовано з максимальною деградацією (рівень: {quality_level})"
                )
                
            except Exception as e:
                await progress_msg.edit_text(f"Помилка обробки аудіо: {str(e)}")
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