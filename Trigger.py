from pyrogram import Client, filters
import json
import re

TRIGGER_FILE = "triggers.json"

def load_triggers():
    try:
        with open(TRIGGER_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_triggers(triggers):
    with open(TRIGGER_FILE, "w") as file:
        json.dump(triggers, file, indent=4)

def add_trigger(word, response_type, response):
    triggers = load_triggers()
    triggers[word] = {"type": response_type, "content": response}
    save_triggers(triggers)

def add_on_commands(app: Client):
    @app.on_message(filters.command("trigger", prefixes=".") & filters.reply)
    def add_trigger_command(client, message):
        if len(message.command) < 2:
            message.reply_text("Please specify the word for the trigger.")
            return
        
        trigger_word = message.command[1]
        if re.match(r"[\/\.\!]", trigger_word):
            message.reply_text("Sorry. I don't trigger on this.")
            return

        if message.reply_to_message:
            if message.reply_to_message.text:
                response_type = "text"
                response_content = message.reply_to_message.text
            elif message.reply_to_message.sticker:
                response_type = "sticker"
                response_content = message.reply_to_message.sticker.file_id
            elif message.reply_to_message.animation:
                response_type = "gif"
                response_content = message.reply_to_message.animation.file_id
            elif message.reply_to_message.photo:
                response_type = "photo"
                response_content = message.reply_to_message.photo.file_id
            elif message.reply_to_message.voice:
                response_type = "voice"
                response_content = message.reply_to_message.voice.file_id
            elif message.reply_to_message.video_note:
                response_type = "video_note"
                response_content = message.reply_to_message.video_note.file_id
            elif message.reply_to_message.video:
                response_type = "video"
                response_content = message.reply_to_message.video.file_id
            elif message.reply_to_message.audio:
                response_type = "audio"
                response_content = message.reply_to_message.audio.file_id
            else:
                message.reply_text("Unsupported message type.")
                return

            add_trigger(trigger_word, response_type, response_content)
            message.reply_text(f"Trigger added: '{trigger_word}' -> '{response_type}'")
        else:
            message.reply_text("Please reply to a message to set as the trigger response.")

    @app.on_message(filters.text & ~filters.command(["trigger"], prefixes="."))
    def trigger_handler(client, message):
        triggers = load_triggers()
        for word, response in triggers.items():
            if word in message.text.split():
                response_type = response["type"]
                response_content = response["content"]

                if response_type == "text":
                    message.reply_text(response_content)
                elif response_type == "sticker":
                    message.reply_sticker(response_content)
                elif response_type == "gif":
                    message.reply_animation(response_content)
                elif response_type == "photo":
                    message.reply_photo(response_content)
                elif response_type == "voice":
                    message.reply_voice(response_content)
                elif response_type == "video_note":
                    message.reply_video_note(response_content)
                elif response_type == "video":
                    message.reply_video(response_content)
                elif response_type == "audio":
                    message.reply_audio(response_content)

                break
