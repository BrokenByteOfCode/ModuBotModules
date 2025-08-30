# module_logic.py
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from gradio_client import Client as GradioClient
import random
import requests
import os

IMAGE_MODELS = {
    "sd35-large": {
        "space": "stabilityai/stable-diffusion-3.5-large",
        "display_name": "Stable Diffusion 3.5 Large"
    },
    "flux-schnell": {
        "space": "black-forest-labs/FLUX.1-schnell",
        "display_name": "FLUX.1 Schnell"
    },
    "sd21": {
        "space": "stabilityai/stable-diffusion",
        "display_name": "Stable Diffusion 2.1"
    }
}

async def generate_image_command(client: Client, message: Message):
    if len(message.command) < 2:
        model_list = "\n".join([f"• {key}: {info['display_name']}" for key, info in IMAGE_MODELS.items()])
        await message.reply_text(
            f"Будь ласка, вкажіть опис зображення.\n\n"
            f"**Використання:**\n"
            f"`.img опис_зображення` - генерує з випадковою моделлю\n"
            f"`.img модель опис_зображення` - генерує з конкретною моделлю\n\n"
            f"**Доступні моделі:**\n{model_list}\n\n"
            f"**Приклади:**\n"
            f"`.img cute cat in space`\n"
            f"`.img flux-schnell beautiful sunset over mountains`"
        )
        return

    args = message.text.split(maxsplit=2)
    
    if args[1] in IMAGE_MODELS:
        model_key = args[1]
        if len(args) < 3:
            await message.reply_text("Будь ласка, вкажіть опис зображення після назви моделі.")
            return
        prompt = args[2]
    else:
        model_key = random.choice(list(IMAGE_MODELS.keys()))
        prompt = message.text.split(maxsplit=1)[1]
    
    model_info = IMAGE_MODELS[model_key]
    
    status_msg = await message.reply_text(
        f"🎨 Генерую зображення...\n"
        f"📝 Опис: `{prompt}`\n"
        f"🤖 Модель: {model_info['display_name']}"
    )
    
    try:
        gradio_client = GradioClient(model_info['space'])
        
        if model_key == "sd35-large":
            result = gradio_client.predict(
                prompt=prompt,
                negative_prompt="blurry, low quality, distorted",
                seed=random.randint(0, 1000000),
                randomize_seed=True,
                width=512,
                height=512,
                guidance_scale=4.5,
                num_inference_steps=40,
                api_name="/infer"
            )
        elif model_key == "flux-schnell":
            result = gradio_client.predict(
                prompt=prompt,
                seed=random.randint(0, 1000000),
                randomize_seed=True,
                width=512,
                height=512,
                num_inference_steps=4,
                api_name="/infer"
            )
        elif model_key == "sd21":
            result = gradio_client.predict(
                prompt=prompt,
                negative="blurry, low quality, distorted",
                scale=9,
                api_name="/infer"
            )
        
        image_path = result[0] if isinstance(result, list) else result
        
        if isinstance(image_path, dict) and 'url' in image_path:
            image_url = image_path['url']
            if not image_url.startswith('http'):
                image_url = f"https://stabilityai-stable-diffusion-3-5-large.hf.space{image_url}"
            
            response = requests.get(image_url)
            response.raise_for_status()
            
            temp_file = f"/tmp/generated_image_{random.randint(1000, 9999)}.webp"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            image_path = temp_file
        
        elif isinstance(image_path, str) and not os.path.exists(image_path):
            if image_path.startswith('/file='):
                image_url = f"https://stabilityai-stable-diffusion-3-5-large.hf.space{image_path}"
                response = requests.get(image_url)
                response.raise_for_status()
                
                temp_file = f"/tmp/generated_image_{random.randint(1000, 9999)}.webp"
                with open(temp_file, 'wb') as f:
                    f.write(response.content)
                image_path = temp_file
        
        username = message.from_user.username or message.from_user.first_name
        caption = f"@{username} | {model_info['display_name']}"
        
        await client.send_photo(
            chat_id=message.chat.id,
            photo=image_path,
            caption=caption,
            reply_to_message_id=message.id
        )
        
        if image_path.startswith('/tmp/'):
            try:
                os.remove(image_path)
            except:
                pass
        
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(
            f"❌ Помилка при генерації зображення:\n`{str(e)}`\n\n"
            f"Спробуйте ще раз або використайте іншу модель."
        )

async def list_models_command(client: Client, message: Message):
    models_info = []
    for key, info in IMAGE_MODELS.items():
        models_info.append(f"🎯 **{key}**\n   └ {info['display_name']}")
    
    models_text = "\n\n".join(models_info)
    
    await message.reply_text(
        f"🤖 **Доступні моделі для генерації зображень:**\n\n"
        f"{models_text}\n\n"
        f"**Використання:**\n"
        f"`.img модель опис` або просто `.img опис` для випадкової моделі"
    )

def register_handlers(app: Client):
    
    img_handler = MessageHandler(
        generate_image_command,
        filters.command(["img", "image", "generate"], prefixes=".")
    )
    
    models_handler = MessageHandler(
        list_models_command,
        filters.command(["models", "imgmodels"], prefixes=".")
    )

    handlers_list = [img_handler, models_handler]

    for handler in handlers_list:
        app.add_handler(handler)
        
    return handlers_list