import time
import psutil
import platform
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler

BOT_START_TIME = datetime.now()

def get_bot_uptime():
    return str(datetime.now() - BOT_START_TIME).split('.')[0]

async def ping_command(client, message):
    start_time = time.time()
    response = await message.reply_text("🏓 Pong!")
    end_time = time.time()
    
    response_time = (end_time - start_time) * 1000
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    
    ping_text = f"""
🏓 **Pong!**

⚡️ **Відгук:** `{response_time:.2f} ms`
💻 **CPU:** `{cpu_percent}%`
🧠 **RAM:** `{memory.percent}%`
⏰ **Аптайм бота:** `{get_bot_uptime()}`
"""
    await response.edit_text(ping_text)

async def fast_ping_command(client, message):
    start_time = time.time()
    response = await message.reply_text("🏓")
    end_time = time.time()
    
    response_time = (end_time - start_time) * 1000
    await response.edit_text(f"🏓 **{response_time:.2f} ms**")

async def detailed_ping_command(client, message):
    start_time = time.time()
    response = await message.reply_text("🔍 Збираю детальну інформацію...")
    
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_freq = psutil.cpu_freq()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    system_uptime = datetime.now() - boot_time
    
    net_io = psutil.net_io_counters()
    
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    
    freq_text = f"`{cpu_freq.current:.0f} MHz`" if cpu_freq else "`N/A`"

    detailed_text = f"""
🔍 **Детальний статус системи**

⚡️ **Відгук:** `{response_time:.2f} ms`

**Система:**
• **OS:** `{platform.system()} {platform.release()}`
• **Архітектура:** `{platform.architecture()[0]}`
• **Аптайм системи:** `{str(system_uptime).split('.')[0]}`
• **Аптайм бота:** `{get_bot_uptime()}`

**Процесор (CPU):**
• **Використання:** `{cpu_percent}%`
• **Ядра:** `{psutil.cpu_count(logical=False)} фізичних / {psutil.cpu_count(logical=True)} логічних`
• **Частота:** {freq_text}

**Пам'ять (RAM):**
• **Використано:** `{memory.used // 1024**2} MB / {memory.total // 1024**2} MB ({memory.percent}%)`

**Диск:**
• **Використано:** `{disk.used // 1024**3} GB / {disk.total // 1024**3} GB ({disk.percent}%)`

**Мережа:**
• **Надіслано:** `{net_io.bytes_sent / 1024**2:.2f} MB`
• **Отримано:** `{net_io.bytes_recv / 1024**2:.2f} MB`
"""
    await response.edit_text(detailed_text)

def register_handlers(app: Client):
    handlers_list = [
        MessageHandler(ping_command, filters.command("ping", prefixes=".") & filters.me),
        MessageHandler(fast_ping_command, filters.command("fastping", prefixes=".") & filters.me),
        MessageHandler(detailed_ping_command, filters.command("detailedping", prefixes=".") & filters.me)
    ]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list