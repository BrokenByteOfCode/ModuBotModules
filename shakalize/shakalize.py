import os
import io
import random
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from moviepy.editor import VideoFileClip
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

async def download_media(message: Message):
    if message.reply_to_message and message.reply_to_message.media:
        return await message.reply_to_message.download()
    elif message.media:
        return await message.download()
    return None

def process_image(file_path, level):
    img = Image.open(file_path)
    
    if level == 0:
        return img
    
    width, height = img.size
    
    quality_map = {
        1: (0.8, 85),
        2: (0.7, 70),
        3: (0.6, 60),
        4: (0.5, 50),
        5: (0.4, 40),
        6: (0.3, 30),
        7: (0.25, 25),
        8: (0.2, 20),
        9: (0.15, 15),
        10: (0.1, 10)
    }
    
    scale, jpeg_quality = quality_map.get(level, (0.1, 10))
    
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    img = img.resize((new_width, new_height), Image.NEAREST)
    
    if level >= 7:
        img = img.filter(ImageFilter.GaussianBlur(radius=level-6))
        
    if level >= 5:
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.5)
        
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=jpeg_quality)
    buffer.seek(0)
    
    return Image.open(buffer)

def process_video(file_path, level):
    clip = VideoFileClip(file_path)
    
    if level == 0:
        return clip
    
    quality_map = {
        1: (480, 128),
        2: (360, 96),
        3: (240, 64),
        4: (180, 48),
        5: (144, 32),
        6: (120, 24),
        7: (96, 16),
        8: (72, 12),
        9: (48, 8),
        10: (36, 4)
    }
    
    height, audio_bitrate = quality_map.get(level, (36, 4))
    
    clip = clip.resize(height=height)
    
    if level >= 5:
        clip = clip.fx(lambda gf, t: gf(t).astype('uint8'))
        
    if level >= 7:
        fps = max(1, 24 - level * 2)
        clip = clip.set_fps(fps)
        
    if level >= 8:
        def add_noise(get_frame, t):
            frame = get_frame(t)
            noise = np.random.randint(0, 50, frame.shape, dtype=np.uint8)
            return np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        clip = clip.fl(add_noise)
    
    return clip

def epic_process_image(file_path):
    img = Image.open(file_path)
    width, height = img.size
    
    img = img.resize((width//20, height//20), Image.NEAREST)
    img = img.resize((width, height), Image.NEAREST)
    
    for _ in range(5):
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(2, 8)))
    
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(random.uniform(0.3, 2.5))
    
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(random.uniform(0.2, 3.0))
    
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(random.uniform(0.1, 4.0))
    
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(random.uniform(0.1, 10.0))
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=random.randint(1, 15))
    buffer.seek(0)
    
    return Image.open(buffer)

def epic_process_video(file_path):
    clip = VideoFileClip(file_path)
    
    clip = clip.resize(height=random.randint(24, 72))
    clip = clip.set_fps(random.randint(1, 8))
    
    def epic_effect(get_frame, t):
        frame = get_frame(t)
        
        noise_level = random.randint(50, 150)
        noise = np.random.randint(-noise_level, noise_level, frame.shape, dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        if random.random() > 0.7:
            frame = np.roll(frame, random.randint(-50, 50), axis=random.randint(0, 1))
        
        return frame
    
    clip = clip.fl(epic_effect)
    
    return clip

async def shakalize_command(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            await message.reply_text("Використання: .shakalize [0-10]\nПриклад: .shakalize 5")
            return
            
        try:
            level = int(message.command[1])
            if not 0 <= level <= 10:
                await message.reply_text("Рівень повинен бути від 0 до 10")
                return
        except ValueError:
            await message.reply_text("Рівень повинен бути числом від 0 до 10")
            return
        
        file_path = await download_media(message)
        if not file_path:
            await message.reply_text("Відповідь на медіа файл або надішліть медіа з командою")
            return
        
        status_msg = await message.reply_text(f"Обробляю з рівнем {level}...")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
            processed_img = process_image(file_path, level)
            
            output_path = f"shakalized_{level}_{os.path.basename(file_path)}.jpg"
            processed_img.save(output_path, quality=85)
            
            await message.reply_photo(output_path)
            os.remove(output_path)
            
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.gif']:
            processed_clip = process_video(file_path, level)
            
            output_path = f"shakalized_{level}_{os.path.splitext(os.path.basename(file_path))[0]}.mp4"
            processed_clip.write_videofile(output_path, verbose=False, logger=None)
            processed_clip.close()
            
            await message.reply_video(output_path)
            os.remove(output_path)
            
        else:
            await message.reply_text("Непідтримуваний формат файлу")
        
        os.remove(file_path)
        await status_msg.delete()
        
    except Exception as e:
        await message.reply_text(f"Помилка: {str(e)}")

async def epic_command(client: Client, message: Message):
    try:
        file_path = await download_media(message)
        if not file_path:
            await message.reply_text("Відповідь на медіа файл або надішліть медіа з командою")
            return
        
        status_msg = await message.reply_text("Створюю ЕПІЧНУ якість...")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
            processed_img = epic_process_image(file_path)
            
            output_path = f"epic_{os.path.basename(file_path)}.jpg"
            processed_img.save(output_path, quality=random.randint(1, 10))
            
            await message.reply_photo(output_path)
            os.remove(output_path)
            
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.gif']:
            processed_clip = epic_process_video(file_path)
            
            output_path = f"epic_{os.path.splitext(os.path.basename(file_path))[0]}.mp4"
            processed_clip.write_videofile(output_path, verbose=False, logger=None, audio_bitrate="8k")
            processed_clip.close()
            
            await message.reply_video(output_path)
            os.remove(output_path)
            
        else:
            await message.reply_text("Непідтримуваний формат файлу")
        
        os.remove(file_path)
        await status_msg.delete()
        
    except Exception as e:
        await message.reply_text(f"Помилка: {str(e)}")

def register_handlers(app: Client):
    shakalize_handler = MessageHandler(
        shakalize_command,
        filters.command("shakalize", prefixes=".")
    )
    
    epic_handler = MessageHandler(
        epic_command,
        filters.command("epic", prefixes=".")
    )

    handlers_list = [shakalize_handler, epic_handler]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list