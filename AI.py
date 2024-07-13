from pyrogram import Client, filters
from g4f.client import Client as G4FClient

def add_on_commands(app: Client):
    g4f_client = G4FClient()

    @app.on_message(filters.command("ask", prefixes="."))
    def ask_gpt(client, message):
        query = ' '.join(message.command[1:])
        if not query:
            message.reply_text("Please provide a query after the command.")
            return
        
        try:
            response = g4f_client.chat.completions.create(
                model="gemini",
                messages=[{"role": "user", "content": query}]
            )
            reply_text = response.choices[0].message.content
        except Exception as e:
            reply_text = f"Error: {str(e)}"
        
        message.reply_text(reply_text)