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

def send_to_discord_embed(description, filename):
    try:
        # DEĞİŞİKLİK: Link metinleri orijinal haline döndü, URL sabit kaldı
        static_telegram_link = "https://web.telegram.org/k/#@hanbot_never_die"
        
        embed_data = {
          "content": "@everyone",
          "embeds": [{
            "title": "🤖 Hanbot Update Watcher",
            "color": 3447003,
            "fields": [
              { "name": "✅ Status: New Version Detected", "value": "A new version of Hanbot has been released. Use the link below to download.", "inline": False },
              { "name": "📁 File Name", "value": f"`{filename}`", "inline": False },
              { "name": "📋 Release Notes", "value": description or "No specific notes provided.", "inline": False },
              { "name": "⬇️ Download Link", "value": f"[Click here to download from Telegram]({static_telegram_link})", "inline": False } # METİN DÜZELTİLDİ
            ],
            "footer": { "text": "Hanbot Watcher" },
            "timestamp": datetime.datetime.utcnow().isoformat()
          }]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=embed_data)
        if response.status_code >= 400: print(f"Discord Hata: {response.text}")
        else: print("Embed mesajı başarıyla Discord'a gönderildi.")
    except Exception as e: print(f"Hata: {e}")

async def main():
    print("SON TEST MODU BAŞLATILDI...")
    async with TelegramClient(StringSession(SESSION_STRING), 12345, 'dummy') as client:
        print(f"'{SOURCE_CHANNEL}' kanalına bağlanıldı...")
        
        message_to_process = None
        async for message in client.iter_messages(SOURCE_CHANNEL, limit=20):
            if message and message.document:
                print(f"İşlenecek mesaj bulundu. Mesaj ID: {message.id}")
                message_to_process = message
                break
        
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
            
            send_to_discord_embed(description_text, filename)
        else:
            print("Son 20 mesajda dosya içeren bir mesaj bulunamadı.")
            
    print("Test tamamlandı.")

if __name__ == "__main__":
    asyncio.run(main())
