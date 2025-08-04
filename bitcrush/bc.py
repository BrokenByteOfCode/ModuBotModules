import numpy as np
from pydub import AudioSegment
import os
import tempfile
from pyrogram import Client, filters
import logging

logger = logging.getLogger(__name__)

def bitcrush(audio, bit_depth=8, sample_rate_reduction=4):
    max_val = 2**(bit_depth - 1) - 1
    min_val = -2**(bit_depth - 1)
    quantized = np.round(audio * max_val) / max_val
    quantized = np.clip(quantized, min_val / max_val, max_val / max_val)
    original_length = len(quantized)
    reduced_length = original_length // sample_rate_reduction
    downsampled = quantized[::sample_rate_reduction]
    upsampled = np.repeat(downsampled, sample_rate_reduction)[:original_length]
    return upsampled

def register_handlers(app: Client):
    @app.on_message(filters.command("bitcrush", prefixes=".") & filters.reply)
    async def bitcrush_command(client, message):
        if not message.reply_to_message or not message.reply_to_message.audio:
            await message.reply_text("❌ Please reply to an audio file")
            return
        
        try:
            status_msg = await message.reply_text("🎵 Processing audio...")
            
            audio_file = await client.download_media(message.reply_to_message.audio)
            
            await status_msg.edit_text("🔧 Applying bitcrush effect...")
            
            audio = AudioSegment.from_file(audio_file)
            audio = audio.set_channels(1)
            
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples /= np.iinfo(audio.array_type).max
            
            bitcrushed_samples = bitcrush(samples)
            bitcrushed_samples = (bitcrushed_samples * np.iinfo(audio.array_type).max).astype(audio.array_type)
            
            bitcrushed_audio = audio._spawn(bitcrushed_samples.tobytes())
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                bitcrushed_audio.export(tmp_file.name, format="mp3")
                tmp_file_path = tmp_file.name
            
            await status_msg.edit_text("📤 Uploading processed audio...")
            
            await message.reply_audio(
                tmp_file_path, 
                caption="🎛 **Bitcrushed Audio**\n8-bit depth • 4x sample rate reduction"
            )
            
            await status_msg.delete()
            
            os.remove(audio_file)
            os.remove(tmp_file_path)
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            await message.reply_text(f"❌ Error processing audio: {str(e)}")
            if 'audio_file' in locals() and os.path.exists(audio_file):
                os.remove(audio_file)
            if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    @app.on_message(filters.command("bitcrushcustom", prefixes=".") & filters.reply)
    async def bitcrush_custom_command(client, message):
        if not message.reply_to_message or not message.reply_to_message.audio:
            await message.reply_text("❌ Please reply to an audio file")
            return
        
        args = message.command[1:]
        if len(args) != 2:
            await message.reply_text("❌ Usage: `.bitcrushcustom <bit_depth> <sample_rate_reduction>`\nExample: `.bitcrushcustom 4 8`")
            return
        
        try:
            bit_depth = int(args[0])
            sample_rate_reduction = int(args[1])
            
            if bit_depth < 1 or bit_depth > 16:
                await message.reply_text("❌ Bit depth must be between 1 and 16")
                return
            
            if sample_rate_reduction < 1 or sample_rate_reduction > 32:
                await message.reply_text("❌ Sample rate reduction must be between 1 and 32")
                return
            
        except ValueError:
            await message.reply_text("❌ Invalid parameters. Use integers only.")
            return
        
        try:
            status_msg = await message.reply_text(f"🎵 Processing audio with {bit_depth}-bit depth and {sample_rate_reduction}x reduction...")
            
            audio_file = await client.download_media(message.reply_to_message.audio)
            
            await status_msg.edit_text("🔧 Applying custom bitcrush effect...")
            
            audio = AudioSegment.from_file(audio_file)
            audio = audio.set_channels(1)
            
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples /= np.iinfo(audio.array_type).max
            
            bitcrushed_samples = bitcrush(samples, bit_depth, sample_rate_reduction)
            bitcrushed_samples = (bitcrushed_samples * np.iinfo(audio.array_type).max).astype(audio.array_type)
            
            bitcrushed_audio = audio._spawn(bitcrushed_samples.tobytes())
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                bitcrushed_audio.export(tmp_file.name, format="mp3")
                tmp_file_path = tmp_file.name
            
            await status_msg.edit_text("📤 Uploading processed audio...")
            
            await message.reply_audio(
                tmp_file_path, 
                caption=f"🎛 **Custom Bitcrushed Audio**\n{bit_depth}-bit depth • {sample_rate_reduction}x sample rate reduction"
            )
            
            await status_msg.delete()
            
            os.remove(audio_file)
            os.remove(tmp_file_path)
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            await message.reply_text(f"❌ Error processing audio: {str(e)}")
            if 'audio_file' in locals() and os.path.exists(audio_file):
                os.remove(audio_file)
            if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)