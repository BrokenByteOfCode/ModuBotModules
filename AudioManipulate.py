from pyrogram import Client, filters
import subprocess
import os
import tempfile

def add_on_commands(app: Client):
    def process_audio(input_file, output_file, filter_option):
        subprocess.run([
            "ffmpeg", "-i", input_file, "-af", filter_option, output_file,
            "-y"
        ], check=True)

    @app.on_message(filters.command("bass", prefixes="."))
    def bass_boost(client, message):
        if message.reply_to_message and (message.reply_to_message.voice or message.reply_to_message.audio):
            file_path = client.download_media(message.reply_to_message.voice or message.reply_to_message.audio)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_output:
                bass_file_path = temp_output.name
            
            try:
                process_audio(file_path, bass_file_path, "bass=g=20")
                client.send_audio(message.chat.id, bass_file_path)
            except subprocess.CalledProcessError as e:
                message.reply_text(f"Error processing audio: {e}")
            finally:
                os.remove(file_path)
                os.remove(bass_file_path)
        else:
            message.reply_text("Please reply to a voice message or audio file to use this command.")

    @app.on_message(filters.command("earrape", prefixes="."))
    def earrape(client, message):
        if message.reply_to_message and (message.reply_to_message.voice or message.reply_to_message.audio):
            file_path = client.download_media(message.reply_to_message.voice or message.reply_to_message.audio)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_output:
                earrape_file_path = temp_output.name
            
            try:
                process_audio(file_path, earrape_file_path, "volume=10")
                client.send_audio(message.chat.id, earrape_file_path)
            except subprocess.CalledProcessError as e:
                message.reply_text(f"Error processing audio: {e}")
            finally:
                os.remove(file_path)
                os.remove(earrape_file_path)
        else:
            message.reply_text("Please reply to a voice message or audio file to use this command.")

    @app.on_message(filters.command("volume", prefixes="."))
    def change_volume(client, message):
        if message.reply_to_message and (message.reply_to_message.voice or message.reply_to_message.audio):
            command_params = message.text.split()
            if len(command_params) != 2:
                message.reply_text("Usage: .volume <level>\nExample: .volume 1.5")
                return

            try:
                volume_level = float(command_params[1])
            except ValueError:
                message.reply_text("Invalid volume level. Please provide a number.")
                return

            file_path = client.download_media(message.reply_to_message.voice or message.reply_to_message.audio)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_output:
                volume_file_path = temp_output.name
            
            try:
                process_audio(file_path, volume_file_path, f"volume={volume_level}")
                client.send_audio(message.chat.id, volume_file_path)
            except subprocess.CalledProcessError as e:
                message.reply_text(f"Error processing audio: {e}")
            finally:
                os.remove(file_path)
                os.remove(volume_file_path)
        else:
            message.reply_text("Please reply to a voice message or audio file to use this command.")
