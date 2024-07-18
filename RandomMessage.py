from pyrogram import Client, filters
import random

# File to store all messages
MESSAGE_FILE = "AllMessagesFromAllChat.txt"

def add_commands(app: Client):
    """
    Add command handlers to the Pyrogram Client.
    
    This function demonstrates how to create a modular structure for your Pyrogram bot.
    Each command is defined as a separate function within this module.
    
    Args:
        app (Client): The Pyrogram Client instance.
    """
    
    @app.on_message(filters.command("random", prefixes="."))
    def random_message_command(client, message):
        """Handle the .random command by sending a random message from the file"""
        try:
            with open(MESSAGE_FILE, 'r') as file:
                lines = file.readlines()
            if lines:
                random_line = random.choice(lines).strip()
                message.reply_text(random_line)
            else:
                message.reply_text("The message file is empty.")
        except FileNotFoundError:
            message.reply_text("The message file does not exist.")
    
    @app.on_message(filters.text & ~filters.command)
    def save_message(client, message):
        """Save all text messages into the file"""
        with open(MESSAGE_FILE, 'a') as file:
            file.write(f"{message.text}\n")
