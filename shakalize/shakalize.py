import os
import io
import random
import subprocess
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
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
        
    if level >= 8:
        img_array = np.array(img)
        noise = np.random.randint(-50, 50, img_array.shape, dtype=np.int16)
        img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(img_array)
        
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=jpeg_quality)
    buffer.seek(0)
    
    return Image.open(buffer)

def process_video_ffmpeg(input_path, output_path, level):
    quality_map = {
        1: ("480", "128k", "24"),
        2: ("360", "96k", "20"),
        3: ("240", "64k", "15"),
        4: ("180", "48k", "12"),
        5: ("144", "32k", "10"),
        6: ("120", "24k", "8"),
        7: ("96", "16k", "6"),
        8: ("72", "12k", "4"),
        9: ("48", "8k", "3"),
        10: ("36", "4k", "2")
    }
    
    height, audio_bitrate, fps = quality_map.get(level, ("36", "4k", "2"))
    
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", f"scale=-1:{height}",
        "-r", fps,
        "-b:a", audio_bitrate,
        "-crf", str(min(51, 18 + level * 3)),
        "-preset", "ultrafast",
        "-y", output_path
    ]
    
    if level >= 8:
        cmd.insert(-2, "-vf")
        cmd.insert(-2, f"scale=-1:{height},noise=alls=20:allf=t+u")
    
    subprocess.run(cmd, capture_output=True)

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
    
    img_array = np.array(img)
    noise_level = random.randint(80, 200)
    noise = np.random.randint(-noise_level, noise_level, img_array.shape, dtype=np.int16)
    img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(img_array)
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=random.randint(1, 15))
    buffer.seek(0)
    
    return Image.open(buffer)

def epic_process_video_ffmpeg(input_path, output_path):
    height = random.randint(24, 72)
    fps = random.randint(1, 5)
    audio_bitrate = random.choice(["4k", "8k", "12k"])
    
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", f"scale=-1:{height},noise=alls={random.randint(50,100)}:allf=t+u,hue=s={random.uniform(0.1, 3.0)}",
        "-r", str(fps),
        "-b:a", audio_bitrate,
        "-crf", "51",
        "-preset", "ultrafast",
        "-y", output_path
    ]
    
    subprocess.run(cmd, capture_output=True)

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
            output_path = f"shakalized_{level}_{os.path.splitext(os.path.basename(file_path))[0]}.mp4"
            process_video_ffmpeg(file_path, output_path, level)
            
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
            output_path = f"epic_{os.path.splitext(os.path.basename(file_path))[0]}.mp4"
            epic_process_video_ffmpeg(file_path, output_path)
            
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