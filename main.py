import subprocess
import sys

# Gerekli kütüphaneleri yükle
try:
    import telethon
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "telethon", "requests"])

import os
import asyncio
import json
import datetime
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import requests

# Bu Pipedream'in ana fonksiyonudur
async def handler(pd: "pipedream"):
    # --- Bağlı Hesaptan Sırları Çekme ---
    secrets = pd.inputs["pipedream_secrets_1"]["$auth"]
    
    SESSION_STRING = secrets["TELEGRAM_SESSION_STRING"]
    SOURCE_CHANNEL = secrets["TELEGRAM_SOURCE_CHANNEL"]
    DISCORD_WEBHOOK_URL = secrets["DISCORD_WEBHOOK_URL"]
    DISCORD_BOT_TOKEN = secrets["DISCORD_BOT_TOKEN"]
    VOICE_CHANNEL_ID = secrets["VOICE_CHANNEL_ID"]
    
    DUMMY_API_ID = 12345
    DUMMY_API_HASH = 'dummy'

    client = TelegramClient(StringSession(SESSION_STRING), DUMMY_API_ID, DUMMY_API_HASH)

    def update_voice_channel_name(version_number):
        """Discord ses kanalının adını günceller."""
        url = f"https://discord.com/api/v10/channels/{VOICE_CHANNEL_ID}"
        new_name = f"✅ Updated: {version_number}"
        
        headers = {
            "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": new_name
        }
        
        try:
            response = requests.patch(url, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"Ses kanalı adı başarıyla güncellendi: {new_name}")
            else:
                print(f"Kanal adı güncellenirken hata oluştu: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"API isteği sırasında hata: {e}")

    @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
    async def message_handler(event):
        message = event.message
        if message.document:
            filename = message.document.attributes[-1].file_name
            description_text = message.text
            print(f"Dosya bulundu: {filename}")
            
            # Versiyon numarasını mesajdan çek
            match = re.search(r'\((\d{2,}\.\d{2,}\.\d{3,}\.\d{4,})\)', description_text)
            if match:
                version = match.group(1)
                print(f"Versiyon numarası bulundu: {version}")
                update_voice_channel_name(version)
            else:
                print("Mesajda versiyon numarası bulunamadı.")
            
            file_path = await message.download_media(file="/tmp/")
            send_to_discord_embed(DISCORD_WEBHOOK_URL, description_text, filename, file_path)

    def send_to_discord_embed(webhook_url, description, filename, file_path):
        # Bu fonksiyon değişmedi, embed mesajını gönderir
        try:
            embed_data = { "embeds": [{ "title": "🛡️ Hanbot Version Watch", "color": 3447003, "fields": [{ "name": "✅ Status: New Version Detected", "value": "A new version of Hanbot has been released. The update file is attached below.", "inline": False }, { "name": "📁 File Name", "value": f"`{filename}`", "inline": False }, { "name": "📋 Release Notes", "value": description or "No specific notes provided.", "inline": False }], "footer": { "text": "Hanbot Watcher" }, "timestamp": datetime.datetime.utcnow().isoformat() }] }
            files = {'file': (os.path.basename(file_path), open(file_path, 'rb'))}
            payload = {'payload_json': json.dumps(embed_data)}
            response = requests.post(webhook_url, data=payload, files=files)
            if response.status_code >= 400: print(f"Discord Hata: {response.text}")
            else: print("Embed mesajı başarıyla Discord'a gönderildi.")
        except Exception as e: print(f"Hata: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)

    # Botu başlat ve sürekli dinlemede kal
    print("Bot giriş anahtarı ile başlatılıyor...")
    await client.start()
    print(f"Telegram'a başarıyla bağlanıldı. '{SOURCE_CHANNEL}' kanalı dinleniyor...")
    await client.run_until_disconnected()
