import os
import asyncio
import json
import datetime
import re
from telethon import TelegramClient
from telethon.sessions import StringSession
import requests

# GitHub Secrets'dan bilgileri çek
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')
SOURCE_CHANNEL = os.getenv('TELEGRAM_SOURCE_CHANNEL')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
VOICE_CHANNEL_ID = os.getenv('VOICE_CHANNEL_ID')

# --- ÖNEMLİ KONTROL ---
# Sırların (secrets) yüklenip yüklenmediğini kontrol edelim.
if not all([SESSION_STRING, SOURCE_CHANNEL, DISCORD_WEBHOOK_URL, DISCORD_BOT_TOKEN, VOICE_CHANNEL_ID]):
    print("HATA: GitHub Secrets'daki değişkenlerden biri veya birkaçı eksik! Lütfen kontrol edin.")
    exit() # Hata varsa programı durdur

def update_voice_channel_name(version_number):
    url = f"https://discord.com/api/v10/channels/{VOICE_CHANNEL_ID}"
    new_name = f"✅ Updated: {version_number}"
    headers = { "Authorization": f"Bot {DISCORD_BOT_TOKEN}", "Content-Type": "application/json" }
    payload = { "name": new_name }
    try:
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code == 200: print(f"Ses kanalı adı başarıyla güncellendi: {new_name}")
        else: print(f"Kanal adı güncellenirken hata oluştu: {response.status_code} - {response.text}")
    except Exception as e: print(f"API isteği sırasında hata: {e}")

def send_to_discord_embed(description, filename, file_path):
    try:
        embed_data = { "embeds": [{ "title": "🛡️ Hanbot Version Watch (TEST)", "color": 3447003, "fields": [{ "name": "✅ Status: New Version Detected", "value": "This is a test message processing the last available update.", "inline": False }, { "name": "📁 File Name", "value": f"`{filename}`", "inline": False }, { "name": "📋 Release Notes", "value": description or "No specific notes provided.", "inline": False }], "footer": { "text": "Hanbot Watcher" }, "timestamp": datetime.datetime.utcnow().isoformat() }] }
        files = {'file': (os.path.basename(file_path), open(file_path, 'rb'))}
        payload = {'payload_json': json.dumps(embed_data)}
        response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
        if response.status_code >= 400: print(f"Discord Hata: {response.text}")
        else: print("Embed mesajı başarıyla Discord'a gönderildi.")
    except Exception as e: print(f"Hata: {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)

async def main():
    print("TEST MODU BAŞLATILDI: Son dosya içeren mesaj aranıyor...")
    async with TelegramClient(StringSession(SESSION_STRING), 12345, 'dummy') as client:
        print(f"'{SOURCE_CHANNEL}' kanalına bağlanıldı...")
        
        message_to_process = None
        # Son 20 mesajı kontrol et, dosya içeren ilkini bul
        async for message in client.iter_messages(SOURCE_CHANNEL, limit=20):
            if message and message.document:
                print(f"İşlenecek mesaj bulundu. Mesaj ID: {message.id}")
                message_to_process = message
                break # Mesajı bulduk, aramayı durdur
        
        if message_to_process:
            filename = message_to_process.document.attributes[-1].file_name
            description_text = message_to_process.text
            print(f"Test için dosya işleniyor: {filename}")

            match = re.search(r'\((\d{2,}\.\d{2,}\.\d{3,}\.\d{4,})\)', description_text)
            if match:
                version = match.group(1)
                print(f"Versiyon numarası bulundu: {version}")
                update_voice_channel_name(version)
            else:
                print("Mesajda versiyon numarası bulunamadı.")
            
            file_path = await message_to_process.download_media(file="./")
            send_to_discord_embed(description_text, filename, file_path)
        else:
            print("Son 20 mesajda dosya içeren bir mesaj bulunamadı.")
            
    print("Test tamamlandı.")

if __name__ == "__main__":
    asyncio.run(main())
