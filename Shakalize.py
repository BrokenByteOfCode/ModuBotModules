import os
import subprocess
import random
import cv2
import numpy as np
from pyrogram import Client, filters
from PIL import Image
from pydub import AudioSegment
from pydub.utils import make_chunks

def shakalize_image(file_path, intensity):
    with Image.open(file_path) as img:
        quality = max(1, 100 - intensity * 10)
        shakalized_path = f"shakalized_{os.path.basename(file_path)}"
        img.save(shakalized_path, quality=quality)
    return shakalized_path

def shakalize_video(file_path, intensity):
    video_bitrate = max(100, 10000 - intensity * 1000)
    audio_bitrate = max(32, 320 - intensity * 32)
    shakalized_path = f"shakalized_{os.path.basename(file_path)}"
    
    command = [
        "ffmpeg",
        "-i", file_path,
        "-b:v", f"{video_bitrate}k",
        "-b:a", f"{audio_bitrate}k",
        "-vf", f"scale=iw/{intensity}:ih/{intensity},scale=iw*{intensity}:ih*{intensity}",
        "-preset", "ultrafast",
        "-y", shakalized_path
    ]
    subprocess.run(command, check=True)
    return shakalized_path

def epicize_video(file_path):
    epicized_path = f"epicized_{os.path.basename(file_path)}"
    
    command = [
        "ffmpeg",
        "-i", file_path,
        "-b:v", "8k",
        "-b:a", "8k",
        "-vf", "scale=160:120",
        "-ar", "8000",
        "-preset", "ultrafast",
        "-y", epicized_path
    ]
    subprocess.run(command, check=True)
    return epicized_path

def corrupt_image(file_path, seed):
    random.seed(seed)
    img = cv2.imread(file_path)
    height, width, _ = img.shape

    num_effects = random.randint(1, 5)
    for _ in range(num_effects):
        effect = random.choice(['noise', 'shift', 'glitch', 'color'])
        
        if effect == 'noise':
            noise = np.random.normal(0, random.randint(20, 80), img.shape).astype(np.uint8)
            img = cv2.add(img, noise)
        elif effect == 'shift':
            shift = random.randint(10, 100)
            direction = random.choice(['horizontal', 'vertical'])
            img = np.roll(img, shift, axis=1 if direction == 'horizontal' else 0)
        elif effect == 'glitch':
            h_start, w_start = random.randint(0, height - 1), random.randint(0, width - 1)
            h_end, w_end = random.randint(h_start + 1, height), random.randint(w_start + 1, width)
            img[h_start:h_end, w_start:w_end] = cv2.bitwise_not(img[h_start:h_end, w_start:w_end])
        elif effect == 'color':
            channel = random.randint(0, 2)
            img[:,:,channel] = cv2.add(img[:,:,channel], random.randint(50, 200))

    corrupted_path = f"corrupted_{seed}_{os.path.basename(file_path)}"
    cv2.imwrite(corrupted_path, img)
    return corrupted_path

def corrupt_video(file_path, seed):
    random.seed(seed)
    cap = cv2.VideoCapture(file_path)
    frame_count, fps = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), int(cap.get(cv2.CAP_PROP_FPS))
    width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    audio_path = f"temp_audio_{seed}.wav"
    subprocess.run(["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", audio_path, "-y"], check=True)
    
    corrupted_path = f"corrupted_{seed}_{os.path.basename(file_path)}"
    out = cv2.VideoWriter(corrupted_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    corruption_probability = random.uniform(0.05, 0.2)

    for _ in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break
        
        if random.random() < corruption_probability:
            effect = random.choice(['noise', 'shift', 'glitch', 'color'])
            if effect == 'noise':
                frame = cv2.add(frame, np.random.normal(0, random.randint(20, 80), frame.shape).astype(np.uint8))
            elif effect == 'shift':
                shift = random.randint(10, 100)
                frame = np.roll(frame, shift, axis=random.choice([0, 1]))
            elif effect == 'glitch':
                h_start, w_start = random.randint(0, height - 1), random.randint(0, width - 1)
                h_end, w_end = random.randint(h_start + 1, height), random.randint(w_start + 1, width)
                frame[h_start:h_end, w_start:w_end] = cv2.bitwise_not(frame[h_start:h_end, w_start:w_end])
            elif effect == 'color':
                frame[:,:,random.randint(0, 2)] = cv2.add(frame[:,:,random.randint(0, 2)], random.randint(50, 200))

        out.write(frame)

    cap.release()
    out.release()
    
    audio = AudioSegment.from_file(audio_path)
    corrupted_audio = AudioSegment.empty()
    chunk_size = random.randint(500, 2000)
    for chunk in make_chunks(audio, chunk_size):
        if random.random() < corruption_probability:
            effect = random.choice(['volume', 'reverse', 'pitch', 'noise'])
            if effect == 'volume':
                chunk = chunk + random.randint(-30, 30)
            elif effect == 'reverse':
                chunk = chunk.reverse()
            elif effect == 'pitch':
                chunk = chunk._spawn(chunk.raw_data, overrides={'frame_rate': int(chunk.frame_rate * (2.0 ** random.uniform(-1.5, 1.5)))})
            elif effect == 'noise':
                noise = AudioSegment.silent(duration=len(chunk)).set_channels(chunk.channels).set_frame_rate(chunk.frame_rate)
                noise = noise.set_sample_width(chunk.sample_width)
                noise = noise.overlay(AudioSegment.from_file(audio_path))
                chunk = chunk.overlay(noise)
        corrupted_audio += chunk

    corrupted_audio_path = f"corrupted_audio_{seed}.wav"
    corrupted_audio.export(corrupted_audio_path, format="wav")
    
    final_path = f"final_corrupted_{seed}_{os.path.basename(file_path)}"
    subprocess.run([
        "ffmpeg", "-i", corrupted_path, 
        "-i", corrupted_audio_path, 
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", 
        final_path, "-y"
    ], check=True)
    
    for path in [audio_path, corrupted_path, corrupted_audio_path]:
        os.remove(path)
    
    return final_path

def add_on_commands(app: Client):
    @app.on_message(filters.command("shakal", prefixes=".") & filters.reply)
    def shakal_command(client, message):
        intensity = 5
        if len(message.command) == 2:
            try:
                intensity = int(message.command[1])
                if intensity < 1 or intensity > 10:
                    raise ValueError
            except ValueError:
                message.reply_text("Invalid intensity. Using default (5).")
                intensity = 5

        reply = message.reply_to_message
        if reply.photo:
            file_path = client.download_media(reply)
            result_path = shakalize_image(file_path, intensity)
            client.send_photo(message.chat.id, result_path, reply_to_message_id=message.id)
        elif reply.video:
            file_path = client.download_media(reply)
            result_path = shakalize_video(file_path, intensity)
            client.send_video(message.chat.id, result_path, reply_to_message_id=message.id)
        else:
            message.reply_text("Please reply to a photo or video.")

        try:
            os.remove(file_path)
            os.remove(result_path)
        except:
            pass

    @app.on_message(filters.command("epic", prefixes=".") & filters.reply)
    def epic_command(client, message):
        reply = message.reply_to_message
        if reply.video:
            file_path = client.download_media(reply)
            result_path = epicize_video(file_path)
            client.send_video(message.chat.id, result_path, reply_to_message_id=message.id)
        else:
            message.reply_text("Please reply to a video.")

        try:
            os.remove(file_path)
            os.remove(result_path)
        except:
            pass

    @app.on_message(filters.command("corrupt", prefixes=".") & filters.reply)
    def corrupt_command(client, message):
        seed = random.randint(1, 1000000)
        if len(message.command) == 2:
            try:
                seed = int(message.command[1])
            except ValueError:
                message.reply_text(f"Invalid seed. Using random seed: {seed}")

        reply = message.reply_to_message
        if reply.photo:
            file_path = client.download_media(reply)
            result_path = corrupt_image(file_path, seed)
            client.send_photo(message.chat.id, result_path, caption=f"Corrupted with seed: {seed}", reply_to_message_id=message.id)
        elif reply.video:
            file_path = client.download_media(reply)
            result_path = corrupt_video(file_path, seed)
            client.send_video(message.chat.id, result_path, caption=f"Corrupted with seed: {seed}", reply_to_message_id=message.id)
        else:
            message.reply_text("Please reply to a photo or video.")

        try:
            os.remove(file_path)
            os.remove(result_path)
        except:
            pass