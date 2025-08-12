from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
import os
import tempfile
import asyncio
import wave
import struct
import subprocess

async def update_progress(message: Message, step: str, current: int, total: int):
    steps = [
        "Downloading Audio",
        "Processing Audio", 
        "Applying Bitcrush",
        "Uploading Result"
    ]
    
    progress_text = ""
    for i, step_name in enumerate(steps):
        if i < current:
            progress_text += f"[✓] {step_name}\n"
        elif i == current:
            progress_text += f"[?] {step_name}...\n"
        else:
            progress_text += f"[ ] {step_name}\n"
    
    try:
        await message.edit_text(f"**Bitcrush Processing:**\n{progress_text}")
    except:
        pass

async def convert_to_wav(input_path: str, output_path: str):
    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', input_path, '-y', output_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()

async def bitcrush_audio(audio_path: str, output_path: str, bit_depth: int = 4, sample_rate: int = 8000):
    temp_wav = audio_path.replace('.', '_temp.') + '.wav'
    
    await convert_to_wav(audio_path, temp_wav)
    
    with wave.open(temp_wav, 'rb') as wav_file:
        frames = wav_file.readframes(-1)
        sample_width = wav_file.getsampwidth()
        channels = wav_file.getnchannels()
    
    if sample_width == 2:
        samples = struct.unpack('<' + 'h' * (len(frames) // 2), frames)
        max_input = 32767
    else:
        samples = struct.unpack('<' + 'B' * len(frames), frames)
        max_input = 127
    
    max_val = 2**(bit_depth - 1) - 1
    min_val = -2**(bit_depth - 1)
    
    crushed_samples = []
    downsample_step = max(1, len(samples) // (sample_rate * 2))
    
    for i in range(0, len(samples), downsample_step):
        sample = samples[i]
        normalized = sample / max_input
        quantized = round(normalized * max_val)
        quantized = max(min_val, min(max_val, quantized))
        crushed = int(quantized * max_input / max_val) if max_val > 0 else 0
        crushed_samples.append(crushed)
    
    format_char = 'h' if sample_width == 2 else 'B'
    crushed_frames = struct.pack('<' + format_char * len(crushed_samples), *crushed_samples)
    
    with wave.open(output_path, 'wb') as out_wav:
        out_wav.setnchannels(1)
        out_wav.setsampwidth(sample_width)
        out_wav.setframerate(sample_rate)
        out_wav.writeframes(crushed_frames)
    
    os.remove(temp_wav)

async def bitcrush_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Reply to audio/voice message to apply bitcrush effect")
        return
    
    reply = message.reply_to_message
    if not (reply.audio or reply.voice or reply.video_note):
        await message.reply_text("Please reply to audio, voice message or video note")
        return
    
    status_msg = await message.reply_text("**Bitcrush Processing:**\n[ ] Downloading Audio\n[ ] Processing Audio\n[ ] Applying Bitcrush\n[ ] Uploading Result")
    
    try:
        await update_progress(status_msg, "Downloading", 0, 4)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            if reply.audio:
                file_path = await client.download_media(reply.audio, file_name=os.path.join(temp_dir, "input.mp3"))
            elif reply.voice:
                file_path = await client.download_media(reply.voice, file_name=os.path.join(temp_dir, "input.ogg"))
            else:
                file_path = await client.download_media(reply.video_note, file_name=os.path.join(temp_dir, "input.mp4"))
            
            await update_progress(status_msg, "Processing", 1, 4)
            await asyncio.sleep(0.5)
            
            output_path = os.path.join(temp_dir, "bitcrushed.wav")
            
            await update_progress(status_msg, "Applying", 2, 4)
            
            bit_depth = 4
            sample_rate = 8000
            
            if len(message.command) > 1:
                try:
                    params = message.command[1].split()
                    if len(params) >= 1:
                        bit_depth = max(1, min(16, int(params[0])))
                    if len(params) >= 2:
                        sample_rate = max(1000, min(48000, int(params[1])))
                except:
                    pass
            
            await bitcrush_audio(file_path, output_path, bit_depth, sample_rate)
            
            await update_progress(status_msg, "Uploading", 3, 4)
            
            await client.send_audio(
                chat_id=message.chat.id,
                audio=output_path,
                caption=f"🎵 Bitcrushed (Depth: {bit_depth}bit, Rate: {sample_rate}Hz)",
                reply_to_message_id=reply.id
            )
            
            await status_msg.edit_text("**Bitcrush Processing:**\n[✓] Downloading Audio\n[✓] Processing Audio\n[✓] Applying Bitcrush\n[✓] Uploading Result\n\n✅ **Complete!**")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

def register_handlers(app: Client):
    bitcrush_handler = MessageHandler(
        bitcrush_command,
        filters.command(["bitcrush", "bcr"], prefixes=".") & filters.me
    )
    
    handlers_list = [bitcrush_handler]
    
    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list