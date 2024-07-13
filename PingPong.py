from pyrogram import Client, filters
import time

def add_on_ping_command(app: Client):
    @app.on_message(filters.command("ping", prefixes="."))
    def ping_command(client, message):
        start_time = time.time()
        
        if message.from_user.is_self:
            response = message.edit_text("Pong!")
        else:
            response = message.reply_text("Pong!")
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        response.edit_text(f"Pong! Response time: {response_time:.2f} ms")
