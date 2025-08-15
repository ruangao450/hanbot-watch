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

def send_to_discord_embed(description, filename, message_link):
    try:
        # DÜZELTME: Artık dosya göndermiyoruz, link ekliyoruz.
        embed_data = {
          "embeds": [{
            "title": "🛡️ Hanbot Version Watch",
            "color": 3447003,
            "fields": [
              { "name": "✅ Status: New Version Detected", "value": "A new version of Hanbot has been released. Click the link below to download from Telegram.", "inline": False },
              { "name": "📁 File Name", "value": f"`{filename}`", "inline": False },
              { "name": "📋 Release Notes", "value": description or "No specific notes provided.", "inline": False }
            ],
            "footer": { "text": "Hanbot Watcher" },
            "timestamp": datetime.datetime.utcnow().isoformat()
          }],
          "components": [ # Buton ekleme
            {
              "type": 1,
              "components": [
                {
                  "type": 2,
                  "label": "Download from Telegram",
                  "style": 5, # Link stili
                  "url": message_link
                }
              ]
            }
          ]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=embed_data)
        if response.status_code >= 400: print(f"Discord Hata: {response.text}")
        else: print("Embed mesajı başarıyla Discord'a gönderildi.")
    except Exception as e: print(f"Hata: {e}")

async def main():
    print("Normal mod başlatıldı: Son 5 dakikadaki yeni mesajlar kontrol edilecek...")
    async with TelegramClient(StringSession(SESSION_STRING), 12345, 'dummy') as client:
        print(f"'{SOURCE_CHANNEL}' kanalı kontrol ediliyor...")
        time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=6)

        async for message in client.iter_messages(SOURCE_CHANNEL, limit=10):
            if message.date > time_threshold and message.document:
                filename = message.document.attributes[-1].file_name
                description_text = message.text
                print(f"Yeni dosya bulundu: {filename}")

                # DÜZELTME: Mesaj linkini oluşturma
                message_link = f"https://t.me/{SOURCE_CHANNEL}/{message.id}"

                match = re.search(r'\((\d{2,}\.\d{2,}\.\d{3,}\.\d{4,})\)', description_text)
                if match:
                    version = match.group(1)
                    print(f"Versiyon numarası bulundu: {version}")
                    update_voice_channel_name(version)
                else:
                    print("Mesajda versiyon numarası bulunamadı.")
                
                send_to_discord_embed(description_text, filename, message_link)
            elif message.date <= time_threshold:
                print("Daha eski mesajlara ulaşıldı, kontrol durduruluyor.")
                break
    print("İşlem tamamlandı.")

if __name__ == "__main__":
    asyncio.run(main())
