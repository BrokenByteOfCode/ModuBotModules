import time
import psutil
import platform
from datetime import datetime, timedelta
from pyrogram import Client, filters

def register_handlers(app: Client):
    @app.on_message(filters.command("ping", prefixes="."))
    async def ping_command(client, message):
        start_time = time.time()
        
        if message.from_user.is_self:
            response = await message.edit_text("🏓 Pong!")
        else:
            response = await message.reply_text("🏓 Pong!")
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        ping_text = f"""🏓 **Pong!**

⚡ **Response Time:** {response_time:.2f} ms
💻 **CPU Usage:** {cpu_percent}%
🧠 **RAM Usage:** {memory.percent}%
⏰ **Bot Uptime:** {str(uptime).split('.')[0]}
🖥 **System:** {platform.system()} {platform.release()}
📡 **Python:** {platform.python_version()}"""

        await response.edit_text(ping_text)

    @app.on_message(filters.command("fastping", prefixes="."))
    async def fast_ping_command(client, message):
        start_time = time.time()
        
        if message.from_user.is_self:
            response = await message.edit_text("🏓")
        else:
            response = await message.reply_text("🏓")
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        await response.edit_text(f"🏓 **{response_time:.2f} ms**")

    @app.on_message(filters.command("detailedping", prefixes="."))
    async def detailed_ping_command(client, message):
        start_time = time.time()
        
        if message.from_user.is_self:
            response = await message.edit_text("🔍 Gathering detailed info...")
        else:
            response = await message.reply_text("🔍 Gathering detailed info...")
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        network = psutil.net_io_counters()
        bytes_sent_mb = network.bytes_sent / (1024 * 1024)
        bytes_recv_mb = network.bytes_recv / (1024 * 1024)
        
        processes = len(psutil.pids())
        
        detailed_text = f"""🔍 **Detailed System Status**

⚡ **Response Time:** {response_time:.2f} ms

🖥 **System Info:**
• OS: {platform.system()} {platform.release()}
• Architecture: {platform.architecture()[0]}
• Python: {platform.python_version()}
• Hostname: {platform.node()}

💻 **CPU:**  
• Usage: {cpu_percent}%
• Cores: {psutil.cpu_count()} ({psutil.cpu_count(logical=False)} physical)
{f"• Frequency: {cpu_freq.current:.0f} MHz" if cpu_freq else ""}

🧠 **Memory:**
• Used: {memory.used // (1024**2)} MB / {memory.total // (1024**2)} MB ({memory.percent}%)
• Available: {memory.available // (1024**2)} MB

💾 **Disk:**
• Used: {disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB ({disk.used/disk.total*100:.1f}%)
• Free: {disk.free // (1024**3)} GB

📡 **Network:**
• Sent: {bytes_sent_mb:.1f} MB
• Received: {bytes_recv_mb:.1f} MB

⚙️ **Other:**
• Running Processes: {processes}
• Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
• Uptime: {str(uptime).split('.')[0]}"""

        await response.edit_text(detailed_text)