from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
import os
import tempfile
import asyncio
import subprocess

async def update_progress(message: Message, current: int):
    steps = ["Downloading Audio", "Processing Audio", "Applying Bitcrush", "Uploading Result"]
    
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

async def run_ffmpeg(cmd):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
        limit=1024*1024
    )
    
    try:
        await asyncio.wait_for(process.wait(), timeout=30.0)
        return process.returncode == 0
    except asyncio.TimeoutError:
        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except:
            process.kill()
        return False

async def bitcrush_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Reply to audio/voice message to apply bitcrush effect")
        return
    
    reply = message.reply_to_message
    if not (reply.audio or reply.voice or reply.video_note):
        await message.reply_text("Please reply to audio, voice message or video note")
        return
    
    status_msg = await message.reply_text("**Bitcrush Processing:**\n[ ] Downloading Audio\n[ ] Processing Audio\n[ ] Applying Bitcrush\n[ ] Uploading Result")
    
    temp_dir = None
    
    try:
        temp_dir = tempfile.mkdtemp()
        
        await update_progress(status_msg, 0)
        
        if reply.audio:
            file_path = await client.download_media(reply.audio, file_name=os.path.join(temp_dir, "input.mp3"))
        elif reply.voice:
            file_path = await client.download_media(reply.voice, file_name=os.path.join(temp_dir, "input.ogg"))
        else:
            file_path = await client.download_media(reply.video_note, file_name=os.path.join(temp_dir, "input.mp4"))
        
        await update_progress(status_msg, 1)
        
        sample_rate = 8000
        if len(message.command) > 1:
            try:
                sample_rate = max(1000, min(22050, int(message.command[1])))
            except:
                pass
        
        await update_progress(status_msg, 2)
        
        output_path = os.path.join(temp_dir, "bitcrushed.ogg")
        
        cmd = [
            'ffmpeg', '-i', file_path,
            '-af', f'aresample={sample_rate}:resampler=soxr,volume=0.7',
            '-ar', str(sample_rate),
            '-ac', '1',
            '-ab', '32k',
            '-y', output_path
        ]
        
        success = await run_ffmpeg(cmd)
        
        if not success or not os.path.exists(output_path):
            raise Exception("Audio processing failed")
        
        await update_progress(status_msg, 3)
        
        await client.send_audio(
            chat_id=message.chat.id,
            audio=output_path,
            caption=f"🎵 Bitcrushed ({sample_rate}Hz)",
            reply_to_message_id=reply.id
        )
        
        await status_msg.edit_text("**Bitcrush Processing:**\n[✓] Downloading Audio\n[✓] Processing Audio\n[✓] Applying Bitcrush\n[✓] Uploading Result\n\n✅ **Complete!**")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

def register_handlers(app: Client):
    bitcrush_handler = MessageHandler(
        bitcrush_command,
        filters.command(["bitcrush", "bcr"], prefixes=".") & filters.me
    )
    
    return [bitcrush_handler]