from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
import os
import tempfile
import asyncio
import subprocess
import shutil

async def update_progress(message: Message, current: int):
    steps = ["Downloading", "Processing", "Bitcrushing", "Uploading"]
    
    progress = ""
    for i, step in enumerate(steps):
        if i < current:
            progress += f"[✓] {step}\n"
        elif i == current:
            progress += f"[?] {step}...\n"
        else:
            progress += f"[ ] {step}\n"
    
    try:
        await message.edit_text(f"**Bitcrush:**\n{progress}")
    except:
        pass

async def run_command(cmd, timeout=20):
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        return process.returncode == 0
    except:
        return False

async def bitcrush_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Reply to audio/voice to bitcrush")
        return
    
    reply = message.reply_to_message
    if not (reply.audio or reply.voice or reply.video_note):
        await message.reply_text("Reply to audio/voice/video note")
        return
    
    status_msg = await message.reply_text("**Bitcrush:**\n[ ] Downloading\n[ ] Processing\n[ ] Bitcrushing\n[ ] Uploading")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        await update_progress(status_msg, 0)
        
        if reply.audio:
            input_file = await client.download_media(reply.audio, file_name=os.path.join(temp_dir, "input.mp3"))
        elif reply.voice:
            input_file = await client.download_media(reply.voice, file_name=os.path.join(temp_dir, "input.ogg"))
        else:
            input_file = await client.download_media(reply.video_note, file_name=os.path.join(temp_dir, "input.mp4"))
        
        await update_progress(status_msg, 1)
        
        rate = 8000
        if len(message.command) > 1:
            try:
                rate = max(4000, min(22050, int(message.command[1])))
            except:
                pass
        
        await update_progress(status_msg, 2)
        
        wav_file = os.path.join(temp_dir, "temp.wav")
        output_file = os.path.join(temp_dir, "crushed.ogg")
        
        conv_cmd = ['ffmpeg', '-i', input_file, '-ac', '1', '-ar', '44100', '-y', wav_file]
        if not await run_command(conv_cmd):
            raise Exception("Convert failed")
        
        crush_cmd = ['sox', wav_file, output_file, 'rate', str(rate), 'dither']
        if not await run_command(crush_cmd):
            crush_cmd = ['ffmpeg', '-i', wav_file, '-ar', str(rate), '-ac', '1', '-ab', '32k', '-y', output_file]
            if not await run_command(crush_cmd):
                raise Exception("Bitcrush failed")
        
        await update_progress(status_msg, 3)
        
        if os.path.exists(output_file):
            await client.send_audio(
                chat_id=message.chat.id,
                audio=output_file,
                caption=f"🎵 Bitcrushed {rate}Hz",
                reply_to_message_id=reply.id
            )
            
            await status_msg.edit_text("**Bitcrush:**\n[✓] Downloading\n[✓] Processing\n[✓] Bitcrushing\n[✓] Uploading\n\n✅ Done!")
        else:
            raise Exception("Output file not found")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

def register_handlers(app: Client):
    bitcrush_handler = MessageHandler(
        bitcrush_command,
        filters.command(["bitcrush", "bcr"], prefixes=".") & filters.me
    )
    
    handlers_list = [bitcrush_handler]
    
    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list